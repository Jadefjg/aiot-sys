"""分组与智能场景 API"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission, verify_token
from app.crud.group import group_crud, job_crud, scene_crud
from app.db.session import get_db
from app.schemas.group import (
    DeviceGroup, DeviceGroupCreate, DeviceGroupUpdate,
    Job, JobCreate, JobUpdate, Scene, SceneCreate, SceneUpdate,
)

router = APIRouter()
scenes_router = APIRouter()
jobs_router = APIRouter()


@router.get("/", response_model=List[DeviceGroup])
def list_groups(
    skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "read")
    return group_crud.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=DeviceGroup, status_code=status.HTTP_201_CREATED)
def create_group(
    group_in: DeviceGroupCreate,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    return group_crud.create(db, group_in)


@router.put("/{group_id}", response_model=DeviceGroup)
def update_group(
    group_id: int, group_in: DeviceGroupUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    group = group_crud.get(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group_crud.update(db, group, group_in)


@router.delete("/{group_id}", response_model=DeviceGroup)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "delete")
    group = group_crud.delete(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group


@scenes_router.get("/", response_model=List[Scene])
def list_scenes(
    skip: int = 0, limit: int = 100, gateway_id: Optional[str] = None,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "read")
    return scene_crud.get_multi(db, skip=skip, limit=limit, gateway_id=gateway_id)


@scenes_router.post("/", response_model=Scene, status_code=status.HTTP_201_CREATED)
def create_scene(
    scene_in: SceneCreate,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    return scene_crud.create(db, scene_in)


@scenes_router.put("/{scene_id}", response_model=Scene)
def update_scene(
    scene_id: int, scene_in: SceneUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    scene = scene_crud.get(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scene_crud.update(db, scene, scene_in)


@scenes_router.delete("/{scene_id}", response_model=Scene)
def delete_scene(
    scene_id: int,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "delete")
    scene = scene_crud.delete(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="场景不存在")
    return scene


@jobs_router.get("/", response_model=List[Job])
def list_jobs(
    skip: int = 0, limit: int = 100, gateway_id: Optional[str] = None,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "read")
    return job_crud.get_multi(db, skip=skip, limit=limit, gateway_id=gateway_id)


@jobs_router.post("/", response_model=Job, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    return job_crud.create(db, job_in)


@jobs_router.put("/{job_id}", response_model=Job)
def update_job(
    job_id: int, job_in: JobUpdate,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    job = job_crud.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job_crud.update(db, job, job_in)


@jobs_router.delete("/{job_id}", response_model=Job)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db), current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "delete")
    job = job_crud.delete(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job
