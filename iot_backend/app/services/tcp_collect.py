"""TCP 采集通道：监听端口，按行解析 JSON/Hex 后写入设备运行时"""
import json
import logging
import socket
import threading
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TcpCollectRuntime:
    def __init__(self):
        self._servers: Dict[str, socket.socket] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._stop = threading.Event()

    def start(self, channel) -> str:
        cfg = channel.config or {}
        port = int(cfg.get("port") or cfg.get("listen_port") or 9000)
        if port < 1024 or port > 65535:
            raise ValueError("TCP 采集端口须在 1024-65535")
        self.stop(channel.channel_id)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        sock.listen(8)
        sock.settimeout(1.0)
        self._servers[channel.channel_id] = sock
        thread = threading.Thread(
            target=self._loop, args=(channel.channel_id, sock, cfg), daemon=True
        )
        self._threads[channel.channel_id] = thread
        thread.start()
        logger.info("TCP collect %s listen :%s", channel.channel_id, port)
        return "running"

    def stop(self, channel_id: str) -> str:
        sock = self._servers.pop(channel_id, None)
        if sock:
            try:
                sock.close()
            except Exception:
                pass
        return "stopped"

    def _loop(self, channel_id: str, sock: socket.socket, cfg: dict) -> None:
        while channel_id in self._servers:
            try:
                conn, addr = sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(
                target=self._client, args=(channel_id, conn, cfg), daemon=True
            ).start()

    def _client(self, channel_id: str, conn: socket.socket, cfg: dict) -> None:
        conn.settimeout(30)
        buf = b""
        try:
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf or b"}" in buf:
                    line, buf = self._take_frame(buf)
                    if line is None:
                        break
                    self._ingest(channel_id, line, cfg)
        except Exception as exc:
            logger.debug("TCP collect client: %s", exc)
        finally:
            conn.close()

    def _take_frame(self, buf: bytes) -> tuple:
        if b"\n" in buf:
            line, rest = buf.split(b"\n", 1)
            return line.strip(), rest
        text = buf.decode("utf-8", errors="replace").strip()
        if text.startswith("{") and text.endswith("}"):
            return buf.strip(), b""
        return None, buf

    def _ingest(self, channel_id: str, raw: bytes, cfg: dict) -> None:
        from app.db.session import SessionLocal
        from app.crud.channel import channel_crud
        from app.services.device_runtime_service import device_runtime
        from app.services.mqtt_service import mqtt_client

        text = raw.decode("utf-8", errors="replace").strip()
        if not text:
            return
        db = SessionLocal()
        try:
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = {"raw": text}
            device_id = (
                (payload.get("device_id") if isinstance(payload, dict) else None)
                or cfg.get("device_id")
            )
            if not device_id:
                return
            values = dict(payload) if isinstance(payload, dict) else {"raw": text}
            values.pop("device_id", None)
            device_runtime.put_values(
                db, device_id, values, publish_alarm=mqtt_client._publish_alarm
            )
            channel_crud.add_log(db, channel_id, f"tcp ingest {device_id}", payload=values)
        except Exception as exc:
            logger.warning("TCP ingest: %s", exc)
        finally:
            db.close()


tcp_collect = TcpCollectRuntime()
