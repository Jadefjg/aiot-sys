# 设备相关模型

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Device(Base):
    """设备表"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)  # 设备唯一标识符
    device_name = Column(String(100), nullable=False)
    product_id = Column(String(100), nullable=False, index=True)  # 产品ID
    device_type = Column(String(100), nullable=True)
    owner_id = Column(Integer, nullable=True, index=True)  # 关联auth_db.users.id（跨库引用）
    status = Column(String(20), default="offline", index=True)  # online, offline
    last_online_at = Column(DateTime, nullable=True)
    firmware_version = Column(String(50), nullable=True)
    hardware_version = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    device_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    data_records = relationship("DeviceData", back_populates="device", cascade="all, delete-orphan")
    commands = relationship("DeviceCommand", back_populates="device", cascade="all, delete-orphan")


class DeviceData(Base):
    """设备数据表"""
    __tablename__ = "device_data"

    id = Column(BigInteger, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    data_type = Column(String(50), nullable=True, index=True)  # telemetry, event, alarm
    data = Column(JSON, nullable=False)
    quality = Column(String(50), default="good")  # good, bad, uncertain
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    device = relationship("Device", back_populates="data_records")


class DeviceCommand(Base):
    """设备命令表"""
    __tablename__ = "device_commands"

    id = Column(BigInteger, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    command_type = Column(String(50), nullable=False)  # control, config, upgrade
    command_data = Column(JSON, nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending, sent, acknowledged, failed
    sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    response_data = Column(JSON, nullable=True)
    created_by = Column(Integer, nullable=True)  # 关联auth_db.users.id
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    device = relationship("Device", back_populates="commands")
