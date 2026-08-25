"""物解析：DGIoT 采集公式 %s 采集值 / %q 标识 / %r 轮次"""
import ast
import operator
from typing import Any, Dict, List, Optional

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _eval(node, names: dict):
    if isinstance(node, ast.Expression):
        return _eval(node.body, names)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Name):
        return names.get(node.id, 0)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left, names), _eval(node.right, names))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand, names))
    raise ValueError("unsupported formula")


def apply_formula(formula: str, sampled, ident=0, round_no=1) -> Optional[float]:
    if not formula:
        return sampled
    expr = (
        str(formula)
        .replace("%s", "s")
        .replace("%q", "q")
        .replace("%r", "r")
    )
    try:
        tree = ast.parse(expr, mode="eval")
        return _eval(tree, {"s": float(sampled), "q": float(ident or 0), "r": float(round_no)})
    except Exception:
        return sampled


def apply_property_formulas(properties: List[dict], values: Dict[str, Any], round_no: int = 1) -> Dict[str, Any]:
    """按物模型采集公式改写上报值"""
    result = dict(values)
    for prop in properties or []:
        name = prop.get("name")
        if not name or name not in result:
            continue
        formula = prop.get("formula") or prop.get("collect_formula")
        if not formula:
            continue
        result[name] = apply_formula(formula, result[name], prop.get("quantity") or 0, round_no)
    return result
