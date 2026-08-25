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
    "device_metadata": "JSON NULL",
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
    _ensure_script_columns()
    _ensure_indexes()
    _ensure_firmware_version_constraint()
    _ensure_permissions()
    _ensure_default_product()


def _ensure_firmware_version_constraint():
    """将 firmware.version 全局唯一改为 (version, product_id) 组合唯一"""
    inspector = inspect(engine)
    if "firmware" not in inspector.get_table_names():
        return
    indexes = inspector.get_indexes("firmware")
    uniques = {ix["name"]: ix for ix in indexes if ix.get("unique")}
    # MySQL 常把 UNIQUE 列建为 version 单列索引
    with engine.begin() as conn:
        for name, ix in list(uniques.items()):
            cols = ix.get("column_names") or []
            if cols == ["version"] and name != "uq_firmware_version_product":
                try:
                    conn.execute(text(f"ALTER TABLE firmware DROP INDEX `{name}`"))
                    logger.info("Dropped global unique index %s on firmware.version", name)
                except Exception as exc:
                    logger.warning("Skip drop firmware index %s: %s", name, exc)
        existing = {ix["name"] for ix in inspector.get_indexes("firmware")}
        # 重新检查（DROP 后）
        try:
            inspector = inspect(engine)
            existing = {ix["name"] for ix in inspector.get_indexes("firmware")}
        except Exception:
            pass
        if "uq_firmware_version_product" not in existing:
            try:
                conn.execute(
                    text(
                        "ALTER TABLE firmware ADD UNIQUE KEY "
                        "`uq_firmware_version_product` (`version`, `product_id`)"
                    )
                )
                logger.info("Created unique key uq_firmware_version_product")
            except Exception as exc:
                logger.warning("Skip uq_firmware_version_product: %s", exc)


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


def _ensure_script_columns():
    inspector = inspect(engine)
    if "scripts" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("scripts")}
    if "language" in existing:
        return
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE scripts ADD COLUMN `language` VARCHAR(20) DEFAULT 'js'"))
            logger.info("Added column scripts.language")
        except Exception as exc:
            logger.warning("Skip scripts.language: %s", exc)


INDEXES = [
    ("device_data", "ix_device_data_device_ts", "device_id, timestamp"),
    ("devices", "ix_devices_link_id", "link_id"),
    ("channels", "ix_channels_enabled", "enabled"),
    ("data_rules", "ix_data_rules_enabled", "enabled"),
]

DEFAULT_PERMISSIONS = [
    ("通道读取", "channel:read", "channel", "read"),
    ("通道写入", "channel:write", "channel", "write"),
    ("规则写入", "rule:write", "rule", "write"),
    ("连接写入", "link:write", "link", "write"),
]


def _ensure_indexes():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, name, cols in INDEXES:
            if table not in tables:
                continue
            existing = {ix["name"] for ix in inspector.get_indexes(table)}
            if name in existing:
                continue
            try:
                conn.execute(text(f"CREATE INDEX `{name}` ON `{table}` ({cols})"))
                logger.info("Created index %s on %s", name, table)
            except Exception as exc:
                logger.warning("Skip index %s: %s", name, exc)


def _ensure_permissions():
    from app.db.session import SessionLocal
    from app.crud.permission import permission_crud
    from app.schemas.permission import PermissionCreate

    db = SessionLocal()
    try:
        for name, code, resource, action in DEFAULT_PERMISSIONS:
            if permission_crud.get_by_code(db, code):
                continue
            permission_crud.create(
                db,
                obj_in=PermissionCreate(
                    name=name, code=code, resource=resource, action=action, description=name
                ),
            )
            logger.info("Seeded permission %s", code)
    except Exception as exc:
        logger.warning("Seed permissions: %s", exc)
    finally:
        db.close()


def _ensure_default_product():
    """保证 demo-meter-1 等默认产品存在，便于 ACL 与物解析"""
    from app.crud.product import product_crud
    from app.db.session import SessionLocal
    from app.schemas.product import ProductCreate

    db = SessionLocal()
    try:
        if product_crud.get_by_product_id(db, "default"):
            return
        product_crud.create(
            db,
            ProductCreate(
                product_id="default",
                name="默认电表产品",
                protocol="mqtt",
                description="演示设备默认产品，含温度/电能物模型",
                model={
                    "properties": [
                        {"name": "temperature", "label": "温度", "unit": "℃", "type": "number", "mode": "r"},
                        {"name": "energy", "label": "电能", "unit": "kWh", "type": "number", "mode": "r"},
                        {"name": "voltage", "label": "电压", "unit": "V", "type": "number", "mode": "r"},
                        {"name": "switch", "label": "开关", "type": "boolean", "mode": "rw"},
                    ],
                    "events": [],
                    "actions": [{"name": "reboot", "label": "重启", "type": "button"}],
                    "validators": [],
                    "settings": [],
                },
                config={"parser": {"type": "json", "mapping": {}}},
            ),
        )
        logger.info("Seeded product default")
    except Exception as exc:
        logger.warning("Seed default product: %s", exc)
    finally:
        db.close()
