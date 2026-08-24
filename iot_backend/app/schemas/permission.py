from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PermissionBase(BaseModel):
    """Base permission model"""
    name: str  # Permission name, e.g: "device:read", "user:create"
    description: Optional[str] = None
    resource: str  # Resource type, e.g: "device", "user"
    action: str  # Action type, e.g: "read", "create", "update", "delete"


class PermissionCreate(PermissionBase):
    """Create permission model"""
    pass


class PermissionUpdate(BaseModel):
    """Update permission model"""
    name: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None


class PermissionInDBBase(PermissionBase):
    """Database permission base model"""
    id: int

    class Config:
        from_attributes = True


class Permission(PermissionInDBBase):
    """Permission response model"""
    pass


class PermissionInDB(PermissionInDBBase):
    """Permission model in database"""
    pass
