#!/usr/bin/env python3
"""初始化默认超级用户（需 MySQL 已启动）

对演示账号：不存在则创建；存在但密码不匹配则重置为默认密码，
保证 admin / superadmin 可用 admin123 登录。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db import models  # noqa: F401
from app.crud.user import user_crud
from app.core.security import verify_password
from app.schemas.user import UserCreate, UserUpdate

# username, password, email — 演示环境固定账号
DEFAULT_USERS = [
    ("admin", "admin123", "admin@example.com"),
    ("superadmin", "admin123", "superadmin@example.com"),
    ("feng", "feng123", "feng@example.com"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for username, password, email in DEFAULT_USERS:
            user = user_crud.get_by_username(db, username)
            if not user:
                user_crud.create_user(
                    db,
                    UserCreate(
                        username=username,
                        email=email,
                        password=password,
                        full_name=username,
                        is_superuser=True,
                        is_active=True,
                    ),
                )
                print(f"created: {username} / {password}")
                continue

            changed = False
            if not verify_password(password, user.hashed_password):
                user_crud.update(db, user, UserUpdate(password=password))
                user = user_crud.get_by_username(db, username)
                changed = True
                print(f"reset password: {username} / {password}")
            if not user.is_active:
                user.is_active = True
                db.add(user)
                db.commit()
                changed = True
                print(f"reactivated: {username}")
            if not user.is_superuser:
                user.is_superuser = True
                db.add(user)
                db.commit()
                changed = True
                print(f"granted superuser: {username}")
            if not changed:
                print(f"skip existing: {username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
