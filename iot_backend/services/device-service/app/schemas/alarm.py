"""告警 Schema"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AlarmBase(BaseModel):
    title: str
    message: Optional[str] = None
    level: str = "warning"
    validator_name: Optional[str] = None
    values: Optional[Dict[str, Any]] = None


class AlarmCreate(AlarmBase):
    device_id: int
    product_id: Optional[str] = None


class Alarm(AlarmBase):
    id: int
    device_id: int
    product_id: Optional[str] = None
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
