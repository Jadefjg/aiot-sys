"""产品与物模型 API"""
import json
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission, verify_token
from app.crud.product import product_crud
from app.db.session import get_db
from app.grpc.clients.mqtt_client import mqtt_grpc_client
from app.schemas.product import Product, ProductCreate, ProductUpdate

router = APIRouter()


def _sync_model(product_id: str, model: dict):
    mqtt_grpc_client.publish_message(
        f"product/{product_id}/model", json.dumps(model or {}, ensure_ascii=False)
    )


@router.get("/", response_model=List[Product])
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "read")
    return product_crud.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    if product_crud.get_by_product_id(db, product_in.product_id):
        raise HTTPException(status_code=400, detail="产品ID已存在")
    return product_crud.create(db, product_in)


@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "read")
    product = product_crud.get_by_product_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product


@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: str,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    product = product_crud.get_by_product_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    product = product_crud.update(db, product, product_in)
    if product_in.model is not None:
        _sync_model(product_id, product.model or {})
    return product


@router.put("/{product_id}/model", response_model=Product)
def update_thing_model(
    product_id: str,
    model: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "write")
    product = product_crud.get_by_product_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    product = product_crud.update(db, product, ProductUpdate(model=model))
    _sync_model(product_id, model)
    return product


@router.delete("/{product_id}", response_model=Product)
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
) -> Any:
    require_permission(current_user["user_id"], "device", "delete")
    product = product_crud.get_by_product_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    return product_crud.delete(db, product.id)
