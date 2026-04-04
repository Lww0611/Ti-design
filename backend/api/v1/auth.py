from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Annotated

from db.db_models.user_table import User
from db.session import get_db
from schemas.user import RegisterRequest, LoginRequest
import hashlib

router = APIRouter(tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _password_sha256_hex(password: str) -> str:
    """先 SHA256 再交给 bcrypt，避免明文过长；用 hex 字符串避免摘要里的 \\0 截断 bcrypt 密码。"""
    return hashlib.sha256(password.encode()).hexdigest()


def _password_sha256_bytes_legacy(password: str) -> bytes:
    """历史注册可能用过 digest()，登录时做一次兼容校验。"""
    return hashlib.sha256(password.encode()).digest()


def hash_password(password: str) -> str:
    return pwd_context.hash(_password_sha256_hex(password))


def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    for secret in (_password_sha256_hex(password), _password_sha256_bytes_legacy(password)):
        try:
            if pwd_context.verify(secret, hashed):
                return True
        except (ValueError, TypeError):
            continue
    return False

# --- 依赖项函数 (原本在 deps/auth.py) ---
def get_current_user(token: Annotated[str, Header(...)], db: Session = Depends(get_db)) -> User:
    """
    从 Header 中提取 token 并验证用户身份
    Token 格式示例: "id-username"
    """
    try:
        # 兼容你原始代码中的 split 逻辑
        user_id, _ = token.split("-", 1)
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="无效 token 格式")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

# --- 路由接口 ---

# 注册
@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        lab=data.lab
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "username": user.username,
        "lab": user.lab
    }

# 登录
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    # 保持原有的简单 Token 生成逻辑
    token = f"{user.id}-{user.username}"

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username
    }

# 获取当前用户信息
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """
    直接依赖 get_current_user 函数，确保逻辑复用
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "lab": current_user.lab
    }