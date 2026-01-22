"""Lark-based parser for Temple templates.

This module provides a Transformer (`ToTypedAST`) that converts the
parse tree produced by `typed_grammar.lark` into typed AST nodes defined in
`temple.typed_ast`.

Grammar Strategy:
- Literal keywords ("if", "for", "include", "set") in rules for clean semantics
- Compound terminals (END_TAG, ELSE_TAG, ELSE_IF_TAG) for closers to avoid LALR ambiguity
- Token class inherits from str, so always check isinstance(Token) before isinstance(str)
"""

# ============================================================================
# Public API (matches production lark_parser.py)
# ============================================================================
from typing import overload, Literal, Any, List, Optional, Sequence, Tuple
import os

import re
from lark import (
    Lark,
    UnexpectedToken,
    UnexpectedCharacters,
    UnexpectedInput,
    Tree,
    Transformer,
    Token,
)

from temple.diagnostics import (
    Diagnostic,
    DiagnosticCollector,
    SourceRange,
    Position,
)

from temple.typed_ast import (
    Block,
    Expression,
    For,
    If,
    Include,
    Text,
)


def _token_range(tk: Token) -> SourceRange:
    """Extract SourceRange from a Lark Token."""
    start = Position(tk.line - 1, tk.column - 1)
    end = Position(tk.end_line - 1, tk.end_column - 1)
    return SourceRange(start, end)


def _make_empty_range() -> SourceRange:
    """Create empty SourceRange for fallback."""
    return SourceRange(Position(0, 0), Position(0, 0))


def _validate_expression_syntax(expr: str) -> Tuple[bool, str]:
    """Validate expression syntax (dot notation, identifiers).

    Returns:
        (is_valid, error_message)
    """
    if not expr or expr.isspace():
        return True, ""  # Empty expressions are allowed

    # Check for trailing dot
    if expr.endswith("."):
        return False, "Expression ends with trailing dot"

    # Check for leading dot
    if expr.startswith("."):
        return False, "Expression starts with leading dot"

    # Check for consecutive dots
    if ".." in expr:
        return False, "Expression contains consecutive dots"

    # Check for mismatched parentheses
    if expr.count("(") != expr.count(")"):
        return False, "Mismatched parentheses"

    return True, ""


GRAMMAR_PATH = os.path.join(os.path.dirname(__file__), "typed_grammar.lark")


def get_parser() -> Lark:
    """Load and return Lark parser for Temple grammar."""
    with open(GRAMMAR_PATH, "r") as f:
        grammar = f.read()
    return Lark(grammar, start="start", parser="lalr")


@overload
def parse_template(
    text: str,
    node_collector: Optional[DiagnosticCollector] = None,
) -> Block: ...


@overload
def parse_template(
    text: str,
    node_collector: Optional[DiagnosticCollector] = None,
    *,
    include_raw: Literal[True],
) -> Tuple[Block, Tree]: ...


def parse_template(
    text: str,
    node_collector: Optional[DiagnosticCollector] = None,
    include_raw: bool = False,
) -> Block | Tuple[Block, Tree]:
    """Parse template text and return AST.

    Args:
        text: Template source text
        node_collector: Optional collector for node-attached diagnostics
        include_raw: If True, return tuple of (AST, raw Lark tree)

    Returns:
        Parsed Block AST, or (Block, Tree) if include_raw=True

    Raises:
        UnexpectedInput: On syntax errors (use parse_with_diagnostics for error collection)
    """
    parser = get_parser()
    tree = parser.parse(text)
    transformer = _LarkToTypedASTTransformer(node_collector)
    if not include_raw:
        return transformer.transform(tree)
    return (transformer.transform(tree), tree)


