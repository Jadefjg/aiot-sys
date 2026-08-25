from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

from app.schemas.permission import Permission as PermissionDetail


class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserRolesAssign(BaseModel):
    """批量分配用户角色"""
    role_ids: List[int] = []


class UserInDBBase(UserBase):
    id: int
    is_active: bool
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Role(RoleBase):
    id: int

    class Config:
        from_attributes = True


class RoleWithPermissions(Role):
    """角色详情，包含已分配权限"""
    permissions: List[PermissionDetail] = []


class RolePermissionsAssign(BaseModel):
    """批量分配角色权限"""
    permission_ids: List[int] = []