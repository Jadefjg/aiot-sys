#!/usr/bin/env python3
"""智能眼镜产品 / 演示设备 / 策略场景种子（幂等，不覆盖其他产品）"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db import models  # noqa: F401
from app.crud.device import device_crud
from app.crud.group import scene_crud
from app.crud.product import product_crud
from app.schemas.device import DeviceCreate
from app.schemas.group import SceneCreate, SceneUpdate
from app.schemas.product import ProductCreate, ProductUpdate

SHARED_PROPS = [
    {"name": "battery", "label": "电量", "type": "number", "mode": "r", "unit": "%"},
    {"name": "charging", "label": "充电中", "type": "boolean", "mode": "r"},
    {"name": "worn", "label": "佩戴", "type": "boolean", "mode": "r"},
    {"name": "temperature", "label": "温度", "type": "number", "mode": "r", "unit": "℃"},
    {"name": "camera_on", "label": "相机", "type": "boolean", "mode": "rw"},
    {"name": "mic_on", "label": "麦克风", "type": "boolean", "mode": "rw"},
    {"name": "storage_free", "label": "剩余存储", "type": "number", "mode": "r", "unit": "MB"},
    {"name": "fw_ar1", "label": "AR1 固件", "type": "string", "mode": "r"},
    {"name": "fw_bes", "label": "BES 固件", "type": "string", "mode": "r"},
]

SHARED_EVENTS = [
    {"name": "photo_captured", "label": "拍照完成"},
    {"name": "clip_ready", "label": "短视频就绪"},
    {"name": "audio_ready", "label": "录音就绪"},
    {"name": "wakeword", "label": "唤醒词"},
    {"name": "overheat", "label": "过热"},
    {"name": "low_battery", "label": "低电量"},
    {"name": "privacy_blocked", "label": "隐私拦截"},
]

SHARED_ACTIONS = [
    {"name": "capture", "label": "抓拍", "type": "button"},
    {"name": "start_record", "label": "开始录像", "type": "button"},
    {"name": "stop_record", "label": "停止录像", "type": "button"},
    {"name": "set_privacy", "label": "隐私模式", "type": "switch"},
    {"name": "ota_start", "label": "开始升级", "type": "button"},
]

SHARED_VALIDATORS = [
    {
        "name": "low_battery",
        "type": "compare",
        "field": "battery",
        "operator": "<",
        "value": 15,
        "title": "眼镜低电量",
        "message": "电量 {battery}% ，建议关闭相机",
        "level": "warning",
    },
    {
        "name": "overheat",
        "type": "compare",
        "field": "temperature",
        "operator": ">",
        "value": 45,
        "title": "眼镜过热",
        "message": "温度 {temperature}℃ ，将关闭相机",
        "level": "error",
    },
    {
        "name": "privacy_unworn_camera",
        "type": "expression",
        "expression": "worn == False and camera_on == True",
        "title": "离耳仍开相机",
        "message": "未佩戴时相机仍开启，触发隐私策略",
        "level": "warning",
    },
]

SHARED_SETTINGS = [
    {"name": "ai_enabled", "label": "云端 AI", "type": "boolean", "default": True},
    {"name": "upload_quality", "label": "上传画质", "type": "string", "default": "720p"},
    {"name": "sample_interval", "label": "遥测间隔秒", "type": "number", "default": 10},
]


def _model(extra_props=None, extra_actions=None):
    return {
        "properties": SHARED_PROPS + (extra_props or []),
        "events": SHARED_EVENTS,
        "actions": SHARED_ACTIONS + (extra_actions or []),
        "validators": SHARED_VALIDATORS,
        "settings": SHARED_SETTINGS,
    }


PRODUCTS = [
    ProductCreate(
        product_id="glasses-full",
        name="智能眼镜·全功能版",
        description="摄像头+麦克风+扬声器，第一视角与语音交互",
        protocol="mqtt",
        version="1.0",
        smart=True,
        controllable=True,
        writable=True,
        ota=True,
        locatable=True,
        model=_model(
            extra_props=[
                {"name": "speaker_on", "label": "扬声器", "type": "boolean", "mode": "rw"},
                {"name": "volume", "label": "音量", "type": "number", "mode": "rw"},
            ],
            extra_actions=[{"name": "play_tts", "label": "播报", "type": "button"}],
        ),
    ),
    ProductCreate(
        product_id="glasses-lite",
        name="智能眼镜·轻量版",
        description="摄像头+麦克风，无扬声器，约 20g 级佩戴",
        protocol="mqtt",
        version="1.0",
        smart=True,
        controllable=True,
        writable=True,
        ota=True,
        locatable=True,
        model=_model(),
    ),
]

DEMO_DEVICES = [
    ("glasses-full-001", "全功能眼镜-演示", "glasses-full"),
    ("glasses-lite-001", "轻量眼镜-演示", "glasses-lite"),
]

GLASSES_PRODUCTS = ("glasses-full", "glasses-lite")


def _glasses_triggers(field: str, operator: str, value):
    """只匹配眼镜产品，避免任意设备的同名属性误触发关相机"""
    return [
        {"product_id": product_id, "field": field, "operator": operator, "value": value}
        for product_id in GLASSES_PRODUCTS
    ]


SCENES = [
    SceneCreate(
        name="glasses-thermal",
        enabled=True,
        triggers=_glasses_triggers("temperature", ">", 45),
        actions=[{"type": "write", "values": {"camera_on": False}}],
    ),
    SceneCreate(
        name="glasses-privacy",
        enabled=True,
        triggers=_glasses_triggers("worn", "==", False),
        actions=[{"type": "write", "values": {"camera_on": False, "mic_on": False}}],
    ),
    SceneCreate(
        name="glasses-low-battery",
        enabled=True,
        triggers=_glasses_triggers("battery", "<", 15),
        actions=[{"type": "write", "values": {"camera_on": False}}],
    ),
]


def _upsert_product(db, item: ProductCreate) -> None:
    existed = product_crud.get_by_product_id(db, item.product_id)
    if existed:
        product_crud.update(db, existed, ProductUpdate(**item.model_dump()))
        print(f"updated product: {item.product_id}")
        return
    product_crud.create(db, item)
    print(f"created product: {item.product_id}")


def _ensure_device(db, device_id: str, name: str, product_id: str) -> None:
    if device_crud.get_by_device_id(db, device_id):
        print(f"skip existing device: {device_id}")
        return
    device_crud.create(
        db,
        DeviceCreate(device_id=device_id, device_name=name, product_id=product_id, device_type="glasses"),
    )
    print(f"created device: {device_id}")


def _ensure_scene(db, item: SceneCreate) -> None:
    for row in scene_crud.get_multi(db, limit=500):
        if row.name == item.name:
            scene_crud.update(db, row, SceneUpdate(**item.model_dump()))
            print(f"updated scene: {item.name}")
            return
    scene_crud.create(db, item)
    print(f"created scene: {item.name}")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for item in PRODUCTS:
            _upsert_product(db, item)
        for device_id, name, product_id in DEMO_DEVICES:
            _ensure_device(db, device_id, name, product_id)
        for scene in SCENES:
            _ensure_scene(db, scene)
    finally:
        db.close()


if __name__ == "__main__":
    main()
