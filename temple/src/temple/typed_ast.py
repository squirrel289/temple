from typing import Any, Dict, List, Optional, Tuple
from temple.diagnostics import Position, SourceRange
from temple.range_utils import make_source_range


class TemplateError(Exception):
    pass


class Node:
    def __init__(self, start: Optional[object] = None):
        # `start` may be a (line, col) tuple or a SourceRange
        self.start = None
        self.source_range = None
        if start is None:
            return

        # Try to normalize allowed inputs into a canonical SourceRange.
        try:
            if isinstance(start, SourceRange):
                sr = make_source_range(source_range=start)
            elif isinstance(start, (tuple, list)):
                sr = make_source_range(start=tuple(start))
            else:
                # Allow duck conversion for Node but prefer explicit ranges.
                sr = make_source_range(source_range=start, allow_duck=True)
        except (TypeError, ValueError):
            # Do not crash callers here; if the provided `start` cannot be
            # coerced into a SourceRange, leave positions unset. This avoids
            # hard crashes for legacy call sites while we migrate callers to
            # provide canonical ranges.
            self.start = None
            self.source_range = None
            return

        self.source_range = sr
        self.start = (sr.start.line, sr.start.column)

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Optional[Dict[str, "Block"]] = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> Any:
        raise NotImplementedError()


