# MQTT Gateway 主入口

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.mqtt.client import mqtt_client
from app.events.publisher import event_publisher
from app.grpc.server import serve_grpc

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
    logger.info("Starting MQTT Gateway...")

    # 连接Redis（事件发布）
    event_publisher.connect()

    # 启动MQTT客户端
    mqtt_client.start()

    # 启动gRPC服务
    grpc_server = serve_grpc()

    logger.info(f"MQTT Gateway started - gRPC port: {settings.GRPC_PORT}")

    yield

    # 关闭时
    logger.info("Shutting down MQTT Gateway...")
    grpc_server.stop(grace=5)
    mqtt_client.stop()
    event_publisher.disconnect()
    logger.info("MQTT Gateway stopped")


app = FastAPI(
    title="MQTT Gateway",
    description="IoT系统MQTT网关服务 - 负责MQTT消息收发和事件发布",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy" if mqtt_client.connected else "degraded",
        "service": settings.SERVICE_NAME,
        "grpc_port": settings.GRPC_PORT,
        "mqtt_connected": mqtt_client.connected,
        "redis_connected": event_publisher.connected,
        "messages_published": mqtt_client.messages_published,
        "messages_received": mqtt_client.messages_received
    }


@app.get("/")
def root():
    """根路径"""
    return {
        "service": "MQTT Gateway",
        "version": "1.0.0",
        "mqtt_broker": f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}"
    }


@app.get("/status")
def get_status():
    """获取详细状态"""
    connected_since = None
    if mqtt_client.connected_since:
        connected_since = mqtt_client.connected_since.isoformat()

    return {
        "mqtt": {
            "connected": mqtt_client.connected,
            "broker": f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}",
            "client_id": settings.MQTT_CLIENT_ID,
            "connected_since": connected_since,
            "messages_published": mqtt_client.messages_published,
            "messages_received": mqtt_client.messages_received
        },
        "redis": {
            "connected": event_publisher.connected,
            "host": f"{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        }
    }
