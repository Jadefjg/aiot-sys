# 用户相关Schema

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class PermissionBase(BaseModel):
    """权限基础模型"""
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    """创建权限"""
    pass


class Permission(PermissionBase):
    """权限响应模型"""
    id: int

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """角色基础模型"""
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """创建角色"""
    pass


class Role(RoleBase):
    """角色响应模型"""
    id: int
    permissions: List[Permission] = []

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """创建用户"""
    password: str
    is_superuser: Optional[bool] = False


class UserUpdate(BaseModel):
    """更新用户"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """用户响应模型"""
    id: int
    is_active: bool
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime
    roles: List[Role] = []

    class Config:
        from_attributes = True


class UserInDB(User):
    """数据库中的用户模型"""
    hashed_password: str
