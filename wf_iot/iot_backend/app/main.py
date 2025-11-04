from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.mqtt_service import mqtt_client, mqtt_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("Starting IOT Backend Service...")

    # 启动MQTT服务
    mqtt_service.start()

    yield

    # 关闭时执行
    print("Shutting down IOT Backend Service...")

    # 停止MQTT服务
    mqtt_service.stop()

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
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_client.connected if mqtt_client.connected else False,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
