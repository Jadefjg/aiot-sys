from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class FirmwareBase(BaseModel):
    version: str
    product_id: str
    file_url: HttpUrl
    file_hash: Optional[str] = None
    description: Optional[str] = None


class FirmwareCreate(FirmwareBase):
    pass


class Firmware(FirmwareBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


class FirmwareUpgradeTaskBase(BaseModel):
    device_id: int
    firmware_id: int


class FirmwareUpgradeTaskCreate(FirmwareUpgradeTaskBase):
    pass


class FirmwareUpgradeTask(FirmwareUpgradeTaskBase):
    id: int
    status: str
    progress: int
    start_time: datetime
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    class Config:
        from_attributes = True