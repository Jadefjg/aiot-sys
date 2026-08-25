"""设备 Schema"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    device_id: str
    device_name: str
    product_id: str
    owner_id: Optional[int] = None
    group_id: Optional[int] = None
    gateway_id: Optional[str] = None
    link_id: Optional[str] = None
    device_type: Optional[str] = None


class DeviceCreate(DeviceBase):
    device_metadata: Optional[Dict[str, Any]] = None


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    owner_id: Optional[int] = None
    group_id: Optional[int] = None
    gateway_id: Optional[str] = None
    link_id: Optional[str] = None
    status: Optional[str] = None
    disabled: Optional[bool] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geo_code: Optional[str] = None
    device_metadata: Optional[Dict[str, Any]] = None


class DeviceInDBBase(DeviceBase):
    id: int
    status: str
    disabled: Optional[bool] = False
    error: Optional[bool] = False
    error_string: Optional[str] = None
    last_online_at: Optional[datetime] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geo_code: Optional[str] = None
    values: Optional[Dict[str, Any]] = None
    device_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Device(DeviceInDBBase):
    pass


class DeviceDataCreate(BaseModel):
    device_id: str
    data: Dict[str, Any]
    data_type: str = "telemetry"
    quality: str = "good"


class DeviceData(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    data_type: Optional[str] = None
    data: Dict[str, Any]
    quality: Optional[str] = None

    class Config:
        from_attributes = True


class DeviceCommandCreate(BaseModel):
    device_id: str
    command_type: str
    command_data: Dict[str, Any]


class DeviceCommand(BaseModel):
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


class DeviceWriteRequest(BaseModel):
    """写属性请求"""
    values: Dict[str, Any]


class DeviceReadRequest(BaseModel):
    """读属性请求"""
    points: List[str] = Field(default_factory=list)


class DeviceActionRequest(BaseModel):
    """执行动作请求"""
    params: Optional[Dict[str, Any]] = None


class DeviceSettingRequest(BaseModel):
    """下发配置请求"""
    data: Dict[str, Any]


class DeviceRegisterRequest(BaseModel):
    """设备注册（可带产品与版本信息）"""
    product_id: Optional[str] = None
    device_name: Optional[str] = None
    settings_version: Optional[str] = None
    model_version: Optional[str] = None
    gateway_id: Optional[str] = None
