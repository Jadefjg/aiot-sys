"""产品 / 设备 ACL CRUD"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.acl import DeviceACL, ProductACL


class CRUDAcl:
    def list_product(self, db: Session, product_id: str) -> List[ProductACL]:
        return db.query(ProductACL).filter(ProductACL.product_id == product_id).all()

    def list_device(self, db: Session, device_id: str) -> List[DeviceACL]:
        return db.query(DeviceACL).filter(DeviceACL.device_id == device_id).all()

    def list_product_for_user(self, db: Session, user_id: int) -> List[ProductACL]:
        return db.query(ProductACL).filter(ProductACL.user_id == user_id).all()

    def list_device_for_user(self, db: Session, user_id: int) -> List[DeviceACL]:
        return db.query(DeviceACL).filter(DeviceACL.user_id == user_id).all()

    def get_product(self, db: Session, user_id: int, product_id: str) -> Optional[ProductACL]:
        return (
            db.query(ProductACL)
            .filter(ProductACL.user_id == user_id, ProductACL.product_id == product_id)
            .first()
        )

    def get_device(self, db: Session, user_id: int, device_id: str) -> Optional[DeviceACL]:
        return (
            db.query(DeviceACL)
            .filter(DeviceACL.user_id == user_id, DeviceACL.device_id == device_id)
            .first()
        )

    def upsert_product(self, db: Session, user_id: int, product_id: str, role: str) -> ProductACL:
        row = self.get_product(db, user_id, product_id)
        if row:
            row.role = role
        else:
            row = ProductACL(user_id=user_id, product_id=product_id, role=role)
            db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def upsert_device(self, db: Session, user_id: int, device_id: str, role: str) -> DeviceACL:
        row = self.get_device(db, user_id, device_id)
        if row:
            row.role = role
        else:
            row = DeviceACL(user_id=user_id, device_id=device_id, role=role)
            db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def delete_product(self, db: Session, user_id: int, product_id: str) -> bool:
        row = self.get_product(db, user_id, product_id)
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True

    def delete_device(self, db: Session, user_id: int, device_id: str) -> bool:
        row = self.get_device(db, user_id, device_id)
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True


acl_crud = CRUDAcl()
