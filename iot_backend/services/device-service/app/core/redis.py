"""与 mqtt-gateway 共用的 Redis（事件总线 + 控制响应队列）"""
from typing import Optional

import redis

from app.core.config import settings

_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _client
