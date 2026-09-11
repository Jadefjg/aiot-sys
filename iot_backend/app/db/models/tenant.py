from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Boolean
from app.db.base import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
