"""接入后流水线：影子/规则之后写入 Redis Stream，代替未部署的 Kafka。
参考文章：接入 → 校验 → 影子 → 规则 → 时序 + 消息队列。
"""
import json
import logging
from typing import Any, Dict, Optional

from app.core.redis import get_redis

logger = logging.getLogger(__name__)
STREAM_KEY = "iot:pipeline:telemetry"
DLQ_KEY = "iot:dlq:messages"
DEBOUNCE_PREFIX = "iot:alert:debounce:"
STREAM_MAX = 100_000
ALERT_TTL = 60


def enqueue_telemetry(device_id: str, values: dict, product_id: str = "") -> None:
    """遥测进入 Redis Stream，下游可扩 Kafka 消费。"""
    client = get_redis()
    if not client:
        return
    try:
        client.xadd(
            STREAM_KEY,
            {
                "device_id": device_id,
                "product_id": product_id or "",
                "payload": json.dumps(values or {}, default=str)[:4000],
            },
            maxlen=STREAM_MAX,
            approximate=True,
        )
    except Exception as exc:
        logger.warning("pipeline xadd: %s", exc)


def stream_len() -> int:
    return _llen_or_xlen(STREAM_KEY, stream=True)


def dlq_len() -> int:
    return _llen_or_xlen(DLQ_KEY, stream=False)


def alert_allowed(device_id: str, title: str, ttl: int = ALERT_TTL) -> bool:
    """告警防抖：同一设备+标题在 TTL 内只放行一次，避免规则风暴。"""
    client = get_redis()
    if not client:
        return True
    key = f"{DEBOUNCE_PREFIX}{device_id}:{title or 'alarm'}"
    try:
        return bool(client.set(key, "1", nx=True, ex=max(1, ttl)))
    except Exception:
        return True


def _llen_or_xlen(key: str, stream: bool) -> int:
    client = get_redis()
    if not client:
        return 0
    try:
        if stream:
            return int(client.xlen(key) or 0)
        return int(client.llen(key) or 0)
    except Exception:
        return 0
