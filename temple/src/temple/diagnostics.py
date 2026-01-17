"""
temple.diagnostics
Parser-agnostic diagnostic types for error reporting.

Provides error, warning, and info diagnostics with source positions
and LSP format conversion. Used by both lark_parser and temple-linter.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum

from .range_utils import make_source_range


@dataclass
class Position:
    """Position in source text (0-indexed)."""

    line: int
    column: int

    # Backwards-compatible alias used in source_map and tests
    @property
    def col(self) -> int:
        return self.column

    def to_lsp(self) -> Dict[str, int]:
        """Convert to LSP Position format (0-indexed)."""
        return {"line": self.line, "character": self.column}

    def __str__(self) -> str:
        return f"{self.line + 1}:{self.column + 1}"  # Human-readable (1-indexed)


@dataclass
class SourceRange:
    """Range in source text."""

    start: Position
    end: Position

    def to_lsp(self) -> Dict[str, Dict[str, int]]:
        """Convert to LSP Range format."""
        return {"start": self.start.to_lsp(), "end": self.end.to_lsp()}

    def __str__(self) -> str:
        return f"{self.start}-{self.end}"


class DiagnosticSeverity(Enum):
    """Diagnostic severity levels matching LSP specification."""

    ERROR = 1
    WARNING = 2
    INFORMATION = 3
    HINT = 4


@dataclass
class DiagnosticTag:
    """Optional tags for diagnostics."""

    UNNECESSARY = 1
    DEPRECATED = 2


@dataclass
class DiagnosticRelatedInformation:
    """Related information for a diagnostic."""

    message: str
    location_uri: str
    location_range: SourceRange


@dataclass
class Diagnostic:
    """Represents a single diagnostic message (error, warning, etc.)."""

    message: str
    source_range: Optional[SourceRange] = None
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    code: Optional[str] = None
    source: str = "temple"
    related_information: List[DiagnosticRelatedInformation] = field(
        default_factory=list
    )
    tags: List[DiagnosticTag] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    # Backwards-compatible convenience fields: allow callers to pass `start`/`end` tuples
    start: Optional[Tuple[int, int]] = None
    end: Optional[Tuple[int, int]] = None

    def __post_init__(self):
        # Normalize and validate source_range/start/end into a canonical SourceRange.
        try:
            self.source_range = make_source_range(
                source_range=self.source_range, start=self.start, end=self.end
            )
        except Exception as e:
            # Fail fast: Diagnostics must have a valid source range.
            raise ValueError(
                f"Diagnostic missing or invalid source position: {e}. Provide `source_range` or `start`/`end` tuples."
            )

        # Canonical tuples for convenience
        self.start = (self.source_range.start.line, self.source_range.start.column)
        self.end = (self.source_range.end.line, self.source_range.end.column)

    def to_lsp(self) -> Dict[str, Any]:
        """Convert to LSP Diagnostic format.

        Returns:
            Dict with LSP diagnostic fields (range, message, severity, etc.)
        """
        diagnostic = {
            "range": self.source_range.to_lsp(),
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
        }

        if self.code:
            diagnostic["code"] = self.code

        if self.related_information:
            diagnostic["relatedInformation"] = [
                {
                    "message": ri.message,
                    "location": {
                        "uri": ri.location_uri,
                        "range": ri.location_range.to_lsp(),
                    },
                }
                for ri in self.related_information
            ]

        if self.tags:
            diagnostic["tags"] = [tag.value for tag in self.tags]

        if self.data:
            diagnostic["data"] = self.data

        return diagnostic

    def to_string(
        self, source_text: Optional[str] = None, include_context: bool = True
    ) -> str:
        """Format diagnostic as human-readable string.

        Args:
            source_text: Full source text for context extraction
            include_context: Whether to include source snippet

        Returns:
            Formatted diagnostic string
        """
        severity_str = {
            DiagnosticSeverity.ERROR: "error",
            DiagnosticSeverity.WARNING: "warning",
            DiagnosticSeverity.INFORMATION: "info",
            DiagnosticSeverity.HINT: "hint",
        }[self.severity]

        code_str = f"[{self.code}] " if self.code else ""
        result = f"{severity_str}: {code_str}{self.message} at {self.source_range}"

        if include_context and source_text:
            lines = source_text.split("\n")
            start_line = self.source_range.start.line
            if 0 <= start_line < len(lines):
                line_content = lines[start_line]
                result += f"\n  {start_line + 1} | {line_content}"
                # Add caret indicator
                col = self.source_range.start.column
                result += f"\n    | {' ' * col}^"

        return result


class DiagnosticCollector:
    """Collects diagnostics during parsing/analysis."""

    def __init__(self):
        self.diagnostics: List[Diagnostic] = []

    def add(self, diagnostic: Diagnostic):
        """Add a diagnostic."""
        self.diagnostics.append(diagnostic)

    def add_error(
        self, message: str, source_range: SourceRange, code: Optional[str] = None
    ):
        """Add an error diagnostic."""
        self.add(
            Diagnostic(
                message=message,
                source_range=source_range,
                severity=DiagnosticSeverity.ERROR,
                code=code,
            )
        )

    def add_warning(
        self, message: str, source_range: SourceRange, code: Optional[str] = None
    ):
        """Add a warning diagnostic."""
        self.add(
            Diagnostic(
                message=message,
                source_range=source_range,
                severity=DiagnosticSeverity.WARNING,
                code=code,
            )
        )

    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return any(d.severity == DiagnosticSeverity.ERROR for d in self.diagnostics)

    def clear(self):
        """Clear all diagnostics."""
        self.diagnostics.clear()


__all__ = [
    "Position",
    "SourceRange",
    "Diagnostic",
    "DiagnosticSeverity",
    "DiagnosticTag",
    "DiagnosticRelatedInformation",
    "DiagnosticCollector",
]
