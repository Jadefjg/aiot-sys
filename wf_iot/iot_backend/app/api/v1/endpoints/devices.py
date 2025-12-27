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
from app.core.dependencies import get_current_active_user, has_permission
from app.services.mqtt_service import mqtt_client
from app.schemas.device import (
    Device, DeviceCreate, DeviceUpdate,
    DeviceDataCreate, DeviceData,
    DeviceCommand, DeviceCommandCreate
)

router = APIRouter()


@router.get("/", response_model=List[Device])
def read_devices(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取设备列表"""
    if product_id:
        devices = device_crud.get_by_product(db, product_id=product_id, skip=skip, limit=limit)
    else:
        # 非超级用户只能看到自己的设备
        owner_id = None if current_user.is_superuser else current_user.id
        devices = device_crud.get_multi(db, skip=skip, limit=limit, owner_id=owner_id)
    return devices


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

    # 如果不是超级用户，设备归属于当前用户
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
    devices = device_crud.get_online_devices(db)

    # 非超级用户只能看到自己的设备
    if not current_user.is_superuser:
        devices = [d for d in devices if d.owner_id == current_user.id]

    return devices


@router.get("/{device_id}", response_model=Device)
def read_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """根据设备ID获取设备"""
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    # 检查权限
    if not current_user.is_superuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")
    return device


@router.put("/{device_id}", response_model=Device)
def update_device(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    device_in: DeviceUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """更新设备信息"""
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查权限
    if not current_user.is_superuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")

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
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查权限
    if not current_user.is_superuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")

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
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 确保 device_id 匹配
    data_in.device_id = device_id

    device_data = device_data_crud.create(db, obj_in=data_in)
    if not device_data:
        raise HTTPException(status_code=500, detail="创建设备数据失败")
    return device_data


@router.get("/{device_id}/data", response_model=List[DeviceData])
def read_device_data(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取设备数据列表"""
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查权限
    if not current_user.is_superuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")

    data = device_data_crud.get_device_data(db, device_id=device.id, skip=skip, limit=limit)
    return data


@router.post("/{device_id}/commands", response_model=DeviceCommand, status_code=status.HTTP_201_CREATED)
def send_device_command(
    *,
    db: Session = Depends(get_db),
    device_id: str,
    command_in: DeviceCommandCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """发送设备命令"""
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查权限
    if not current_user.is_superuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")

    # 确保 device_id 匹配
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
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查权限
    if not current_user.is_superuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")

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
    device = device_crud.get_by_device_id(db, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 检查权限
    if not current_user.is_superuser and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")

    # 发布控制指令到MQTT主题
    topic = f"device/{device_id}/control"
    payload = json.dumps(command)
    mqtt_client.publish(topic, payload)
    return {"message": f"控制指令已发送到设备 {device_id}"}
