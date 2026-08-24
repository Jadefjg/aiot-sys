# 设备相关Schema

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class DeviceBase(BaseModel):
    """设备基础模型"""
    device_id: str
    device_name: str
    product_id: str
    device_type: Optional[str] = None
    owner_id: Optional[int] = None


class DeviceCreate(DeviceBase):
    """创建设备"""
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_metadata: Optional[Dict[str, Any]] = None


class DeviceUpdate(BaseModel):
    """更新设备"""
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    owner_id: Optional[int] = None
    status: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_metadata: Optional[Dict[str, Any]] = None


class Device(DeviceBase):
    """设备响应模型"""
    id: int
    status: str
    last_online_at: Optional[datetime] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    device_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceDataCreate(BaseModel):
    """创建设备数据"""
    device_id: str  # 设备唯一标识符
    data_type: Optional[str] = "telemetry"
    data: Dict[str, Any]
    quality: Optional[str] = "good"


class DeviceData(BaseModel):
    """设备数据响应模型"""
    id: int
    device_id: int
    timestamp: datetime
    data_type: Optional[str] = None
    data: Dict[str, Any]
    quality: str
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceCommandCreate(BaseModel):
    """创建设备命令"""
    device_id: str  # 设备唯一标识符
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
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """设备列表响应"""
    devices: List[Device]
    total: int
    page: int
    page_size: int
