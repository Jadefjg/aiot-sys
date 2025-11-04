# 作用：路由聚合，聚合所有API路由
from fastapi import APIRouter

from app.api.v1.endpoints import auth,users,devices,firmware,permissions

api_router = APIRouter()


api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(firmware.router, prefix="/firmware", tags=["firmware"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])