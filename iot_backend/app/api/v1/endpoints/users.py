from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_superuser, get_current_active_user
from app.crud.user import role_crud, user_crud
from app.db.session import get_db
from app.schemas.user import Role, User, UserCreate, UserRolesAssign, UserUpdate


router = APIRouter()


@router.get("/", response_model=List[User])
def read_user(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """Retrieve users"""
    return user_crud.get_multi(db, skip=skip, limit=limit, current_user=current_user)


@router.post("/", response_model=User)
def create_user(
    *,
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """Create new user"""
    user = user_crud.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    if user_in.email:
        user = user_crud.get_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(status_code=400, detail="Email already registered")
    return user_crud.create_user(db, obj_in=user_in)


@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    password: str = None,
    full_name: str = None,
    email: str = None,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Update own user."""
    update_in = UserUpdate()
    if password is not None:
        update_in.password = password
    if full_name is not None:
        update_in.full_name = full_name
    if email is not None:
        update_in.email = email
    return user_crud.update(db, db_obj=current_user, obj_in=update_in)


@router.get("/me", response_model=User)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Get current user."""
    return current_user


@router.get("/me/permissions")
def read_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """获取当前用户权限代码列表"""
    if current_user.is_superuser:
        return {"permissions": ["*"]}
    permissions = user_crud.get_user_permissions(db, current_user.id)
    return {"permissions": [p.code for p in permissions]}


@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    user = user_crud.get_user(db, user_id=user_id)
    if user == current_user:
        return user
    if not user_crud.is_superuser(current_user):
        raise HTTPException(status_code=404, detail="User not found")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=User)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user_crud.is_superuser(current_user) and user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_data = user_in.model_dump(exclude_unset=True)
    if not user_crud.is_superuser(current_user):
        update_data.pop("is_superuser", None)
    if "username" not in update_data:
        # 保持兼容：未传 username 时不改用户名
        pass
    return user_crud.update(db, db_obj=user, obj_in=UserUpdate(**update_data))


@router.delete("/{user_id}")
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """删除用户"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_crud.delete(db, id=user_id)
    return {"message": "用户已删除"}


@router.get("/{user_id}/roles", response_model=List[Role])
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """获取用户已分配角色"""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_crud.get_user_roles(db, user_id)


@router.post("/{user_id}/roles", status_code=status.HTTP_200_OK)
def assign_roles_to_user(
    user_id: int,
    body: UserRolesAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """批量分配用户角色"""
    user = user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for role_id in body.role_ids:
        if not role_crud.get(db, id=role_id):
            raise HTTPException(status_code=404, detail=f"Role {role_id} not found")

    roles = user_crud.set_user_roles(db, user_id=user_id, role_ids=body.role_ids)
    return {
        "message": "角色分配成功",
        "roles": [Role.model_validate(r) for r in roles],
    }
