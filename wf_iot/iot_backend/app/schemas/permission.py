from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PermissionBase(BaseModel):
    """CPú@!‹"""
    name: str  # CPğ‚: "device:read", "user:create"
    description: Optional[str] = None
    resource: str  # D{‹‚: "device", "user"
    action: str  # Í\{‹‚: "read", "create", "update", "delete"


class PermissionCreate(PermissionBase):
    """úCP!‹"""
    pass


class PermissionUpdate(BaseModel):
    """ô°CP!‹"""
    name: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None


class PermissionInDBBase(PermissionBase):
    """pn“CPú@!‹"""
    id: int

    class Config:
        from_attributes = True


class Permission(PermissionInDBBase):
    """CPÍ”!‹"""
    pass


class PermissionInDB(PermissionInDBBase):
    """pn“-„CP!‹"""
    pass
