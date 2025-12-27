# API路由聚合

from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, roles, permissions

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(roles.router, prefix="/roles", tags=["角色管理"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["权限管理"])
