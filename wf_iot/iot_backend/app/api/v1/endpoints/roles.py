from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.user import Role, RoleCreate
from app.crud.user import role_crud # Assuming role_crud is defined in crud/user.py or a separate crud/role.py
from app.core.security import get_current_active_user


router = APIRouter()


@router.post("/", response_model=Role, status_code=status.HTTP_201_CREATED)
def create_new_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Requires admin/role:create permission
    ):
    db_role = role_crud.get_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(status_code=400, detail="Role name already exists")
    return role_crud.create_role(db=db, role=role)

# ... 其他角色管理API，如获取角色列表、更新角色、删除角色、为角色分配权限、为用户分配角色等