class Text(Node):
    def __init__(self, text: str, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.text = text
        # canonical: use `text`

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Optional[Dict[str, "Block"]] = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> str:
        return self.text


class Expression(Node):
    def __init__(
        self,
        expr: Optional[str] = None,
        start: Optional[Tuple[int, int]] = None,
        source_range: Optional["SourceRange"] = None,
        **kwargs,
    ):
        # Accept both `expr` and legacy `value` kwarg, and optional `source_range` for compatibility
        expr_val = expr
        super().__init__(start)
        self.expr = expr_val
        # Allow explicit source_range to be passed by callers (type checker, tests)
        if source_range is not None:
            self.source_range = source_range

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

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Optional[Dict[str, "Block"]] = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> Any:
        val = self._resolve(context)
        if mapping is not None and self.start is not None:
            mapping.append((path or "/", self.start))
        return val


class If(Node):
    def __init__(
        self,
        condition: str,
        body: "Block",
        elif_parts: Optional[List[Tuple[str, "Block"]]] = None,
        else_if_parts: Optional[List[Tuple[str, "Block"]]] = None,
        else_body: Optional["Block"] = None,
        start: Optional[Tuple[int, int]] = None,
    ):
        super().__init__(start)
        self.condition = condition
        # Normalize body to a Block instance (tests expect .body.nodes)
        if isinstance(body, Block):
            self.body = body
        else:
            nodes = body if body is not None else []
            self.body = Block(nodes, start)
        # Handle positional `start` accidentally passed as `elif_parts` (legacy call sites)
        if (
            isinstance(elif_parts, tuple)
            and len(elif_parts) == 2
            and all(isinstance(x, int) for x in elif_parts)
        ):
            # caller passed start as third positional arg; shift into `start`
            start = elif_parts
            elif_parts = None

        # Support both legacy `elif_parts` and new `else_if_parts`
        parts = else_if_parts if else_if_parts is not None else (elif_parts or [])
        # Normalize elif/else_if bodies to Blocks
        normalized: List[Tuple[str, Block]] = []
        for c, b in parts:
            if isinstance(b, Block):
                normalized.append((c, b))
            else:
                bnodes = b if b is not None else []
                blk = Block(bnodes, start)
                normalized.append((c, blk))
        self.else_if_parts = normalized
        # Normalize else_body to Block or None
        if isinstance(else_body, Block):
            self.else_body = else_body
        elif else_body is None:
            self.else_body = None
        else:
            bn = else_body if isinstance(else_body, list) else [else_body]
            self.else_body = Block(bn, start)

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Optional[Dict[str, "Block"]] = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> Any:
        cond_val = Expression(self.condition).evaluate(
            context, includes, path + "/cond", mapping
        )
        if cond_val:
            return self.body.evaluate(context, includes, path + "/body", mapping)
        # Check else-if branches
        for idx, (else_if_cond, else_if_body_blk) in enumerate(self.else_if_parts):
            elif_val = Expression(else_if_cond).evaluate(
                context, includes, path + f"/else_if[{idx}]/cond", mapping
            )
            if elif_val:
                return else_if_body_blk.evaluate(
                    context, includes, path + f"/else_if[{idx}]/body", mapping
                )
        # Check else branch
        if self.else_body:
            return self.else_body.evaluate(context, includes, path + "/else", mapping)
        return None


class For(Node):
    def __init__(
        self,
        var: Optional[str],
        iterable: Optional[str],
        body: Optional["Block"] = None,
        start: Optional[Tuple[int, int]] = None,
    ):
        super().__init__(start)
        # Require var and iterable to be provided to avoid silent runtime errors.
        if var is None:
            raise TemplateError("For loop 'var' parameter is required")
        if iterable is None:
            raise TemplateError("For loop 'iterable' parameter is required")
        # Accept keyword args used in tests: var, iterable
        self.var = var
        self.iterable = iterable
        # Compatibility aliases for older code/tests that expect legacy names
        self.var_name = self.var
        self.iterable_expr = self.iterable
        # Body may be a Block or a list of nodes; normalize to Block
        if isinstance(body, Block):
            self.body = body
        else:
            nodes = body if body is not None else []
            self.body = Block(nodes, start)
        # legacy alias
        self.body_block = self.body

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Optional[Dict[str, "Block"]] = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> List[Any]:
        iterable = Expression(self.iterable).evaluate(
            context, includes, path + "/iter", mapping
        )
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
            local_ctx[self.var] = item
            # loop helper
            loop = {
                "index": idx + 1,
                "index0": idx,
                "first": idx == 0,
                "last": (length is not None and idx == length - 1)
                if length is not None
                else False,
                "length": length,
            }
            local_ctx["loop"] = loop
            val = self.body.evaluate(
                local_ctx, includes, path + f"/for[{self.var}][{idx}]", mapping
            )
            if isinstance(val, list):
                results.extend(val)
            else:
                results.append(val)
        return results


class Include(Node):
    def __init__(self, name: str, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.name = name

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Optional[Dict[str, "Block"]] = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> Any:
        if not includes or self.name not in includes:
            raise TemplateError(f"Include not found: {self.name}")
        return includes[self.name].evaluate(
            context, includes, path + f"/include[{self.name}]", mapping
        )


class Block(Node):
    def __init__(self, *args, **kwargs):
        """Flexible constructor to support legacy and current callsites.

        Supported signatures:
        - Block(nodes: List[Node], start: Optional[Tuple[int,int]] = None)
        - Block(name: str, nodes: List[Node], start: Optional[Tuple[int,int]] = None)
        """
        # Normalize possible signatures
        if len(args) == 0:
            nodes = []
            start = None
            name = None
        elif len(args) == 1:
            # Block(nodes)
            nodes = args[0]
            start = kwargs.get("start")
            name = None
        elif len(args) == 2:
            # Block(nodes, start) OR Block(name, nodes)
            if isinstance(args[0], str):
                name = args[0]
                nodes = args[1]
                start = kwargs.get("start")
            else:
                nodes = args[0]
                start = args[1]
                name = None
        else:
            # Block(name, nodes, start)
            name = args[0] if isinstance(args[0], str) else None
            nodes = args[1]
            start = args[2] if len(args) > 2 else kwargs.get("start")

        super().__init__(start)
        self.name = name
        # canonical storage
        self.nodes = list(nodes) if nodes is not None else []
        # Provide .body alias for older code expecting `.body`
        self.body = self.nodes

    def __iter__(self):
        return iter(self.nodes)

    def __len__(self):
        return len(self.nodes)

    def __getitem__(self, idx):
        return self.nodes[idx]

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Optional[Dict[str, "Block"]] = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> Any:
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
    def __init__(
        self,
        items: Optional[List[Node]] = None,
        start: Optional[Tuple[int, int]] = None,
    ):
        super().__init__(start)
        self.items = items or []

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Optional[Dict[str, "Block"]] = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> List[Any]:
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
    def __init__(
        self,
        pairs: Optional[List[Tuple[str, Node]]] = None,
        start: Optional[Tuple[int, int]] = None,
    ):
        super().__init__(start)
        # pairs: list of (key, Node)
        self.pairs = pairs or []

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Optional[Dict[str, "Block"]] = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> Dict[str, Any]:
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


# Placeholder classes until they are implemented in typed_ast
class FunctionDef(Node):
    pass


class FunctionCall(Node):
    pass


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
    "FunctionDef",
    "FunctionCall",
]
