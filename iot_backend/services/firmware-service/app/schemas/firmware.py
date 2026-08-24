# 固件相关Schema

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FirmwareBase(BaseModel):
    """固件基础模型"""
    version: str
    product_id: str
    description: Optional[str] = None
    release_notes: Optional[str] = None
    is_beta: Optional[bool] = False
    min_hardware_version: Optional[str] = None


class FirmwareCreate(FirmwareBase):
    """创建固件"""
    file_name: str
    file_path: str
    file_url: str
    file_size: int
    file_hash: Optional[str] = None


class FirmwareUpdate(BaseModel):
    """更新固件"""
    description: Optional[str] = None
    release_notes: Optional[str] = None
    is_active: Optional[bool] = None
    is_beta: Optional[bool] = None
    min_hardware_version: Optional[str] = None


class Firmware(FirmwareBase):
    """固件响应模型"""
    id: int
    file_name: str
    file_path: str
    file_url: str
    file_size: int
    file_hash: Optional[str] = None
    is_active: bool
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FirmwareUpgradeTaskCreate(BaseModel):
    """创建升级任务"""
    device_id: int
    device_identifier: str
    firmware_id: int


class FirmwareUpgradeTaskUpdate(BaseModel):
    """更新升级任务"""
    status: Optional[str] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None


class FirmwareUpgradeTask(BaseModel):
    """升级任务响应模型"""
    id: int
    device_id: int
    device_identifier: str
    firmware_id: int
    status: str
    progress: int
    celery_task_id: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FirmwareListResponse(BaseModel):
    """固件列表响应"""
    firmwares: List[Firmware]
    total: int
    page: int
    page_size: int
