"""Checkpointer factory and durable workflow-thread repository.

LangGraph integrations are optional dependencies so the API can start when a
workflow backend is not installed. Production deployments should install the
selected ``langgraph-checkpoint-*`` package and set CHECKPOINTER_BACKEND.
"""
from __future__ import annotations
from uuid import uuid4
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.models.agent_workflow import AgentWorkflow


def get_checkpointer(backend: str | None = None):
    name = (backend or settings.CHECKPOINTER_BACKEND).lower()
    if name == "memory":
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
    if name == "redis":
        try:
            from langgraph.checkpoint.redis import RedisSaver
        except ImportError as exc:
            raise RuntimeError("Redis checkpointer requires langgraph-checkpoint-redis") from exc
        return RedisSaver.from_conn_string(settings.AGENT_CHECKPOINTER_REDIS_URL)
    if name in {"postgres", "postgresql"}:
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as exc:
            raise RuntimeError("PostgreSQL checkpointer requires langgraph-checkpoint-postgres") from exc
        return PostgresSaver.from_conn_string(settings.AGENT_CHECKPOINTER_POSTGRES_URL)
    raise ValueError(f"Unsupported CHECKPOINTER_BACKEND: {name}")


def get_or_create_thread(db: Session, workflow_name: str, owner_id: str, metadata: dict | None = None) -> str:
    """Return the stable thread id used in LangGraph config for this owner/workflow."""
    row = db.query(AgentWorkflow).filter_by(workflow_name=workflow_name, owner_id=str(owner_id)).one_or_none()
    if row is None:
        row = AgentWorkflow(workflow_name=workflow_name, owner_id=str(owner_id), thread_id=f"{workflow_name}:{uuid4()}", metadata_json=metadata)
        db.add(row)
    elif metadata is not None:
        row.metadata_json = metadata
    db.commit()
    db.refresh(row)
    return row.thread_id
