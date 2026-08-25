"""设备远程控制：注册、属性、sync/read/write/action/setting、历史、网关下发"""
import json
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.crud.device import device_crud, device_data_crud
from app.crud.group import binding_crud, job_crud, scene_crud, script_crud
from app.db.session import get_db
from app.services import access_control as access
from app.services.timeseries import timeseries
from app.schemas.device import (
    Device,
    DeviceActionRequest,
    DeviceReadRequest,
    DeviceRegisterRequest,
    DeviceSettingRequest,
    DeviceWriteRequest,
)
from app.schemas.user import User
from app.services.device_runtime_service import device_runtime
from app.services.mqtt_service import mqtt_client

router = APIRouter()


def _get_owned_device(db: Session, device_id: str, user: User, min_role: str = "viewer"):
    return access.load_device(db, user, device_id, min_role)


def _mysql_series(db, device, wanted, start, end, limit) -> dict:
    if start and end:
        rows = device_data_crud.get_data_by_time_range(db, device.id, start, end)
    else:
        rows = list(reversed(device_data_crud.get_device_data(db, device.id, limit=limit)))
    series: dict = {}
    for row in rows:
        data = row.data or {}
        ts = row.timestamp.isoformat() if row.timestamp else None
        for key, value in data.items():
            if wanted and key not in wanted:
                continue
            if not isinstance(value, (int, float)):
                continue
            series.setdefault(key, []).append([ts, value])
    return series


def _mqtt_call(device, action: str, payload: dict) -> dict:
    if not mqtt_client.connected:
        raise HTTPException(status_code=503, detail="MQTT 未连接，无法下发控制")
    try:
        return device_runtime.request(mqtt_client.publish, device, action, payload)
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc))


