"""产品/设备细粒度授权：owner=admin，设备 ACL 覆盖产品 ACL"""
from typing import Iterable, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from app.crud.acl import acl_crud
from app.crud.device import device_crud
from app.crud.product import product_crud
from app.db.models.device import Device
from app.db.models.product import Product
from app.db.models.user import User

RANK = {"viewer": 1, "operator": 2, "admin": 3}


def best_role(*roles: Optional[str]) -> Optional[str]:
    picked = None
    score = 0
    for role in roles:
        n = RANK.get(role or "", 0)
        if n > score:
            picked, score = role, n
    return picked


def allowed(role: Optional[str], min_role: str) -> bool:
    return RANK.get(role or "", 0) >= RANK.get(min_role, 99)


def product_role(db: Session, user: User, product_id: str) -> Optional[str]:
    if user.is_superuser:
        return "admin"
    row = acl_crud.get_product(db, user.id, product_id)
    inherited = None
    owned = (
        db.query(Device.id)
        .filter(Device.product_id == product_id, Device.owner_id == user.id)
        .first()
    )
    if owned:
        inherited = "viewer"
    else:
        device_ids = [r.device_id for r in acl_crud.list_device_for_user(db, user.id)]
        if device_ids and db.query(Device.id).filter(
            Device.product_id == product_id, Device.device_id.in_(device_ids)
        ).first():
            inherited = "viewer"
    return best_role(row.role if row else None, inherited)


def device_role(db: Session, user: User, device: Device) -> Optional[str]:
    if user.is_superuser:
        return "admin"
    owner = "admin" if device.owner_id == user.id else None
    drow = acl_crud.get_device(db, user.id, device.device_id)
    prow = acl_crud.get_product(db, user.id, device.product_id) if device.product_id else None
    return best_role(owner, drow.role if drow else None, prow.role if prow else None)


def ensure_device(db: Session, user: User, device: Device, min_role: str = "viewer") -> str:
    role = device_role(db, user, device)
    if not allowed(role, min_role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
    return role or "viewer"


def ensure_product(db: Session, user: User, product_id: str, min_role: str = "viewer") -> str:
    role = product_role(db, user, product_id)
    if not allowed(role, min_role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
    return role or "viewer"


def load_device(db: Session, user: User, device_id: str, min_role: str = "viewer") -> Device:
    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    ensure_device(db, user, device, min_role)
    return device


def load_product(db: Session, user: User, product_id: str, min_role: str = "viewer"):
    product = product_crud.get_by_product_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    ensure_product(db, user, product_id, min_role)
    return product


def visible_device_query(db: Session, user: User) -> Query:
    query = db.query(Device)
    if user.is_superuser:
        return query
    products = [r.product_id for r in acl_crud.list_product_for_user(db, user.id)]
    devices = [r.device_id for r in acl_crud.list_device_for_user(db, user.id)]
    conds = [Device.owner_id == user.id]
    if products:
        conds.append(Device.product_id.in_(products))
    if devices:
        conds.append(Device.device_id.in_(devices))
    return query.filter(or_(*conds))


def list_visible_devices(
    db: Session,
    user: User,
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
) -> List[Device]:
    query = visible_device_query(db, user)
    if product_id:
        query = query.filter(Device.product_id == product_id)
    if gateway_id:
        query = query.filter(Device.gateway_id == gateway_id)
    return query.offset(skip).limit(limit).all()


def visible_product_ids(db: Session, user: User) -> List[str]:
    if user.is_superuser:
        return [p.product_id for p in db.query(Product.product_id).all()]
    ids = {r.product_id for r in acl_crud.list_product_for_user(db, user.id)}
    for device in visible_device_query(db, user).all():
        if device.product_id:
            ids.add(device.product_id)
    return list(ids)


def list_visible_products(db: Session, user: User, skip: int = 0, limit: int = 100) -> List[Product]:
    query = db.query(Product)
    if not user.is_superuser:
        ids = visible_product_ids(db, user)
        if not ids:
            return []
        query = query.filter(Product.product_id.in_(ids))
    return query.offset(skip).limit(limit).all()


def snapshot(db: Session, user: User) -> dict:
    if user.is_superuser:
        return {"is_superuser": True, "products": {}, "devices": {}}
    products = {r.product_id: r.role for r in acl_crud.list_product_for_user(db, user.id)}
    devices = {}
    for device in visible_device_query(db, user).limit(5000).all():
        role = device_role(db, user, device)
        if role:
            devices[device.device_id] = role
    return {"is_superuser": False, "products": products, "devices": devices}


def visible_device_pk_ids(db: Session, user: User) -> Optional[Iterable[int]]:
    """非超管返回可见设备主键；超管返回 None 表示不过滤"""
    if user.is_superuser:
        return None
    return [d.id for d in visible_device_query(db, user).all()]


def visible_device_id_set(db: Session, user: User) -> Optional[set]:
    """非超管返回可见 device_id 字符串集合；超管返回 None"""
    if user.is_superuser:
        return None
    return {d.device_id for d in visible_device_query(db, user).all()}


def ensure_gateway(db: Session, user: User, gateway_id: Optional[str], min_role: str = "operator") -> None:
    """网关设备 ACL；未指定 gateway 时仅超管可操作全局自动化"""
    if user.is_superuser:
        return
    if not gateway_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="全局场景/任务仅超级管理员可操作，请指定 gateway_id",
        )
    load_device(db, user, gateway_id, min_role)


def ensure_devices(
    db: Session,
    user: User,
    device_ids: Iterable[Optional[str]],
    min_role: str = "operator",
) -> None:
    """校验一组设备标识的 ACL"""
    if user.is_superuser:
        return
    seen = set()
    for device_id in device_ids:
        if not device_id or device_id in seen:
            continue
        seen.add(device_id)
        load_device(db, user, device_id, min_role)


def filter_by_gateway(rows: list, db: Session, user: User) -> list:
    """按可见网关过滤场景/任务/脚本/联动"""
    visible = visible_device_id_set(db, user)
    if visible is None:
        return rows
    return [r for r in rows if not getattr(r, "gateway_id", None) or r.gateway_id in visible]


def can_enumerate_users(db: Session, user: User) -> bool:
    """仅超管或具备任一产品/设备 admin 的用户可枚举用户列表"""
    if user.is_superuser:
        return True
    for row in acl_crud.list_product_for_user(db, user.id):
        if row.role == "admin":
            return True
    for row in acl_crud.list_device_for_user(db, user.id):
        if row.role == "admin":
            return True
    return False


def collect_scene_device_ids(scene_like) -> List[str]:
    """从场景 triggers/actions 提取设备 ID"""
    ids: List[str] = []
    for item in getattr(scene_like, "triggers", None) or []:
        if isinstance(item, dict) and item.get("device_id"):
            ids.append(item["device_id"])
    for item in getattr(scene_like, "actions", None) or []:
        if isinstance(item, dict) and item.get("device_id"):
            ids.append(item["device_id"])
    for item in getattr(scene_like, "conditions", None) or []:
        if isinstance(item, dict) and item.get("device_id"):
            ids.append(item["device_id"])
    return ids
