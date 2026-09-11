"""JWT jti 撤销服务：Redis 可用时跨进程共享，否则使用进程内缓存。"""
import time
import threading
from typing import Optional
from app.core.config import settings

_lock = threading.Lock()
_local: dict[str, float] = {}

def _redis():
    try:
        import redis
        return redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=2, decode_responses=True)
    except Exception:
        return None

def revoke(jti: str, expires_at: int) -> None:
    if not jti:
        return
    ttl = max(1, int(expires_at - time.time()))
    client = _redis()
    if client:
        try:
            client.setex(f"iot:jwt:revoked:{jti}", ttl, "1")
            return
        except Exception:
            pass
    with _lock:
        _local[jti] = time.time() + ttl

def is_revoked(jti: Optional[str]) -> bool:
    if not jti:
        return False
    client = _redis()
    if client:
        try:
            return bool(client.exists(f"iot:jwt:revoked:{jti}"))
        except Exception:
            pass
    now = time.time()
    with _lock:
        for key, expiry in list(_local.items()):
            if expiry <= now:
                _local.pop(key, None)
        return _local.get(jti, 0) > now
