"""用户认证服务：JWT、密码哈希、注册/登录/重置密码"""
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.db_models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, username: str, role: str = "user") -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": str(username),
        "role": str(role),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, key=settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """解码 JWT，返回 payload；验证失败返回空字典"""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return {}


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def register_user(db: Session, username: str, email: str, password: str, nickname: str = None) -> User:
    """注册新用户，返回 User 对象"""
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        nickname=nickname or username,
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """验证用户凭据，成功返回 User，失败返回 None"""
    user = get_user_by_username(db, username)
    if not user:
        user = get_user_by_email(db, username)  # 也支持邮箱登录
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def generate_reset_token(db: Session, email: str) -> str | None:
    """生成密码重置 token，返回 token 字符串；用户不存在返回 None"""
    user = get_user_by_email(db, email)
    if not user:
        return None
    token = str(uuid.uuid4())
    user.reset_token = token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()
    return token


def reset_password(db: Session, token: str, new_password: str) -> bool:
    """通过重置 token 修改密码，成功返回 True"""
    user = db.query(User).filter(
        User.reset_token == token,
        User.reset_token_expires > datetime.now(timezone.utc),
    ).first()
    if not user:
        return False
    user.password_hash = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return True
