"""百万级 AIoT 规模档位：对照当前部署给出选型与缺口。
参考：https://mp.weixin.qq.com/s/Hc878kPSOXpb-rm-QTd3dw
"""
from typing import Any, Dict, List

from app.core.config import settings
from app.core.redis import get_redis
from app.services.timeseries import timeseries

STAGES: List[Dict[str, Any]] = [
    {
        "id": "prototype",
        "name": "阶段 1 · 原型验证",
        "devices": "几千",
        "tps": "百级",
        "stack": "单节点 MQTT + MySQL + HTTP 管理面",
        "this_repo": "docker compose COMPOSE_PROFILES=local（当前默认）",
    },
    {
        "id": "small",
        "name": "阶段 2 · 小规模生产",
        "devices": "1–10 万",
        "tps": "千–万",
        "stack": "3 节点 EMQX + Redis 影子 + Influx/TDengine",
        "this_repo": "开启 INFLUX_ENABLED，影子走 Redis，MQTT 用 EMQX",
    },
    {
        "id": "medium",
        "name": "阶段 3 · 中等规模",
        "devices": "10–50 万",
        "tps": "万–十万",
        "stack": "MQTT 集群 + Kafka 管道 + 规则引擎 + 时序集群",
        "this_repo": "接入 Kafka/通道转发，规则引擎与灰度 OTA",
    },
    {
        "id": "large",
        "name": "阶段 4 · 大规模",
        "devices": "50–200 万",
        "tps": "10 万+",
        "stack": "MQTT 分片 + 边缘聚合 + 时序集群 + AI",
        "this_repo": "网关汇聚子设备、媒体 AI、微服务拆分",
    },
    {
        "id": "xlarge",
        "name": "阶段 5 · 超大规模",
        "devices": "200 万+",
        "tps": "区域分片",
        "stack": "多 Region MQTT + 全局 LB + 存储分层",
        "this_repo": "按区域拆库/拆 Broker，不在单机 Compose 内完成",
    },
]

TARGETS = {
    "devices": "100 万+",
    "tps": "10 万+",
    "latency_ms": 500,
    "availability": "99.99%",
    "ota_success": "99.5%+",
}

SELECTION = [
    {"area": "接入协议", "recommend": "MQTT 3.1.1 / 百万级用 MQTT 5.0 共享订阅", "now": "MQTT 为主，CoAP/AMQP 骨架"},
    {"area": "Broker", "recommend": "百万级首选 EMQX 集群；开发可用 Mosquitto", "now": "local=EMQX，shared=Mosquitto"},
    {"area": "设备影子", "recommend": "Redis 热缓存 + desired/reported/delta", "now": "Redis 缓存 + MySQL 持久化"},
    {"area": "时序存储", "recommend": "TDengine / InfluxDB，禁止用 MySQL 存遥测", "now": "Influx 可选，事件仍落 MySQL"},
    {"area": "消息管道", "recommend": "接入 → 校验 → 影子 → 规则 → 时序 + Kafka", "now": "MQTT worker + 规则/场景引擎"},
    {"area": "OTA", "recommend": "灰度批次 100→1k→1万→全量，失败率>5% 暂停", "now": "FirmwareRollout 分批推送"},
    {"area": "连接风暴", "recommend": "指数退避 + 接入限流", "now": "可配置 MQTT_CONNECT_RATE_LIMIT"},
    {"area": "边缘", "recommend": "高频点在网关聚合后再上报", "now": "网关/子设备主题路由"},
    {"area": "消息队列", "recommend": "Kafka 削峰；原型可用 Redis Stream", "now": "Redis Stream iot:pipeline:telemetry"},
    {"area": "告警风暴", "recommend": "聚合 + 防抖 + 限流", "now": "规则边沿触发 + Redis 60s 防抖"},
]

PITFALLS = [
    {"pit": "连接风暴", "why": "大量设备同时断连重连", "fix": "指数退避 + 随机抖动 + MQTT_CONNECT_RATE_LIMIT"},
    {"pit": "消息风暴", "why": "规则引擎触发海量告警", "fix": "边沿触发 + 告警防抖 TTL"},
    {"pit": "Topic 爆炸", "why": "Topic 过多占 Broker 内存", "fix": "device/{id}/{type} 三层，禁止无节制通配"},
    {"pit": "存储瓶颈", "why": "MySQL 存时序", "fix": "Influx/TDengine，property 不再写 MySQL"},
    {"pit": "OTA 失败", "why": "一次推全量", "fix": "灰度 100→1k→1万 + 失败率>5% 暂停/回滚"},
    {"pit": "影子不一致", "why": "离线期间 desired 未同步", "fix": "delta + 上线补偿"},
    {"pit": "消息积压", "why": "下游慢于上游", "fix": "Redis Stream / Kafka 缓冲"},
]