def parse_with_diagnostics(
    text: str, node_collector: Optional[DiagnosticCollector] = None
) -> Tuple[Block, Tuple[Diagnostic, ...]]:
    """Parse template text and collect diagnostics.

    Args:
        text: Template source text
        node_collector: Optional collector for both global and node-attached diagnostics

    Returns:
        Tuple of (AST, diagnostics list). AST may be partial if errors occurred.

    Example:
        >>> ast, diagnostics = parse_with_diagnostics("{% if x %}{{ user.name }}")
        >>> len(diagnostics) > 0  # Missing {% end %}
        True
    """
    collector = node_collector or DiagnosticCollector()
    ast = None

    # First, scan for expression syntax errors directly from text
    expr_pattern = r"\{\{(.*?)\}\}"
    for match in re.finditer(expr_pattern, text, re.DOTALL):
        expr_text = match.group(1).strip()
        is_valid, error_msg = _validate_expression_syntax(expr_text)
        if not is_valid:
            # Calculate position
            start_offset = match.start()
            lines_before = text[:start_offset].count("\n")
            line_start = text.rfind("\n", 0, start_offset) + 1
            col = start_offset - line_start

            collector.add_error(
                f"Invalid expression syntax: {error_msg}",
                SourceRange(
                    Position(lines_before, col),
                    Position(lines_before, col + len(match.group())),
                ),
                code="INVALID_EXPRESSION",
            )

    try:
        ast = parse_template(text, node_collector=collector)
        return ast, collector.diagnostics
    except UnexpectedToken as e:
        # Extract position from Lark exception
        line = e.line - 1  # Lark uses 1-indexed, convert to 0-indexed
        column = e.column - 1 if e.column else 0

        # Build helpful error message
        expected = (
            ", ".join(getattr(e, "expected", []))
            if getattr(e, "expected", None)
            else "valid token"
        )
        token_repr = getattr(e, "token", None)
        token_str = str(token_repr) if token_repr is not None else str(e)
        message = f"Unexpected token '{token_str}'. Expected {expected}"

        source_range = SourceRange(
            Position(line, column), Position(line, column + len(token_str))
        )

        collector.add_error(message, source_range, code="UNEXPECTED_TOKEN")

        # Return partial AST (empty block)
        return Block([]), collector.diagnostics

    except UnexpectedCharacters as e:
        line = e.line - 1
        column = e.column - 1 if e.column else 0

        message = f"Unexpected character at position {line + 1}:{column + 1}"
        if e.allowed:
            message += f". Expected one of: {', '.join(e.allowed)}"

        source_range = SourceRange(Position(line, column), Position(line, column + 1))

        collector.add_error(message, source_range, code="UNEXPECTED_CHARACTER")
        return Block([]), collector.diagnostics

    except UnexpectedInput as e:
        # Generic parse error
        line = getattr(e, "line", 1) - 1
        column = getattr(e, "column", 1) - 1

        message = f"Syntax error: {str(e)}"
        source_range = SourceRange(Position(line, column), Position(line, column + 1))

        collector.add_error(message, source_range, code="SYNTAX_ERROR")
        return Block([]), collector.diagnostics

    except Exception as e:
        # Catch-all for unexpected errors
        message = f"Parser error: {str(e)}"
        source_range = SourceRange(Position(0, 0), Position(0, 0))
        collector.add_error(message, source_range, code="PARSER_ERROR")
        return Block([]), collector.diagnostics


