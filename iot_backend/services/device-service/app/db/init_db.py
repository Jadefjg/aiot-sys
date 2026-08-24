"""启动时同步 device-service 表结构"""
from app.db.base import Base
from app.db.session import engine
from app.db import models  # noqa: F401


def ensure_schema():
    Base.metadata.create_all(bind=engine)
