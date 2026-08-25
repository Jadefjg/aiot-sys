from app.services.timeseries import _safe_id, numeric_fields


def test_numeric_fields_skip_strings():
    assert numeric_fields({"temperature": 21.5, "on": True, "name": "meter"}) == {
        "temperature": 21.5,
        "on": 1.0,
    }


def test_safe_id_strips_wildcards():
    assert _safe_id("demo-meter-1") == "demo-meter-1"
    assert "+" not in _safe_id("a+b")
