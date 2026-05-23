import redis

from app.config import settings

_redis = None


def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            _redis.ping()
        except Exception:
            _redis = None
    return _redis


def cache_set(key: str, value: str, expire: int = 7200):
    r = get_redis()
    if r:
        r.setex(f"visdrone:{key}", expire, value)


def cache_get(key: str) -> str | None:
    r = get_redis()
    if r:
        return r.get(f"visdrone:{key}")
    return None


def cache_delete(key: str):
    r = get_redis()
    if r:
        r.delete(f"visdrone:{key}")


def rate_check(key: str, limit: int = 30, window: int = 60) -> bool:
    """Return True if under limit, False if rate exceeded."""
    r = get_redis()
    if not r:
        return True
    rkey = f"visdrone:rate:{key}"
    current = r.incr(rkey)
    if current == 1:
        r.expire(rkey, window)
    return current <= limit
