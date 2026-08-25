"""通道 / 规则 / 影子 Schema"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ChannelBase(BaseModel):
    channel_id: str
    name: str
    kind: str = "collect"
    protocol: str = "mqtt"
    product_ids: Optional[List[str]] = None
    enabled: bool = False
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    protocol: Optional[str] = None
    product_ids: Optional[List[str]] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class Channel(ChannelBase):
    id: int
    status: str = "stopped"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChannelLog(BaseModel):
    id: int
    channel_id: str
    level: str
    message: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DataRuleBase(BaseModel):
    name: str
    product_id: Optional[str] = None
    device_id: Optional[str] = None
    enabled: bool = True
    field: Optional[str] = None
    operator: str = ">"
    value: Optional[Any] = None
    actions: Optional[List[Dict[str, Any]]] = None


class DataRuleCreate(DataRuleBase):
    pass


class DataRuleUpdate(BaseModel):
    name: Optional[str] = None
    product_id: Optional[str] = None
    device_id: Optional[str] = None
    enabled: Optional[bool] = None
    field: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None
    actions: Optional[List[Dict[str, Any]]] = None


class DataRule(DataRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceShadow(BaseModel):
    device_id: str
    reported: Optional[Dict[str, Any]] = None
    desired: Optional[Dict[str, Any]] = None
    version: int = 1
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShadowDesired(BaseModel):
    desired: Dict[str, Any]


class ChannelIngest(BaseModel):
    device_id: str
    values: Optional[Dict[str, Any]] = None
    raw: Optional[Any] = None
