#!/usr/bin/env python3
"""眼镜固件模拟：按现有 MQTT 主题上报电量/佩戴/相机，并响应 write/action"""
import argparse
import json
import os
import time
import uuid

import paho.mqtt.client as mqtt

DEFAULT_STATE = {
    "battery": 82,
    "charging": False,
    "worn": True,
    "temperature": 36.5,
    "camera_on": True,
    "mic_on": True,
    "storage_free": 2048,
    "fw_ar1": "1.0.0",
    "fw_bes": "1.0.0",
}


def _topic(device_id: str, suffix: str) -> str:
    return f"device/{device_id}/{suffix}"


class GlassesSim:
    def __init__(self, host: str, port: int, device_id: str, product_id: str):
        self.device_id = device_id
        self.product_id = product_id
        self.state = dict(DEFAULT_STATE)
        if product_id == "glasses-full":
            self.state.update({"speaker_on": True, "volume": 60})
        self.client = mqtt.Client(client_id=f"sim-{device_id}-{uuid.uuid4().hex[:6]}")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(host, port, 60)

    def _pub(self, suffix: str, payload: dict) -> None:
        self.client.publish(_topic(self.device_id, suffix), json.dumps(payload), qos=1)

    def _on_connect(self, client, userdata, flags, rc):
        for suffix in ("write", "action", "sync", "read", "setting"):
            client.subscribe(_topic(self.device_id, suffix))
        self._pub("register", {"product_id": self.product_id, "device_name": self.device_id})
        self._pub("online", {"status": "online"})
        self._pub("values", self.state)

    def _reply(self, kind: str, msg_id, extra=None):
        body = {"msg_id": msg_id, "ok": True, "values": self.state}
        if extra:
            body.update(extra)
        self._pub(f"{kind}/response", body)

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode() or "{}")
        except json.JSONDecodeError:
            data = {}
        parts = msg.topic.split("/")
        kind = parts[-1] if parts else ""
        msg_id = data.get("msg_id")
        if kind == "write":
            values = data.get("values") or {}
            self.state.update(values)
            self._pub("values", self.state)
            self._reply("write", msg_id)
        elif kind == "action":
            self._handle_action(data.get("action") or "default", data.get("params") or {}, msg_id)
        elif kind in ("sync", "read"):
            self._reply(kind, msg_id)
        elif kind == "setting":
            self._reply("setting", msg_id, {"name": data.get("name")})

    def _handle_action(self, action: str, params: dict, msg_id) -> None:
        if action == "set_privacy":
            self.state["camera_on"] = False
            self.state["mic_on"] = False
            self._pub("values", self.state)
        elif action == "capture":
            self._pub("event", {
                "type": "photo_captured",
                "object_key": f"sim/{self.device_id}/{uuid.uuid4().hex}.jpg",
                "content_type": "image/jpeg",
                "width": 1920,
                "height": 1080,
            })
        self._reply("action", msg_id, {"action": action, "params": params})

    def loop(self, interval: int) -> None:
        self.client.loop_start()
        try:
            while True:
                time.sleep(interval)
                self.state["battery"] = max(1, int(self.state["battery"]) - 1)
                self._pub("heartbeat", {"ts": int(time.time())})
                self._pub("values", {"battery": self.state["battery"], "worn": self.state["worn"],
                                     "camera_on": self.state["camera_on"], "temperature": self.state["temperature"]})
        except KeyboardInterrupt:
            self._pub("offline", {"status": "offline"})
            self.client.loop_stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="智能眼镜 MQTT 模拟器")
    parser.add_argument("--host", default=os.getenv("MQTT_BROKER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MQTT_BROKER_PORT", "1883")))
    parser.add_argument("--device-id", default="glasses-full-001")
    parser.add_argument("--product-id", default="glasses-full")
    parser.add_argument("--interval", type=int, default=10)
    args = parser.parse_args()
    GlassesSim(args.host, args.port, args.device_id, args.product_id).loop(args.interval)


if __name__ == "__main__":
    main()
