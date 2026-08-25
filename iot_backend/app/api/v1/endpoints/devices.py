"""
设备管理API端点
"""
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.db.session import get_db
from app.crud.device import device_crud, device_data_crud, device_command_crud
from app.schemas.user import User
from app.core.dependencies import get_current_active_user
from app.services import access_control as access
from app.services.mqtt_service import mqtt_client
from app.crud.product import product_crud
from app.schemas.device import (
    Device, DeviceCreate, DeviceUpdate,
    DeviceDataCreate, DeviceData,
    DeviceCommand, DeviceCommandCreate
)
from pydantic import BaseModel


class DeviceImportItem(BaseModel):
    device_id: str
    device_name: str
    product_id: str
    gateway_id: Optional[str] = None
    group_id: Optional[int] = None


class DeviceImportBody(BaseModel):
    devices: List[DeviceImportItem]

router = APIRouter()


@router.get("/", response_model=List[Device])
def read_devices(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[str] = Query(None),
    gateway_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取设备列表"""
    return access.list_visible_devices(
        db, current_user, skip=skip, limit=limit,
        product_id=product_id, gateway_id=gateway_id,
    )


@router.post("/", response_model=Device, status_code=status.HTTP_201_CREATED)
def create_device(
    *,
    db: Session = Depends(get_db),
    device_in: DeviceCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """创建新设备"""
    device = device_crud.get_by_device_id(db, device_id=device_in.device_id)
    if device:
        raise HTTPException(status_code=400, detail="设备ID已存在")

    product = product_crud.get_by_product_id(db, device_in.product_id)
    if product:
        access.ensure_product(db, current_user, device_in.product_id, "operator")
    if not current_user.is_superuser and not device_in.owner_id:
        device_in.owner_id = current_user.id

    device = device_crud.create(db, device_in)
    return device


@router.get("/status/online", response_model=List[Device])
def get_online_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取所有在线设备"""
    query = access.visible_device_query(db, current_user)
    from app.db.models.device import Device as DeviceModel
    return query.filter(DeviceModel.status == "online").all()


@router.get("/export")
def export_devices(
    db: Session = Depends(get_db),
    product_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """导出设备 JSON"""
    devices = access.list_visible_devices(
        db, current_user, skip=0, limit=10000, product_id=product_id,
    )
    payload = [
        {
            "device_id": d.device_id,
            "device_name": d.device_name,
            "product_id": d.product_id,
            "gateway_id": d.gateway_id,
            "group_id": d.group_id,
            "status": d.status,
            "latitude": d.latitude,
            "longitude": d.longitude,
        }
        for d in devices
    ]
    return {"count": len(payload), "devices": payload}


@router.post("/import")
def import_devices(
    *,
    db: Session = Depends(get_db),
    body: DeviceImportBody,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """批量导入设备"""
    created, skipped = [], []
    for item in body.devices:
        if device_crud.get_by_device_id(db, device_id=item.device_id):
            skipped.append(item.device_id)
            continue
        obj = DeviceCreate(**item.model_dump())
        product = product_crud.get_by_product_id(db, obj.product_id)
        if product:
            access.ensure_product(db, current_user, obj.product_id, "operator")
        if not current_user.is_superuser and not obj.owner_id:
            obj.owner_id = current_user.id
        device_crud.create(db, obj)
        created.append(item.device_id)
    return {"created": created, "skipped": skipped, "created_count": len(created)}


@router.get("/{device_id}", response_model=Device)
def read_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """根据设备ID获取设备"""
    return access.load_device(db, current_user, device_id, "viewer")


@router.put("/{device_id}", response_model=Device)
def update_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    device_in: DeviceUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """更新设备信息"""
    device = access.load_device(db, current_user, device_id, "operator")
    device = device_crud.update(db, db_obj=device, obj_in=device_in)
    return device


@router.delete("/{device_id}", response_model=Device)
def delete_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """删除设备"""
    device = access.load_device(db, current_user, device_id, "admin")
    device = device_crud.delete(db, id=device.id)
    return device


@router.post("/{device_id}/data", response_model=DeviceData, status_code=status.HTTP_201_CREATED)
def create_device_data(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    data_in: DeviceDataCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """创建设备数据"""
    access.load_device(db, current_user, device_id, "operator")
    data_in.device_id = device_id
    device_data = device_data_crud.create(db, obj_in=data_in)
    if device_data:
        return device_data
    from datetime import datetime
    from app.services.timeseries import timeseries
    if timeseries.enabled:
        return {
            "id": 0,
            "device_id": 0,
            "timestamp": datetime.utcnow(),
            "data_type": data_in.data_type,
            "data": data_in.data,
            "quality": data_in.quality or "good",
            "created_at": datetime.utcnow(),
        }
    raise HTTPException(status_code=500, detail="创建设备数据失败")


@router.get("/{device_id}/data", response_model=List[DeviceData])
def read_device_data(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取设备数据列表（遥测来自 Influx）"""
    device = access.load_device(db, current_user, device_id, "viewer")
    from app.services.timeseries import timeseries
    if timeseries.enabled:
        rows = timeseries.query_rows(device.device_id, limit=limit)
        from datetime import datetime
        out = []
        for i, row in enumerate(rows[skip:skip + limit]):
            ts = row.get("timestamp")
            try:
                parsed = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.utcnow()
            except Exception:
                parsed = datetime.utcnow()
            out.append({
                "id": i + skip + 1,
                "device_id": device.id,
                "timestamp": parsed,
                "data_type": "property",
                "data": row.get("data") or {},
                "quality": "good",
                "created_at": parsed,
            })
        return out
    return device_data_crud.get_device_data(db, device_id=device.id, skip=skip, limit=limit)


@router.get("/{device_id}/track")
def read_device_track(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    limit: int = Query(200, le=500),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """设备定位轨迹"""
    device = access.load_device(db, current_user, device_id, "viewer")

    rows = []
    from app.services.timeseries import timeseries
    if timeseries.enabled:
        for row in timeseries.query_rows(device.device_id, data_type="location", limit=limit):
            rows.append(type("R", (), {"data": row.get("data"), "timestamp": row.get("timestamp")})())
    else:
        rows = device_data_crud.get_location_track(db, device_id=device.id, limit=limit)
    points = []
    for row in rows:
        data = row.data or {}
        lat = data.get("latitude") or data.get("lat")
        lng = data.get("longitude") or data.get("lng") or data.get("lon")
        if lat is None or lng is None:
            continue
        points.append({
            "timestamp": row.timestamp,
            "latitude": float(lat),
            "longitude": float(lng),
            "geo_code": data.get("geo_code"),
        })
    if device.latitude is not None and device.longitude is not None:
        if not points or points[-1]["latitude"] != device.latitude:
            points.append({
                "timestamp": device.updated_at or device.last_online_at,
                "latitude": device.latitude,
                "longitude": device.longitude,
                "geo_code": device.geo_code,
                "current": True,
            })
    return {"device_id": device_id, "points": points}


@router.post("/{device_id}/commands", response_model=DeviceCommand, status_code=status.HTTP_201_CREATED)
def send_device_command(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    command_in: DeviceCommandCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """发送设备命令"""
    access.load_device(db, current_user, device_id, "operator")
    command_in.device_id = device_id

    # 创建命令记录
    command = device_command_crud.create(db, obj_in=command_in, created_by=current_user.id)
    if not command:
        raise HTTPException(status_code=500, detail="创建命令失败")

    # 通过MQTT发送命令
    try:
        topic = f"device/{device_id}/command"
        payload = {
            "command_id": command.id,
            "command_type": command.command_type,
            "command_data": command.command_data
        }
        mqtt_client.publish(topic=topic, payload=json.dumps(payload))

        # 更新命令状态为已发送
        device_command_crud.update_status(db, command.id, "sent")
    except Exception as e:
        # 如果发送失败，更新状态
        device_command_crud.update_status(db, command.id, "failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"发送命令失败: {str(e)}")

    return command


@router.get("/{device_id}/commands", response_model=List[DeviceCommand])
def get_device_commands(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取设备待处理命令"""
    access.load_device(db, current_user, device_id, "viewer")
    commands = device_command_crud.get_pending_commands(db, device_id=device_id)
    return commands


@router.post("/{device_id}/control", status_code=status.HTTP_202_ACCEPTED)
async def control_device(
    device_id: str,
    command: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """发送控制指令到设备"""
    access.load_device(db, current_user, device_id, "operator")

    # 发布控制指令到MQTT主题
    topic = f"device/{device_id}/control"
    payload = json.dumps(command)
    mqtt_client.publish(topic, payload)
    return {"message": f"控制指令已发送到设备 {device_id}"}
