# 配置管理（device-service）
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Device Service 配置（兼容 Docker 无前缀环境变量）"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "device-service"
    SERVICE_HOST: str = "0.0.0.0"
    HTTP_PORT: int = 8102
    GRPC_PORT: int = 50052
    DEBUG: bool = False

    DATABASE_URL: Optional[str] = None
    MYSQL_HOST: str = "mysql-device"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "iot_device"
    MYSQL_PASSWORD: str = "device123456"
    MYSQL_DATABASE: str = "iot_device"

    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    AUTH_SERVICE_GRPC: str = "auth-service:50051"
    MQTT_GATEWAY_GRPC: str = "mqtt-gateway:50054"

    EVENT_CHANNEL_DEVICE_DATA: str = "device.data.received"
    EVENT_CHANNEL_DEVICE_STATUS: str = "device.status.changed"
    EVENT_CHANNEL_DEVICE_HEARTBEAT: str = "device.heartbeat"
    EVENT_CHANNEL_COMMAND_RESPONSE: str = "device.command.response"
    EVENT_CHANNEL_DEVICE_LIFECYCLE: str = "device.lifecycle"
    CONTROL_RESP_PREFIX: str = "iot:ctrl:resp:"
    CONTROL_TIMEOUT: int = 30

    @property
    def sqlalchemy_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def redis_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
