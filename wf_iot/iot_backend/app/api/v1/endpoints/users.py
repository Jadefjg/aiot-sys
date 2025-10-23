from typing import List, Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

from app.db.session import get_db
from app.crud.user import user_crud
from app.schemas.user import User, UserCreate, UserUpdate
from app.core.security import get_current_active_user, get_current_active_superuser


router = APIRouter()


@router.get("/", response_model=List[User])
def read_user(
        db:Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_active_superuser),
    ) -> Any:
    """Retrieve users"""
    users = user_crud.get_multi(db, skip=skip, limit=limit, current_user=current_user)
    return users

@router.post("/", response_model=User)
def create_user(
        *,
        user_in: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_superuser),  # Requires admin/user: create permission
    ) -> Any:
    """Create new user"""
    user = user_crud.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = user_crud.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = user_crud.create_user(db, obj_in=user_in)
    return user


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
    current_user_data = UserUpdate(**current_user.__dict__)
    if password is not None:
        current_user_data.password = password
    if full_name is not None:
        current_user_data.full_name = full_name
    if email is not None:
        current_user_data.email = email
    user = user_crud.update_user(db, obj_in=current_user_data)
    return user

@router.get("/me", response_model=User)
def read_user_me(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ) -> Any:
    """
    Get current user.
    """
    return current_user


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
    # 只有超级用户或用户本人可以更新用户信息
    if not user_crud.is_superuser(current_user) and user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    user = user_crud.update(db, db_obj=user, obj_in=user_in)
    return user