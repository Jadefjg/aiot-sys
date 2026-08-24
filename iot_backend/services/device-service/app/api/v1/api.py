# API路由聚合

from fastapi import APIRouter

from app.api.v1.endpoints import devices, products, alarms, groups, device_control

api_router = APIRouter()

api_router.include_router(devices.router, prefix="/devices", tags=["设备管理"])
api_router.include_router(device_control.router, prefix="/devices", tags=["设备控制"])
api_router.include_router(products.router, prefix="/products", tags=["产品物模型"])
api_router.include_router(alarms.router, prefix="/alarms", tags=["告警"])
api_router.include_router(groups.router, prefix="/groups", tags=["分组"])
api_router.include_router(groups.scenes_router, prefix="/scenes", tags=["场景"])
api_router.include_router(groups.jobs_router, prefix="/jobs", tags=["定时任务"])
