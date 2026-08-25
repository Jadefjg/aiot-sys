"""分组与智能场景 API"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.crud.group import group_crud, job_crud, scene_crud
from app.db.session import get_db
from app.schemas.group import (
    DeviceGroup,
    DeviceGroupCreate,
    DeviceGroupUpdate,
    Job,
    JobCreate,
    JobUpdate,
    Scene,
    SceneCreate,
    SceneUpdate,
)
from app.schemas.user import User
from app.services import access_control as access

router = APIRouter()
scenes_router = APIRouter()
jobs_router = APIRouter()


def _ensure_scene_write(db: Session, user: User, scene_like) -> None:
    gateway_id = getattr(scene_like, "gateway_id", None)
    device_ids = access.collect_scene_device_ids(scene_like)
    if gateway_id:
        access.ensure_gateway(db, user, gateway_id, "operator")
    elif not device_ids:
        access.ensure_gateway(db, user, None, "operator")
    access.ensure_devices(db, user, device_ids, "operator")


def _ensure_scene_manage(db: Session, user: User, scene) -> None:
    """更新/删除：有网关按网关；无网关则按触发/动作设备或超管"""
    if user.is_superuser:
        return
    if scene.gateway_id:
        access.ensure_gateway(db, user, scene.gateway_id, "operator")
        return
    device_ids = access.collect_scene_device_ids(scene)
    if not device_ids:
        raise HTTPException(status_code=403, detail="全局场景仅超级管理员可操作")
    access.ensure_devices(db, user, device_ids, "operator")


def _ensure_job_write(db: Session, user: User, job_like) -> None:
    gateway_id = getattr(job_like, "gateway_id", None)
    access.ensure_gateway(db, user, gateway_id, "operator")
    action = getattr(job_like, "action", None) or {}
    if isinstance(action, dict) and action.get("device_id"):
        access.ensure_devices(db, user, [action["device_id"]], "operator")


@router.get("/", response_model=List[DeviceGroup])
def list_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return group_crud.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=DeviceGroup, status_code=status.HTTP_201_CREATED)
def create_group(
    group_in: DeviceGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
    return group_crud.create(db, group_in)


@router.put("/{group_id}", response_model=DeviceGroup)
def update_group(
    group_id: int,
    group_in: DeviceGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
    group = group_crud.get(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group_crud.update(db, group, group_in)


@router.delete("/{group_id}", response_model=DeviceGroup)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足，需要超级管理员权限")
    group = group_crud.delete(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group


@scenes_router.get("/", response_model=List[Scene])
def list_scenes(
    skip: int = 0,
    limit: int = 100,
    gateway_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if gateway_id and not current_user.is_superuser:
        access.load_device(db, current_user, gateway_id, "viewer")
    rows = scene_crud.get_multi(db, skip=0, limit=500, gateway_id=gateway_id)
    rows = access.filter_by_gateway(rows, db, current_user)
    return rows[skip:skip + limit]


@scenes_router.post("/", response_model=Scene, status_code=status.HTTP_201_CREATED)
def create_scene(
    scene_in: SceneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    _ensure_scene_write(db, current_user, scene_in)
    obj = scene_crud.create(db, scene_in)
    from app.services.scene_engine import scene_engine
    scene_engine.invalidate()
    return obj


@scenes_router.put("/{scene_id}", response_model=Scene)
def update_scene(
    scene_id: int,
    scene_in: SceneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    scene = scene_crud.get(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    _ensure_scene_manage(db, current_user, scene)

    class _Merged:
        pass

    merged = _Merged()
    merged.gateway_id = scene_in.gateway_id if scene_in.gateway_id is not None else scene.gateway_id
    merged.triggers = scene.triggers if scene_in.triggers is None else scene_in.triggers
    merged.conditions = scene.conditions if scene_in.conditions is None else scene_in.conditions
    merged.actions = scene.actions if scene_in.actions is None else scene_in.actions
    _ensure_scene_write(db, current_user, merged)
    obj = scene_crud.update(db, scene, scene_in)
    from app.services.scene_engine import scene_engine
    scene_engine.invalidate()
    return obj


@scenes_router.delete("/{scene_id}", response_model=Scene)
def delete_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    scene = scene_crud.get(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    _ensure_scene_manage(db, current_user, scene)
    scene = scene_crud.delete(db, scene_id)
    from app.services.scene_engine import scene_engine
    scene_engine.invalidate()
    return scene


@jobs_router.get("/", response_model=List[Job])
def list_jobs(
    skip: int = 0,
    limit: int = 100,
    gateway_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if gateway_id and not current_user.is_superuser:
        access.load_device(db, current_user, gateway_id, "viewer")
    rows = job_crud.get_multi(db, skip=0, limit=500, gateway_id=gateway_id)
    rows = access.filter_by_gateway(rows, db, current_user)
    return rows[skip:skip + limit]


@jobs_router.post("/", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    _ensure_job_write(db, current_user, job_in)
    return job_crud.create(db, job_in)


@jobs_router.put("/{job_id}", response_model=Job)
def update_job(
    job_id: int,
    job_in: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    job = job_crud.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    access.ensure_gateway(db, current_user, job.gateway_id, "operator")
    gateway_id = job_in.gateway_id if job_in.gateway_id is not None else job.gateway_id
    action = job_in.action if job_in.action is not None else job.action
    class _Tmp:
        pass
    tmp = _Tmp()
    tmp.gateway_id = gateway_id
    tmp.action = action
    _ensure_job_write(db, current_user, tmp)
    return job_crud.update(db, job, job_in)


@jobs_router.delete("/{job_id}", response_model=Job)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    job = job_crud.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    access.ensure_gateway(db, current_user, job.gateway_id, "operator")
    return job_crud.delete(db, job_id)
