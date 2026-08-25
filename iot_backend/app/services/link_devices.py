"""按连接加载绑定设备，避免全表扫描。"""
from typing import List

from sqlalchemy.orm import Session

from app.crud.device import device_crud
from app.crud.product import product_crud


def bound_devices_for_link(db: Session, link_id: str) -> List[dict]:
    """返回协议插件可用的设备绑定列表。"""
    items = []
    for device in device_crud.get_by_link_id(db, link_id):
        product = product_crud.get_by_product_id(db, device.product_id)
        cfg = ((product.config or {}).get("modbus") if product else None) or {}
        meta = device.device_metadata or {}
        items.append({
            "device_id": device.device_id,
            "product_id": device.product_id,
            "slave": meta.get("slave") or cfg.get("slave_id") or 1,
            "points": cfg.get("points") or [],
            "address": meta.get("address") or meta.get("meter") or "",
        })
    return items
