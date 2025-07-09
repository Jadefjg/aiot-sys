# 作用：依赖注入

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.db.session import get_db
from app.crud.user import user_crud,role_crud
from app.schemas.user import User
from app.core.config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")
async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=
        [settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = user_crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# 权限检查依赖 (示例，实际可能更复杂)
def has_permission(permission_name: str):
    def _has_permission(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        # 检查 current_user 是否拥有 permission_name 权限
        # 这需要查询 UserRole 和 RolePermission 表
        # 简化示例：假设用户ID为1是管理员，拥有所有权限
        if current_user.id == 1: # For demonstration, replace with actual permission check
            return True
        # 实际逻辑：
        # user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
        # for ur in user_roles:
        # role_permissions = db.query(RolePermission).filter(RolePermission.role_id == ur.role_id).all()
        # for rp in role_permissions:
        # permission = db.query(Permission).filter(Permission.id == rp.permission_id, Permission.name == permission_name).first()
        # if permission:
        # return True
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return _has_permission