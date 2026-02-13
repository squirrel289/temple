"""
linter.py
Core linting logic for templated files.

Integrates temple core parser for comprehensive syntax validation.
"""

from typing import Any

from temple.compiler.schema import Schema, SchemaParser
from temple.compiler.type_checker import TypeChecker
from temple.diagnostics import (
    Diagnostic,
    DiagnosticCollector,
    DiagnosticSeverity,
)
from temple.lark_parser import parse_with_diagnostics


class TemplateLinter:
    """
    Template linter with syntax validation using temple core parser.

    Validates template syntax and returns diagnostics for:
    - Unclosed blocks (if, for, etc.)
    - Malformed expressions
    - Invalid statements
    - Syntax errors
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.semantic_enabled = self.config.get("enable_semantic_validation", True)
        self.default_context = self.config.get("context")
        self.default_schema = self._coerce_schema(
            schema=self.config.get("schema"),
            schema_path=self.config.get("schema_path"),
        )

    def lint(
        self,
        text: str,
        node_collector: DiagnosticCollector | None = None,
        *,
        context: dict[str, Any] | None = None,
        schema: Schema | dict[str, Any] | None = None,
        schema_path: str | None = None,
    ) -> list[Diagnostic]:
        """
        Parse template and return syntax + semantic diagnostics.

        Args:
            text: Template content to validate
            context: Optional runtime context used for semantic checks
            schema: Optional schema object or JSON-schema dict
            schema_path: Optional schema file path

        Returns:
            List of Diagnostic objects with syntax and semantic findings

        Example:
            >>> linter = TemplateLinter()
            >>> diagnostics = linter.lint("{% if user.active %}{{ user.name }}")
            >>> len(diagnostics) > 0  # Missing {% end %}
            True
        """
        ast, syntax_diagnostics = parse_with_diagnostics(
            text, node_collector=node_collector
        )
        diagnostics = list(syntax_diagnostics)

        if not self.semantic_enabled:
            return diagnostics
        if self._has_syntax_errors(diagnostics):
            return diagnostics

        effective_schema = self._coerce_schema(
            schema=schema if schema is not None else self.default_schema,
            schema_path=schema_path,
        )
        effective_context = context if context is not None else self.default_context

        if effective_schema is None and effective_context is None:
            return diagnostics

        type_checker = TypeChecker(schema=effective_schema, data=effective_context)
        type_checker.check(ast)
        diagnostics.extend(self._to_semantic_diagnostics(type_checker))
        return diagnostics

    @staticmethod
    def _has_syntax_errors(diagnostics: list[Diagnostic]) -> bool:
        return any(diag.severity == DiagnosticSeverity.ERROR for diag in diagnostics)

    @staticmethod
    def _coerce_schema(
        schema: Schema | dict[str, Any] | None,
        schema_path: str | None = None,
    ) -> Schema | None:
        if isinstance(schema, Schema):
            return schema
        if isinstance(schema, dict):
            return SchemaParser.from_json_schema(schema)
        if schema_path:
            return SchemaParser.from_file(schema_path)
        return None

    @staticmethod
    def _to_semantic_diagnostics(type_checker: TypeChecker) -> list[Diagnostic]:
        semantic_diagnostics: list[Diagnostic] = []
        for err in type_checker.errors.errors:
            data = {}
            if err.expected_type is not None:
                data["expected_type"] = err.expected_type
            if err.actual_type is not None:
                data["actual_type"] = err.actual_type
            if err.suggestion is not None:
                data["suggestion"] = err.suggestion

            semantic_diagnostics.append(
                Diagnostic(
                    message=err.message,
                    source_range=err.source_range,
                    severity=DiagnosticSeverity.ERROR,
                    code=err.kind,
                    source="temple-type-checker",
                    data=data,
                )
            )
        return semantic_diagnostics


# CLI entry point for LSP server usage
if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Temple Linter CLI")
    parser.add_argument("--lint", action="store_true", help="Run linter")
    parser.add_argument("--input", type=str, help="Input text to lint")
    parser.add_argument(
        "--delegate-base-lint",
        action="store_true",
        help="Delegate base linting to caller",
    )
    parser.add_argument(
        "--filename", type=str, help="Filename for base format detection", default=None
    )
    args = parser.parse_args()

    if args.lint and args.input is not None:
        linter = TemplateLinter()
        template_diags = linter.lint(args.input)
        cleaned_text = args.input  # Replace with actual template stripping if needed
        if args.delegate_base_lint:
            # Emit base lint request
            print(
                json.dumps(
                    {
                        "template_diagnostics": template_diags,
                        "base_lint_request": {
                            "text": cleaned_text,
                            "filename": args.filename,
                        },
                    }
                )
            )
            # Read base diagnostics from stdin (as JSON)
            try:
                base_diags = json.loads(sys.stdin.read())
            except Exception:
                base_diags = []
            # Merge and output
            print(json.dumps(template_diags + base_diags))
            sys.exit(0)
        else:
            # Run base linting in-process (if implemented)
            print(json.dumps(template_diags))
            sys.exit(0)
    else:
        print(json.dumps([]))
        sys.exit(0)
