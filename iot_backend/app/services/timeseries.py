"""InfluxDB 遥测唯一存储与查询；未启用时调用方可读 MySQL 遗留行"""
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="influx")


def numeric_fields(data: Optional[dict]) -> Dict[str, float]:
    """只写入可画曲线的数值字段"""
    fields: Dict[str, float] = {}
    for key, value in (data or {}).items():
        if isinstance(value, bool):
            fields[str(key)] = 1.0 if value else 0.0
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            fields[str(key)] = float(value)
    return fields


def _safe_id(value: str) -> str:
    return "".join(c for c in (value or "") if c.isalnum() or c in "-_.") or "unknown"


class TimeseriesStore:
    def __init__(self):
        self._client = None
        self._failed = False

    @property
    def enabled(self) -> bool:
        return bool(
            settings.INFLUX_ENABLED
            and settings.INFLUX_URL
            and settings.INFLUX_TOKEN
        )

    def ping(self) -> bool:
        if not self.enabled:
            return False
        try:
            client = self._get_client()
            return bool(client and client.ping())
        except Exception:
            return False

    def write_values(
        self,
        device_id: str,
        product_id: str,
        values: dict,
        data_type: str = "property",
        ts: Optional[datetime] = None,
    ) -> None:
        if not self.enabled or self._failed:
            return
        fields = self._fields(values)
        if not fields:
            return
        _pool.submit(self._write_sync, device_id, product_id, fields, data_type, ts)

    def _fields(self, data: Optional[dict]) -> dict:
        """遥测唯一写入 Influx：数值 + 布尔 + 短字符串"""
        fields = {}
        for key, value in (data or {}).items():
            name = str(key)
            if isinstance(value, bool):
                fields[name] = value
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                fields[name] = float(value)
            elif isinstance(value, str) and len(value) <= 256:
                fields[name] = value
        return fields

    def query_series(
        self,
        device_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        points: Optional[List[str]] = None,
        limit: int = 500,
    ) -> Optional[Dict[str, List[list]]]:
        """成功返回 series；未启用/失败返回 None"""
        if not self.enabled:
            return None
        try:
            client = self._get_client()
            if not client:
                return None
            stop = end or datetime.now(timezone.utc)
            begin = start or (stop - timedelta(hours=24))
            if begin.tzinfo is None:
                begin = begin.replace(tzinfo=timezone.utc)
            if stop.tzinfo is None:
                stop = stop.replace(tzinfo=timezone.utc)
            did = _safe_id(device_id)
            flux = (
                f'from(bucket: "{settings.INFLUX_BUCKET}") '
                f"|> range(start: {begin.isoformat()}, stop: {stop.isoformat()}) "
                f'|> filter(fn: (r) => r._measurement == "telemetry") '
                f'|> filter(fn: (r) => r.device_id == "{did}") '
                f"|> limit(n: {max(1, min(int(limit), 5000))})"
            )
            tables = client.query_api().query(flux, org=settings.INFLUX_ORG)
            series: Dict[str, List[list]] = {}
            wanted = set(points or [])
            for table in tables or []:
                for record in table.records:
                    field = record.get_field()
                    if wanted and field not in wanted:
                        continue
                    value = record.get_value()
                    ts = record.get_time()
                    iso = ts.isoformat() if ts else None
                    if isinstance(value, bool):
                        value = 1.0 if value else 0.0
                    if not isinstance(value, (int, float)):
                        continue
                    series.setdefault(field, []).append([iso, float(value)])
            for key in series:
                series[key].sort(key=lambda x: x[0] or "")
            return series
        except Exception as exc:
            logger.warning("Influx query: %s", exc)
            return None

    def query_rows(
        self,
        device_id: str,
        data_type: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """按时间倒序列出遥测点，供 /data 与轨迹使用"""
        series = self.query_series(device_id, limit=max(limit, 50))
        if not series:
            return []
        by_ts: Dict[str, dict] = {}
        for field, points in series.items():
            if data_type == "location" and field not in ("latitude", "longitude", "lat", "lng", "lon"):
                continue
            for iso, value in points:
                row = by_ts.setdefault(iso or "", {})
                row[field] = value
        rows = sorted(by_ts.items(), key=lambda x: x[0], reverse=True)[:limit]
        return [{"timestamp": ts, "data": data} for ts, data in rows]

    def _get_client(self):
        if self._client:
            return self._client
        if not self.enabled:
            return None
        try:
            from influxdb_client import InfluxDBClient
            self._client = InfluxDBClient(
                url=settings.INFLUX_URL,
                token=settings.INFLUX_TOKEN,
                org=settings.INFLUX_ORG,
                timeout=5000,
            )
            return self._client
        except Exception as exc:
            logger.warning("Influx client: %s", exc)
            self._failed = True
            return None

    def _write_sync(
        self,
        device_id: str,
        product_id: str,
        fields: Dict[str, float],
        data_type: str,
        ts: Optional[datetime],
    ) -> None:
        try:
            from influxdb_client import Point, WritePrecision
            from influxdb_client.client.write_api import SYNCHRONOUS

            client = self._get_client()
            if not client:
                return
            point = (
                Point("telemetry")
                .tag("device_id", _safe_id(device_id))
                .tag("product_id", _safe_id(product_id or "default"))
                .tag("data_type", data_type or "property")
            )
            for key, value in fields.items():
                point = point.field(key, value)
            when = ts or datetime.now(timezone.utc)
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            point = point.time(when, WritePrecision.NS)
            client.write_api(write_options=SYNCHRONOUS).write(
                bucket=settings.INFLUX_BUCKET, org=settings.INFLUX_ORG, record=point
            )
        except Exception as exc:
            logger.warning("Influx write: %s", exc)


timeseries = TimeseriesStore()
