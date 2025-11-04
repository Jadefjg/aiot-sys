from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.user import Permission
from app.schemas.permission import PermissionCreate, PermissionUpdate


class CRUDPermission:
    """CPCRUDÍ\{"""

    def get(self, db: Session, permission_id: int) -> Optional[Permission]:
        """9nID·ÖCP"""
        return db.query(Permission).filter(Permission.id == permission_id).first()

    def get_by_name(self, db: Session, name: str) -> Optional[Permission]:
        """9nð·ÖCP"""
        return db.query(Permission).filter(Permission.name == name).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Permission]:
        """·ÖCPh"""
        return db.query(Permission).offset(skip).limit(limit).all()

    def get_by_resource(self, db: Session, resource: str) -> List[Permission]:
        """9nD{‹·ÖCPh"""
        return db.query(Permission).filter(Permission.resource == resource).all()

    def get_by_action(self, db: Session, action: str) -> List[Permission]:
        """9nÍ\{‹·ÖCPh"""
        return db.query(Permission).filter(Permission.action == action).all()

    def create(self, db: Session, *, obj_in: PermissionCreate) -> Permission:
        """úCP"""
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
        """ô°CP"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, permission_id: int) -> Permission:
        """ dCP"""
        obj = db.query(Permission).get(permission_id)
        db.delete(obj)
        db.commit()
        return obj


# úCPCRUDž‹
permission_crud = CRUDPermission()
