"""告警 CRUD"""
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models.alarm import Alarm
from app.schemas.alarm import AlarmCreate


class CRUDAlarm:
    def create(self, db: Session, obj_in: AlarmCreate) -> Alarm:
        db_obj = Alarm(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: int) -> Optional[Alarm]:
        return db.query(Alarm).filter(Alarm.id == id).first()

    def get_multi(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        device_id: Optional[int] = None,
        acknowledged: Optional[bool] = None,
    ) -> List[Alarm]:
        query = db.query(Alarm)
        if device_id is not None:
            query = query.filter(Alarm.device_id == device_id)
        if acknowledged is not None:
            query = query.filter(Alarm.acknowledged == acknowledged)
        return query.order_by(desc(Alarm.created_at)).offset(skip).limit(limit).all()

    def acknowledge(self, db: Session, alarm: Alarm, user_id: int) -> Alarm:
        from datetime import datetime

        alarm.acknowledged = True
        alarm.acknowledged_at = datetime.utcnow()
        alarm.acknowledged_by = user_id
        db.add(alarm)
        db.commit()
        db.refresh(alarm)
        return alarm


alarm_crud = CRUDAlarm()
