#!/usr/bin/env python3
"""补齐演示产品与设备引用的默认产品"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db import models  # noqa: F401
from app.crud.product import product_crud
from app.crud.device import device_crud
from app.schemas.product import ProductCreate

DEFAULT_PRODUCTS = [
    ProductCreate(
        product_id="default",
        name="默认产品",
        description="演示设备默认产品",
        protocol="mqtt",
        version="1.0",
        controllable=True,
        writable=True,
        model={
            "properties": [
                {"name": "energy", "label": "电能", "type": "number", "mode": "r", "unit": "kWh"},
                {"name": "temperature", "label": "温度", "type": "number", "mode": "r", "unit": "℃"},
            ],
            "events": [],
            "actions": [],
            "validators": [],
            "settings": [],
        },
    ),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for item in DEFAULT_PRODUCTS:
            if product_crud.get_by_product_id(db, item.product_id):
                print(f"skip existing product: {item.product_id}")
                continue
            product_crud.create(db, item)
            print(f"created product: {item.product_id}")

        orphan_ids = {
            d.product_id
            for d in device_crud.get_multi(db, skip=0, limit=10000)
            if d.product_id and not product_crud.get_by_product_id(db, d.product_id)
        }
        for product_id in sorted(orphan_ids):
            product_crud.create(
                db,
                ProductCreate(
                    product_id=product_id,
                    name=product_id,
                    protocol="mqtt",
                    version="1.0",
                    controllable=True,
                    writable=True,
                    model={
                        "properties": [],
                        "events": [],
                        "actions": [],
                        "validators": [],
                        "settings": [],
                    },
                ),
            )
            print(f"created orphan product: {product_id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
