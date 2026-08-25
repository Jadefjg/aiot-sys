"""产品管理 API"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.crud.acl import acl_crud
from app.crud.product import product_crud
from app.db.session import get_db
from app.schemas.product import Product, ProductCreate, ProductUpdate
from app.schemas.user import User
from app.services import access_control as access
from app.services.mqtt_service import mqtt_client
import json

router = APIRouter()


@router.get("/", response_model=List[Product])
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return access.list_visible_products(db, current_user, skip=skip, limit=limit)


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if product_crud.get_by_product_id(db, product_in.product_id):
        raise HTTPException(status_code=400, detail="产品ID已存在")
    product = product_crud.create(db, product_in)
    if not current_user.is_superuser:
        acl_crud.upsert_product(db, current_user.id, product.product_id, "admin")
    return product


@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    return access.load_product(db, current_user, product_id, "viewer")


@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: str,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    product = access.load_product(db, current_user, product_id, "admin")
    product = product_crud.update(db, product, product_in)
    # 物模型变更通过 MQTT 同步
    if product_in.model is not None:
        mqtt_client.publish(
            f"product/{product_id}/model", json.dumps(product.model or {})
        )
    return product


@router.put("/{product_id}/model", response_model=Product)
def update_thing_model(
    product_id: str,
    model: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """单独更新物模型并同步到 MQTT"""
    product = access.load_product(db, current_user, product_id, "admin")
    product = product_crud.update(db, product, ProductUpdate(model=model))
    mqtt_client.publish(f"product/{product_id}/model", json.dumps(model))
    return product


@router.put("/{product_id}/config/{name}", response_model=Product)
def update_product_config(
    product_id: str,
    name: str,
    config: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """更新协议配置并发布 product/{id}/config/{name}"""
    product = access.load_product(db, current_user, product_id, "admin")
    merged = dict(product.config or {})
    merged[name] = config
    product = product_crud.update(db, product, ProductUpdate(config=merged))
    mqtt_client.publish(f"product/{product_id}/config/{name}", json.dumps(config))
    return product


@router.put("/{product_id}/channels", response_model=Product)
def bind_product_channels(
    product_id: str,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """物接入 / 物存储：绑定采集通道与资源通道"""
    product = access.load_product(db, current_user, product_id, "admin")
    merged = dict(product.config or {})
    dgiot = dict(merged.get("dgiot") or {})
    if "ingest_channels" in body:
        dgiot["ingest_channels"] = body["ingest_channels"]
    if "storage_channels" in body:
        dgiot["storage_channels"] = body["storage_channels"]
    if "node_type" in body:
        dgiot["node_type"] = body["node_type"]
    if "network" in body:
        dgiot["network"] = body["network"]
    merged["dgiot"] = dgiot
    from app.crud.channel import channel_crud
    from app.schemas.channel import ChannelUpdate
    for cid in (dgiot.get("ingest_channels") or []) + (dgiot.get("storage_channels") or []):
        ch = channel_crud.get_by_channel_id(db, cid)
        if not ch:
            continue
        pids = list(ch.product_ids or [])
        if product_id not in pids:
            pids.append(product_id)
            channel_crud.update(db, ch, ChannelUpdate(product_ids=pids))
    return product_crud.update(db, product, ProductUpdate(config=merged))


@router.delete("/{product_id}", response_model=Product)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    product = access.load_product(db, current_user, product_id, "admin")
    return product_crud.delete(db, product.id)
