from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import User
from app.utils.security import hash_password, verify_password, create_token, decode_token

security_scheme = HTTPBearer()


def register_user(db: Session, username: str, email: str, password: str) -> User:
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "用户名已存在")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "邮箱已注册")

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        nickname=username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, username: str, password: str) -> dict:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")

    token = create_token(user.id, user.username)
    return {
        "token": token,
        "user": {"id": user.id, "username": user.username, "email": user.email, "role": user.role},
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(401, "Token无效或已过期")

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user
