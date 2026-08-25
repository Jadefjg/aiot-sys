"""连接器 Schema"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LinkBase(BaseModel):
    link_id: str
    name: str
    linker: str = "tcp-client"
    protocol: Optional[str] = "modbus"
    gateway_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class LinkCreate(LinkBase):
    pass


class LinkUpdate(BaseModel):
    name: Optional[str] = None
    linker: Optional[str] = None
    protocol: Optional[str] = None
    gateway_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    error_string: Optional[str] = None


class Link(LinkBase):
    id: int
    status: str = "closed"
    error_string: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BindingBase(BaseModel):
    name: Optional[str] = None
    gateway_id: Optional[str] = None
    device1_id: str
    device2_id: str
    bidirectional: bool = True
    enabled: bool = True


class BindingCreate(BindingBase):
    pass


class BindingUpdate(BaseModel):
    name: Optional[str] = None
    gateway_id: Optional[str] = None
    device1_id: Optional[str] = None
    device2_id: Optional[str] = None
    bidirectional: Optional[bool] = None
    enabled: Optional[bool] = None


class Binding(BindingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScriptBase(BaseModel):
    name: str
    gateway_id: Optional[str] = None
    content: str
    language: str = "js"
    interval_seconds: int = 0
    delay_seconds: int = 0
    repeat_count: int = 0
    enabled: bool = True


class ScriptCreate(ScriptBase):
    pass


class ScriptUpdate(BaseModel):
    name: Optional[str] = None
    gateway_id: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    interval_seconds: Optional[int] = None
    delay_seconds: Optional[int] = None
    repeat_count: Optional[int] = None
    enabled: Optional[bool] = None


class Script(ScriptBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LinkOpenBody(BaseModel):
    devices: Optional[List[Dict[str, Any]]] = None
