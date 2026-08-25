"""DL/T645 协议插件：protocol/dlt645/{linker}/{link_id}/#"""
import json
import logging
import threading
import time
from typing import Dict, List, Optional

from app.services.dlt645_codec import (
    build_read, build_switch, decode_energy, parse_frame, split_frames
)

logger = logging.getLogger(__name__)


class Dlt645Plugin:
    def __init__(self):
        self.bindings: Dict[str, dict] = {}
        self._mqtt = None
        self.connected = False
        self.devices = {}

    def attach(self, mqtt_service) -> None:
        self._mqtt = mqtt_service
        mqtt_service.register_handler("protocol/dlt645/", self.on_protocol)
        mqtt_service.register_handler("link/", self.on_link_up)

    def on_protocol(self, topic: str, payload: bytes) -> None:
        parts = topic.split("/")
        if len(parts) < 5:
            return
        linker, link_id, action = parts[2], parts[3], parts[4]
        data = self._json(payload)
        if action == "open":
            old = self.bindings.get(link_id)
            if old:
                old["running"] = False
            devices = data.get("devices") or self._load_devices(link_id)
            interval = data.get("interval") or data.get("poll_interval") or 5
            self.bindings[link_id] = {
                "linker": linker, "devices": devices, "running": True, "interval": interval
            }
            t = threading.Thread(target=self._poll, args=(link_id,), daemon=True)
            t.start()
            logger.info("DLT645 bind %s devices=%s", link_id, len(devices))
        elif action == "close":
            item = self.bindings.pop(link_id, None)
            if item:
                item["running"] = False
        elif action == "action":
            self._switch(link_id, data)

    def on_link_up(self, topic: str, payload: bytes) -> None:
        parts = topic.split("/")
        if len(parts) < 4 or parts[3] != "up":
            return
        link_id = parts[2]
        if link_id not in self.bindings:
            return
        for frame in split_frames(payload):
            parsed = parse_frame(frame)
            if not parsed:
                continue
            addr, _ctrl, body = parsed
            energy = decode_energy(body)
            device_id = self._match(link_id, addr)
            if device_id and energy is not None:
                self._mqtt.publish(f"device/{device_id}/values", json.dumps({"energy": energy}))

    def _poll(self, link_id: str):
        while self.bindings.get(link_id, {}).get("running"):
            item = self.bindings[link_id]
            for device in item.get("devices") or []:
                addr = str(device.get("address") or device.get("meter") or "")
                if not addr:
                    continue
                frame = build_read(addr)
                self._mqtt.publish(f"link/{item['linker']}/{link_id}/down", frame)
            time.sleep(max(int(item.get("interval") or 5), 1))

    def _switch(self, link_id: str, data: dict):
        item = self.bindings.get(link_id)
        if not item:
            return
        addr = str(data.get("address") or "")
        close_sw = bool(data.get("close", True))
        self._mqtt.publish(
            f"link/{item['linker']}/{link_id}/down",
            build_switch(addr, close_sw),
        )
        if data.get("msg_id") and data.get("device_id"):
            self._mqtt.publish(
                f"device/{data['device_id']}/action/response",
                json.dumps({"msg_id": data["msg_id"], "result": {"close": close_sw}}),
            )

    def _match(self, link_id: str, addr: str) -> Optional[str]:
        for device in self.bindings.get(link_id, {}).get("devices") or []:
            raw = str(device.get("address") or "").replace(" ", "").upper()
            if raw and raw in addr.upper():
                return device.get("device_id")
        logger.warning("DLT645 address unmatched %s on %s", addr, link_id)
        return None

    def _load_devices(self, link_id: str) -> List[dict]:
        from app.db.session import SessionLocal
        from app.services.link_devices import bound_devices_for_link

        db = SessionLocal()
        try:
            return bound_devices_for_link(db, link_id)
        finally:
            db.close()

    def _json(self, payload: bytes) -> dict:
        try:
            return json.loads(payload.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    async def start(self) -> bool:
        self.connected = True
        return True

    async def stop(self) -> bool:
        for item in self.bindings.values():
            item["running"] = False
        self.bindings.clear()
        self.connected = False
        return True


dlt645_plugin = Dlt645Plugin()
