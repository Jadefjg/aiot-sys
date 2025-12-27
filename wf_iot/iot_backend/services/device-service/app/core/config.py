# 配置管理（device-service专用）

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Device Service配置"""

    # 服务配置
    SERVICE_NAME: str = "device-service"
    SERVICE_HOST: str = "0.0.0.0"
    HTTP_PORT: int = 8102
    GRPC_PORT: int = 50052
    DEBUG: bool = False

    # 数据库配置（device专用数据库）
    MYSQL_HOST: str = "mysql_db"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "iot_device_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    # Redis配置（事件订阅）
    REDIS_HOST: str = "redis_cache"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # gRPC服务地址
    AUTH_SERVICE_GRPC: str = "auth-service:50051"
    MQTT_GATEWAY_GRPC: str = "mqtt-gateway:50054"

    # 事件通道配置
    EVENT_CHANNEL_DEVICE_DATA: str = "device.data.received"
    EVENT_CHANNEL_DEVICE_STATUS: str = "device.status.changed"
    EVENT_CHANNEL_DEVICE_HEARTBEAT: str = "device.heartbeat"
    EVENT_CHANNEL_COMMAND_RESPONSE: str = "device.command.response"

    # Consul配置（服务发现）
    CONSUL_HOST: str = "consul"
    CONSUL_PORT: int = 8500

    class Config:
        env_file = ".env"
        env_prefix = "DEVICE_"


settings = Settings()
