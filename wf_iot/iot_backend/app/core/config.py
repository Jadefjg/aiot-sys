# 作用：配置管理（数据库连接、Redis连接、MQTT配置等）

from pydantic.v1 import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "iot_user"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "iot_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD} @ {self.MYSQL_HOST}:{self.MYSQL_PORT} / {self.MYSQL_DATABASE}"

    # redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # MQTT配置
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None

    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # 固件存储配置
    FIRMWARE_UPLOAD_DIR: str = "/app/firmware_storage"
    FIRMWARE_BASE_URL: str = "http://localhost/firmware_files"

    # 应用配置
    PROJECT_NAME: str = "IoT System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()