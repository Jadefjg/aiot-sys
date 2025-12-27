# 配置管理（mqtt-gateway专用）

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """MQTT Gateway配置"""

    # 服务配置
    SERVICE_NAME: str = "mqtt-gateway"
    SERVICE_HOST: str = "0.0.0.0"
    GRPC_PORT: int = 50054
    DEBUG: bool = False

    # MQTT配置
    MQTT_BROKER_HOST: str = "mqtt_broker"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_CLIENT_ID: str = "mqtt_gateway_service"

    # Redis配置（事件发布）
    REDIS_HOST: str = "redis_cache"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # 事件通道配置
    EVENT_CHANNEL_DEVICE_DATA: str = "device.data.received"
    EVENT_CHANNEL_DEVICE_STATUS: str = "device.status.changed"
    EVENT_CHANNEL_DEVICE_HEARTBEAT: str = "device.heartbeat"
    EVENT_CHANNEL_COMMAND_RESPONSE: str = "device.command.response"
    EVENT_CHANNEL_FIRMWARE_STATUS: str = "device.firmware.status"

    # Consul配置（服务发现）
    CONSUL_HOST: str = "consul"
    CONSUL_PORT: int = 8500

    class Config:
        env_file = ".env"
        env_prefix = "MQTT_"


settings = Settings()
