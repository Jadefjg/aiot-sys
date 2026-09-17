"""规模档位与百万级选型体检"""
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.schemas.user import User
from app.services import access_control as access
from app.services.scale_profile import assess
from app.services.shadow_service import online_count

router = APIRouter()


@router.get("/profile")
def get_scale_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    query = access.visible_device_query(db, current_user)
    count = query.count()
    data = assess(count)
    data["online_cached"] = online_count()
    return data
