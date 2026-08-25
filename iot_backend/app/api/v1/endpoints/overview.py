"""控制台总览：一次返回仪表盘/大屏 KPI"""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.crud.alarm import alarm_crud
from app.crud.channel import channel_crud, rule_crud
from app.crud.group import group_crud
from app.db.session import get_db
from app.schemas.user import User
from app.services import access_control as access
from app.services.timeseries import timeseries

router = APIRouter()


@router.get("/")
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    query = access.visible_device_query(db, current_user)
    devices = query.limit(5000).all()
    online = sum(1 for d in devices if d.status == "online")
    errors = sum(1 for d in devices if d.error)
    products = access.list_visible_products(db, current_user, limit=500)
    pks = access.visible_device_pk_ids(db, current_user)
    alarms = alarm_crud.get_multi(db, limit=8, acknowledged=False, device_ids=pks)
    return {
        "devices": len(devices),
        "online": online,
        "offline": max(len(devices) - online, 0),
        "errors": errors,
        "products": len(products),
        "groups": len(group_crud.get_multi(db, limit=500)),
        "channels": len(channel_crud.get_multi(db, limit=200)),
        "rules": len(rule_crud.get_multi(db, limit=200)),
        "influx": {
            "enabled": timeseries.enabled,
            "connected": timeseries.ping() if timeseries.enabled else False,
        },
        "recent_devices": [
            {
                "device_id": d.device_id,
                "device_name": d.device_name,
                "product_id": d.product_id,
                "status": d.status,
                "error": d.error,
            }
            for d in devices[:8]
        ],
        "recent_alarms": [
            {"id": a.id, "title": a.title, "level": a.level, "created_at": a.created_at}
            for a in alarms
        ],
    }
