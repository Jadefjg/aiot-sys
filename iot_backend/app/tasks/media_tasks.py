"""媒体 AI 占位任务：无外部模型时写本地摘要，不阻塞 MQTT 主链路"""
import logging

from celery_worker import celery_app
from app.crud.media import media_crud
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="media_tasks.analyze_media")
def analyze_media(media_id: int) -> dict:
    db = SessionLocal()
    try:
        row = media_crud.get(db, media_id)
        if not row:
            return {"status": "missing"}
        result = {
            "engine": "stub",
            "summary": f"{row.media_type} from {row.device_id}",
            "labels": [row.media_type],
        }
        media_crud.update_ai(db, row, "done", result)
        return {"status": "done", "id": media_id}
    except Exception as exc:
        logger.warning("analyze_media failed: %s", exc)
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()
