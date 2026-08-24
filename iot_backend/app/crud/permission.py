from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.user import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate


class CRUDPermission:
    """权限CRUD操作类"""

    def get(self, db: Session, permission_id: int) -> Optional[Permission]:
        """根据ID获取权限"""
        return db.query(Permission).filter(Permission.id == permission_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Permission]:
        """根据名称获取权限"""
        return db.query(Permission).filter(Permission.name == name).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Permission]:
        """获取权限列表"""
        return db.query(Permission).offset(skip).limit(limit).all()

    def get_by_resource(self, db: Session, resource: str) -> List[Permission]:
        """根据资源类型获取权限列表"""
        return db.query(Permission).filter(Permission.resource == resource).all()

    def get_by_action(self, db: Session, action: str) -> List[Permission]:
        """根据操作类型获取权限列表"""
        return db.query(Permission).filter(Permission.action == action).all()

    def create(self, db: Session, *, obj_in: PermissionCreate) -> Permission:
        """创建权限"""
        db_obj = Permission(
            name=obj_in.name,
            description=obj_in.description,
            resource=obj_in.resource,
            action=obj_in.action,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: Permission, obj_in: PermissionUpdate
    ) -> Permission:
        """更新权限"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, permission_id: int) -> Permission:
        """删除权限"""
        obj = db.query(Permission).get(permission_id)
        db.delete(obj)
        db.commit()
        return obj


# 权限CRUD实例
permission_crud = CRUDPermission()
