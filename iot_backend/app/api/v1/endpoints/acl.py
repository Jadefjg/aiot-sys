"""产品 / 设备 ACL 与当前用户授权快照"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.crud.acl import acl_crud
from app.crud.device import device_crud
from app.crud.product import product_crud
from app.crud.user import user_crud
from app.db.session import get_db
from app.schemas.acl import AccessSnapshot, AclEntry, AclGrant, AclList, UserOption
from app.schemas.user import User
from app.services import access_control as access

router = APIRouter()


def _username(db: Session, user_id: int) -> str:
    user = user_crud.get_user(db, user_id)
    return user.username if user else str(user_id)


@router.get("/me", response_model=AccessSnapshot)
def my_access(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return access.snapshot(db, current_user)


@router.get("/users", response_model=List[UserOption])
def user_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """授权下拉：仅 id / 用户名"""
    _ = current_user
    users = user_crud.get_multi(db, skip=0, limit=500)
    return [UserOption(id=u.id, username=u.username) for u in users]


@router.get("/products/{product_id}", response_model=AclList)
def list_product_acl(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if not product_crud.get_by_product_id(db, product_id):
        raise HTTPException(status_code=404, detail="产品不存在")
    my_role = access.ensure_product(db, current_user, product_id, "viewer")
    items = [
        AclEntry(user_id=r.user_id, username=_username(db, r.user_id), role=r.role, product_id=product_id)
        for r in acl_crud.list_product(db, product_id)
    ]
    return AclList(my_role=my_role, items=items)


@router.post("/products/{product_id}", response_model=AclEntry)
def grant_product_acl(
    product_id: str,
    body: AclGrant,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if not product_crud.get_by_product_id(db, product_id):
        raise HTTPException(status_code=404, detail="产品不存在")
    access.ensure_product(db, current_user, product_id, "admin")
    if not user_crud.get_user(db, body.user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    row = acl_crud.upsert_product(db, body.user_id, product_id, body.role)
    return AclEntry(
        user_id=row.user_id, username=_username(db, row.user_id),
        role=row.role, product_id=product_id,
    )


@router.delete("/products/{product_id}/{user_id}")
def revoke_product_acl(
    product_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    access.ensure_product(db, current_user, product_id, "admin")
    if not acl_crud.delete_product(db, user_id, product_id):
        raise HTTPException(status_code=404, detail="授权不存在")
    return {"ok": True}


@router.get("/devices/{device_id}", response_model=AclList)
def list_device_acl(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    my_role = access.ensure_device(db, current_user, device, "viewer")
    items = [
        AclEntry(user_id=r.user_id, username=_username(db, r.user_id), role=r.role, device_id=device_id)
        for r in acl_crud.list_device(db, device_id)
    ]
    return AclList(my_role=my_role, items=items)


@router.post("/devices/{device_id}", response_model=AclEntry)
def grant_device_acl(
    device_id: str,
    body: AclGrant,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    access.ensure_device(db, current_user, device, "admin")
    if not user_crud.get_user(db, body.user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    row = acl_crud.upsert_device(db, body.user_id, device_id, body.role)
    return AclEntry(
        user_id=row.user_id, username=_username(db, row.user_id),
        role=row.role, device_id=device_id,
    )


@router.delete("/devices/{device_id}/{user_id}")
def revoke_device_acl(
    device_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    device = device_crud.get_by_device_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    access.ensure_device(db, current_user, device, "admin")
    if not acl_crud.delete_device(db, user_id, device_id):
        raise HTTPException(status_code=404, detail="授权不存在")
    return {"ok": True}
