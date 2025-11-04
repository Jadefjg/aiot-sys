from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey,JSON, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False) # 设备唯一标识符
    device_name = Column(String(100), nullable=False)
    product_id = Column(String(100), nullable=False) # 产品ID，用于区分设备类型
    device_type = Column(String(100), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True) # 关联用户
    status = Column(String(20), default="offline") # online, offline, active, inactive
    last_online_at = Column(DateTime, nullable=True)
    firmware_version = Column(String(50), nullable=True) # 当前固件版本
    hardware_version = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    device_metadata = Column(JSON, nullable=True) # 存储设备额外信息，如位置、传感器类型等
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    owner = relationship("User", back_populates="devices")
    data_records = relationship("DeviceData", back_populates="device",cascade="all,delete-orphan")
    upgrade_tasks = relationship("FirmwareUpgradeTask",back_populates="device", cascade="all,delete-orphan")


class DeviceData(Base):
    __tablename__ = "device_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    data_type = Column(String(50), nullable=True) # telemetry, event, alarm, etc
    data = Column(JSON, nullable=False) # 存储传感器数据，如 {"temperature": 25.5,"humidity": 60}
    quality = Column(String(50), default="good") # good, bad, uncertain
    created_at = Column(DateTime, default=datetime.now)

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
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    device = relationship("Device")
    creator = relationship("User")