@router.post("/{device_id}/register", response_model=Device)
def register_device(
    device_id: str,
    body: Optional[DeviceRegisterRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """设备注册/自动建档（需产品或设备 operator 权限）"""
    body = body or DeviceRegisterRequest()
    product_id = body.product_id or "default"
    existing = device_crud.get_by_device_id(db, device_id)
    if existing:
        access.ensure_device(db, current_user, existing, "operator")
    else:
        access.ensure_product(db, current_user, product_id, "operator")
    return device_runtime.register(
        db,
        device_id,
        product_id=product_id,
        device_name=body.device_name,
        gateway_id=body.gateway_id,
    )


@router.get("/{device_id}/values")
def get_device_values(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取设备最新属性快照"""
    device = _get_owned_device(db, device_id, current_user)
    return {"device_id": device_id, "values": device.values or {}, "status": device.status}


@router.post("/{device_id}/values")
def put_device_values(
    device_id: str,
    body: DeviceWriteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """属性上报（走 Validators 告警链路）"""
    _get_owned_device(db, device_id, current_user, "operator")
    device = device_runtime.put_values(
        db, device_id, body.values, publish_alarm=mqtt_client._publish_alarm
    )
    return {"device_id": device_id, "values": device.values}


@router.get("/{device_id}/sync")
def sync_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = _get_owned_device(db, device_id, current_user, "operator")
    return {"device_id": device_id, "response": _mqtt_call(device, "sync", {})}


@router.post("/{device_id}/read")
def read_device_points(
    device_id: str,
    body: DeviceReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = _get_owned_device(db, device_id, current_user, "operator")
    resp = _mqtt_call(device, "read", {"points": body.points})
    return {"device_id": device_id, "response": resp}


@router.post("/{device_id}/write")
def write_device_points(
    device_id: str,
    body: DeviceWriteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = _get_owned_device(db, device_id, current_user, "operator")
    resp = _mqtt_call(device, "write", {"values": body.values})
    return {"device_id": device_id, "response": resp}


@router.post("/{device_id}/action/{action}")
def invoke_device_action(
    device_id: str,
    action: str,
    body: Optional[DeviceActionRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = _get_owned_device(db, device_id, current_user, "operator")
    body = body or DeviceActionRequest()
    resp = _mqtt_call(device, "action", {"action": action, "params": body.params or {}})
    return {"device_id": device_id, "action": action, "response": resp}


@router.post("/{device_id}/setting/{name}")
def push_device_setting(
    device_id: str,
    name: str,
    body: DeviceSettingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = _get_owned_device(db, device_id, current_user, "operator")
    resp = _mqtt_call(device, "setting", {"name": name, "data": body.data})
    return {"device_id": device_id, "setting": name, "response": resp}


@router.get("/{device_id}/history")
def device_history(
    device_id: str,
    points: Optional[str] = Query(None, description="逗号分隔的测点名"),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """时序历史：Influx 为唯一遥测库；未启用时才读 MySQL 遗留数据"""
    device = _get_owned_device(db, device_id, current_user, "viewer")
    wanted = [p.strip() for p in (points or "").split(",") if p.strip()]
    series = timeseries.query_series(device.device_id, start, end, wanted, limit)
    if timeseries.enabled:
        return {
            "device_id": device_id,
            "series": series or {},
            "count": sum(len(v) for v in (series or {}).values()),
            "source": "influx",
        }
    series = _mysql_series(db, device, wanted, start, end, limit)
    count = sum(len(v) for v in series.values())
    return {"device_id": device_id, "series": series, "count": count, "source": "mysql"}


DOWNLOAD_LOADERS = {
    "scene": lambda db, gid: [s.__dict__ for s in scene_crud.get_multi(db, gateway_id=gid, limit=500)],
    "job": lambda db, gid: [s.__dict__ for s in job_crud.get_multi(db, gateway_id=gid, limit=500)],
    "binding": lambda db, gid: [s.__dict__ for s in binding_crud.get_multi(db, gateway_id=gid, limit=500)],
    "script": lambda db, gid: [s.__dict__ for s in script_crud.get_multi(db, gateway_id=gid, limit=500)],
}


def _clean_row(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_")}


@router.get("/{device_id}/download/{database}")
def download_to_gateway(
    device_id: str,
    database: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """将场景/定时/联动/脚本配置经 MQTT 下发到网关"""
    device = _get_owned_device(db, device_id, current_user, "operator")
    loader = DOWNLOAD_LOADERS.get(database)
    if not loader:
        raise HTTPException(status_code=400, detail="不支持的配置类型")
    items = [_clean_row(r) for r in loader(db, device_id)]
    topic = f"device/{device.device_id}/download/{database}"
    mqtt_client.publish(topic, json.dumps({"database": database, "items": items}, default=str))
    return {"device_id": device_id, "database": database, "count": len(items), "topic": topic}


@router.post("/{device_id}/meter/switch")
def meter_switch(
    device_id: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """DL/T645 拉合闸"""
    device = _get_owned_device(db, device_id, current_user, "operator")
    close_sw = bool(body.get("close", True))
    meta = device.device_metadata or {}
    address = body.get("address") or meta.get("address") or meta.get("meter")
    msg_id = str(uuid.uuid4())
    payload = {
        "msg_id": msg_id,
        "device_id": device_id,
        "action": "switch",
        "close": close_sw,
        "address": address,
        "params": {"close": close_sw, "address": address},
    }
    mqtt_client.publish(device_runtime._target_topic(device, "action"), json.dumps(payload))
    if device.link_id:
        from app.crud.link import link_crud
        from app.services.dlt645_plugin import dlt645_plugin

        link = link_crud.get_by_link_id(db, device.link_id)
        linker = (link.linker if link else None) or "tcp-client"
        dlt645_plugin.on_protocol(
            f"protocol/dlt645/{linker}/{device.link_id}/action",
            json.dumps({
                "device_id": device_id,
                "address": address,
                "close": close_sw,
                "msg_id": msg_id,
            }).encode(),
        )
    return {"device_id": device_id, "close": close_sw, "accepted": True, "msg_id": msg_id}
