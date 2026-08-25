"""连接器：按 MQTT 契约 link/{linker}/{link_id}/{open|close|up|down} 管理 TCP"""
import json
import logging
import socket
import threading
from typing import Dict, Optional

from app.db.session import SessionLocal
from app.crud.link import link_crud

logger = logging.getLogger(__name__)


class TcpSession:
    def __init__(self, linker: str, link_id: str, host: str, port: int, publish):
        self.linker = linker
        self.link_id = link_id
        self.host = host
        self.port = int(port)
        self.publish = publish
        self.sock: Optional[socket.socket] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def open(self) -> bool:
        self.sock = socket.create_connection((self.host, self.port), timeout=8)
        self.sock.settimeout(2)
        self.running = True
        self.thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.thread.start()
        return True

    def close(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None

    def send(self, data: bytes):
        if self.sock:
            self.sock.sendall(data)

    def _recv_loop(self):
        while self.running and self.sock:
            try:
                chunk = self.sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            if not chunk:
                break
            topic = f"link/{self.linker}/{self.link_id}/up"
            self.publish(topic, chunk)
        self.running = False


class LinkBusService:
    """进程内连接器插件，通过 MQTT 与协议插件协作"""

    def __init__(self):
        self.sessions: Dict[str, TcpSession] = {}
        self._mqtt = None
        self.connected = False
        self.devices = {}
        self._lock = threading.Lock()

    def attach(self, mqtt_service) -> None:
        self._mqtt = mqtt_service
        mqtt_service.register_handler("link/", self.on_link_message)

    def on_link_message(self, topic: str, payload: bytes) -> None:
        parts = topic.split("/")
        if len(parts) < 4:
            return
        linker, link_id, action = parts[1], parts[2], parts[3]
        if action == "open":
            self._open(linker, link_id, payload)
        elif action == "close":
            with self._lock:
                self._close(link_id)
        elif action == "down":
            session = self.sessions.get(link_id)
            if session:
                session.send(payload)

    def _open(self, linker: str, link_id: str, payload: bytes):
        options = {}
        try:
            options = json.loads(payload.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            options = {}
        host = options.get("host") or options.get("remote") or "127.0.0.1"
        port = options.get("port") or 502
        if linker not in ("tcp-client", "tcp", "modbus-tcp"):
            logger.warning("Linker %s 暂仅实现 TCP 客户端", linker)
            return
        with self._lock:
            existing = self.sessions.get(link_id)
            if existing and existing.running and existing.host == host and existing.port == int(port):
                logger.info("Link %s already open %s:%s", link_id, host, port)
                return
            self._close(link_id)
            session = TcpSession(linker, link_id, host, port, self._mqtt.publish)
            try:
                session.open()
                self.sessions[link_id] = session
                self._set_status(link_id, "open")
                logger.info("Link opened %s %s:%s", link_id, host, port)
            except OSError as exc:
                self._set_status(link_id, "error", str(exc))
                logger.error("Link open failed %s: %s", link_id, exc)

    def _close(self, link_id: str):
        session = self.sessions.pop(link_id, None)
        if session:
            session.close()
        self._set_status(link_id, "closed")

    def _set_status(self, link_id: str, status: str, error: Optional[str] = None):
        db = SessionLocal()
        try:
            link_crud.set_status(db, link_id, status, error)
        finally:
            db.close()

    async def start(self) -> bool:
        self.connected = True
        return True

    async def stop(self) -> bool:
        for link_id in list(self.sessions):
            self._close(link_id)
        self.connected = False
        return True


link_bus_service = LinkBusService()
