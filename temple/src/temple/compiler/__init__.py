"""
temple.compiler
Production-grade typed DSL compiler for Temple.

This package implements:
1. Parser (ast_nodes, parser.py) — item 34 ✅
2. Type system (types, schema, type_checker) — item 35 ✅
3. Diagnostics (diagnostics, source_map, error_formatter) — item 36 ✅
4. Serializers (serializers/) — item 37 ✅
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
    walk_ast,
)
from temple.compiler.parser import TypedTemplateParser
from temple.compiler.types import (
    BaseType,
    StringType,
    NumberType,
    BooleanType,
    NullType,
    ArrayType,
    ObjectType,
    TupleType,
    UnionType,
    ReferenceType,
    AnyType,
    optional,
    infer_type_from_value,
)
from temple.compiler.schema import (
    Schema,
    SchemaParser,
    SchemaBuilder,
    object_schema,
    array_schema,
)
from temple.compiler.type_checker import TypeChecker, TypeEnvironment
from temple.compiler.type_errors import TypeError, TypeErrorCollector
from temple.compiler.diagnostics import (
    Diagnostic,
    DiagnosticSeverity,
    DiagnosticCollector,
    SuppressionComment,
)
from temple.compiler.source_map import SourceMap, DiagnosticMapper, PositionTracker
from temple.compiler.error_formatter import ErrorFormatter, ContextRenderer
from temple.compiler.serializers import (
    Serializer,
    SerializationError,
    SerializationContext,
    JSONSerializer,
    MarkdownSerializer,
    HTMLSerializer,
    YAMLSerializer,
)

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
    # Utilities
    "walk_ast",
    # Parser
    "TypedTemplateParser",
    # Type System (Item 35)
    "BaseType",
    "StringType",
    "NumberType",
    "BooleanType",
    "NullType",
    "ArrayType",
    "ObjectType",
    "TupleType",
    "UnionType",
    "ReferenceType",
    "AnyType",
    "optional",
    "infer_type_from_value",
    # Schema
    "Schema",
    "SchemaParser",
    "SchemaBuilder",
    "object_schema",
    "array_schema",
    # Type Checker
    "TypeChecker",
    "TypeEnvironment",
    # Type Errors
    "TypeError",
    "TypeErrorCollector",
]
