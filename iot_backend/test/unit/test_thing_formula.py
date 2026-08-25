from app.services.thing_formula import apply_formula, apply_property_formulas


def test_percent_s_scale():
    assert apply_formula("%s*0.1", 255) == 25.5


def test_property_formulas():
    props = [{"name": "energy", "formula": "%s/100", "quantity": 0}]
    out = apply_property_formulas(props, {"energy": 1234, "status": 1})
    assert out["energy"] == 12.34
    assert out["status"] == 1
