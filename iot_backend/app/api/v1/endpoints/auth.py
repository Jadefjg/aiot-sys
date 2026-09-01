from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.crud.user import user_crud
from app.db.session import get_db
from app.schemas.token import Token
from app.schemas.user import User, UserCreate, UserRegister

router = APIRouter()


def _issue_token(db: Session, username: str, password: str) -> dict:
    """校验账号并签发 token；失败统一返回 401"""
    username = (username or "").strip()
    password = password or ""
    user = user_crud.authenticate(db, username=username, password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_crud.is_active(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires,
        ),
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    登录：兼容
    - application/x-www-form-urlencoded（OAuth2 / 前端）
    - application/json {"username","password"}
    """
    content_type = (request.headers.get("content-type") or "").lower()
    username = ""
    password = ""

    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
        if isinstance(body, dict):
            username = str(body.get("username") or body.get("email") or "")
            password = str(body.get("password") or "")
    else:
        form = await request.form()
        username = str(form.get("username") or form.get("email") or "")
        password = str(form.get("password") or "")

    return _issue_token(db, username, password)


@router.post("/token", response_model=Token)
def login_token_alias(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """Swagger OAuth2 兼容别名"""
    return _issue_token(db, form_data.username, form_data.password)


@router.post("/test-token", response_model=User)
def test_token(current_user: User = Depends(get_current_active_user)) -> Any:
    """Test access token"""
    return current_user


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)) -> Any:
    """公开注册普通账号，无需登录"""
    username = (user_in.username or "").strip()
    password = user_in.password or ""
    if len(username) < 3 or len(username) > 20:
        raise HTTPException(status_code=400, detail="用户名长度须为 3-20 个字符")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码长度不能少于 6 位")
    if user_crud.get_user_by_username(db, username=username):
        raise HTTPException(status_code=400, detail="用户名已被注册")
    if user_in.email and user_crud.get_by_email(db, email=user_in.email):
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    created = user_crud.create_user(
        db,
        obj_in=UserCreate(
            username=username,
            email=user_in.email,
            password=password,
            full_name=user_in.full_name,
            is_active=True,
            is_superuser=False,
        ),
    )
    return created
