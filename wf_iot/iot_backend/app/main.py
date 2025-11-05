from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.protocol_manager import protocol_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("Starting IOT Backend Service...")

    # 初始化协议管理器
    protocol_manager.initialize()

    # 启动所有协议服务 (MQTT, CoAP, AMQP等)
    startup_results = await protocol_manager.start_all()

    # 记录启动状态
    for protocol, success in startup_results.items():
        status = "✓" if success else "✗"
        print(f"{status} {protocol.upper()} service: {'Started' if success else 'Failed'}")

    yield

    # 关闭时执行
    print("Shutting down IOT Backend Service...")

    # 停止所有协议服务
    shutdown_results = await protocol_manager.stop_all()

    # 记录关闭状态
    for protocol, success in shutdown_results.items():
        status = "✓" if success else "✗"
        print(f"{status} {protocol.upper()} service: {'Stopped' if success else 'Failed'}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",  # "/api/v1/openapi.json"
    lifespan=lifespan
)

# 设置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router,prefix=settings.API_V1_STR) # prefix="/api/v1"

@app.get("/")
async def root():
    return {
        "message": "IOT Backend Service",
        "version": settings.PROJECT_VERSION,
        "status": "Running",
    }

@app.get("/health")
async def health_check():
    """
    健康检查端点
    监控所有协议服务的连接状态
    """
    # 获取所有协议服务状态
    protocol_statuses = protocol_manager.get_service_status()

    # 计算总体状态
    all_connected = all(
        status.get("connected", False)
        for status in protocol_statuses
        if status
    )

    # 构建健康检查响应
    response = {
        "status": "healthy" if all_connected else "degraded",
        "timestamp": "2024-01-01T00:00:00Z",
        "protocols": {}
    }

    # 添加每个协议的详细信息
    for status in protocol_statuses:
        if status:
            protocol_name = status["protocol"]
            response["protocols"][protocol_name] = {
                "connected": status.get("connected", False),
                "device_count": status.get("device_count", 0)
            }

    # 添加总体连接状态
    response["all_protocols_connected"] = all_connected

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
