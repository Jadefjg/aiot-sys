"""启动时确保新表与设备扩展列存在"""
import logging

from sqlalchemy import inspect, text

from app.db.base import Base, import_models
from app.db.session import engine

logger = logging.getLogger(__name__)

DEVICE_EXTRA_COLUMNS = {
    "group_id": "INT NULL",
    "gateway_id": "VARCHAR(100) NULL",
    "link_id": "VARCHAR(100) NULL",
    "disabled": "BOOLEAN DEFAULT 0",
    "error": "BOOLEAN DEFAULT 0",
    "error_string": "TEXT NULL",
    "geo_code": "VARCHAR(50) NULL",
    "values": "JSON NULL",
}


def ensure_schema():
    import_models()
    Base.metadata.create_all(bind=engine)
    _ensure_device_columns()


def _ensure_device_columns():
    inspector = inspect(engine)
    if "devices" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("devices")}
    with engine.begin() as conn:
        for name, ddl in DEVICE_EXTRA_COLUMNS.items():
            if name in existing:
                continue
            try:
                conn.execute(text(f"ALTER TABLE devices ADD COLUMN `{name}` {ddl}"))
                logger.info("Added column devices.%s", name)
            except Exception as exc:
                logger.warning("Skip column %s: %s", name, exc)
