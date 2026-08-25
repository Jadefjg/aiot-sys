from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import datetime


class PermissionBase(BaseModel):
    """Base permission model"""
    name: str  # 权限名称，如「读取设备」
    code: Optional[str] = None  # 权限代码，如 device:read
    description: Optional[str] = None
    resource: str  # Resource type, e.g: "device", "user"
    action: str  # Action type, e.g: "read", "create", "update", "delete"

    @model_validator(mode="after")
    def fill_default_code(self):
        """未传 code 时根据 resource:action 自动生成"""
        if not self.code:
            self.code = f"{self.resource}:{self.action}"
        return self


class PermissionCreate(PermissionBase):
    """Create permission model"""
    pass


class PermissionUpdate(BaseModel):
    """Update permission model"""
    name: Optional[str] = None
    code: Optional[str] = None
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
