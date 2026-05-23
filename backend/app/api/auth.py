from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import is_db_available
from app.services.auth_service import register_user, login_user, get_current_user
from app.utils.security import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if not is_db_available():
        raise HTTPException(503, "数据库不可用，请先启动 docker-compose up -d")
    user = register_user(db, req.username, req.email, req.password)
    return {
        "success": True,
        "message": "注册成功",
        "data": {"id": user.id, "username": user.username, "email": user.email},
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    if not is_db_available():
        raise HTTPException(503, "数据库不可用，请先启动 docker-compose up -d")
    # Rate limit: max 10 login attempts per IP per minute
    from app.redis_client import rate_check
    if not rate_check(f"login:{req.username}", 10, 60):
        raise HTTPException(429, "登录尝试过于频繁，请稍后再试")
    result = login_user(db, req.username, req.password)
    # Cache token in Redis
    from app.redis_client import cache_set
    cache_set(f"token:{result['user']['id']}", result["token"], 7200)
    return {"success": True, "message": "登录成功", "data": result}


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    if not is_db_available():
        raise HTTPException(503, "数据库不可用，请先启动 docker-compose up -d")
    row = db.execute(text("SELECT id FROM users WHERE username=:u"), {"u": req.username}).fetchone()
    if not row:
        raise HTTPException(404, "用户名不存在")
    if len(req.new_password) < 6:
        raise HTTPException(400, "新密码至少6位")
    db.execute(
        text("UPDATE users SET password_hash=:p WHERE username=:u"),
        {"p": hash_password(req.new_password), "u": req.username},
    )
    db.commit()
    return {"success": True, "message": "密码重置成功，请返回登录"}


@router.get("/stats")
def stats(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not is_db_available():
        raise HTTPException(503, "数据库不可用")
    total = db.execute(text("SELECT COUNT(*) FROM detection_records WHERE user_id=:uid"), {"uid": user.id}).fetchone()[0]
    objects = db.execute(text("SELECT COALESCE(SUM(total_objects),0) FROM detection_records WHERE user_id=:uid"), {"uid": user.id}).fetchone()[0]
    success = db.execute(text("SELECT COUNT(*) FROM detection_records WHERE user_id=:uid AND status='completed'"), {"uid": user.id}).fetchone()[0]
    rate = round(success / total * 100, 1) if total > 0 else 100.0
    days = db.execute(text("SELECT COUNT(DISTINCT DATE(created_at)) FROM detection_records WHERE user_id=:uid"), {"uid": user.id}).fetchone()[0]
    return {"success": True, "data": {"total_detections": total, "total_objects": objects, "success_rate": rate, "usage_days": days}}


@router.get("/me")
def me(user=Depends(get_current_user)):
    if not is_db_available():
        raise HTTPException(503, "数据库不可用")
    return {
        "success": True,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "role": user.role,
            "avatar_url": user.avatar_url,
            "created_at": str(user.created_at),
        },
    }
