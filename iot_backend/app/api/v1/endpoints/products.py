"""产品管理 API"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.crud.product import product_crud
from app.db.session import get_db
from app.schemas.product import Product, ProductCreate, ProductUpdate
from app.schemas.user import User
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
    return product_crud.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    *,
    db: Session = Depends(get_db),
    product_in: ProductCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if product_crud.get_by_product_id(db, product_in.product_id):
        raise HTTPException(status_code=400, detail="产品ID已存在")
    return product_crud.create(db, product_in)


@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    product = product_crud.get_by_product_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product


@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: str,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    product = product_crud.get_by_product_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
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
    product = product_crud.get_by_product_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    product = product_crud.update(db, product, ProductUpdate(model=model))
    mqtt_client.publish(f"product/{product_id}/model", json.dumps(model))
    return product


@router.delete("/{product_id}", response_model=Product)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    product = product_crud.get_by_product_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product_crud.delete(db, product.id)
