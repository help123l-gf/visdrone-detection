"""Redis 缓存服务"""
import json
from typing import Optional, Any

import redis

from app.config import settings


class CacheService:
    """Redis 缓存封装"""

    def __init__(self):
        self._client: redis.Redis | None = None
        self._enabled = False
        self._init_client()

    def _init_client(self):
        try:
            self._client = redis.Redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD or None,
                socket_connect_timeout=3,
                decode_responses=True,
            )
            self._client.ping()
            self._enabled = True
            print(f"[Redis] Connected to {settings.REDIS_URL}")
        except Exception as e:
            print(f"[Redis] Connection failed ({e}) — caching disabled")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def get(self, key: str) -> Optional[str]:
        if not self._enabled:
            return None
        try:
            return self._client.get(key)
        except redis.RedisError:
            return None

    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        if not self._enabled:
            return False
        try:
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            self._client.setex(key, expire, value)
            return True
        except redis.RedisError:
            return False

    def delete(self, key: str) -> bool:
        if not self._enabled:
            return False
        try:
            self._client.delete(key)
            return True
        except redis.RedisError:
            return False

    def get_json(self, key: str) -> Optional[Any]:
        val = self.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val

    def increment(self, key: str, amount: int = 1) -> int:
        if not self._enabled:
            return 0
        try:
            return self._client.incrby(key, amount)
        except redis.RedisError:
            return 0

    def keys(self, pattern: str = "*") -> list:
        if not self._enabled:
            return []
        try:
            return self._client.keys(pattern)
        except redis.RedisError:
            return []


# 全局单例
cache_service = CacheService()