PIPELINE = [
    {"step": 1, "name": "接入", "now": "EMQX MQTT 长连接"},
    {"step": 2, "name": "解析/校验", "now": "物模型 parser + JSON；非法进 DLQ"},
    {"step": 3, "name": "设备影子", "now": "Redis desired/reported/delta"},
    {"step": 4, "name": "规则引擎", "now": "条件边沿 + 告警/写点/转发"},
    {"step": 5, "name": "时序存储", "now": "Influx；未启用才落 MySQL"},
    {"step": 6, "name": "消息队列", "now": "Redis Stream（Kafka 可替换）"},
]

PLAYBOOK = {
    "prototype": ["保持 COMPOSE_PROFILES=local", "打开 INFLUX_ENABLED", "影子走 Redis", "灰度 OTA 用 100 台试点"],
    "small": ["EMQX 至少 3 节点", "遥测禁止写 MySQL", "设置 MQTT_CONNECT_RATE_LIMIT", "观察 OTA 成功率"],
    "medium": ["接入 Kafka 替换 Redis Stream", "规则与告警防抖压测", "时序集群化"],
    "large": ["MQTT 按设备 ID 分片", "边缘网关聚合高频点", "微服务拆分接入面"],
    "xlarge": ["多 Region Broker", "全局 LB + TLS 卸载", "热/冷存储分层"],
}

PROTOCOLS = [
    {"scene": "通用传感器", "recommend": "MQTT 3.1.1", "reason": "成熟、客户端丰富"},
    {"scene": "百万级高并发", "recommend": "MQTT 5.0 共享订阅", "reason": "服务端负载均衡"},
    {"scene": "NB-IoT 低功耗", "recommend": "CoAP", "reason": "UDP 开销小"},
    {"scene": "摄像头/网关", "recommend": "HTTP + WebSocket", "reason": "带宽充足"},
    {"scene": "工业控制", "recommend": "TCP/Modbus", "reason": "低延迟确定性"},
]


def _connect_limit() -> int:
    try:
        from app.services.settings_store import connect_rate_limit
        return connect_rate_limit()
    except Exception:
        return int(settings.MQTT_CONNECT_RATE_LIMIT or 0)


def _detect_stage(device_count: int, influx: bool, redis_ok: bool) -> str:
    configured = (settings.SCALE_STAGE or "").strip().lower()
    try:
        from app.services import settings_store
        stored = settings_store.get_values("scale", redact=False) or {}
        configured = (stored.get("stage") or configured or "").strip().lower()
    except Exception:
        pass
    if configured in {s["id"] for s in STAGES}:
        return configured
    if device_count >= 500_000 and influx and redis_ok:
        return "large"
    if device_count >= 100_000 and influx:
        return "medium"
    if device_count >= 10_000 and (influx or redis_ok):
        return "small"
    return "prototype"


def assess(device_count: int = 0) -> Dict[str, Any]:
    redis_ok = get_redis() is not None
    influx_on = bool(timeseries.enabled)
    stage_id = _detect_stage(device_count, influx_on, redis_ok)
    gaps = []
    if not redis_ok:
        gaps.append("Redis 不可用：影子热缓存与在线集合无法工作")
    if not influx_on:
        gaps.append("未启用 Influx：遥测仍可能压 MySQL，无法支撑十万级写入")
    if settings.MQTT_BROKER_HOST in ("mqtt_lite", "localhost") and stage_id not in ("prototype",):
        gaps.append("生产 Broker 建议 EMQX 集群，Mosquitto 仅适合开发")
    if device_count > 5000 and not influx_on:
        gaps.append("设备数已超过原型档，请开启 INFLUX_ENABLED")
    return {
        "stage": stage_id,
        "stage_meta": next(s for s in STAGES if s["id"] == stage_id),
        "device_count": device_count,
        "capabilities": {
            "redis": redis_ok,
            "influx": influx_on,
            "mqtt_host": settings.MQTT_BROKER_HOST,
            "connect_rate_limit": _connect_limit(),
        },
        "targets": TARGETS,
        "stages": STAGES,
        "selection": SELECTION,
        "gaps": gaps,
        "pipeline": PIPELINE,
        "pitfalls": PITFALLS,
        "playbook": PLAYBOOK.get(stage_id, PLAYBOOK["prototype"]),
        "protocols": PROTOCOLS,
        "pipeline_stats": _pipeline_stats(),
        "reference": "https://mp.weixin.qq.com/s/Hc878kPSOXpb-rm-QTd3dw",
    }


def _pipeline_stats() -> Dict[str, Any]:
    try:
        from app.services.message_pipeline import dlq_len, stream_len
        return {"stream": stream_len(), "dlq": dlq_len(), "alert_debounce_s": 60}
    except Exception:
        return {"stream": 0, "dlq": 0, "alert_debounce_s": 60}
