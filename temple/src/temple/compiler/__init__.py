"""
temple.compiler
Production-grade typed DSL compiler for Temple.

This package implements:
1. Parser (ast_nodes, parser.py)
2. Type system (type_checker.py) — item 35
3. Diagnostics (diagnostics.py) — item 36
4. Serializers (serializers/) — item 37
"""

from temple.compiler.ast_nodes import (
    Position,
    SourceRange,
    ASTNode,
    Text,
    Expression,
    If,
    For,
    Include,
    Block,
)
from temple.compiler.parser import TypedTemplateParser

__all__ = [
    # Position & Source Info
    "Position",
    "SourceRange",
    # AST Nodes
    "ASTNode",
    "Text",
    "Expression",
    "If",
    "For",
    "Include",
    "Block",
    # Parser
    "TypedTemplateParser",
]
