"""眼镜媒体：本地对象目录 + 元数据入库 + 异步 AI 占位任务"""
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.media import media_crud
from app.db.models.media import DeviceMedia

logger = logging.getLogger(__name__)

EVENT_TYPES = {
    "photo_captured": "photo",
    "clip_ready": "clip",
    "audio_ready": "audio",
}


def _safe_dir() -> Path:
    root = Path(getattr(settings, "MEDIA_UPLOAD_DIR", "/app/media_storage"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def _enqueue_ai(media_id: int) -> None:
    if not getattr(settings, "MEDIA_AI_ENABLED", True):
        return
    try:
        from celery_worker import celery_app
        celery_app.send_task("media_tasks.analyze_media", args=[media_id])
    except Exception as exc:
        logger.warning("enqueue AI skipped: %s", exc)


def record_event(db: Session, device_id: str, payload: Dict[str, Any]) -> Optional[DeviceMedia]:
    """MQTT event 元数据落库（无二进制）"""
    event_type = payload.get("type") or payload.get("name")
    media_type = EVENT_TYPES.get(event_type)
    if not media_type:
        return None
    object_key = payload.get("object_key") or f"event/{device_id}/{uuid.uuid4().hex}"
    existed = media_crud.get_by_key(db, object_key)
    if existed:
        return existed
    extra = {k: v for k, v in payload.items() if k not in {"type", "name", "object_key", "content_type", "size_bytes"}}
    row = media_crud.create(
        db,
        device_id=device_id,
        media_type=media_type,
        object_key=object_key,
        content_type=payload.get("content_type"),
        size_bytes=int(payload.get("size_bytes") or 0),
        extra=extra or None,
        ai_status="pending",
    )
    _enqueue_ai(row.id)
    return row


def save_upload(db: Session, device_id: str, filename: str, content: bytes, content_type: str) -> DeviceMedia:
    suffix = Path(filename or "bin").suffix or ".bin"
    object_key = f"upload/{device_id}/{uuid.uuid4().hex}{suffix}"
    dest = _safe_dir() / object_key
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    media_type = "photo"
    if content_type.startswith("video/"):
        media_type = "clip"
    elif content_type.startswith("audio/"):
        media_type = "audio"
    row = media_crud.create(
        db,
        device_id=device_id,
        media_type=media_type,
        object_key=object_key,
        file_path=str(dest),
        content_type=content_type,
        size_bytes=len(content),
        ai_status="pending",
    )
    _enqueue_ai(row.id)
    return row
