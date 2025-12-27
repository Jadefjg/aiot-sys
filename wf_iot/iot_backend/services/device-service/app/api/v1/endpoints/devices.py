# 设备管理API端点

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.crud.device import device_crud, device_data_crud, device_command_crud
from app.db.session import get_db
from app.schemas.device import (
    Device, DeviceCreate, DeviceUpdate, DeviceListResponse,
    DeviceData, DeviceDataCreate,
    DeviceCommand, DeviceCommandCreate
)
from app.grpc.clients.auth_client import auth_grpc_client
from app.grpc.clients.mqtt_client import mqtt_grpc_client

router = APIRouter()


def verify_token(authorization: str = Header(None)) -> dict:
    """验证JWT Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证信息")

    token = authorization.split(" ")[1]
    valid, user_id, username, error = auth_grpc_client.validate_token(token)

    if not valid:
        raise HTTPException(status_code=401, detail=error or "Token无效")

    return {"user_id": user_id, "username": username}


def check_permission(user_id: int, resource: str, action: str):
    """检查用户权限"""
    allowed, reason = auth_grpc_client.check_permission(user_id, resource, action)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason or "权限不足")


@router.get("/", response_model=DeviceListResponse)
def list_devices(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    product_id: Optional[str] = None,
    owner_id: Optional[int] = None,
    current_user: dict = Depends(verify_token),
) -> Any:
    """获取设备列表"""
    check_permission(current_user["user_id"], "device", "read")

    skip = (page - 1) * page_size
    devices, total = device_crud.get_multi(
        db, skip=skip, limit=page_size,
        owner_id=owner_id, status=status, product_id=product_id
    )
    return DeviceListResponse(
        devices=devices,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/", response_model=Device)
def create_device(
    *,
    db: Session = Depends(get_db),
    device_in: DeviceCreate,
    current_user: dict = Depends(verify_token),
) -> Any:
    """创建新设备"""
    check_permission(current_user["user_id"], "device", "write")

    # 检查设备ID是否已存在
    existing = device_crud.get_by_device_id(db, device_in.device_id)
    if existing:
        raise HTTPException(status_code=400, detail="设备ID已存在")

    device = device_crud.create(db, obj_in=device_in)
    return device


@router.get("/{device_id}", response_model=Device)
def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    """获取设备详情"""
    check_permission(current_user["user_id"], "device", "read")

    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device


@router.put("/{device_id}", response_model=Device)
def update_device(
    device_id: str,
    *,
    db: Session = Depends(get_db),
    device_in: DeviceUpdate,
    current_user: dict = Depends(verify_token),
) -> Any:
    """更新设备信息"""
    check_permission(current_user["user_id"], "device", "write")

    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    device = device_crud.update(db, db_obj=device, obj_in=device_in)
    return device


@router.delete("/{device_id}")
def delete_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    """删除设备"""
    check_permission(current_user["user_id"], "device", "delete")

    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    device_crud.delete(db, device_id=device.id)
    return {"message": "设备已删除"}


@router.get("/{device_id}/data", response_model=List[DeviceData])
def get_device_data(
    device_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    data_type: Optional[str] = None,
    current_user: dict = Depends(verify_token),
) -> Any:
    """获取设备数据"""
    check_permission(current_user["user_id"], "device", "read")

    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    data = device_data_crud.get_device_data(db, device.id, data_type=data_type, limit=limit)
    return data


@router.post("/{device_id}/command", response_model=DeviceCommand)
def send_device_command(
    device_id: str,
    *,
    db: Session = Depends(get_db),
    command_in: DeviceCommandCreate,
    current_user: dict = Depends(verify_token),
) -> Any:
    """发送设备命令"""
    check_permission(current_user["user_id"], "device", "write")

    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 创建命令记录
    command_in.device_id = device_id
    command = device_command_crud.create(db, obj_in=command_in, created_by=current_user["user_id"])
    if not command:
        raise HTTPException(status_code=400, detail="创建命令失败")

    # 通过MQTT Gateway发送命令
    success, result = mqtt_grpc_client.send_device_command(
        device_id=device_id,
        command_type=command_in.command_type,
        command_data=command_in.command_data
    )

    if success:
        # 更新命令状态为已发送
        device_command_crud.update_status(db, command.id, "sent")
    else:
        # 更新命令状态为失败
        device_command_crud.update_status(db, command.id, "failed", {"error": result})

    return command


@router.get("/{device_id}/commands", response_model=List[DeviceCommand])
def get_device_commands(
    device_id: str,
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(verify_token),
) -> Any:
    """获取设备命令历史"""
    check_permission(current_user["user_id"], "device", "read")

    commands = device_command_crud.get_device_commands(db, device_id, status=status, limit=limit)
    return commands
