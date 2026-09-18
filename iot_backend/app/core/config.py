# 作用：配置管理（数据库连接、Redis连接、MQTT配置等）

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "iot_user"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "iot_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    # redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    # Agent Workflow 状态持久化：redis（推荐多副本）或 postgres；memory 仅适用于开发
    CHECKPOINTER_BACKEND: str = "redis"
    CHECKPOINTER_REDIS_URL: Optional[str] = None
    CHECKPOINTER_POSTGRES_URL: Optional[str] = None

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def AGENT_CHECKPOINTER_REDIS_URL(self) -> str:
        return self.CHECKPOINTER_REDIS_URL or self.REDIS_URL

    @property
    def AGENT_CHECKPOINTER_POSTGRES_URL(self) -> str:
        return self.CHECKPOINTER_POSTGRES_URL or self.DATABASE_URL

    # MQTT配置
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_CONNECT_TIMEOUT_SECONDS: int = 10
    MQTT_PUBLISH_RETRIES: int = 3
    MQTT_RETRY_BACKOFF_SECONDS: float = 0.5
    # 每秒接纳新连接/注册上限，0 表示不限（原型档）
    MQTT_CONNECT_RATE_LIMIT: int = 0
    # prototype | small | medium | large | xlarge；空则按设备数与能力探测
    SCALE_STAGE: str = "prototype"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MAX_EXPORT_DEVICES: int = 10000

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # 固件存储配置
    FIRMWARE_UPLOAD_DIR: str = "/app/firmware_storage"
    FIRMWARE_BASE_URL: str = "http://localhost/firmware_files"
    MEDIA_UPLOAD_DIR: str = "/app/media_storage"
    MEDIA_BASE_URL: str = "http://localhost/media_files"
    MEDIA_AI_ENABLED: bool = True

    # 应用配置
    PROJECT_NAME: str = "IoT System"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # InfluxDB 时序库：遥测唯一存储（设备快照仍在 MySQL）
    INFLUX_URL: str = ""
    INFLUX_TOKEN: str = ""
    INFLUX_ORG: str = "iot"
    INFLUX_BUCKET: str = "telemetry"
    INFLUX_ENABLED: bool = False

    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def CORS_ORIGINS_LIST(self) -> list:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
