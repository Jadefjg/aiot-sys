# 配置管理（firmware-service专用）

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Firmware Service配置"""

    # 服务配置
    SERVICE_NAME: str = "firmware-service"
    SERVICE_HOST: str = "0.0.0.0"
    HTTP_PORT: int = 8103
    GRPC_PORT: int = 50053
    DEBUG: bool = False

    # 数据库配置（firmware专用数据库）
    MYSQL_HOST: str = "mysql_db"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "iot_firmware_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    # Redis配置（Celery broker）
    REDIS_HOST: str = "redis_cache"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Celery配置
    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.REDIS_URL

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return self.REDIS_URL

    # gRPC服务地址
    AUTH_SERVICE_GRPC: str = "auth-service:50051"
    DEVICE_SERVICE_GRPC: str = "device-service:50052"
    MQTT_GATEWAY_GRPC: str = "mqtt-gateway:50054"

    # 固件存储配置
    FIRMWARE_UPLOAD_DIR: str = "/app/firmware_storage"
    FIRMWARE_BASE_URL: str = "http://firmware-service:8103/files"

    # Consul配置（服务发现）
    CONSUL_HOST: str = "consul"
    CONSUL_PORT: int = 8500

    class Config:
        env_file = ".env"
        env_prefix = "FIRMWARE_"


settings = Settings()
