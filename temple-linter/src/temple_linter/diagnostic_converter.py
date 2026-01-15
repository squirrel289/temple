"""
diagnostic_converter.py
Convert temple core diagnostics to LSP format.
"""

from typing import Optional
from temple.diagnostics import Diagnostic, DiagnosticSeverity, SourceRange
from lsprotocol.types import (
    Diagnostic as LspDiagnostic,
    DiagnosticSeverity as LspSeverity,
    Position,
    Range,
)


def temple_to_lsp_diagnostic(diag: Diagnostic) -> LspDiagnostic:
    """
    Convert temple Diagnostic to LSP Diagnostic.
    
    Args:
        diag: Temple core Diagnostic object
        
    Returns:
        LSP Diagnostic for editor display
        
    Example:
        >>> from temple.diagnostics import Diagnostic, DiagnosticSeverity, SourceRange, Position as TemplePosition
        >>> temple_diag = Diagnostic(
        ...     message="Unclosed block",
        ...     severity=DiagnosticSeverity.ERROR,
        ...     source_range=SourceRange(TemplePosition(0, 0), TemplePosition(0, 10)),
        ...     code="UNCLOSED_BLOCK"
        ... )
        >>> lsp_diag = temple_to_lsp_diagnostic(temple_diag)
        >>> lsp_diag.severity == LspSeverity.Error
        True
    """
    severity_map = {
        DiagnosticSeverity.ERROR: LspSeverity.Error,
        DiagnosticSeverity.WARNING: LspSeverity.Warning,
        DiagnosticSeverity.INFORMATION: LspSeverity.Information,
        DiagnosticSeverity.HINT: LspSeverity.Hint,
    }
    
    # Convert source range to LSP range
    lsp_range = source_range_to_lsp_range(diag.source_range)
    
    return LspDiagnostic(
        range=lsp_range,
        severity=severity_map.get(diag.severity, LspSeverity.Error),
        code=diag.code,
        source=diag.source or "temple",
        message=diag.message,
    )


def source_range_to_lsp_range(source_range: Optional[SourceRange]) -> Range:
    """
    Convert temple SourceRange to LSP Range.
    
    Args:
        source_range: Temple SourceRange or None
        
    Returns:
        LSP Range (defaults to 0,0 if source_range is None)
    """
    if source_range is None:
        return Range(
            start=Position(line=0, character=0),
            end=Position(line=0, character=0),
        )
    
    return Range(
        start=Position(
            line=source_range.start.line,
            character=source_range.start.column,
        ),
        end=Position(
            line=source_range.end.line,
            character=source_range.end.column,
        ),
    )
