# 用户管理API端点

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.user import user_crud
from app.db.session import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.api.v1.endpoints.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取用户列表"""
    users = user_crud.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """创建新用户"""
    # 检查用户名是否已存在
    user = user_crud.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="该用户名已被注册",
        )
    # 检查邮箱是否已存在
    if user_in.email:
        user = user_crud.get_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=400,
                detail="该邮箱已被注册",
            )
    user = user_crud.create(db, obj_in=user_in)
    return user


@router.get("/me", response_model=User)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取当前用户信息"""
    return current_user


@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """根据ID获取用户"""
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """更新用户信息"""
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )
    user = user_crud.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}")
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """删除用户"""
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )
    user_crud.delete(db, user_id=user_id)
    return {"message": "用户已删除"}


@router.post("/{user_id}/roles/{role_id}")
def assign_role_to_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """为用户分配角色"""
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_crud.assign_role(db, user_id=user_id, role_id=role_id)
    return {"message": "角色分配成功"}


@router.delete("/{user_id}/roles/{role_id}")
def remove_role_from_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """移除用户角色"""
    user = user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user_crud.remove_role(db, user_id=user_id, role_id=role_id)
    return {"message": "角色移除成功"}
