"""设备媒体元数据（照片/短视频/录音），二进制走本地对象目录"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String

from app.db.base import Base


class DeviceMedia(Base):
    __tablename__ = "device_media"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    media_type = Column(String(20), nullable=False, index=True)
    object_key = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(500), nullable=True)
    content_type = Column(String(100), nullable=True)
    size_bytes = Column(Integer, default=0)
    extra = Column(JSON, nullable=True)
    ai_status = Column(String(20), default="pending")
    ai_result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
