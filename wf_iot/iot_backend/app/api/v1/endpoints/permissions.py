from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.permission import Permission, PermissionCreate, PermissionUpdate
from app.crud.permission import permission_crud
from app.core.dependencies import get_current_active_user, get_current_active_superuser
from app.db.models.user import User

router = APIRouter()


@router.post("/", response_model=Permission, status_code=status.HTTP_201_CREATED)
def create_permission(
    permission_in: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    创建权限（需要超级用户）
    """
    # 检查权限名称是否已存在
    db_permission = permission_crud.get_by_name(db, name=permission_in.name)
    if db_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this name already exists"
        )
    return permission_crud.create(db, obj_in=permission_in)


@router.get("/", response_model=List[Permission])
def get_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取权限列表
    """
    permissions = permission_crud.get_multi(db, skip=skip, limit=limit)
    return permissions


@router.get("/{permission_id}", response_model=Permission)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据ID获取权限详情
    """
    permission = permission_crud.get(db, permission_id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission


@router.get("/resource/{resource}", response_model=List[Permission])
def get_permissions_by_resource(
    resource: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据资源类型获取权限列表
    """
    permissions = permission_crud.get_by_resource(db, resource=resource)
    return permissions


@router.get("/action/{action}", response_model=List[Permission])
def get_permissions_by_action(
    action: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据操作类型获取权限列表
    """
    permissions = permission_crud.get_by_action(db, action=action)
    return permissions


@router.put("/{permission_id}", response_model=Permission)
def update_permission(
    permission_id: int,
    permission_in: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    更新权限（需要超级用户）
    """
    permission = permission_crud.get(db, permission_id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )

    # 如果更改名称，检查是否重复
    if permission_in.name and permission_in.name != permission.name:
        existing_permission = permission_crud.get_by_name(db, name=permission_in.name)
        if existing_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission with this name already exists"
            )

    return permission_crud.update(db, db_obj=permission, obj_in=permission_in)


@router.delete("/{permission_id}", response_model=Permission)
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """
    删除权限（需要超级用户）
    """
    permission = permission_crud.get(db, permission_id=permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission_crud.delete(db, permission_id=permission_id)
