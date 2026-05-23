"""
认证工具：密码哈希 + JWT 令牌生成/验证
"""
import hashlib
import hmac
import secrets
import time
import json
from datetime import datetime, timezone

# JWT 签名密钥（生产环境应放在环境变量中）
SECRET_KEY = "visdrone-secret-key-change-in-production"


def hash_password(password: str) -> str:
    """对密码进行 SHA256 加盐哈希，返回 "salt$hash" 格式的字符串"""
    salt = secrets.token_hex(16)  # 随机盐值，每个用户不同
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${h}"


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码是否正确"""
    try:
        salt, stored_hash = password_hash.split("$", 1)
        h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
        return hmac.compare_digest(h, stored_hash)
    except (ValueError, AttributeError):
        return False


def create_token(user_id: int, username: str, expires_hours: int = 24) -> str:
    """生成一个简单的 JWT-like token（用 base64 编码的 JSON + 签名）"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + expires_hours * 3600,
        "iat": int(time.time()),
    }

    # Base64URL 编码
    def b64encode(data: dict) -> str:
        s = json.dumps(data, separators=(",", ":"))
        return __import__("base64").urlsafe_b64encode(s.encode()).rstrip(b"=").decode()

    header_b64 = b64encode(header)
    payload_b64 = b64encode(payload)

    # HMAC-SHA256 签名
    signing_input = f"{header_b64}.{payload_b64}"
    sig = hmac.new(
        SECRET_KEY.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()
    sig_b64 = __import__("base64").urlsafe_b64encode(sig).rstrip(b"=").decode()

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_token(token: str) -> dict | None:
    """验证并解析 token，返回 payload 字典，无效则返回 None"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, sig_b64 = parts

        # 验证签名
        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            signing_input.encode(),
            hashlib.sha256,
        ).digest()
        expected_sig_b64 = (
            __import__("base64").urlsafe_b64encode(expected_sig).rstrip(b"=").decode()
        )

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None

        # 解码 payload
        # 补齐 base64 padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(
            __import__("base64").urlsafe_b64decode(payload_b64).decode()
        )

        # 检查是否过期
        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None
