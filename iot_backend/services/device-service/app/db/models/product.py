"""产品与物模型"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.db.base import Base


class Product(Base):
    """产品模板：承载物模型与能力开关"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    protocol = Column(String(50), nullable=True)
    version = Column(String(50), nullable=True)
    image_url = Column(String(255), nullable=True)
    is_gateway = Column(Boolean, default=False)
    smart = Column(Boolean, default=False)
    controllable = Column(Boolean, default=True)
    writable = Column(Boolean, default=True)
    programmable = Column(Boolean, default=False)
    configurable = Column(Boolean, default=False)
    ota = Column(Boolean, default=False)
    locatable = Column(Boolean, default=False)
    model = Column(JSON, nullable=True, default=dict)
    config = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
