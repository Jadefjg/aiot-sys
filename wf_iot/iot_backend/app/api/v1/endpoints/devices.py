import json
from typing import List,Dict,Any,Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.sql.functions import current_user

from app.db.session import get_db
from app.crud.device import device_crud, device_command_crud
from app.schemas.user import User
from app.core.dependencies import get_current_active_user, has_permission
from app.services.mqtt_service import mqtt_client # 假设已初始化MQTT客户端
from app.schemas.device import Device, DeviceCreate, DeviceUpdate,DeviceDataCreate, DeviceData, DeviceCommand, DeviceCommandCreate

router = APIRouter()

@router.get("/",response_model=List[Device])
def read_devices(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[str] = Query(None),
    )->Any:
    """Retrieve devices"""
    if product_id:
        devices = device_crud.get_devices_by_product_id(db, product_id=product_id, skp=skip, limit=limit)
    else:
        # 非超级用户只能看到自己的设备
        owner_id = None if current_user.is_anonymous else current_user.id
        devices = device_crud.get_multi(db,skip=skip, limit=limit, owner_id=owner_id)
    return devices


@router.post("/", response_model=Device)
def create_device(
        *,
        db: Session = Depends(get_db),
        device_in: DeviceCreate,
        current_user: User = Depends(get_current_active_user),
    ) -> Any:
    """Create new device"""
    device = device_crud.get_by_device_id(db, device_id=device_in.device_id)
    if device:
        raise HTTPException(status_code=400, detail="Device already exists")

    # 如果不是超级用户，设备归属于当前用户
    if not current_user.is_superuser and not device_in.owner_id:
        device_in.owner_id = current_user.id

    device = device_crud.create(db, device_in)
    return device

@router.get("/{device_id}", response_model=Device)
def read_device(
        *,
        db: Session = Depends(get_db),
        device_id: str,
        current_user: User = Depends(get_current_active_user),
    ) -> Any:
    """ Get device by ID. """
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    # 检查权限
    if not current_user.is_superuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return device

@router.put("/{device_id}", response_model=Device)
def update_device(
        *,
        db: Session = Depends(get_db),
        device_id: str,
        device_in: DeviceUpdate,
        current_user: User = Depends(get_current_active_user),
    ) -> Any:
    """Update device"""
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 检查权限
    if not current_user.is_supperuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    device = device_crud.update(db, db_obj=device, obj_in=device_in)
    return device

@router.delete("/{device_id}", response_model=Device)
def delete_device(
        *,
        db: Session = Depends(get_db),
        device_id: str,
        current_user: User = Depends(get_current_active_user),
    ) -> Any:
    """Delete device"""
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 检查权限
    if not current_user.is_superuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    device = device_crud.delete(db, db_obj=device.id)
    return device


"""
@router.post("/", response_model=Device, status_code=status.HTTP_201_CREATED,
dependencies=[Depends(has_permission("device:create"))])
def create_device(
    device: DeviceCreate,
    db: Session = Depends(get_db),
    ):
    db_device = device_crud.get_device_by_unique_id(db,
    unique_device_id=device.device_id)
    if db_device:
        raise HTTPException(status_code=400, detail="Device ID already registered")
    return device_crud.create_device(db=db, device=device)
"""

@router.post("/{device_id}/data", response_model=DeviceData)
def create_device_data(
        *,
        db: Session = Depends(get_db),
        device_id: str,
        data_in: DeviceDataCreate,
        current_user: User = Depends(get_current_active_user),
    ) -> Any:
    """Create new device data"""
    # 确保 device_id 匹配
    data_in.device_id = device_id

    device_data = device_data_crud.create(db, obj_in=data_in)
    if not device_data:
        raise HTTPException(status_code=404, detail="Device data not found")
    return device_data

@router.get("/{device_id}/data", response_model=DeviceData)
def read_device_data(
        *,
        db: Session = Depends(get_db),
        device_id: str,
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_active_user),
    ) -> Any:
    """ Get device data """
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 检查权限
    if not current_user.is_supperuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    data = device_data_crud.get_device_data(db, device_id=device_id, skip=skip, limit=limit)
    return data

@router.post("/{device_id}/commands}", response_model=DeviceCommand)
def send_device_command(
        *,
        db: Session = Depends(get_db),
        device_id: str,
        command_in: DeviceCommandCreate,
        current_user: Depends = Depends(get_current_active_user),
    ) -> Any:
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 检查权限
    if not current_user.is_supperuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 确保 device_id 匹配
    command_in.device_id = device_id

    # 创建命令记录
    command = device_command_curd.create(db, obj_in=command_in, create_by=current_user.id)

    if not command:
        raise HTTPException(status_code=404, detail="Command not found")

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
        device_command_crud.update_status(db,command.id,"failed",{"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to send command:{str(e)}")
    return command

@router.get("/status/online", response_model=List[Device])
def get_online_devices(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ) -> Any:
    """ Get all online devices """
    devices = device_crud.get_online_devices(db)

    # 非超级用户只能看到自己的设备
    if not current_user.is_superuser:
        devices = [d for d in devices if d.owner_id == current_user.id]

    return devices



















@router.post("/data", response_model=DeviceData,status_code=status.HTTP_201_CREATED)
def receive_device_data(
    device_data: DeviceDataCreate,
    db: Session = Depends(get_db)
    ):
    # 实际物联网场景中，设备数据通常通过MQTT直接进入消息队列或特定服务，而不是HTTP API
    # 此处仅为演示通过HTTP接收数据的情况
    recorded_data = device_crud.record_device_data(db, device_data)
    if not recorded_data:
        raise HTTPException(status_code=404, detail="Device not found")
    return recorded_data


@router.post("/{device_id}/control", status_code=status.HTTP_202_ACCEPTED,dependencies=[Depends(has_permission("device:control"))])
async def control_device(
    device_id: str,
    command: Dict[str, Any],
    db: Session = Depends(get_db),
    ):
    db_device = device_crud.get_device_by_unique_id(db,unique_device_id=device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    # 发布控制指令到MQTT主题
    topic = f"device/{device_id}/control"
    payload = json.dumps(command)
    mqtt_client.publish(topic, payload)
    return {"message": f"Control command sent to device {device_id}"}

# ... 其他设备管理API，如获取设备列表、更新设备信息、删除设备等