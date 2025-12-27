# Device Service 主入口

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.grpc.clients.auth_client import auth_grpc_client
from app.grpc.clients.mqtt_client import mqtt_grpc_client
from app.events.subscriber import event_subscriber

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
    logger.info("Starting Device Service...")

    # 连接gRPC服务
    auth_grpc_client.connect()
    mqtt_grpc_client.connect()

    # 连接Redis并开始订阅事件
    event_subscriber.connect()
    event_subscriber.start()

    logger.info(f"Device Service started - HTTP port: {settings.HTTP_PORT}")

    yield

    # 关闭时
    logger.info("Shutting down Device Service...")
    event_subscriber.disconnect()
    mqtt_grpc_client.close()
    auth_grpc_client.close()
    logger.info("Device Service stopped")


app = FastAPI(
    title="Device Service",
    description="IoT系统设备服务 - 设备CRUD、设备数据、设备命令",
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
        "service": "Device Service",
        "version": "1.0.0",
        "docs": "/docs"
    }
