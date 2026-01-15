from typing import Any, Dict, List, Optional, Tuple
from temple.diagnostics import Position, SourceRange


class TemplateError(Exception):
    pass


class Node:
    def __init__(self, start: Optional[object] = None):
        # `start` may be a (line, col) tuple or a SourceRange
        self.start = None
        self.source_range = None
        if start is not None:
            # If a SourceRange is provided, prefer that
            try:
                if isinstance(start, SourceRange):
                    self.source_range = start
                    self.start = (start.start.line, start.start.col)
                else:
                    # Assume a (line, col) tuple
                    line, col = start
                    self.start = (line, col)
                    self.source_range = SourceRange(
                        Position(line, col), Position(line, col)
                    )
            except Exception:
                # Fallback: try to coerce to tuple
                try:
                    line, col = tuple(start)
                    self.start = (line, col)
                    self.source_range = SourceRange(
                        Position(line, col), Position(line, col)
                    )
                except Exception:
                    self.start = None
                    self.source_range = None

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Dict[str, "Block"] | None = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> Any:
        raise NotImplementedError()


class Text(Node):
    def __init__(self, text: str, start: Optional[Tuple[int, int]] = None):
        super().__init__(start)
        self.text = text
        # Backwards-compatible alias
        self.value = text

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Dict[str, "Block"] | None = None,
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
        value: Optional[str] = None,
        **kwargs,
    ):
        # Accept both `expr` and legacy `value` kwarg, and optional `source_range` for compatibility
        expr_val = expr if expr is not None else value
        super().__init__(start)
        self.expr = expr_val
        # Backwards-compatible alias
        self.value = expr_val
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
        includes: Dict[str, "Block"] | None = None,
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
            self.body_block = body
        else:
            nodes = body if body is not None else []
            self.body = Block(nodes, start)
            self.body_block = self.body
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
        normalized = []
        self.else_if_blocks = []
        for c, b in parts:
            if isinstance(b, Block):
                normalized.append((c, b))
                self.else_if_blocks.append((c, b))
            else:
                bnodes = b if b is not None else []
                blk = Block(bnodes, start)
                normalized.append((c, blk))
                self.else_if_blocks.append((c, blk))
        self.else_if_parts = normalized
        # Backwards-compatible alias expected by older code/tests
        self.elif_parts = self.else_if_parts
        # Normalize else_body to Block or None
        if isinstance(else_body, Block):
            self.else_body = else_body
            self.else_body_block = else_body
        elif else_body is None:
            self.else_body = None
            self.else_body_block = None
        else:
            bn = else_body if isinstance(else_body, list) else [else_body]
            self.else_body = Block(bn, start)
            self.else_body_block = self.else_body

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Dict[str, "Block"] | None = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> Any:
        cond_val = Expression(self.condition).evaluate(
            context, includes, path + "/cond", mapping
        )
        if cond_val:
            return self.body_block.evaluate(context, includes, path + "/body", mapping)
        # Check else-if branches
        for idx, (else_if_cond, else_if_body_nodes) in enumerate(self.else_if_parts):
            elif_val = Expression(else_if_cond).evaluate(
                context, includes, path + f"/else_if[{idx}]/cond", mapping
            )
            if elif_val:
                return self.else_if_blocks[idx][1].evaluate(
                    context, includes, path + f"/else_if[{idx}]/body", mapping
                )
        # Check else branch
        if self.else_body:
            return self.else_body_block.evaluate(
                context, includes, path + "/else", mapping
            )
        return None


class For(Node):
    def __init__(
        self,
        var: str = None,
        iterable: str = None,
        body: "Block" = None,
        start: Optional[Tuple[int, int]] = None,
    ):
        super().__init__(start)
        # Accept keyword args used in tests: var, iterable
        self.var = var
        self.var_name = var
        self.iterable = iterable
        self.iterable_expr = iterable
        # Body may be a Block or a list of nodes; normalize to Block
        if isinstance(body, Block):
            self.body = body
            self.body_block = body
        else:
            nodes = body if body is not None else []
            self.body = Block(nodes, start)
            self.body_block = self.body

    def evaluate(
        self,
        context: Dict[str, Any],
        includes: Dict[str, "Block"] | None = None,
        path: str = "",
        mapping: Optional[List[Tuple[str, Tuple[int, int]]]] = None,
    ) -> List[Any]:
        iterable = Expression(self.iterable_expr).evaluate(
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
            local_ctx[self.var_name] = item
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
            val = self.body_block.evaluate(
                local_ctx, includes, path + f"/for[{self.var_name}][{idx}]", mapping
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
        includes: Dict[str, "Block"] | None = None,
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
        includes: Dict[str, "Block"] | None = None,
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
        includes: Dict[str, "Block"] | None = None,
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
        includes: Dict[str, "Block"] | None = None,
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
