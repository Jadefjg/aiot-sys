"""
角色管理API端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.user import (
    Role, RoleCreate, RoleUpdate, RoleWithPermissions,
    RolePermissionsAssign,
)
from app.schemas.permission import Permission as PermissionOut
from app.crud.user import role_crud
from app.crud.permission import permission_crud
from app.core.dependencies import get_current_active_user


router = APIRouter()


def _role_with_permissions(db: Session, role) -> RoleWithPermissions:
    """组装带权限列表的角色响应"""
    permissions = role_crud.get_role_permissions(db, role_id=role.id)
    return RoleWithPermissions(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=permissions,
    )


@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """创建新角色"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
    db_role = role_crud.get_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(status_code=400, detail="角色名称已存在")
    return role_crud.create(db=db, obj_in=role)


@router.get("/", response_model=List[RoleWithPermissions])
def get_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """获取角色列表"""
    roles = role_crud.get_multi(db, skip=skip, limit=limit)
    return [_role_with_permissions(db, role) for role in roles]


@router.get("/{role_id}", response_model=RoleWithPermissions)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """根据ID获取角色"""
    role = role_crud.get(db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return _role_with_permissions(db, role)


@router.put("/{role_id}", response_model=Role)
def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """更新角色信息"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
    role = role_crud.get(db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    # 检查名称是否冲突
    if role_in.name and role_in.name != role.name:
        existing = role_crud.get_by_name(db, name=role_in.name)
        if existing:
            raise HTTPException(status_code=400, detail="角色名称已存在")
    return role_crud.update(db, db_obj=role, name=role_in.name, description=role_in.description)


@router.delete("/{role_id}", response_model=Role)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """删除角色"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
    role = role_crud.get(db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role_crud.delete(db, id=role_id)


@router.get("/{role_id}/permissions", response_model=List[PermissionOut])
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """获取角色的权限列表"""
    role = role_crud.get(db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    return role_crud.get_role_permissions(db, role_id=role_id)


@router.post("/{role_id}/permissions", status_code=status.HTTP_200_OK)
def assign_permissions_to_role(
    role_id: int,
    body: RolePermissionsAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """批量分配角色权限"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
    role = role_crud.get(db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    for permission_id in body.permission_ids:
        if not permission_crud.get(db, permission_id=permission_id):
            raise HTTPException(
                status_code=404,
                detail=f"Permission {permission_id} not found",
            )

    permissions = role_crud.set_role_permissions(
        db, role_id=role_id, permission_ids=body.permission_ids
    )
    return {
        "message": "权限分配成功",
        "permissions": [PermissionOut.model_validate(p) for p in permissions],
    }


@router.post("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_201_CREATED)
def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """为角色分配权限"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
    role = role_crud.get(db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if not permission_crud.get(db, permission_id=permission_id):
        raise HTTPException(status_code=404, detail="Permission not found")
    role_crud.assign_permission(db, role_id=role_id, permission_id=permission_id)
    return {"message": "权限分配成功"}


@router.delete("/{role_id}/permissions/{permission_id}")
def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """移除角色的权限"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
    role = role_crud.get(db, id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    success = role_crud.remove_permission(db, role_id=role_id, permission_id=permission_id)
    if not success:
        raise HTTPException(status_code=404, detail="角色未分配该权限")
    return {"message": "权限移除成功"}
