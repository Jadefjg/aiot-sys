# 设备相关模型
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, BigInteger
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Device(Base):
    """设备表"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    device_name = Column(String(100), nullable=False)
    product_id = Column(String(100), nullable=False, index=True)
    device_type = Column(String(100), nullable=True)
    owner_id = Column(Integer, nullable=True, index=True)
    group_id = Column(Integer, ForeignKey("device_groups.id"), nullable=True)
    gateway_id = Column(String(100), nullable=True, index=True)
    link_id = Column(String(100), nullable=True)
    status = Column(String(20), default="offline", index=True)
    disabled = Column(Boolean, default=False)
    error = Column(Boolean, default=False)
    error_string = Column(Text, nullable=True)
    last_online_at = Column(DateTime, nullable=True)
    firmware_version = Column(String(50), nullable=True)
    hardware_version = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_code = Column(String(50), nullable=True)
    values = Column(JSON, nullable=True)
    device_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    data_records = relationship(
        "DeviceData", back_populates="device", cascade="all, delete-orphan"
    )
    commands = relationship(
        "DeviceCommand", back_populates="device", cascade="all, delete-orphan"
    )
    alarms = relationship("Alarm", back_populates="device", cascade="all, delete-orphan")
    group = relationship("DeviceGroup", backref="devices")


class DeviceData(Base):
    __tablename__ = "device_data"

    id = Column(BigInteger, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    data_type = Column(String(50), nullable=True, index=True)
    data = Column(JSON, nullable=False)
    quality = Column(String(50), default="good")
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="data_records")


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id = Column(BigInteger, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    command_type = Column(String(50), nullable=False)
    command_data = Column(JSON, nullable=False)
    status = Column(String(20), default="pending", index=True)
    sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    response_data = Column(JSON, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="commands")
