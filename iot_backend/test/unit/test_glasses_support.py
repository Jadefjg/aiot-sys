"""智能眼镜增量能力：物模型种子、媒体事件、场景动作回落到触发设备"""
from app.services.media_service import EVENT_TYPES, record_event
from app.services.scene_engine import SceneEngine, _compare, _match_rule
from app.services.validator_service import evaluate_validators


def test_glasses_validators_low_battery_and_privacy():
    rules = [
        {"name": "low_battery", "field": "battery", "operator": "<", "value": 15, "title": "低电"},
        {
            "name": "privacy",
            "type": "expression",
            "expression": "worn == False and camera_on == True",
            "title": "隐私",
        },
    ]
    low = evaluate_validators(rules, {"battery": 10, "worn": True, "camera_on": True})
    assert any(item["validator_name"] == "low_battery" for item in low)
    privacy = evaluate_validators(rules, {"battery": 80, "worn": False, "camera_on": True})
    assert any(item["validator_name"] == "privacy" for item in privacy)
    ok = evaluate_validators(rules, {"battery": 80, "worn": True, "camera_on": True})
    assert ok == []


def test_scene_rule_can_filter_product():
    values = {"temperature": 50}
    assert _match_rule({"field": "temperature", "operator": ">", "value": 45}, "g1", values, "glasses-full")
    assert not _match_rule(
        {"field": "temperature", "operator": ">", "value": 45, "product_id": "glasses-lite"},
        "g1",
        values,
        "glasses-full",
    )


def test_scene_action_defaults_to_source_device():
    engine = SceneEngine()
    called = {}

    def fake_write(db, device_id, values):
        called["device_id"] = device_id
        called["values"] = values

    engine._write_device = fake_write
    engine._execute_actions(None, [{"type": "write", "values": {"camera_on": False}}], "glasses-full-001")
    assert called["device_id"] == "glasses-full-001"
    assert called["values"]["camera_on"] is False


def test_media_event_types_only_capture_media():
    assert EVENT_TYPES["photo_captured"] == "photo"
    assert EVENT_TYPES["clip_ready"] == "clip"
    assert record_event.__name__ == "record_event"


def test_compare_mixed_types_do_not_raise():
    assert _compare("hot", ">", 45) is False
    assert _compare(None, "<", 15) is False
    assert _compare(50, ">", 45) is True


def test_seed_glasses_triggers_include_product_id():
    from scripts.seed_glasses import GLASSES_PRODUCTS, SCENES

    for scene in SCENES:
        assert scene.triggers
        assert all(item.get("product_id") in GLASSES_PRODUCTS for item in scene.triggers)
