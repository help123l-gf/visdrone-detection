"""
认证 API：登录、注册、忘记密码
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.utils.auth_utils import hash_password, verify_password, create_token

router = APIRouter(prefix="/auth", tags=["auth"])


# ── 请求/响应模型 ──

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: str | None = None
    user: dict | None = None


# ── 登录 ──

@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """用户登录：验证用户名密码，返回 JWT token"""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, username, email, nickname, password_hash, is_active FROM users WHERE username = ?",
            (req.username,),
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not row["is_active"]:
            raise HTTPException(status_code=403, detail="账号已被禁用")

        if not verify_password(req.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        token = create_token(row["id"], row["username"])

        return AuthResponse(
            success=True,
            message="登录成功",
            token=token,
            user={
                "id": row["id"],
                "username": row["username"],
                "email": row["email"],
                "nickname": row["nickname"] or row["username"],
            },
        )
    finally:
        conn.close()


# ── 注册 ──

@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """用户注册：创建新账号"""
    # 基本校验
    if len(req.username) < 3 or len(req.username) > 20:
        raise HTTPException(status_code=422, detail="用户名长度需在3-20字符之间")
    if len(req.password) < 6:
        raise HTTPException(status_code=422, detail="密码至少6位")

    conn = get_db()
    try:
        # 检查用户名是否已存在
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (req.username,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="用户名已被注册")

        # 检查邮箱是否已存在
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (req.email,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="邮箱已被注册")

        # 插入新用户
        password_hash = hash_password(req.password)
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash, nickname) VALUES (?, ?, ?, ?)",
            (req.username, req.email, password_hash, req.username),
        )
        conn.commit()
        user_id = cursor.lastrowid

        token = create_token(user_id, req.username)

        return AuthResponse(
            success=True,
            message="注册成功",
            token=token,
            user={
                "id": user_id,
                "username": req.username,
                "email": req.email,
                "nickname": req.username,
            },
        )
    finally:
        conn.close()


# ── 忘记密码 ──

@router.post("/forgot-password", response_model=AuthResponse)
def forgot_password(req: ForgotPasswordRequest):
    """忘记密码：验证邮箱是否存在"""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", (req.email,)
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="该邮箱未注册")

        # 简化处理：直接返回成功消息
        # 实际生产环境应发送重置邮件，这里只做验证
        return AuthResponse(
            success=True,
            message="验证成功，重置链接已发送到您的邮箱（演示模式）",
        )
    finally:
        conn.close()
