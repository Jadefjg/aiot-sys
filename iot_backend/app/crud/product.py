"""产品 CRUD"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class CRUDProduct:
    def get(self, db: Session, id: int) -> Optional[Product]:
        return db.query(Product).filter(Product.id == id).first()

    def get_by_product_id(self, db: Session, product_id: str) -> Optional[Product]:
        return db.query(Product).filter(Product.product_id == product_id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        return db.query(Product).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: ProductCreate) -> Product:
        data = obj_in.model_dump()
        if not data.get("model"):
            data["model"] = {
                "properties": [],
                "events": [],
                "actions": [],
                "validators": [],
                "settings": [],
            }
        db_obj = Product(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Product, obj_in: ProductUpdate) -> Product:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Product]:
        obj = db.query(Product).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


product_crud = CRUDProduct()
