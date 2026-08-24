from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class DeviceBase(BaseModel):
    device_id: str
    device_name: str
    product_id: str
    owner_id: Optional[int] = None

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    owner_id: Optional[int] = None
    status: Optional[str] = None
    firmware_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DeviceInDBBase(DeviceBase):
    id: int
    status: str
    last_online_at: Optional[datetime] = None
    firmware_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class Device(DeviceInDBBase):
    pass


class DeviceDataCreate(BaseModel):
    device_id: str # 设备的唯一标识符，而非数据库ID
    data: Dict[str, Any]


class DeviceData(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    data: Dict[str, Any]
    class Config:
        from_attributes = True


class DeviceCommandCreate(BaseModel):
    """创建设备命令的请求模型"""
    device_id: int
    command_type: str
    command_data: Dict[str, Any]


class DeviceCommand(BaseModel):
    """设备命令响应模型"""
    id: int
    device_id: int
    command_type: str
    command_data: Dict[str, Any]
    status: str
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    response_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