class _LarkToTypedASTTransformer(Transformer[Block]):
    """Internal transformer: Lark parse tree → Typed AST.

    Handles:
    - text and expression nodes
    - if_stmt with else_if_chain and else_clause
    - for_stmt with loop iteration
    - include_stmt and set_stmt (inline)
    - block wrapping
    """

    def __init__(self, node_collector: Optional[DiagnosticCollector] = None):
        super().__init__()
        self.node_collector = node_collector

    # Terminal handlers
    def TEXT(self, tk: Token):
        return Text(_token_range(tk), str(tk))

    # text: TEXT
    def text(self, items: Sequence[Any]):
        for it in items:
            if isinstance(it, Token):
                return Text(_token_range(it), str(it))
            elif isinstance(it, Text):
                return it
        return Text(_make_empty_range(), "")

    # Helper to extract content strings
    def _extract_str(self, items: Sequence[Any]) -> str:
        """Extract string content from items (either Token or str)."""
        for it in items:
            if isinstance(it, str):
                return it.strip()
        return ""

    # Content extraction rules
    def condition(self, items: Sequence[Any]) -> str:
        return self._extract_str(items)

    def loop_args(self, items: Sequence[Any]) -> str:
        return self._extract_str(items)

    def include_args(self, items: Sequence[Any]) -> str:
        return self._extract_str(items)

    def set_args(self, items: Sequence[Any]) -> str:
        return self._extract_str(items)

    def expr_content(self, items: Sequence[Any]) -> str:
        return self._extract_str(items)

    # expression: EXPR_OPEN expr_content EXPR_CLOSE
    def expression(self, items: Sequence[Any]):
        content = ""
        src = _make_empty_range()

        for it in items:
            if isinstance(it, str):
                content = it
            elif isinstance(it, Token) and getattr(it, "type", "") == "EXPR_CONTENT":
                content = str(it).strip()
                src = _token_range(it)

        is_valid, msg = _validate_expression_syntax(content)
        expr_node = Expression(src, content)

        if not is_valid and self.node_collector is not None:
            self.node_collector.add_error(f"Expression syntax: {msg}", src)

        return expr_node

    # if_stmt: STMT_OPEN "if" condition STMT_CLOSE block else_if_chain? else_clause? END_TAG
    def if_stmt(self, items: Sequence[Any]):
        cond = ""
        body: Optional[Block] = None
        else_if_parts: List[Tuple[str, Block]] = []
        else_body: Optional[Block] = None
        src = _make_empty_range()

        # Extract components - Tokens inherit from str, so check Token first!
        for it in items:
            if isinstance(it, str):
                if not cond:
                    cond = it
            elif isinstance(it, Block):
                if body is None:
                    body = it
                else:
                    else_body = it
            elif isinstance(it, list):
                # else_if_chain returns list
                else_if_parts = it

        # Try to get source range from first token
        for it in items:
            if isinstance(it, Token):
                src = _token_range(it)
                break

        # print(f"DEBUG if_stmt returning: cond={cond!r}, body={body}, else_if_parts={else_if_parts}, else_body={else_body}")
        return If(
            src,
            cond,
            body or Block([]),
            else_if_parts=else_if_parts,
            else_body=else_body,
        )

    # else_if_chain: (ELSE_IF_TAG block)+
    def else_if_chain(self, items: Sequence[Any]):
        """Parse else-if chain from compound ELSE_IF_TAG terminals.

        ELSE_IF_TAG captures the entire {% else if CONDITION %} tag.
        Extract condition using same logic as main condition rule would use.
        """
        parts: List[Tuple[str, Block]] = []

        # Items alternate: ELSE_IF_TAG, block, ELSE_IF_TAG, block, ...
        i = 0
        while i < len(items):
            cond = ""
            body = Block([])

            # Look for ELSE_IF_TAG token and extract condition
            if (
                i < len(items)
                and isinstance(items[i], Token)
                and getattr(items[i], "type", "") == "ELSE_IF_TAG"
            ):
                # Extract condition from '{% else if CONDITION %}'
                # This extraction logic should match how 'condition' rule works
                tag_text = str(items[i])
                m = re.match(r"\{%\s*else\s+if\s+(.+?)\s*%\}", tag_text)
                cond = m.group(1).strip() if m else ""

            if i + 1 < len(items) and isinstance(items[i + 1], Block):
                body = items[i + 1]

            parts.append((cond, body))
            i += 2

        return parts

    # else_clause: ELSE_TAG block
    def else_clause(self, items: Sequence[Any]):
        """Return the else block."""
        for it in items:
            if isinstance(it, Block):
                return it
        return Block([])

    # for_stmt: STMT_OPEN "for" loop_args STMT_CLOSE block END_TAG
    def for_stmt(self, items: Sequence[Any]):
        loop_args_str = ""
        body: Optional[Block] = None
        src = _make_empty_range()

        for it in items:
            if isinstance(it, Token):
                src = _token_range(it)
            elif isinstance(it, str) and not loop_args_str:
                loop_args_str = it
            elif isinstance(it, Block) and body is None:
                body = it

        # Parse 'var in iterable'
        var = ""
        iterable = ""
        if loop_args_str:
            m = re.match(r"(\w+)\s+in\s+(\S+)", loop_args_str)
            if m:
                var = m.group(1)
                iterable = m.group(2)

        return For(src, var, iterable, body or Block([]))

    # include_stmt: STMT_OPEN "include" include_args STMT_CLOSE
    def include_stmt(self, items: Sequence[Any]):
        args = self._extract_str(items)
        src = _make_empty_range()

        for it in items:
            if isinstance(it, Token):
                src = _token_range(it)
                break

        # Strip surrounding quotes if present
        name = re.sub(r"^\s*[\'\"]|[\'\"]\s*$", "", args)
        return Include(src, name)

    # set_stmt: STMT_OPEN "set" set_args STMT_CLOSE
    def set_stmt(self, items: Sequence[Any]):
        """Placeholder for set statement (not in typed_ast yet)."""
        # Return None or a placeholder node
        return None

    # inline_stmt: STMT_OPEN (include_stmt | set_stmt) STMT_CLOSE
    def inline_stmt(self, items: Sequence[Any]):
        """Pass through include or set statement."""
        for it in items:
            if isinstance(it, Token):
                continue
            # Return the nested statement (Include or None)
            if it is not None:
                return it
        return None

    # block: (text | expression | if_stmt | for_stmt | include_stmt | set_stmt)*
    def block(self, items: Sequence[Any]) -> Block:
        """Wrap items in Block, filtering out None values."""
        flattened: List[Any] = []

        for it in items:
            # Skip None (from set_stmt or Tree objects)
            if it is None or hasattr(it, "data"):
                continue
            if isinstance(it, list):
                flattened.extend(it)
            else:
                flattened.append(it)

        return Block(flattened) if flattened else Block([])

    # start: block
    def start(self, items: Sequence[Any]) -> Block:
        """Top-level rule wraps into Block."""
        for it in items:
            if isinstance(it, Block):
                return it
        return Block([])


__all__ = [
    "parse_template",
    "parse_with_diagnostics",
    "get_parser",
]
