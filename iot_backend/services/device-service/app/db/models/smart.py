"""智能场景配置（边缘执行的云端镜像）"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.db.base import Base


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    gateway_id = Column(String(100), nullable=True, index=True)
    enabled = Column(Boolean, default=True)
    time_range = Column(JSON, nullable=True)
    weekdays = Column(JSON, nullable=True)
    triggers = Column(JSON, nullable=True)
    conditions = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=True)
    delay_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    gateway_id = Column(String(100), nullable=True, index=True)
    enabled = Column(Boolean, default=True)
    cron_time = Column(String(50), nullable=True)
    weekdays = Column(JSON, nullable=True)
    action = Column(JSON, nullable=True)
    data = Column(JSON, nullable=True)
    once = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
