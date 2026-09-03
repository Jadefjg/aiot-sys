from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.media import DeviceMedia


class CRUDMedia:
    def get(self, db: Session, media_id: int) -> Optional[DeviceMedia]:
        return db.query(DeviceMedia).filter(DeviceMedia.id == media_id).first()

    def get_by_key(self, db: Session, object_key: str) -> Optional[DeviceMedia]:
        return db.query(DeviceMedia).filter(DeviceMedia.object_key == object_key).first()

    def list_by_device(self, db: Session, device_id: str, limit: int = 50) -> List[DeviceMedia]:
        return (
            db.query(DeviceMedia)
            .filter(DeviceMedia.device_id == device_id)
            .order_by(DeviceMedia.id.desc())
            .limit(limit)
            .all()
        )

    def create(self, db: Session, **kwargs) -> DeviceMedia:
        row = DeviceMedia(**kwargs)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def update_ai(self, db: Session, row: DeviceMedia, status: str, result: dict) -> DeviceMedia:
        row.ai_status = status
        row.ai_result = result
        db.add(row)
        db.commit()
        db.refresh(row)
        return row


media_crud = CRUDMedia()
