"""设备告警"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Alarm(Base):
    """物模型 Validator 触发的告警记录"""

    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    product_id = Column(String(100), nullable=True, index=True)
    validator_name = Column(String(100), nullable=True)
    level = Column(String(20), default="warning")  # info/warning/error/critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    values = Column(JSON, nullable=True)
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    device = relationship("Device", back_populates="alarms")
