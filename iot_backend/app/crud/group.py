"""分组与智能场景 CRUD"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db.models.group import DeviceGroup
from app.db.models.smart import Binding, Job, Scene, Script
from app.schemas.group import (
    DeviceGroupCreate,
    DeviceGroupUpdate,
    JobCreate,
    JobUpdate,
    SceneCreate,
    SceneUpdate,
)
from app.schemas.link import BindingCreate, BindingUpdate, ScriptCreate, ScriptUpdate


class CRUDDeviceGroup:
    def get(self, db: Session, id: int) -> Optional[DeviceGroup]:
        return db.query(DeviceGroup).filter(DeviceGroup.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[DeviceGroup]:
        return db.query(DeviceGroup).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: DeviceGroupCreate) -> DeviceGroup:
        db_obj = DeviceGroup(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, db_obj: DeviceGroup, obj_in: DeviceGroupUpdate
    ) -> DeviceGroup:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[DeviceGroup]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


class CRUDScene:
    def get(self, db: Session, id: int) -> Optional[Scene]:
        return db.query(Scene).filter(Scene.id == id).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100, gateway_id: Optional[str] = None
    ) -> List[Scene]:
        query = db.query(Scene)
        if gateway_id:
            query = query.filter(Scene.gateway_id == gateway_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: SceneCreate) -> Scene:
        db_obj = Scene(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Scene, obj_in: SceneUpdate) -> Scene:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Scene]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


class CRUDJob:
    def get(self, db: Session, id: int) -> Optional[Job]:
        return db.query(Job).filter(Job.id == id).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100, gateway_id: Optional[str] = None
    ) -> List[Job]:
        query = db.query(Job)
        if gateway_id:
            query = query.filter(Job.gateway_id == gateway_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: JobCreate) -> Job:
        db_obj = Job(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Job, obj_in: JobUpdate) -> Job:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Job]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


class CRUDBinding:
    def get(self, db: Session, id: int) -> Optional[Binding]:
        return db.query(Binding).filter(Binding.id == id).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100, gateway_id: Optional[str] = None
    ) -> List[Binding]:
        query = db.query(Binding)
        if gateway_id:
            query = query.filter(Binding.gateway_id == gateway_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: BindingCreate) -> Binding:
        db_obj = Binding(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Binding, obj_in: BindingUpdate) -> Binding:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Binding]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


class CRUDScript:
    def get(self, db: Session, id: int) -> Optional[Script]:
        return db.query(Script).filter(Script.id == id).first()

    def get_multi(
        self, db: Session, skip: int = 0, limit: int = 100, gateway_id: Optional[str] = None
    ) -> List[Script]:
        query = db.query(Script)
        if gateway_id:
            query = query.filter(Script.gateway_id == gateway_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: ScriptCreate) -> Script:
        db_obj = Script(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Script, obj_in: ScriptUpdate) -> Script:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Script]:
        obj = self.get(db, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


group_crud = CRUDDeviceGroup()
scene_crud = CRUDScene()
job_crud = CRUDJob()
binding_crud = CRUDBinding()
script_crud = CRUDScript()
