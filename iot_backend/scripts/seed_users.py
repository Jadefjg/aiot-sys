#!/usr/bin/env python3
"""初始化默认超级用户（需 MySQL 已启动）"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db import models  # noqa: F401
from app.crud.user import user_crud
from app.schemas.user import UserCreate

DEFAULT_USERS = [
    ("admin", "admin123", "admin@example.com"),
    ("feng", "feng123", "feng@example.com"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = {u.username for u in user_crud.get_multi(db, skip=0, limit=200)}
        for username, password, email in DEFAULT_USERS:
            if username in existing:
                print(f"skip existing: {username}")
                continue
            user_crud.create_user(
                db,
                UserCreate(
                    username=username,
                    email=email,
                    password=password,
                    full_name=username,
                    is_superuser=True,
                ),
            )
            print(f"created: {username} / {password}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
