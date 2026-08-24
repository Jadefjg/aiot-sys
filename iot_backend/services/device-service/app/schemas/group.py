"""分组与智能场景 Schema"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DeviceGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class DeviceGroupCreate(DeviceGroupBase):
    pass


class DeviceGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None


class DeviceGroup(DeviceGroupBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SceneBase(BaseModel):
    name: str
    gateway_id: Optional[str] = None
    enabled: bool = True
    time_range: Optional[Dict[str, Any]] = None
    weekdays: Optional[List[int]] = None
    triggers: Optional[List[Dict[str, Any]]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    delay_seconds: int = 0


class SceneCreate(SceneBase):
    pass


class SceneUpdate(BaseModel):
    name: Optional[str] = None
    gateway_id: Optional[str] = None
    enabled: Optional[bool] = None
    time_range: Optional[Dict[str, Any]] = None
    weekdays: Optional[List[int]] = None
    triggers: Optional[List[Dict[str, Any]]] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    delay_seconds: Optional[int] = None


class Scene(SceneBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobBase(BaseModel):
    name: str
    gateway_id: Optional[str] = None
    enabled: bool = True
    cron_time: Optional[str] = None
    weekdays: Optional[List[int]] = None
    action: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    once: bool = False


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    name: Optional[str] = None
    gateway_id: Optional[str] = None
    enabled: Optional[bool] = None
    cron_time: Optional[str] = None
    weekdays: Optional[List[int]] = None
    action: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    once: Optional[bool] = None


class Job(JobBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
