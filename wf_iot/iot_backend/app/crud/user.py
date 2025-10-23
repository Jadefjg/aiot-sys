from typing import List, Optional  # Optional[X] 是 Union[X, None] 的简写，表示值可以是类型X或None
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.user import User, Role, Permission, UserRole, RolePermission
from app.schemas.user import UserCreate, UserUpdate, RoleCreate,PermissionCreate
from app.core.security import get_password_hash, verify_password


class CRUDUser:
    def get(self, db: Session, id: int) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, db: Session, obj_in: UserCreate) -> User:
        return self.create(db, obj_in)
    
    def update_user(self, db: Session, obj_in: UserUpdate) -> User:
        # 这个方法需要当前用户对象，这里简化处理
        user = db.query(User).filter(User.username == obj_in.username).first()
        if user:
            return self.update(db, db_obj=user, obj_in=obj_in)
        return None

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100, current_user=None) ->List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: UserCreate) -> User:
        hashed_password = get_password_hash(obj_in.password)
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=hashed_password,
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> User:
        obj = db.query(User).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

    def assign_role(self, db: Session, user_id: int, role_id: int) -> UserRole:
        # 检查是否已经分配了该角色
        existing = db.query(UserRole).filter(
        and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        ).first()
        if existing:
            return existing
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.add(user_role)
        db.commit()
        db.refresh(user_role)
        return user_role

    def remove_role(self, db: Session, user_id: int, role_id: int) -> bool:
        user_role = db.query(UserRole).filter(
            and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        ).first()
        if user_role:
            db.delete(user_role)
            db.commit()
            return True
        return False

    def get_user_permissions(self, db: Session, user_id: int) ->List[Permission]:
        """获取用户的所有权限"""
        permissions = db.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(
            UserRole.user_id == user_id
            ).distinct().all()
        return permissions

    def has_permission(self, db: Session, user_id: int, resource: str, action:str) -> bool:
        """检查用户是否有特定权限"""
        permission = db.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(
        and_(
            UserRole.user_id == user_id,
            Permission.resource == resource,
            Permission.action == action
        )
        ).first()
        return permission is not None


class CRUDRole:
    def get(self, db: Session, id: int) -> Optional[Role]:
        return db.query(Role).filter(Role.id == id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Role]:
        return db.query(Role).filter(Role.name == name).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) ->List[Role]:
        return db.query(Role).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: RoleCreate) -> Role:
        db_obj = Role(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def assign_permission(self, db: Session, role_id: int, permission_id: int) -> RolePermission:
        existing = db.query(RolePermission).filter(
            and_(RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id)
        ).first()
        if existing:
            return existing
        role_permission = RolePermission(role_id=role_id,permission_id=permission_id)
        db.add(role_permission)
        db.commit()
        db.refresh(role_permission)
        return role_permission


class CRUDPermission:
    def get(self, db: Session, id: int) -> Optional[Permission]:
        return db.query(Permission).filter(Permission.id == id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Permission]:
        return db.query(Permission).filter(Permission.name == name).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
        return db.query(Permission).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: PermissionCreate) -> Permission:
        db_obj = Permission(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# 实例化CRUD对象
user_crud = CRUDUser()
role_crud = CRUDRole()
permission_crud = CRUDPermission()