"""Expression helpers for Temple runtime and tooling.

Supports a safe MVP expression subset:
- dotted variable lookup (including numeric index segments: ``user.skills.0``)
- list literals
- boolean operators: ``not``, ``and``, ``or``
- comparisons: ``==``, ``!=``, ``<``, ``<=``, ``>``, ``>=``
"""

from __future__ import annotations

import ast
import re
from typing import Any

_SIMPLE_PATH_RE = re.compile(r"^[A-Za-z_]\w*(?:\.(?:[A-Za-z_]\w*|\d+))*$")
_INDEX_ACCESS_RE = re.compile(r"(?<=[A-Za-z_\]\)])\.(\d+)\b")


def normalize_expression(expr: str) -> str:
    """Normalize Temple expression text into Python-parseable form."""
    # Convert dotted numeric index access to subscript form: a.b.0 -> a.b[0]
    return _INDEX_ACCESS_RE.sub(r"[\1]", expr)


def is_simple_path(expr: str) -> bool:
    return bool(_SIMPLE_PATH_RE.fullmatch(expr.strip()))


def resolve_simple_path(path: str, context: dict[str, Any] | None) -> Any:
    """Resolve a dot path in dictionaries/lists with graceful missing handling."""
    if context is None:
        return None

    value: Any = context
    for part in path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, (list, tuple)):
            if not part.isdigit():
                return None
            idx = int(part)
            if idx < 0 or idx >= len(value):
                return None
            value = value[idx]
        else:
            return None
    return value


class _ExpressionEvaluator:
    def __init__(self, context: dict[str, Any]):
        self.context = context

    def eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            return self.context.get(node.id)

        if isinstance(node, ast.Attribute):
            parent = self.eval(node.value)
            if isinstance(parent, dict):
                return parent.get(node.attr)
            return getattr(parent, node.attr, None)

        if isinstance(node, ast.Subscript):
            container = self.eval(node.value)
            key = self.eval(node.slice)
            return self._subscript(container, key)

        if isinstance(node, ast.List):
            return [self.eval(item) for item in node.elts]

        if isinstance(node, ast.Tuple):
            return tuple(self.eval(item) for item in node.elts)

        if isinstance(node, ast.UnaryOp):
            value = self.eval(node.operand)
            if isinstance(node.op, ast.Not):
                return not bool(value)
            if isinstance(node.op, ast.USub):
                return -value if isinstance(value, (int, float)) else None
            if isinstance(node.op, ast.UAdd):
                return +value if isinstance(value, (int, float)) else None
            return None

        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                result = self.eval(node.values[0])
                for expr in node.values[1:]:
                    if not result:
                        return result
                    result = self.eval(expr)
                return result
            if isinstance(node.op, ast.Or):
                result = self.eval(node.values[0])
                for expr in node.values[1:]:
                    if result:
                        return result
                    result = self.eval(expr)
                return result
            return None

        if isinstance(node, ast.Compare):
            return self._evaluate_compare(node)

        if isinstance(node, ast.BinOp):
            left = self.eval(node.left)
            right = self.eval(node.right)
            if isinstance(node.op, ast.Add):
                try:
                    return left + right
                except Exception:
                    return None
            if isinstance(node.op, ast.Sub):
                return left - right if isinstance(left, (int, float)) and isinstance(right, (int, float)) else None
            if isinstance(node.op, ast.Mult):
                return left * right if isinstance(left, (int, float, str)) and isinstance(right, (int, float)) else None
            if isinstance(node.op, ast.Div):
                if isinstance(left, (int, float)) and isinstance(right, (int, float)) and right != 0:
                    return left / right
                return None
            return None

        if isinstance(node, ast.Dict):
            out: dict[Any, Any] = {}
            for key_node, value_node in zip(node.keys, node.values):
                if key_node is None:
                    continue
                out[self.eval(key_node)] = self.eval(value_node)
            return out

        return None

    def _subscript(self, container: Any, key: Any) -> Any:
        if isinstance(container, dict):
            return container.get(key)
        if isinstance(container, (list, tuple)):
            if not isinstance(key, int):
                return None
            if key < 0 or key >= len(container):
                return None
            return container[key]
        try:
            return container[key]
        except Exception:
            return None

    def _evaluate_compare(self, node: ast.Compare) -> bool:
        left = self.eval(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self.eval(comparator)
            if isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            elif isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            elif isinstance(op, ast.Gt):
                ok = left > right
            elif isinstance(op, ast.GtE):
                ok = left >= right
            else:
                return False

            if not ok:
                return False
            left = right
        return True


def evaluate_expression(expr: str | None, context: dict[str, Any] | None) -> Any:
    """Evaluate an expression against context. Returns None on unsupported/invalid input."""
    if expr is None:
        return None

    stripped = expr.strip()
    if not stripped:
        return None

    if is_simple_path(stripped):
        return resolve_simple_path(stripped, context)

    try:
        parsed = ast.parse(normalize_expression(stripped), mode="eval")
    except Exception:
        return None

    evaluator = _ExpressionEvaluator(context or {})
    try:
        return evaluator.eval(parsed.body)
    except Exception:
        return None


def _path_from_node(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        parent = _path_from_node(node.value)
        if parent is None:
            return None
        return f"{parent}.{node.attr}"

    if isinstance(node, ast.Subscript):
        parent = _path_from_node(node.value)
        if parent is None:
            return None
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
            return f"{parent}.{node.slice.value}"
        return parent

    return None


class _VariablePathCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.paths: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        self.paths.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        path = _path_from_node(node)
        if path:
            self.paths.add(path)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        path = _path_from_node(node)
        if path:
            self.paths.add(path)
        self.generic_visit(node)


def extract_variable_paths(expr: str | None) -> set[str]:
    """Extract variable paths referenced by an expression."""
    if expr is None:
        return set()

    stripped = expr.strip()
    if not stripped:
        return set()

    if is_simple_path(stripped):
        return {stripped}

    try:
        parsed = ast.parse(normalize_expression(stripped), mode="eval")
    except Exception:
        return set()

    collector = _VariablePathCollector()
    collector.visit(parsed)
    return collector.paths
