"""连接器：serial / tcp / udp 等物理链路"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text

from app.db.base import Base


class Link(Base):
    """连接实例，对应 MQTT 主题 link/{linker}/{link_id}/#"""

    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    linker = Column(String(50), nullable=False, default="tcp-client")
    protocol = Column(String(50), nullable=True, default="modbus")
    gateway_id = Column(String(100), nullable=True, index=True)
    options = Column(JSON, nullable=True, default=dict)
    status = Column(String(20), default="closed")
    error_string = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
