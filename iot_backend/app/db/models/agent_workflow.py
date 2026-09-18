"""Persistent identity for Agent Workflow conversations."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, JSON, String, UniqueConstraint
from app.db.base import Base


class AgentWorkflow(Base):
    __tablename__ = "agent_workflows"
    __table_args__ = (UniqueConstraint("workflow_name", "owner_id", name="uq_agent_workflow_owner"),)

    id = Column(Integer, primary_key=True, index=True)
    workflow_name = Column(String(100), nullable=False, index=True)
    owner_id = Column(String(100), nullable=False, index=True)
    thread_id = Column(String(255), nullable=False, unique=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
