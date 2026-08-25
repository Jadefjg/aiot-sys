from types import SimpleNamespace

from app.services.thing_parser import decode_hex, decode_values


def test_decode_hex_be_scale():
    # 00 64 at offset 0, len 2, scale 0.1 -> 10.0
    out = decode_hex("0064", {"temperature": {"offset": 0, "len": 2, "scale": 0.1, "endian": "be"}})
    assert out["temperature"] == 10.0


def test_decode_values_json_map_keeps_unmapped():
    product = SimpleNamespace(config={"parser": {"type": "map", "mapping": {"temp": "temperature"}}})
    out = decode_values(product, {"temp": 26.5, "energy": 12})
    assert out["temperature"] == 26.5
    assert out["energy"] == 12
    assert "temp" not in out


def test_decode_values_nested_data():
    product = SimpleNamespace(config={})
    out = decode_values(product, {"data": {"energy": 12}})
    assert out["energy"] == 12


def test_decode_values_hex_raw_field():
    product = SimpleNamespace(config={
        "parser": {"type": "hex", "mapping": {"voltage": {"offset": 0, "len": 2, "scale": 0.1}}}
    })
    out = decode_values(product, {"raw": "00C8"})
    assert out["voltage"] == 20.0


def test_decode_values_kv():
    product = SimpleNamespace(config={"parser": {"type": "kv"}})
    out = decode_values(product, "temp=25,energy=3.2")
    assert out["temp"] == 25
    assert out["energy"] == 3.2
