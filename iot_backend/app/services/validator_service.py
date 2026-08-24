"""物模型 Validator 告警引擎"""
import logging
import operator
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

OPS = {
    "=": operator.eq,
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}


def _replace_placeholders(text: str, values: Dict[str, Any]) -> str:
    if not text:
        return text or ""

    def repl(match):
        key = match.group(1)
        return str(values.get(key, match.group(0)))

    return re.sub(r"\{(\w+)\}", repl, text)


def _eval_compare(rule: Dict[str, Any], values: Dict[str, Any]) -> bool:
    field = rule.get("field")
    op_name = rule.get("operator", "==")
    threshold = rule.get("value")
    if field is None or field not in values:
        return False
    fn = OPS.get(op_name)
    if not fn:
        return False
    try:
        return bool(fn(values[field], threshold))
    except TypeError:
        return False


def _eval_expression(rule: Dict[str, Any], values: Dict[str, Any]) -> bool:
    """简易表达式：支持 field 与数字的比较，如 temperature > 30"""
    expr = (rule.get("expression") or "").strip()
    if not expr:
        return False
    # 仅允许安全子集：标识符、数字、比较符、空格
    if not re.fullmatch(r"[\w\s.<>=!+\-*/()]+", expr):
        logger.warning("拒绝不安全表达式: %s", expr)
        return False
    local = dict(values)
    try:
        return bool(eval(expr, {"__builtins__": {}}, local))  # noqa: S307
    except Exception as exc:
        logger.warning("表达式评估失败 %s: %s", expr, exc)
        return False


def evaluate_validators(
    validators: List[Dict[str, Any]], values: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """评估物模型 validators，返回触发的告警描述列表"""
    triggered: List[Dict[str, Any]] = []
    for rule in validators or []:
        rule_type = rule.get("type", "compare")
        hit = False
        if rule_type == "expression":
            hit = _eval_expression(rule, values)
        else:
            hit = _eval_compare(rule, values)
        if not hit:
            continue
        title = _replace_placeholders(rule.get("title", "告警"), values)
        message = _replace_placeholders(rule.get("message", ""), values)
        triggered.append(
            {
                "validator_name": rule.get("name") or rule.get("field"),
                "level": rule.get("level", "warning"),
                "title": title,
                "message": message,
                "values": values,
            }
        )
    return triggered
