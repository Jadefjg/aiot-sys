# Firmware Service 主入口

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1.api import api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Firmware Service...")

    # 确保固件存储目录存在
    os.makedirs(settings.FIRMWARE_UPLOAD_DIR, exist_ok=True)

    logger.info(f"Firmware Service started - HTTP port: {settings.HTTP_PORT}")

    yield

    # 关闭时
    logger.info("Shutting down Firmware Service...")
    logger.info("Firmware Service stopped")


app = FastAPI(
    title="Firmware Service",
    description="IoT系统固件服务 - 固件管理、升级任务",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(api_router, prefix="/api/v1")

# 挂载静态文件（固件下载）
app.mount("/files", StaticFiles(directory=settings.FIRMWARE_UPLOAD_DIR), name="firmware_files")


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "http_port": settings.HTTP_PORT,
        "grpc_port": settings.GRPC_PORT
    }


@app.get("/")
def root():
    """根路径"""
    return {
        "service": "Firmware Service",
        "version": "1.0.0",
        "docs": "/docs"
    }
