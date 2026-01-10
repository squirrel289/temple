"""
temple.compiler.ast_nodes
AST node definitions with source position tracking.

All AST nodes carry position information (line, column) for error reporting and diagnostics.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Tuple, Any


@dataclass(frozen=True)
class Position:
    """Source position: (line, column), both 0-indexed."""
    line: int
    col: int

    def __repr__(self) -> str:
        return f"({self.line}, {self.col})"

    def __str__(self) -> str:
        return f"Line {self.line + 1}, Column {self.col + 1}"

    def to_lsp(self) -> dict:
        """Convert to LSP position (0-indexed, same as Position)."""
        return {"line": self.line, "character": self.col}


@dataclass(frozen=True)
class SourceRange:
    """Range in source: start to end position."""
    start: Position
    end: Position

    def __repr__(self) -> str:
        return f"{self.start}-{self.end}"

    def __str__(self) -> str:
        if self.start.line == self.end.line:
            return f"Line {self.start.line + 1}, Columns {self.start.col + 1}-{self.end.col + 1}"
        return f"Lines {self.start.line + 1}-{self.end.line + 1}"

    def to_lsp(self) -> dict:
        """Convert to LSP range."""
        return {
            "start": self.start.to_lsp(),
            "end": self.end.to_lsp(),
        }


class ASTNode(ABC):
    """Base class for all AST nodes. All nodes carry source position information."""

    def __init__(self, source_range: SourceRange):
        self.source_range = source_range

    @property
    def start(self) -> Position:
        return self.source_range.start

    @property
    def end(self) -> Position:
        return self.source_range.end

    @abstractmethod
    def __repr__(self) -> str:
        pass


@dataclass
class Text(ASTNode):
    """Raw text content (not processed by DSL)."""
    value: str
    source_range: SourceRange

    def __init__(self, value: str, source_range: SourceRange):
        super().__init__(source_range)
        self.value = value

    def __repr__(self) -> str:
        # Show first 50 chars, escape newlines
        escaped = self.value[:50].replace("\n", "\\n")
        ellipsis = "..." if len(self.value) > 50 else ""
        return f"Text({escaped!r}{ellipsis}, {self.source_range})"


@dataclass
class Expression(ASTNode):
    """Variable insertion: {{ expression }}"""
    value: str  # Expression content (stripped of delimiters)
    source_range: SourceRange

    def __init__(self, value: str, source_range: SourceRange):
        super().__init__(source_range)
        self.value = value

    def __repr__(self) -> str:
        return f"Expression({self.value!r}, {self.source_range})"


@dataclass
class If(ASTNode):
    """Conditional block: {% if condition %} ... {% endif %}"""
    condition: str  # Expression to evaluate
    body: List[ASTNode]  # Nodes inside if block
    elif_parts: List[Tuple[str, List[ASTNode]]] = None  # [(condition, body), ...]
    else_body: Optional[List[ASTNode]] = None
    source_range: SourceRange = None

    def __init__(
        self,
        condition: str,
        body: List[ASTNode],
        source_range: SourceRange,
        elif_parts: Optional[List[Tuple[str, List[ASTNode]]]] = None,
        else_body: Optional[List[ASTNode]] = None,
    ):
        super().__init__(source_range)
        self.condition = condition
        self.body = body
        self.elif_parts = elif_parts or []
        self.else_body = else_body

    def __repr__(self) -> str:
        parts = f"if {self.condition!r}: {len(self.body)} nodes"
        if self.elif_parts:
            parts += f", {len(self.elif_parts)} elif"
        if self.else_body:
            parts += f", else: {len(self.else_body)} nodes"
        return f"If({parts}, {self.source_range})"


@dataclass
class For(ASTNode):
    """Loop block: {% for item in collection %} ... {% endfor %}"""
    var: str  # Loop variable name
    iterable: str  # Expression to iterate over
    body: List[ASTNode]
    source_range: SourceRange = None

    def __init__(self, var: str, iterable: str, body: List[ASTNode], source_range: SourceRange):
        super().__init__(source_range)
        self.var = var
        self.iterable = iterable
        self.body = body

    def __repr__(self) -> str:
        return f"For({self.var!r} in {self.iterable!r}: {len(self.body)} nodes, {self.source_range})"


@dataclass
class Include(ASTNode):
    """Include directive: {% include "filename" %}"""
    path: str  # File path to include
    source_range: SourceRange = None

    def __init__(self, path: str, source_range: SourceRange):
        super().__init__(source_range)
        self.path = path

    def __repr__(self) -> str:
        return f"Include({self.path!r}, {self.source_range})"


@dataclass
class Block(ASTNode):
    """Generic block: {% block name %} ... {% endblock %}"""
    name: str  # Block name
    body: List[ASTNode]
    source_range: SourceRange = None

    def __init__(self, name: str, body: List[ASTNode], source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.body = body

    def __repr__(self) -> str:
        return f"Block({self.name!r}: {len(self.body)} nodes, {self.source_range})"


# Additional nodes for future use

@dataclass
class FunctionDef(ASTNode):
    """Function definition: {% function name(args) %} ... {% endfunction %}"""
    name: str
    args: List[str]  # Parameter names
    body: List[ASTNode]
    source_range: SourceRange = None

    def __init__(self, name: str, args: List[str], body: List[ASTNode], source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.args = args
        self.body = body

    def __repr__(self) -> str:
        return f"FunctionDef({self.name!r}({', '.join(self.args)}): {len(self.body)} nodes, {self.source_range})"


@dataclass
class FunctionCall(ASTNode):
    """Function call within template: {{ func_name(args) }}"""
    name: str
    args: List[str]  # Argument expressions
    source_range: SourceRange = None

    def __init__(self, name: str, args: List[str], source_range: SourceRange):
        super().__init__(source_range)
        self.name = name
        self.args = args

    def __repr__(self) -> str:
        return f"FunctionCall({self.name!r}({len(self.args)} args), {self.source_range})"


# Utility function for working with AST

def walk_ast(node: ASTNode) -> List[ASTNode]:
    """Depth-first walk of AST tree. Yields all nodes including container's children."""
    result = [node]
    
    if isinstance(node, (If, For, Block, FunctionDef)):
        # Walk container's body
        for child in node.body:
            result.extend(walk_ast(child))
        
        # Walk If's elif and else parts
        if isinstance(node, If):
            for _, elif_body in node.elif_parts:
                for child in elif_body:
                    result.extend(walk_ast(child))
            if node.else_body:
                for child in node.else_body:
                    result.extend(walk_ast(child))
    
    return result
