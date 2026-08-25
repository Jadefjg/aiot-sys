"""连接器 CRUD"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.link import Link
from app.schemas.link import LinkCreate, LinkUpdate


class CRUDLink:
    def get(self, db: Session, id: int) -> Optional[Link]:
        return db.query(Link).filter(Link.id == id).first()

    def get_by_link_id(self, db: Session, link_id: str) -> Optional[Link]:
        return db.query(Link).filter(Link.link_id == link_id).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        gateway_id: Optional[str] = None,
    ) -> List[Link]:
        query = db.query(Link)
        if gateway_id:
            query = query.filter(Link.gateway_id == gateway_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: LinkCreate) -> Link:
        db_obj = Link(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Link, obj_in: LinkUpdate) -> Link:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Link]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def set_status(
        self, db: Session, link_id: str, status: str, error: Optional[str] = None
    ) -> Optional[Link]:
        obj = self.get_by_link_id(db, link_id)
        if not obj:
            return None
        obj.status = status
        obj.error_string = error
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


link_crud = CRUDLink()
