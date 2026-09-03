from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class DeviceMediaOut(BaseModel):
    id: int
    device_id: str
    media_type: str
    object_key: str
    content_type: Optional[str] = None
    size_bytes: int = 0
    extra: Optional[Dict[str, Any]] = None
    ai_status: str = "pending"
    ai_result: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MediaEventIn(BaseModel):
    type: str
    object_key: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: int = 0
    extra: Optional[Dict[str, Any]] = None
