# API路由聚合

from fastapi import APIRouter
from app.api.v1.endpoints import firmware

api_router = APIRouter()

api_router.include_router(firmware.router, prefix="/firmware", tags=["固件管理"])
