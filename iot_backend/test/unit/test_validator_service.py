"""物模型 Validator 单元测试"""
from app.services.validator_service import evaluate_validators


def test_compare_greater_than():
    rules = [{"type": "compare", "field": "temperature", "operator": ">", "value": 30,
              "title": "高温", "message": "温度 {temperature}"}]
    hit = evaluate_validators(rules, {"temperature": 36.5})
    assert len(hit) == 1
    assert hit[0]["title"] == "高温"
    assert "36.5" in hit[0]["message"]


def test_compare_not_triggered():
    rules = [{"type": "compare", "field": "temperature", "operator": ">", "value": 30, "title": "高温"}]
    assert evaluate_validators(rules, {"temperature": 20}) == []


def test_expression_rule():
    rules = [{"type": "expression", "expression": "humidity < 20", "title": "干燥"}]
    hit = evaluate_validators(rules, {"humidity": 10})
    assert len(hit) == 1


def test_unsafe_expression_rejected():
    rules = [{"type": "expression", "expression": "__import__('os').system('ls')", "title": "x"}]
    assert evaluate_validators(rules, {}) == []
