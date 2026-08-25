"""Modbus 协议插件：protocol/modbus/{linker}/{link_id}/#"""
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional

from app.db.session import SessionLocal
from app.services.modbus_codec import (
    build_read,
    build_write_multi,
    build_write_single,
    decode_point,
    encode_point,
    parse_mbap,
    parse_read_registers,
)

logger = logging.getLogger(__name__)


class ModbusBinding:
    def __init__(self, linker: str, link_id: str, devices: List[dict], interval_ms: int = 1000):
        self.linker = linker
        self.link_id = link_id
        self.devices = devices
        self.interval = max(interval_ms, 200) / 1000.0
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._tid = 1
        self._pending: Dict[int, dict] = {}

    def next_tid(self) -> int:
        self._tid = (self._tid + 1) & 0xFFFF or 1
        return self._tid


class ModbusPlugin:
    def __init__(self):
        self.bindings: Dict[str, ModbusBinding] = {}
        self._mqtt = None
        self.connected = False
        self.devices = {}

    def attach(self, mqtt_service) -> None:
        self._mqtt = mqtt_service
        mqtt_service.register_handler("protocol/modbus/", self.on_protocol)
        mqtt_service.register_handler("link/", self.on_link_up)

    def on_protocol(self, topic: str, payload: bytes) -> None:
        parts = topic.split("/")
        if len(parts) < 5:
            return
        linker, link_id, action = parts[2], parts[3], parts[4]
        data = self._json(payload)
        if action == "open":
            self._bind(linker, link_id, data)
        elif action == "close":
            self._unbind(link_id)
        elif action in ("poll", "sync", "read"):
            self._read(link_id, data)
        elif action == "write":
            self._write(link_id, data)

    def on_link_up(self, topic: str, payload: bytes) -> None:
        parts = topic.split("/")
        if len(parts) < 4 or parts[3] != "up":
            return
        link_id = parts[2]
        binding = self.bindings.get(link_id)
        if not binding:
            return
        parsed = parse_mbap(payload)
        if not parsed:
            return
        tid, _unit, pdu = parsed
        pending = binding._pending.pop(tid, None)
        if not pending:
            return
        regs = parse_read_registers(pdu)
        values = {}
        for point in pending.get("points") or []:
            qty = int(point.get("quantity") or (2 if "32" in str(point.get("type")) else 1))
            chunk = regs[:qty]
            regs = regs[qty:]
            val = decode_point(chunk, point)
            if val is not None:
                values[point["name"]] = val
        if values:
            self._mqtt.publish(f"device/{pending['device_id']}/values", json.dumps(values))
        msg_id = pending.get("msg_id")
        if msg_id:
            self._mqtt.publish(
                f"device/{pending['device_id']}/read/response",
                json.dumps({"msg_id": msg_id, "values": values}),
            )

    def _bind(self, linker: str, link_id: str, data: dict):
        devices = data.get("devices") or self._load_devices(link_id)
        interval = int(data.get("poll_interval") or 1000)
        self._unbind(link_id)
        binding = ModbusBinding(linker, link_id, devices, interval)
        binding.running = True
        binding.thread = threading.Thread(target=self._poll_loop, args=(binding,), daemon=True)
        binding.thread.start()
        self.bindings[link_id] = binding
        logger.info("Modbus bind %s devices=%s", link_id, len(devices))

    def _unbind(self, link_id: str):
        binding = self.bindings.pop(link_id, None)
        if binding:
            binding.running = False

    def _poll_loop(self, binding: ModbusBinding):
        while binding.running:
            for device in binding.devices:
                try:
                    self._issue_read(binding, device, device.get("points") or [])
                except Exception as exc:
                    logger.debug("Modbus poll %s: %s", device.get("device_id"), exc)
            time.sleep(binding.interval)

    def _issue_read(self, binding: ModbusBinding, device: dict, points: List[dict], msg_id=None):
        if not points:
            return
        slave = int(device.get("slave") or device.get("slave_id") or 1)
        address = min(int(p.get("address") or 0) for p in points)
        end = max(int(p.get("address") or 0) + int(p.get("quantity") or 1) for p in points)
        qty = max(end - address, 1)
        func = int(points[0].get("function") or 3)
        tid = binding.next_tid()
        frame = build_read(slave, address, qty, func=func, tid=tid)
        now = time.time()
        for old in [k for k, v in binding._pending.items() if now - v.get("ts", 0) > 15]:
            binding._pending.pop(old, None)
        binding._pending[tid] = {
            "device_id": device["device_id"], "points": points, "msg_id": msg_id, "ts": now
        }
        self._mqtt.publish(f"link/{binding.linker}/{binding.link_id}/down", frame)

    def _read(self, link_id: str, data: dict):
        binding = self.bindings.get(link_id)
        if not binding:
            return
        device = self._find_device(binding, data.get("device_id"))
        if device:
            self._issue_read(binding, device, device.get("points") or [], data.get("msg_id"))

    def _write(self, link_id: str, data: dict):
        binding = self.bindings.get(link_id)
        if not binding:
            return
        device = self._find_device(binding, data.get("device_id"))
        if not device:
            return
        slave = int(device.get("slave") or 1)
        values = data.get("values") or {}
        results = {}
        for point in device.get("points") or []:
            name = point.get("name")
            if name not in values:
                continue
            regs = encode_point(values[name], point)
            tid = binding.next_tid()
            addr = int(point.get("address") or 0)
            frame = (
                build_write_single(slave, addr, regs[0], tid)
                if len(regs) == 1
                else build_write_multi(slave, addr, regs, tid)
            )
            self._mqtt.publish(f"link/{binding.linker}/{binding.link_id}/down", frame)
            results[name] = True
        if data.get("msg_id"):
            self._mqtt.publish(
                f"device/{device['device_id']}/write/response",
                json.dumps({"msg_id": data["msg_id"], "results": results}),
            )

    def _find_device(self, binding: ModbusBinding, device_id: Optional[str]) -> Optional[dict]:
        for item in binding.devices:
            if item.get("device_id") == device_id:
                return item
        return binding.devices[0] if binding.devices else None

    def _load_devices(self, link_id: str) -> List[dict]:
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
        for link_id in list(self.bindings):
            self._unbind(link_id)
        self.connected = False
        return True


modbus_plugin = ModbusPlugin()
