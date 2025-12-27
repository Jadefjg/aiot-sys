# 配置管理（auth-service专用）

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Auth Service配置"""

    # 服务配置
    SERVICE_NAME: str = "auth-service"
    SERVICE_HOST: str = "0.0.0.0"
    HTTP_PORT: int = 8101
    GRPC_PORT: int = 50051
    DEBUG: bool = False

    # 数据库配置（auth专用数据库）
    MYSQL_HOST: str = "mysql_db"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "iot_auth_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    # Redis配置
    REDIS_HOST: str = "redis_cache"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Consul配置（服务发现）
    CONSUL_HOST: str = "consul"
    CONSUL_PORT: int = 8500

    class Config:
        env_file = ".env"
        env_prefix = "AUTH_"


settings = Settings()
