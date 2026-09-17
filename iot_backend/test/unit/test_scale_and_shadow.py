from unittest.mock import patch

from app.services.shadow_service import compute_delta, document
from app.services.scale_profile import assess


def test_compute_delta_only_unmatched_keys():
    assert compute_delta({"a": 1, "b": 2}, {"a": 1, "b": 3}) == {"b": 2}
    assert compute_delta({"a": 1}, {"a": 1}) == {}
    assert compute_delta({"power": "on"}, {}) == {"power": "on"}
    assert compute_delta({}, {"power": "on"}) == {}
    assert compute_delta(None, None) == {}


def test_shadow_document_includes_delta():
    doc = document("dev-1", reported={"a": 1}, desired={"a": 2, "b": 3}, version=4)
    assert doc["delta"] == {"a": 2, "b": 3}
    assert doc["version"] == 4


def test_assess_uses_configured_stage():
    with patch("app.services.scale_profile.get_redis", return_value=object()), patch(
        "app.services.scale_profile.timeseries"
    ) as ts, patch(
        "app.services.scale_profile.settings"
    ) as settings:
        ts.enabled = True
        settings.SCALE_STAGE = "small"
        settings.MQTT_BROKER_HOST = "mqtt_broker"
        settings.MQTT_CONNECT_RATE_LIMIT = 0
        with patch("app.services.settings_store.get_values", return_value={"stage": "small"}):
            data = assess(12_000)
        assert data["stage"] == "small"
        assert data["device_count"] == 12_000
        assert any(row["area"] == "OTA" for row in data["selection"])
        assert data["playbook"]
        assert data["pipeline"]
        assert data["pitfalls"]


def test_assess_auto_detects_prototype_when_stage_empty():
    with patch("app.services.scale_profile.get_redis", return_value=None), patch(
        "app.services.scale_profile.timeseries"
    ) as ts, patch(
        "app.services.scale_profile.settings"
    ) as settings:
        ts.enabled = False
        settings.SCALE_STAGE = ""
        settings.MQTT_BROKER_HOST = "localhost"
        settings.MQTT_CONNECT_RATE_LIMIT = 0
        with patch("app.services.settings_store.get_values", return_value={}):
            data = assess(80)
        assert data["stage"] == "prototype"
        assert any("Redis" in g for g in data["gaps"])
        assert any("Influx" in g for g in data["gaps"])


def test_alert_debounce_without_redis_allows():
    from app.services.message_pipeline import alert_allowed
    with patch("app.services.message_pipeline.get_redis", return_value=None):
        assert alert_allowed("dev-1", "高温") is True


def test_alert_debounce_nx_once():
    from app.services.message_pipeline import alert_allowed

    client = type("R", (), {})()
    calls = []

    def set_nx(key, val, nx=False, ex=None):
        calls.append(key)
        return len(calls) == 1

    client.set = set_nx
    with patch("app.services.message_pipeline.get_redis", return_value=client):
        assert alert_allowed("dev-1", "高温") is True
        assert alert_allowed("dev-1", "高温") is False

