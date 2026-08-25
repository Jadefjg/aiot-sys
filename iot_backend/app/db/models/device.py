from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    device_name = Column(String(100), nullable=False)
    product_id = Column(String(100), nullable=False, index=True)
    device_type = Column(String(100), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("device_groups.id"), nullable=True)
    # 网关/子设备层级：子设备挂 gateway_id
    gateway_id = Column(String(100), nullable=True, index=True)
    link_id = Column(String(100), nullable=True, index=True)
    status = Column(String(20), default="offline")
    disabled = Column(Boolean, default=False)
    error = Column(Boolean, default=False)
    error_string = Column(Text, nullable=True)
    last_online_at = Column(DateTime, nullable=True)
    firmware_version = Column(String(50), nullable=True)
    hardware_version = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_code = Column(String(50), nullable=True)
    # 最新属性快照（内存态落库）
    values = Column(JSON, nullable=True, default=dict)
    device_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="devices")
    group = relationship("DeviceGroup", backref="devices")
    data_records = relationship(
        "DeviceData", back_populates="device", cascade="all,delete-orphan"
    )
    upgrade_tasks = relationship(
        "FirmwareUpgradeTask", back_populates="device", cascade="all,delete-orphan"
    )
    alarms = relationship("Alarm", back_populates="device", cascade="all,delete-orphan")


class DeviceData(Base):
    __tablename__ = "device_data"
    __table_args__ = (
        Index("ix_device_data_device_ts", "device_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    data_type = Column(String(50), nullable=True) # telemetry, event, alarm, etc
    data = Column(JSON, nullable=False) # 存储传感器数据，如 {"temperature": 25.5,"humidity": 60}
    quality = Column(String(50), default="good") # good, bad, uncertain
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    device = relationship("Device", back_populates="data_records")


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False,index=True)
    command_type = Column(String(50), nullable=False)  # control, config,upgrade, etc.
    command_data = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")  # pending, sent,acknowledged, failed
    sent_at = Column(DateTime, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    response_data = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    device = relationship("Device")
    creator = relationship("User")