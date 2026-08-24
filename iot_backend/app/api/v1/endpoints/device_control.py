"""设备远程控制：注册、属性、sync/read/write/action/setting"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.crud.device import device_crud
from app.db.session import get_db
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


def _get_owned_device(db: Session, device_id: str, user: User):
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    if not user.is_superuser and device.owner_id != user.id:
        raise HTTPException(status_code=403, detail="权限不足")
    return device


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
    """设备注册/自动建档"""
    body = body or DeviceRegisterRequest()
    return device_runtime.register(
        db,
        device_id,
        product_id=body.product_id,
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
    _get_owned_device(db, device_id, current_user)
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
    device = _get_owned_device(db, device_id, current_user)
    return {"device_id": device_id, "response": _mqtt_call(device, "sync", {})}


@router.post("/{device_id}/read")
def read_device_points(
    device_id: str,
    body: DeviceReadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = _get_owned_device(db, device_id, current_user)
    resp = _mqtt_call(device, "read", {"points": body.points})
    return {"device_id": device_id, "response": resp}


@router.post("/{device_id}/write")
def write_device_points(
    device_id: str,
    body: DeviceWriteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = _get_owned_device(db, device_id, current_user)
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
    device = _get_owned_device(db, device_id, current_user)
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
    device = _get_owned_device(db, device_id, current_user)
    resp = _mqtt_call(device, "setting", {"name": name, "data": body.data})
    return {"device_id": device_id, "setting": name, "response": resp}
