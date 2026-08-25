"""通道、规则、影子 CRUD"""
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models.channel import Channel, ChannelLog, DataRule, DeviceShadow
from app.schemas.channel import ChannelCreate, ChannelUpdate, DataRuleCreate, DataRuleUpdate


class CRUDChannel:
    def get(self, db: Session, id: int) -> Optional[Channel]:
        return db.query(Channel).filter(Channel.id == id).first()

    def get_by_channel_id(self, db: Session, channel_id: str) -> Optional[Channel]:
        return db.query(Channel).filter(Channel.channel_id == channel_id).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100, kind: Optional[str] = None
    ) -> List[Channel]:
        query = db.query(Channel)
        if kind:
            query = query.filter(Channel.kind == kind)
        return query.offset(skip).limit(limit).all()

    def get_enabled(self, db: Session, kind: Optional[str] = None) -> List[Channel]:
        query = db.query(Channel).filter(Channel.enabled.is_(True))
        if kind:
            query = query.filter(Channel.kind == kind)
        return query.all()

    def create(self, db: Session, obj_in: ChannelCreate) -> Channel:
        db_obj = Channel(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Channel, obj_in: ChannelUpdate) -> Channel:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Channel]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def add_log(self, db: Session, channel_id: str, message: str, payload=None, level="info"):
        log = ChannelLog(channel_id=channel_id, message=message, payload=payload, level=level)
        db.add(log)
        db.commit()
        return log

    def list_logs(self, db: Session, channel_id: str, limit: int = 50) -> List[ChannelLog]:
        return (
            db.query(ChannelLog)
            .filter(ChannelLog.channel_id == channel_id)
            .order_by(ChannelLog.id.desc())
            .limit(limit)
            .all()
        )


class CRUDRule:
    def get(self, db: Session, id: int) -> Optional[DataRule]:
        return db.query(DataRule).filter(DataRule.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 200) -> List[DataRule]:
        return db.query(DataRule).offset(skip).limit(limit).all()

    def get_enabled(self, db: Session, product_id: Optional[str] = None) -> List[DataRule]:
        query = db.query(DataRule).filter(DataRule.enabled.is_(True))
        if product_id:
            query = query.filter(
                or_(DataRule.product_id.is_(None), DataRule.product_id == product_id)
            )
        return query.all()

    def create(self, db: Session, obj_in: DataRuleCreate) -> DataRule:
        db_obj = DataRule(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: DataRule, obj_in: DataRuleUpdate) -> DataRule:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[DataRule]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


class CRUDShadow:
    def get(self, db: Session, device_id: str) -> Optional[DeviceShadow]:
        return db.query(DeviceShadow).filter(DeviceShadow.device_id == device_id).first()

    def upsert_reported(self, db: Session, device_id: str, values: dict) -> DeviceShadow:
        obj = self.get(db, device_id)
        if not obj:
            obj = DeviceShadow(device_id=device_id, reported=values, desired={}, version=1)
            db.add(obj)
        else:
            merged = dict(obj.reported or {})
            merged.update(values)
            obj.reported = merged
            obj.version = (obj.version or 1) + 1
            db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def set_desired(self, db: Session, device_id: str, desired: dict) -> DeviceShadow:
        obj = self.get(db, device_id)
        if not obj:
            obj = DeviceShadow(device_id=device_id, reported={}, desired=desired, version=1)
        else:
            obj.desired = desired
            obj.version = (obj.version or 1) + 1
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


channel_crud = CRUDChannel()
rule_crud = CRUDRule()
shadow_crud = CRUDShadow()
