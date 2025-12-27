# 用户、角色、权限CRUD操作

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models.user import User, Role, Permission, UserRole, RolePermission
from app.schemas.user import UserCreate, UserUpdate, RoleCreate, PermissionCreate
from app.core.security import get_password_hash, verify_password


class CRUDUser:
    """用户CRUD操作"""

    def get(self, db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: UserCreate) -> User:
        """创建用户"""
        hashed_password = get_password_hash(obj_in.password)
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=hashed_password,
            full_name=obj_in.full_name,
            is_supperuser=obj_in.is_superuser
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: User, obj_in: UserUpdate) -> User:
        """更新用户"""
        update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, user_id: int) -> Optional[User]:
        """删除用户"""
        obj = db.query(User).filter(User.id == user_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        """验证用户凭证"""
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """检查用户是否激活"""
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        """检查用户是否为超级用户"""
        return user.is_supperuser

    def assign_role(self, db: Session, user_id: int, role_id: int) -> Optional[UserRole]:
        """为用户分配角色"""
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
        """移除用户角色"""
        user_role = db.query(UserRole).filter(
            and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
        ).first()
        if user_role:
            db.delete(user_role)
            db.commit()
            return True
        return False

    def get_user_roles(self, db: Session, user_id: int) -> List[Role]:
        """获取用户的所有角色"""
        roles = db.query(Role).join(UserRole).filter(
            UserRole.user_id == user_id
        ).all()
        return roles

    def get_user_permissions(self, db: Session, user_id: int) -> List[Permission]:
        """获取用户的所有权限"""
        permissions = db.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(
            UserRole.user_id == user_id
        ).distinct().all()
        return permissions

    def has_permission(self, db: Session, user_id: int, resource: str, action: str) -> bool:
        """检查用户是否有特定权限"""
        # 先检查是否为超级用户
        user = self.get(db, user_id)
        if user and user.is_supperuser:
            return True

        permission = db.query(Permission).join(RolePermission).join(Role).join(UserRole).filter(
            and_(
                UserRole.user_id == user_id,
                Permission.resource == resource,
                Permission.action == action
            )
        ).first()
        return permission is not None


class CRUDRole:
    """角色CRUD操作"""

    def get(self, db: Session, role_id: int) -> Optional[Role]:
        """根据ID获取角色"""
        return db.query(Role).filter(Role.id == role_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        return db.query(Role).filter(Role.name == name).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
        """获取角色列表"""
        return db.query(Role).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: RoleCreate) -> Role:
        """创建角色"""
        db_obj = Role(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, role_id: int) -> Optional[Role]:
        """删除角色"""
        obj = db.query(Role).filter(Role.id == role_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def assign_permission(self, db: Session, role_id: int, permission_id: int) -> Optional[RolePermission]:
        """为角色分配权限"""
        existing = db.query(RolePermission).filter(
            and_(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id)
        ).first()
        if existing:
            return existing
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        db.add(role_permission)
        db.commit()
        db.refresh(role_permission)
        return role_permission

    def remove_permission(self, db: Session, role_id: int, permission_id: int) -> bool:
        """移除角色权限"""
        role_permission = db.query(RolePermission).filter(
            and_(RolePermission.role_id == role_id, RolePermission.permission_id == permission_id)
        ).first()
        if role_permission:
            db.delete(role_permission)
            db.commit()
            return True
        return False

    def get_role_permissions(self, db: Session, role_id: int) -> List[Permission]:
        """获取角色的所有权限"""
        permissions = db.query(Permission).join(RolePermission).filter(
            RolePermission.role_id == role_id
        ).all()
        return permissions


class CRUDPermission:
    """权限CRUD操作"""

    def get(self, db: Session, permission_id: int) -> Optional[Permission]:
        """根据ID获取权限"""
        return db.query(Permission).filter(Permission.id == permission_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Permission]:
        """根据名称获取权限"""
        return db.query(Permission).filter(Permission.name == name).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
        """获取权限列表"""
        return db.query(Permission).offset(skip).limit(limit).all()

    def get_by_resource(self, db: Session, resource: str) -> List[Permission]:
        """根据资源获取权限列表"""
        return db.query(Permission).filter(Permission.resource == resource).all()

    def create(self, db: Session, obj_in: PermissionCreate) -> Permission:
        """创建权限"""
        db_obj = Permission(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, permission_id: int) -> Optional[Permission]:
        """删除权限"""
        obj = db.query(Permission).filter(Permission.id == permission_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj


# 实例化CRUD对象
user_crud = CRUDUser()
role_crud = CRUDRole()
permission_crud = CRUDPermission()
