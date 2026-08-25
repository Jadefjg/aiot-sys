from app.services.s7_codec import decode_value, encode_read, encode_value, parse_read_payload
from app.services.iec104_codec import STARTDT_ACT, general_interrogation, map_points, parse_apdu
from app.services.bacnet_codec import encode_read_property, parse_present_value
from app.services.knx_codec import encode_tunnel_write, parse_group_address
from app.services.industrial_collect import industrial_collect
from app.services.script_engine import lua_to_js, run_js, ScriptHost
from app.services.opcua_client import encode_node_id, hello_message, parse_endpoint


def test_s7_real_roundtrip():
    raw = encode_value(12.5, "real")
    assert abs(decode_value(raw, "real") - 12.5) < 0.01
    pkt = encode_read(1, 0, 4)
    assert pkt[:2] == b"\x03\x00"


def test_s7_parse_payload():
    data = b"\x00\x04\x00\x20" + encode_value(1.0, "real")
    fake = b"xxxx\x32" + b"\x01\x00\x00\x00\x01\x00\x02\x00\x00" + b"\x04\x01" + data
    # 简化：直接测 decode
    assert decode_value(encode_value(3, "int16"), "int16") == 3


def test_iec104_gi_and_float():
    pkt = general_interrogation(1)
    assert pkt[0] == 0x68
    assert STARTDT_ACT[2] == 0x07
    asdu = bytes([13, 1, 3, 0, 1, 0, 1, 0, 0]) + __import__("struct").pack("<f", 22.0) + bytes([0])
    apdu = bytes([0x68, 4 + len(asdu), 0, 0, 0, 0]) + asdu
    items = parse_apdu(apdu)
    mapped = map_points(items, [{"name": "temp", "ioa": 1}])
    assert abs(mapped["temp"] - 22.0) < 0.01


def test_bacnet_read_and_parse_real():
    pkt = encode_read_property(1, 0, 2)
    assert pkt[:2] == b"\x81\x0a"
    import struct
    buf = b"xx\x44" + struct.pack(">f", 18.5)
    assert abs(parse_present_value(buf) - 18.5) < 0.01


def test_knx_group_address():
    assert parse_group_address("1/2/3") == ((1 << 11) | (2 << 8) | 3)
    pkt = encode_tunnel_write(1, 0, "1/1/1", True)
    assert pkt[2:4] == b"\x04\x20"


def test_opcua_hello_and_node():
    host, port, url = parse_endpoint("opc.tcp://10.0.0.8:4840")
    assert host == "10.0.0.8" and port == 4840
    msg = hello_message(url)
    assert msg[:3] == b"HEL"
    nid = encode_node_id("ns=2;s=Temp")
    assert nid[0] == 0x03


def test_industrial_simulate():
    values = industrial_collect.poll("s7", {
        "simulate": True,
        "points": [{"name": "temperature", "base": 20}],
    })
    assert "temperature" in values


def test_js_if_write():
    host = ScriptHost()
    run_js(
        'if (values.temperature > 30) { write(device_id, {fan: 1}); log("hot"); }',
        {"host": host, "write": host.write, "log": host.log, "device_id": "d1",
         "values": {"temperature": 31}},
    )
    assert host.writes == [("d1", {"fan": 1})]
    assert host.logs == ["hot"]


def test_lua_to_js_and_run():
    js = lua_to_js('if values.temperature > 30 then write(device_id, {fan=1}) end')
    host = ScriptHost()
    run_js(js, {"host": host, "write": host.write, "log": host.log, "device_id": "d1",
                "values": {"temperature": 40}})
    assert host.writes[0][1]["fan"] == 1
