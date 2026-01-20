# temple_linter package
"""
Temple Linter - LSP-based linter for Temple DSL templates.

Provides comprehensive syntax validation, semantic type checking,
and advanced IDE features for Temple templates.
"""

# Re-export commonly used temple core types for convenience
try:
    from temple.compiler import (
        TypedTemplateParser,
        TypeChecker,
        Diagnostic,
        DiagnosticSeverity,
        Schema,
        SchemaParser,
    )
    from temple.compiler.ast_nodes import (
        Block,
        Expression,
        If,
        For,
        Include,
        Text,
    )

    __all__ = [
        "TypedTemplateParser",
        "TypeChecker",
        "Diagnostic",
        "DiagnosticSeverity",
        "Schema",
        "SchemaParser",
        "Block",
        "Expression",
        "If",
        "For",
        "Include",
        "Text",
    ]
except ImportError as e:
    import warnings

    warnings.warn(
        f"Could not import temple core: {e}. Please install temple: pip install temple",
        ImportWarning,
    )
    __all__ = []
