# 权限管理API端点

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.user import permission_crud
from app.db.session import get_db
from app.schemas.user import Permission, PermissionCreate, User
from app.api.v1.endpoints.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[Permission])
def read_permissions(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取权限列表"""
    permissions = permission_crud.get_multi(db, skip=skip, limit=limit)
    return permissions


@router.post("/", response_model=Permission)
def create_permission(
    *,
    db: Session = Depends(get_db),
    permission_in: PermissionCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """创建新权限"""
    permission = permission_crud.get_by_name(db, name=permission_in.name)
    if permission:
        raise HTTPException(
            status_code=400,
            detail="该权限名已存在",
        )
    permission = permission_crud.create(db, obj_in=permission_in)
    return permission


@router.get("/{permission_id}", response_model=Permission)
def read_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """根据ID获取权限"""
    permission = permission_crud.get(db, permission_id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=404,
            detail="权限不存在",
        )
    return permission


@router.delete("/{permission_id}")
def delete_permission(
    *,
    db: Session = Depends(get_db),
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """删除权限"""
    permission = permission_crud.get(db, permission_id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=404,
            detail="权限不存在",
        )
    permission_crud.delete(db, permission_id=permission_id)
    return {"message": "权限已删除"}


@router.get("/resource/{resource}", response_model=List[Permission])
def read_permissions_by_resource(
    resource: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """根据资源获取权限列表"""
    permissions = permission_crud.get_by_resource(db, resource=resource)
    return permissions
