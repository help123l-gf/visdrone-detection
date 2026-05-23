"""用户认证 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator

from app.database import get_db
from app.services import auth_service
from app.models.db_models import User

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / Response Schemas ──

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    nickname: str | None = None

    @field_validator("username")
    @classmethod
    def username_length(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 20:
            raise ValueError("用户名长度需在3-20字符之间")
        return v

    @field_validator("password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("密码至少6位")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("新密码至少6位")
        return v


class AuthResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


class UserInfoResponse(BaseModel):
    success: bool
    message: str
    data: dict | None = None


# ── 辅助函数 ──

def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": user.nickname,
        "role": user.role,
        "avatar_url": user.avatar_url,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ── 注册 ──

@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # 检查用户名
    if auth_service.get_user_by_username(db, req.username):
        raise HTTPException(status_code=400, detail="用户名已被占用")
    # 检查邮箱
    if auth_service.get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    user = auth_service.register_user(
        db, req.username, req.email, req.password, req.nickname
    )
    token = auth_service.create_access_token(user.id, user.username, user.role)

    return AuthResponse(
        success=True,
        message="注册成功",
        data={"token": token, "user": _user_to_dict(user)},
    )


# ── 登录 ──

@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = auth_service.create_access_token(user.id, user.username, user.role)

    return AuthResponse(
        success=True,
        message="登录成功",
        data={"token": token, "user": _user_to_dict(user)},
    )


# ── 获取当前用户信息 ──

@router.get("/me", response_model=UserInfoResponse)
def get_me(
    db: Session = Depends(get_db),
    user: User | None = Depends(
        __import__("app.api.deps", fromlist=["get_current_user"]).get_current_user
    ),
):
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return UserInfoResponse(
        success=True,
        message="获取成功",
        data=_user_to_dict(user),
    )


# ── 忘记密码（发送重置令牌） ──

@router.post("/forgot-password", response_model=AuthResponse)
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    token = auth_service.generate_reset_token(db, req.email)
    # 实际生产环境应发送邮件；这里直接返回 token 方便开发测试
    if token:
        return AuthResponse(
            success=True,
            message=f"重置令牌已生成（开发模式直接返回）",
            data={"reset_token": token},
        )
    else:
        # 为安全起见，用户不存在也返回成功
        return AuthResponse(
            success=True,
            message="如果该邮箱已注册，重置链接已发送",
        )


# ── 重置密码 ──

@router.post("/reset-password", response_model=AuthResponse)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    ok = auth_service.reset_password(db, req.token, req.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="重置令牌无效或已过期")
    return AuthResponse(
        success=True,
        message="密码重置成功，请使用新密码登录",
    )
