#!/usr/bin/env python3
"""Create an isolated load-test tenant, user, product, and devices.

Intended for a local/test database only. Idempotent by stable IDs.
"""
import argparse
import json
import os
import sys
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core import security
from app.db.session import SessionLocal
from app.db.models.tenant import Tenant
from app.db.models.user import User
from app.db.models.product import Product
from app.db.models.device import Device


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--devices", type=int, default=100)
    p.add_argument("--tenant-id", default="perf-local")
    p.add_argument("--username", default="perf_load_user")
    p.add_argument("--password", default="Perf-Load-Only-ChangeMe-123!")
    p.add_argument("--ttl-minutes", type=int, default=30)
    args = p.parse_args()
    if args.devices < 1 or args.devices > 10000:
        raise SystemExit("devices 必须在 1..10000；万级请使用专用压测机")
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.tenant_id == args.tenant_id).first()
        if not tenant:
            tenant = Tenant(tenant_id=args.tenant_id, name="Local Performance Test", enabled=True)
            db.add(tenant); db.flush()
        user = db.query(User).filter(User.username == args.username).first()
        if not user:
            user = User(username=args.username, email=f"{args.username}@invalid.local", hashed_password=security.get_password_hash(args.password), is_active=True, is_superuser=True, tenant_id=tenant.id)
            db.add(user); db.flush()
        else:
            user.tenant_id, user.is_superuser, user.is_active = tenant.id, True, True
        product_id = f"perf-product-{args.tenant_id}"
        product = db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            product = Product(product_id=product_id, tenant_id=tenant.id, name="Performance Sensor", protocol="MQTT", version="1.0", model={"properties":[{"name":"temperature","type":"number"}],"events":[],"actions":[],"validators":[],"settings":[]})
            db.add(product); db.flush()
        for i in range(args.devices):
            did = f"perf-{args.tenant_id}-{i:06d}"
            if not db.query(Device).filter(Device.device_id == did).first():
                db.add(Device(device_id=did, device_name=did, product_id=product_id, tenant_id=tenant.id, owner_id=user.id, status="offline", values={}))
        db.commit()
        token = security.create_access_token({"sub": user.username}, timedelta(minutes=args.ttl_minutes))
        print(json.dumps({"tenant_id": tenant.tenant_id, "tenant_pk": tenant.id, "username": user.username, "password": args.password, "product_id": product_id, "devices": args.devices, "token": token, "expires_in_minutes": args.ttl_minutes}, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
