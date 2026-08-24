"""智能场景相关配置（边缘侧可执行配置的云端镜像）"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.db.base import Base


class Scene(Base):
    """场景：触发器 + 条件 + 动作"""

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
    """定时任务"""

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


class Binding(Base):
    """设备联动绑定"""

    __tablename__ = "bindings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    gateway_id = Column(String(100), nullable=True, index=True)
    device1_id = Column(String(100), nullable=False)
    device2_id = Column(String(100), nullable=False)
    bidirectional = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Script(Base):
    """边缘 JS 脚本配置"""

    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    gateway_id = Column(String(100), nullable=True, index=True)
    content = Column(Text, nullable=False)
    interval_seconds = Column(Integer, default=0)
    delay_seconds = Column(Integer, default=0)
    repeat_count = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
