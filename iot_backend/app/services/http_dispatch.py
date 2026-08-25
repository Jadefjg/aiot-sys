"""后台 HTTP 转发，避免阻塞 MQTT / 采集线程"""
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="http-dispatch")


def post_json(url: str, payload: dict, timeout: float = 3) -> None:
    if not url:
        return
    _pool.submit(_run, url, payload, timeout)


def _run(url: str, payload: dict, timeout: float) -> None:
    try:
        import requests
        requests.post(url, json=payload, timeout=timeout)
    except Exception as exc:
        logger.warning("HTTP dispatch %s: %s", url, exc)
