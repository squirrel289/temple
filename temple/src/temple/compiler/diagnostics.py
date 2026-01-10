"""
temple.compiler.diagnostics
Diagnostic types and collection system.

Provides error, warning, and info diagnostics with source positions
and LSP format conversion.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from .ast_nodes import SourceRange, Position


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
    source_range: SourceRange
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    code: Optional[str] = None
    source: str = "temple-compiler"
    related_information: List[DiagnosticRelatedInformation] = field(default_factory=list)
    tags: List[DiagnosticTag] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    
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
                        "range": ri.location_range.to_lsp()
                    }
                }
                for ri in self.related_information
            ]
        
        if self.tags:
            diagnostic["tags"] = [tag.value for tag in self.tags]
        
        if self.data:
            diagnostic["data"] = self.data
        
        return diagnostic
    
    def to_string(self, source_text: Optional[str] = None, include_context: bool = True) -> str:
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
        
        lines = []
        
        # Header: [source] severity: message at line:col
        header = f"[{self.source}] {severity_str}: {self.message}"
        lines.append(header)
        
        # Location
        lines.append(f"  at line {self.source_range.start.line + 1}, column {self.source_range.start.col + 1}")
        
        # Source context if available
        if include_context and source_text:
            context = self._extract_context(source_text)
            if context:
                lines.append("")
                lines.extend(context)
        
        # Code reference
        if self.code:
            lines.append(f"  code: {self.code}")
        
        # Related information
        if self.related_information:
            lines.append("")
            lines.append("  Related:")
            for ri in self.related_information:
                lines.append(f"    - {ri.message}")
        
        return "\n".join(lines)
    
    def _extract_context(self, source_text: str, context_lines: int = 2) -> List[str]:
        """Extract source context around error location.
        
        Args:
            source_text: Full source text
            context_lines: Number of lines before/after to include
        
        Returns:
            Formatted context lines with pointer
        """
        text_lines = source_text.split('\n')
        error_line = self.source_range.start.line
        
        # Clamp to valid range
        start_line = max(0, error_line - context_lines)
        end_line = min(len(text_lines), error_line + context_lines + 1)
        
        context = []
        for i in range(start_line, end_line):
            line_num = i + 1
            prefix = "→ " if i == error_line else "  "
            
            # Add line with number
            if i < len(text_lines):
                context.append(f"{prefix}{line_num:4d} | {text_lines[i]}")
                
                # Add pointer for error line
                if i == error_line:
                    pointer_line = " " * 8 + " " * self.source_range.start.col + "^"
                    if self.source_range.end.line == error_line:
                        width = max(1, self.source_range.end.col - self.source_range.start.col)
                        if width > 1:
                            pointer_line += "~" * (width - 1)
                    context.append(pointer_line)
        
        return context


@dataclass
class SuppressionComment:
    """Represents a suppression comment in the template.
    
    Format: {# @suppress ERROR_CODE [, ERROR_CODE2, ...] #}
    """
    suppressed_codes: List[str]
    source_range: SourceRange
    
    def suppresses(self, code: Optional[str]) -> bool:
        """Check if this suppression applies to the given error code.
        
        Args:
            code: Error code to check
        
        Returns:
            True if code is in suppressed_codes or if suppressing all codes
        """
        if not code:
            return False
        return code in self.suppressed_codes or "*" in self.suppressed_codes


class DiagnosticCollector:
    """Collects diagnostics from parsing, type checking, and validation phases."""
    
    def __init__(self):
        self.diagnostics: List[Diagnostic] = []
        self.suppressions: List[SuppressionComment] = []
    
    def add(
        self,
        message: str,
        source_range: SourceRange,
        severity: DiagnosticSeverity = DiagnosticSeverity.ERROR,
        code: Optional[str] = None,
        source: str = "temple-compiler",
        related_information: Optional[List[DiagnosticRelatedInformation]] = None,
    ) -> Diagnostic:
        """Add a diagnostic.
        
        Args:
            message: Error message
            source_range: Source position
            severity: Diagnostic severity
            code: Error code for categorization
            source: Source of diagnostic
            related_information: Related info
        
        Returns:
            Created Diagnostic
        """
        diagnostic = Diagnostic(
            message=message,
            source_range=source_range,
            severity=severity,
            code=code,
            source=source,
            related_information=related_information or []
        )
        self.diagnostics.append(diagnostic)
        return diagnostic
    
    def add_error(
        self,
        message: str,
        source_range: SourceRange,
        code: Optional[str] = None
    ) -> Diagnostic:
        """Add an error diagnostic."""
        return self.add(message, source_range, DiagnosticSeverity.ERROR, code)
    
    def add_warning(
        self,
        message: str,
        source_range: SourceRange,
        code: Optional[str] = None
    ) -> Diagnostic:
        """Add a warning diagnostic."""
        return self.add(message, source_range, DiagnosticSeverity.WARNING, code)
    
    def add_info(
        self,
        message: str,
        source_range: SourceRange,
        code: Optional[str] = None
    ) -> Diagnostic:
        """Add an info diagnostic."""
        return self.add(message, source_range, DiagnosticSeverity.INFORMATION, code)
    
    def add_hint(
        self,
        message: str,
        source_range: SourceRange,
        code: Optional[str] = None
    ) -> Diagnostic:
        """Add a hint diagnostic."""
        return self.add(message, source_range, DiagnosticSeverity.HINT, code)
    
    def add_suppression(self, suppression: SuppressionComment):
        """Register a suppression comment."""
        self.suppressions.append(suppression)
    
    def parse_suppression(self, comment_text: str, source_range: SourceRange) -> Optional[SuppressionComment]:
        """Parse a suppression comment.
        
        Format: @suppress CODE1[, CODE2, ...]
        
        Args:
            comment_text: Comment text (without delimiters)
            source_range: Source position of comment
        
        Returns:
            SuppressionComment or None if not a suppression
        """
        text = comment_text.strip()
        if not text.startswith("@suppress"):
            return None
        
        # Extract codes
        codes_text = text.replace("@suppress", "", 1).strip()
        codes = [code.strip() for code in codes_text.split(",") if code.strip()]
        
        if not codes:
            return None
        
        suppression = SuppressionComment(
            suppressed_codes=codes,
            source_range=source_range
        )
        self.add_suppression(suppression)
        return suppression
    
    def get_filtered_diagnostics(self) -> List[Diagnostic]:
        """Get diagnostics after applying suppressions.
        
        Returns:
            List of diagnostics not suppressed
        """
        filtered = []
        for diagnostic in self.diagnostics:
            if self._is_suppressed(diagnostic):
                continue
            filtered.append(diagnostic)
        return filtered
    
    def _is_suppressed(self, diagnostic: Diagnostic) -> bool:
        """Check if a diagnostic is suppressed.
        
        Suppression applies if there's a suppression comment before the diagnostic
        on the same line or within the block.
        """
        for suppression in self.suppressions:
            # Simple heuristic: suppression on same line or line before
            if (suppression.source_range.start.line >= diagnostic.source_range.start.line - 1 and
                suppression.source_range.start.line <= diagnostic.source_range.start.line):
                if suppression.suppresses(diagnostic.code):
                    return True
        return False
    
    def has_errors(self) -> bool:
        """Check if there are any errors (after filtering suppressions)."""
        return any(
            d.severity == DiagnosticSeverity.ERROR
            for d in self.get_filtered_diagnostics()
        )
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings (after filtering suppressions)."""
        return any(
            d.severity == DiagnosticSeverity.WARNING
            for d in self.get_filtered_diagnostics()
        )
    
    def error_count(self) -> int:
        """Count errors (after filtering suppressions)."""
        return sum(
            1 for d in self.get_filtered_diagnostics()
            if d.severity == DiagnosticSeverity.ERROR
        )
    
    def warning_count(self) -> int:
        """Count warnings (after filtering suppressions)."""
        return sum(
            1 for d in self.get_filtered_diagnostics()
            if d.severity == DiagnosticSeverity.WARNING
        )
    
    def to_lsp(self) -> List[Dict[str, Any]]:
        """Convert all diagnostics to LSP format."""
        return [d.to_lsp() for d in self.get_filtered_diagnostics()]
    
    def format_all(self, source_text: Optional[str] = None) -> str:
        """Format all diagnostics as a report.
        
        Args:
            source_text: Source for context extraction
        
        Returns:
            Formatted report string
        """
        filtered = self.get_filtered_diagnostics()
        
        if not filtered:
            return "No diagnostics"
        
        lines = [f"Found {len(filtered)} diagnostic(s):\n"]
        
        for i, diagnostic in enumerate(filtered, 1):
            lines.append(f"{i}. {diagnostic.to_string(source_text)}")
            lines.append("")
        
        # Summary
        errors = sum(1 for d in filtered if d.severity == DiagnosticSeverity.ERROR)
        warnings = sum(1 for d in filtered if d.severity == DiagnosticSeverity.WARNING)
        
        summary_parts = []
        if errors:
            summary_parts.append(f"{errors} error{'s' if errors != 1 else ''}")
        if warnings:
            summary_parts.append(f"{warnings} warning{'s' if warnings != 1 else ''}")
        
        if summary_parts:
            lines.append(f"Summary: {', '.join(summary_parts)}")
        
        return "\n".join(lines)
