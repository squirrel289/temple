from typing import Any, Dict, List, Optional, Tuple


class TemplateError(Exception):
    pass


class Node:
    def __init__(self, start: Optional[Tuple[int, int]] = None):
        self.start = start

    def evaluate(self, context: Dict[str, Any], includes: Dict[str, "Block"] | None = None, path: str = "", mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None) -> Any:
        raise NotImplementedError()


class Text(Node):
    def __init__(self, text: str, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.text = text

    def evaluate(self, context: Dict[str, Any], includes: Dict[str, "Block"] | None = None, path: str = "", mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None) -> str:
        return self.text


class Expression(Node):
    def __init__(self, expr: str, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.expr = expr

    def _resolve(self, context: Dict[str, Any]) -> Any:
        # very small dot-notation resolver (supports integers for list indices)
        parts = self.expr.split(".") if self.expr else []
        cur: Any = context
        for p in parts:
            if isinstance(cur, list) and p.isdigit():
                idx = int(p)
                try:
                    cur = cur[idx]
                except Exception as e:
                    raise TemplateError(f"Index error in expression '{self.expr}': {e}")
            elif isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                # missing -> None
                return None
        return cur

    def evaluate(self, context: Dict[str, Any], includes: Dict[str, "Block"] | None = None, path: str = "", mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None) -> Any:
        val = self._resolve(context)
        if mapping is not None and self.start is not None:
            mapping.append((path or "/", self.start))
        return val


class If(Node):
    def __init__(self, condition: str, body: "Block", elif_parts: Optional[List[Tuple[str, "Block"]]] = None, else_body: Optional["Block"] = None, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.condition = condition
        self.body = body
        self.elif_parts = elif_parts or []
        self.else_body = else_body

    def evaluate(self, context: Dict[str, Any], includes: Dict[str, "Block"] | None = None, path: str = "", mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None) -> Any:
        cond_val = Expression(self.condition).evaluate(context, includes, path + "/cond", mapping)
        if cond_val:
            return self.body.evaluate(context, includes, path + "/body", mapping)
        
        # Check elif branches
        for idx, (elif_cond, elif_body) in enumerate(self.elif_parts):
            elif_val = Expression(elif_cond).evaluate(context, includes, path + f"/elif[{idx}]/cond", mapping)
            if elif_val:
                return elif_body.evaluate(context, includes, path + f"/elif[{idx}]/body", mapping)
        
        # Check else branch
        if self.else_body:
            return self.else_body.evaluate(context, includes, path + "/else", mapping)
        return None


class For(Node):
    def __init__(self, var_name: str, iterable_expr: str, body: "Block", start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.var_name = var_name
        self.iterable_expr = iterable_expr
        self.body = body

    def evaluate(self, context: Dict[str, Any], includes: Dict[str, "Block"] | None = None, path: str = "", mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None) -> List[Any]:
        iterable = Expression(self.iterable_expr).evaluate(context, includes, path + "/iter", mapping)
        if iterable is None:
            return []
        # try to get length for loop helpers
        try:
            length = len(iterable)
        except Exception:
            length = None
        results = []
        for idx, item in enumerate(iterable):
            local_ctx = dict(context)
            local_ctx[self.var_name] = item
            # loop helper
            loop = {
                "index": idx + 1,
                "index0": idx,
                "first": idx == 0,
                "last": (length is not None and idx == length - 1) if length is not None else False,
                "length": length,
            }
            local_ctx["loop"] = loop
            val = self.body.evaluate(local_ctx, includes, path + f"/for[{self.var_name}][{idx}]", mapping)
            if isinstance(val, list):
                results.extend(val)
            else:
                results.append(val)
        return results


class Include(Node):
    def __init__(self, name: str, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.name = name

    def evaluate(self, context: Dict[str, Any], includes: Dict[str, "Block"] | None = None, path: str = "", mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None) -> Any:
        if not includes or self.name not in includes:
            raise TemplateError(f"Include not found: {self.name}")
        return includes[self.name].evaluate(context, includes, path + f"/include[{self.name}]", mapping)


class Block(Node):
    def __init__(self, nodes: Optional[List[Node]] = None, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.nodes = nodes or []

    def evaluate(self, context: Dict[str, Any], includes: Dict[str, "Block"] | None = None, path: str = "", mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None) -> Any:
        out: List[Any] = []
        for idx, n in enumerate(self.nodes):
            v = n.evaluate(context, includes, path + f"/{idx}", mapping)
            # flatten nested Blocks and For results conservatively
            if isinstance(v, list):
                out.extend(v)
            elif v is None:
                continue
            else:
                out.append(v)
        if mapping is not None and self.start is not None:
            mapping.append((path or "/", self.start))
        return out


class Array(Node):
    def __init__(self, items: Optional[List[Node]] = None, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.items = items or []

    def evaluate(self, context: Dict[str, Any], includes: Dict[str, "Block"] | None = None, path: str = "", mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None) -> List[Any]:
        out: List[Any] = []
        for idx, it in enumerate(self.items):
            v = it.evaluate(context, includes, path + f"/{idx}", mapping)
            if isinstance(v, list):
                out.extend(v)
            elif v is None:
                continue
            else:
                out.append(v)
        if mapping is not None and self.start is not None:
            mapping.append((path or "/", self.start))
        return out


class ObjectNode(Node):
    def __init__(self, pairs: Optional[List[Tuple[str, Node]]] = None, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        # pairs: list of (key, Node)
        self.pairs = pairs or []

    def evaluate(self, context: Dict[str, Any], includes: Dict[str, "Block"] | None = None, path: str = "", mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for key, node in self.pairs:
            v = node.evaluate(context, includes, path + f"/{key}", mapping)
            # if v is a single-item list, unwrap to scalar
            if isinstance(v, list) and len(v) == 1:
                out[key] = v[0]
            else:
                out[key] = v
        if mapping is not None and self.start is not None:
            mapping.append((path or "/", self.start))
        return out


__all__ = [
    "Node",
    "Text",
    "Expression",
    "If",
    "For",
    "Include",
    "Block",
    "Array",
    "ObjectNode",
    "TemplateError",
]
