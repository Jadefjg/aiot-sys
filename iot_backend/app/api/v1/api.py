# 作用：路由聚合，聚合所有API路由
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth, users, devices, firmware, permissions, roles,
    products, alarms, groups, device_control,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(device_control.router, prefix="/devices", tags=["device-control"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["alarms"])
api_router.include_router(groups.router, prefix="/groups", tags=["groups"])
api_router.include_router(groups.scenes_router, prefix="/scenes", tags=["scenes"])
api_router.include_router(groups.jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(firmware.router, prefix="/firmware", tags=["firmware"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
