# 配置管理（mqtt-gateway）
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """MQTT Gateway 配置（与 device-service 共用 Redis db0 事件总线）"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "mqtt-gateway"
    SERVICE_HOST: str = "0.0.0.0"
    GRPC_PORT: int = 50054
    HTTP_PORT: int = 8104
    DEBUG: bool = False

    MQTT_BROKER_HOST: str = "emqx"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_CLIENT_ID: str = "mqtt_gateway_service"

    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    EVENT_CHANNEL_DEVICE_DATA: str = "device.data.received"
    EVENT_CHANNEL_DEVICE_STATUS: str = "device.status.changed"
    EVENT_CHANNEL_DEVICE_HEARTBEAT: str = "device.heartbeat"
    EVENT_CHANNEL_COMMAND_RESPONSE: str = "device.command.response"
    EVENT_CHANNEL_FIRMWARE_STATUS: str = "device.firmware.status"
    EVENT_CHANNEL_DEVICE_LIFECYCLE: str = "device.lifecycle"
    CONTROL_RESP_PREFIX: str = "iot:ctrl:resp:"

    @property
    def redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
