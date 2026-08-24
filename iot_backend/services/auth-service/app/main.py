# Auth Service 主入口

import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.grpc.server import serve_grpc


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：启动gRPC服务
    grpc_server = serve_grpc()
    print(f"Auth Service HTTP服务启动在端口 {settings.HTTP_PORT}")

    yield

    # 关闭时：停止gRPC服务
    grpc_server.stop(grace=5)
    print("Auth Service 已关闭")


app = FastAPI(
    title="Auth Service",
    description="IoT系统认证服务 - 用户管理、角色权限、JWT认证",
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
        "service": "Auth Service",
        "version": "1.0.0",
        "docs": "/docs"
    }
