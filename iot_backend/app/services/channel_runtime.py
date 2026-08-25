"""资源通道：采集数据转发到 Webhook / MQTT / 二次存储日志"""
import json
import logging
import time
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.crud.channel import channel_crud

logger = logging.getLogger(__name__)


class ChannelRuntime:
    def __init__(self):
        self._res_cache = []
        self._res_at = 0.0

    def invalidate(self) -> None:
        self._res_at = 0.0

    def on_device_values(self, db: Session, device, values: Dict[str, Any]) -> None:
        product_id = device.product_id
        now = time.time()
        if now - self._res_at > 3:
            self._res_cache = channel_crud.get_enabled(db, kind="resource")
            self._res_at = now
        for channel in self._res_cache:
            products = channel.product_ids or []
            if products and product_id not in products:
                continue
            cfg = channel.config or {}
            proto = (channel.protocol or "").lower()
            try:
                if proto in ("webhook", "http"):
                    self._webhook(cfg.get("url"), device.device_id, values)
                elif proto in ("mqtt", "mqtt_forward"):
                    topic = cfg.get("topic") or f"resource/{channel.channel_id}/{device.device_id}/values"
                    topic = (
                        topic.replace("{channel}", channel.channel_id)
                        .replace("{device}", device.device_id)
                        .replace("+", device.device_id)
                    )
                    if "#" in topic:
                        logger.warning("Skip MQTT resource topic %s", topic)
                    else:
                        self._mqtt(topic, values)
                elif proto in ("mysql", "tdengine", "storage", "influx"):
                    continue
                channel_crud.add_log(
                    db, channel.channel_id, f"{device.device_id} 转发成功", payload=values
                )
            except Exception as exc:
                logger.warning("Resource channel %s: %s", channel.channel_id, exc)
                channel_crud.add_log(db, channel.channel_id, str(exc), level="error")

    def start_collect(self, db: Session, channel) -> str:
        proto = (channel.protocol or "").lower()
        cfg = channel.config or {}
        if proto == "tcp":
            from app.services.tcp_collect import tcp_collect
            status_name = tcp_collect.start(channel)
            channel_crud.add_log(db, channel.channel_id, f"TCP 采集监听 {cfg.get('port') or 9000}")
            return status_name
        if proto in ("opcua", "s7", "iec104", "bacnet", "knx"):
            from app.services.industrial_collect import industrial_collect
            status_name = industrial_collect.start(channel)
            channel_crud.add_log(db, channel.channel_id, f"{proto} 采集已启动")
            return status_name
        if proto == "modbus" and cfg.get("link_id"):
            from app.crud.link import link_crud
            from app.services.link_bus_service import link_bus_service
            from app.services.modbus_plugin import modbus_plugin

            link = link_crud.get_by_link_id(db, cfg["link_id"])
            if link:
                options = json.dumps(link.options or {})
                link_bus_service.on_link_message(f"link/{link.linker}/{link.link_id}/open", options.encode())
                payload = json.dumps({"poll_interval": cfg.get("poll_interval", 1000)})
                modbus_plugin.on_protocol(
                    f"protocol/modbus/{link.linker}/{link.link_id}/open", payload.encode()
                )
        if proto == "dlt645" and cfg.get("link_id"):
            from app.crud.link import link_crud
            from app.services.dlt645_plugin import dlt645_plugin
            from app.services.link_bus_service import link_bus_service

            link = link_crud.get_by_link_id(db, cfg["link_id"])
            if link:
                options = json.dumps(link.options or {})
                link_bus_service.on_link_message(f"link/{link.linker}/{link.link_id}/open", options.encode())
                devices = cfg.get("devices") or []
                if not devices:
                    from app.services.link_devices import bound_devices_for_link
                    devices = bound_devices_for_link(db, link.link_id)
                dlt645_plugin.on_protocol(
                    f"protocol/dlt645/{link.linker}/{link.link_id}/open",
                    json.dumps({
                        "devices": devices,
                        "interval": cfg.get("poll_interval", 5),
                    }).encode(),
                )
        channel_crud.add_log(db, channel.channel_id, "采集通道已启用")
        return "running"

    def stop_collect(self, db: Session, channel) -> str:
        cfg = channel.config or {}
        proto = (channel.protocol or "").lower()
        if proto == "tcp":
            from app.services.tcp_collect import tcp_collect
            tcp_collect.stop(channel.channel_id)
        if proto in ("opcua", "s7", "iec104", "bacnet", "knx"):
            from app.services.industrial_collect import industrial_collect
            industrial_collect.stop(channel.channel_id)
        if cfg.get("link_id") and proto in ("modbus", "dlt645"):
            from app.crud.link import link_crud
            from app.services.link_bus_service import link_bus_service

            link = link_crud.get_by_link_id(db, cfg["link_id"])
            if link:
                if proto == "modbus":
                    from app.services.modbus_plugin import modbus_plugin
                    modbus_plugin.on_protocol(
                        f"protocol/modbus/{link.linker}/{link.link_id}/close", b"{}"
                    )
                if proto == "dlt645":
                    from app.services.dlt645_plugin import dlt645_plugin
                    dlt645_plugin.on_protocol(
                        f"protocol/dlt645/{link.linker}/{link.link_id}/close", b"{}"
                    )
                link_bus_service.on_link_message(f"link/{link.linker}/{link.link_id}/close", b"{}")
        channel_crud.add_log(db, channel.channel_id, "采集通道已停止")
        return "stopped"

    def _webhook(self, url: str, device_id: str, values: dict) -> None:
        from app.services.http_dispatch import post_json
        post_json(url, {"device_id": device_id, "values": values})

    def _mqtt(self, topic: str, values: dict) -> None:
        from app.services.mqtt_service import mqtt_client
        mqtt_client.publish(topic, json.dumps(values, default=str))


channel_runtime = ChannelRuntime()
