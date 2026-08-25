"""工业协议采集运行时：OPC UA / S7 / IEC104 / BACnet / KNX 轮询写入物模型"""
import logging
import random
import socket
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

INDUSTRIAL = ("opcua", "s7", "iec104", "bacnet", "knx")


class IndustrialCollect:
    def __init__(self):
        self._stop: Dict[str, threading.Event] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self.connected = False
        self.devices: Dict[str, dict] = {}

    def start(self, channel) -> str:
        self.stop(channel.channel_id)
        event = threading.Event()
        self._stop[channel.channel_id] = event
        thread = threading.Thread(target=self._loop, args=(channel, event), daemon=True)
        self._threads[channel.channel_id] = thread
        thread.start()
        self.connected = True
        return "running"

    def stop(self, channel_id: str) -> str:
        event = self._stop.pop(channel_id, None)
        if event:
            event.set()
        self._threads.pop(channel_id, None)
        return "stopped"

    def _loop(self, channel, event: threading.Event) -> None:
        cfg = dict(channel.config or {})
        proto = (channel.protocol or "").lower()
        interval = max(float(cfg.get("poll_interval") or cfg.get("interval") or 5), 1)
        while not event.wait(interval):
            try:
                values = self.poll(proto, cfg)
                device_id = cfg.get("device_id")
                if values and device_id:
                    self._ingest(device_id, values, channel.channel_id)
            except Exception as exc:
                logger.warning("Industrial %s %s: %s", proto, channel.channel_id, exc)

    def poll(self, proto: str, cfg: dict) -> Dict[str, Any]:
        if cfg.get("simulate"):
            return self._simulate(cfg)
        if proto == "opcua":
            return self._poll_opcua(cfg)
        if proto == "s7":
            return self._poll_s7(cfg)
        if proto == "iec104":
            return self._poll_iec104(cfg)
        if proto == "bacnet":
            return self._poll_bacnet(cfg)
        if proto == "knx":
            return self._poll_knx(cfg)
        return {}

    def write(self, proto: str, cfg: dict, values: dict) -> bool:
        if cfg.get("simulate"):
            return True
        try:
            if proto == "opcua":
                from app.services.opcua_client import write_nodes
                mapping = {p.get("node") or p.get("node_id"): p.get("name") for p in cfg.get("points") or []}
                payload = {}
                for node, name in mapping.items():
                    if name in values and node:
                        payload[node] = values[name]
                return write_nodes(cfg.get("endpoint") or cfg.get("host"), payload)
            if proto == "s7":
                return self._write_s7(cfg, values)
            if proto == "iec104":
                return self._write_iec104(cfg, values)
            if proto == "bacnet":
                return self._write_bacnet(cfg, values)
            if proto == "knx":
                return self._write_knx(cfg, values)
        except Exception as exc:
            logger.warning("Industrial write %s: %s", proto, exc)
        return False

    def _simulate(self, cfg: dict) -> Dict[str, Any]:
        out = {}
        for point in cfg.get("points") or []:
            name = point.get("name")
            if not name:
                continue
            base = float(point.get("base") or 20)
            out[name] = round(base + random.random() * 5, 2)
        return out

    def _poll_opcua(self, cfg: dict) -> Dict[str, Any]:
        from app.services.opcua_client import read_nodes
        points = cfg.get("points") or []
        nodes = [p.get("node") or p.get("node_id") for p in points if p.get("node") or p.get("node_id")]
        raw = read_nodes(cfg.get("endpoint") or f"opc.tcp://{cfg.get('host')}:{cfg.get('port') or 4840}", nodes)
        out = {}
        for point in points:
            node = point.get("node") or point.get("node_id")
            if point.get("name") and node in raw:
                out[point["name"]] = raw[node]
        return out

    def _poll_s7(self, cfg: dict) -> Dict[str, Any]:
        from app.services.s7_codec import decode_value, encode_read, parse_read_payload, point_spec, cotp_connect, s7_setup
        sock = self._tcp(cfg.get("host"), int(cfg.get("port") or 102))
        if not sock:
            return {}
        try:
            sock.sendall(cotp_connect(int(cfg.get("rack") or 0), int(cfg.get("slot") or 1)))
            sock.recv(4096)
            sock.sendall(s7_setup())
            sock.recv(4096)
            out = {}
            for point in cfg.get("points") or []:
                db, offset, size, kind = point_spec(point)
                sock.sendall(encode_read(db, offset, size))
                raw = parse_read_payload(sock.recv(4096))
                value = decode_value(raw, kind)
                if point.get("name") and value is not None:
                    out[point["name"]] = value
            return out
        finally:
            sock.close()

    def _write_s7(self, cfg: dict, values: dict) -> bool:
        from app.services.s7_codec import cotp_connect, encode_write, pack_points, s7_setup
        sock = self._tcp(cfg.get("host"), int(cfg.get("port") or 102))
        if not sock:
            return False
        try:
            sock.sendall(cotp_connect(int(cfg.get("rack") or 0), int(cfg.get("slot") or 1)))
            sock.recv(4096)
            sock.sendall(s7_setup())
            sock.recv(4096)
            for point, data in pack_points(cfg.get("points") or [], values):
                sock.sendall(encode_write(int(point.get("db") or 1), int(point.get("offset") or 0), data))
                sock.recv(4096)
            return True
        finally:
            sock.close()

    def _poll_iec104(self, cfg: dict) -> Dict[str, Any]:
        from app.services.iec104_codec import STARTDT_ACT, general_interrogation, map_points, parse_apdu
        sock = self._tcp(cfg.get("host"), int(cfg.get("port") or 2404))
        if not sock:
            return {}
        try:
            sock.sendall(STARTDT_ACT)
            sock.recv(4096)
            sock.sendall(general_interrogation(int(cfg.get("common_address") or cfg.get("ca") or 1)))
            buf = sock.recv(8192)
            return map_points(parse_apdu(buf), cfg.get("points") or [])
        finally:
            sock.close()

    def _write_iec104(self, cfg: dict, values: dict) -> bool:
        from app.services.iec104_codec import STARTDT_ACT, encode_setpoint_float, encode_single_command
        sock = self._tcp(cfg.get("host"), int(cfg.get("port") or 2404))
        if not sock:
            return False
        try:
            sock.sendall(STARTDT_ACT)
            sock.recv(4096)
            ca = int(cfg.get("common_address") or 1)
            by_name = {p.get("name"): p for p in cfg.get("points") or []}
            for name, value in values.items():
                point = by_name.get(name)
                if not point:
                    continue
                ioa = int(point.get("ioa") or 0)
                if isinstance(value, bool):
                    sock.sendall(encode_single_command(ca, ioa, value))
                else:
                    sock.sendall(encode_setpoint_float(ca, ioa, float(value)))
                sock.recv(4096)
            return True
        finally:
            sock.close()

    def _poll_bacnet(self, cfg: dict) -> Dict[str, Any]:
        from app.services.bacnet_codec import encode_read_property, object_from_point, parse_present_value
        host, port = cfg.get("host"), int(cfg.get("port") or 47808)
        out = {}
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(float(cfg.get("timeout") or 2))
        try:
            for i, point in enumerate(cfg.get("points") or [], start=1):
                obj_type, instance = object_from_point(point)
                sock.sendto(encode_read_property(i, obj_type, instance), (host, port))
                try:
                    data, _addr = sock.recvfrom(2048)
                except socket.timeout:
                    continue
                value = parse_present_value(data)
                if point.get("name") and value is not None:
                    out[point["name"]] = value
        finally:
            sock.close()
        return out

    def _write_bacnet(self, cfg: dict, values: dict) -> bool:
        from app.services.bacnet_codec import encode_write_property, object_from_point
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            for i, point in enumerate(cfg.get("points") or [], start=1):
                name = point.get("name")
                if name not in values:
                    continue
                obj_type, instance = object_from_point(point)
                sock.sendto(
                    encode_write_property(i, obj_type, instance, values[name]),
                    (cfg.get("host"), int(cfg.get("port") or 47808)),
                )
            return True
        finally:
            sock.close()

    def _poll_knx(self, cfg: dict) -> Dict[str, Any]:
        from app.services.knx_codec import encode_connect_request, encode_tunnel_read, map_points, parse_cemi_value, parse_connect_response
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(float(cfg.get("timeout") or 2))
        host, port = cfg.get("host"), int(cfg.get("port") or 3671)
        try:
            sock.sendto(encode_connect_request(port), (host, port))
            data, _addr = sock.recvfrom(2048)
            channel = parse_connect_response(data)
            found = {}
            for i, point in enumerate(cfg.get("points") or []):
                ga = point.get("group_address") or point.get("address")
                sock.sendto(encode_tunnel_read(channel, i, ga), (host, port))
                try:
                    resp, _ = sock.recvfrom(2048)
                    addr, value = parse_cemi_value(resp)
                    if addr:
                        found[addr] = value
                except socket.timeout:
                    continue
            return map_points(found, cfg.get("points") or [])
        except Exception as exc:
            logger.debug("KNX poll: %s", exc)
            return {}
        finally:
            sock.close()

    def _write_knx(self, cfg: dict, values: dict) -> bool:
        from app.services.knx_codec import encode_connect_request, encode_tunnel_write, parse_connect_response
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            host, port = cfg.get("host"), int(cfg.get("port") or 3671)
            sock.sendto(encode_connect_request(port), (host, port))
            data, _ = sock.recvfrom(2048)
            channel = parse_connect_response(data)
            for i, point in enumerate(cfg.get("points") or []):
                name = point.get("name")
                if name not in values:
                    continue
                sock.sendto(
                    encode_tunnel_write(channel, i, point.get("group_address") or "1/1/1", values[name]),
                    (host, port),
                )
            return True
        except Exception:
            return False
        finally:
            sock.close()

    def _tcp(self, host: Optional[str], port: int) -> Optional[socket.socket]:
        if not host:
            return None
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        try:
            sock.connect((host, port))
            return sock
        except Exception:
            sock.close()
            return None

    def _ingest(self, device_id: str, values: dict, channel_id: str) -> None:
        from app.db.session import SessionLocal
        from app.crud.channel import channel_crud
        from app.services.device_runtime_service import device_runtime
        from app.services.mqtt_service import mqtt_client

        db = SessionLocal()
        try:
            device_runtime.put_values(db, device_id, values, publish_alarm=mqtt_client._publish_alarm)
            channel_crud.add_log(db, channel_id, f"industrial ingest {device_id}", payload=values)
        finally:
            db.close()


industrial_collect = IndustrialCollect()
