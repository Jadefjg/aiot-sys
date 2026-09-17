"""单体 Redis 客户端：影子缓存、在线集合、死信、连接限流"""
from typing import Optional

import redis

from app.core.config import settings

_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    global _client
    if _client is not None:
        return _client
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1)
        client.ping()
        _client = client
        return _client
    except Exception:
        return None
