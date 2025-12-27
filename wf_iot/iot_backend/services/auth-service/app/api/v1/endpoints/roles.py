# 角色管理API端点

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.user import role_crud
from app.db.session import get_db
from app.schemas.user import Role, RoleCreate, User, Permission
from app.api.v1.endpoints.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[Role])
def read_roles(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取角色列表"""
    roles = role_crud.get_multi(db, skip=skip, limit=limit)
    return roles


@router.post("/", response_model=Role)
def create_role(
    *,
    db: Session = Depends(get_db),
    role_in: RoleCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """创建新角色"""
    role = role_crud.get_by_name(db, name=role_in.name)
    if role:
        raise HTTPException(
            status_code=400,
            detail="该角色名已存在",
        )
    role = role_crud.create(db, obj_in=role_in)
    return role


@router.get("/{role_id}", response_model=Role)
def read_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """根据ID获取角色"""
    role = role_crud.get(db, role_id=role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail="角色不存在",
        )
    return role


@router.delete("/{role_id}")
def delete_role(
    *,
    db: Session = Depends(get_db),
    role_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """删除角色"""
    role = role_crud.get(db, role_id=role_id)
    if not role:
        raise HTTPException(
            status_code=404,
            detail="角色不存在",
        )
    role_crud.delete(db, role_id=role_id)
    return {"message": "角色已删除"}


@router.get("/{role_id}/permissions", response_model=List[Permission])
def read_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取角色的权限列表"""
    role = role_crud.get(db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    permissions = role_crud.get_role_permissions(db, role_id=role_id)
    return permissions


@router.post("/{role_id}/permissions/{permission_id}")
def assign_permission_to_role(
    *,
    db: Session = Depends(get_db),
    role_id: int,
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """为角色分配权限"""
    role = role_crud.get(db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    role_crud.assign_permission(db, role_id=role_id, permission_id=permission_id)
    return {"message": "权限分配成功"}


@router.delete("/{role_id}/permissions/{permission_id}")
def remove_permission_from_role(
    *,
    db: Session = Depends(get_db),
    role_id: int,
    permission_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """移除角色权限"""
    role = role_crud.get(db, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    role_crud.remove_permission(db, role_id=role_id, permission_id=permission_id)
    return {"message": "权限移除成功"}
