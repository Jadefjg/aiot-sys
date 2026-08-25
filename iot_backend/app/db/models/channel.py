"""DGIoT 风格：采集/资源通道、规则、设备影子"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.db.base import Base


class Channel(Base):
    """数据通道：采集通道收数，资源通道落库/转发"""

    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    kind = Column(String(20), nullable=False, default="collect")  # collect | resource
    protocol = Column(String(50), nullable=False, default="mqtt")
    product_ids = Column(JSON, nullable=True, default=list)
    enabled = Column(Boolean, default=False, index=True)
    status = Column(String(20), default="stopped")
    config = Column(JSON, nullable=True, default=dict)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChannelLog(Base):
    """通道订阅/转发日志"""

    __tablename__ = "channel_logs"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String(100), index=True, nullable=False)
    level = Column(String(20), default="info")
    message = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DataRule(Base):
    """规则引擎：属性条件 → 告警/转发/写点"""

    __tablename__ = "data_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    product_id = Column(String(100), nullable=True, index=True)
    device_id = Column(String(100), nullable=True, index=True)
    enabled = Column(Boolean, default=True, index=True)
    field = Column(String(100), nullable=True)
    operator = Column(String(10), default=">")
    value = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeviceShadow(Base):
    """设备影子：reported / desired"""

    __tablename__ = "device_shadows"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    reported = Column(JSON, nullable=True, default=dict)
    desired = Column(JSON, nullable=True, default=dict)
    version = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
