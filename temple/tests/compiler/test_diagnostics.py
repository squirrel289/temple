"""
Tests for the diagnostic system.
"""

import pytest
from temple.compiler.diagnostics import (
    Diagnostic, DiagnosticSeverity, DiagnosticCollector,
    SuppressionComment
)
from temple.compiler.ast_nodes import Position, SourceRange


class TestDiagnostic:
    """Test Diagnostic class."""
    
    def test_create_diagnostic(self):
        diag = Diagnostic(
            message="Test error",
            source_range=SourceRange(Position(0, 0), Position(0, 5))
        )
        assert diag.message == "Test error"
        assert diag.severity == DiagnosticSeverity.ERROR
    
    def test_diagnostic_to_lsp(self):
        diag = Diagnostic(
            message="Test error",
            source_range=SourceRange(Position(0, 5), Position(0, 10)),
            code="TEST_001"
        )
        lsp = diag.to_lsp()
        
        assert lsp["message"] == "Test error"
        assert lsp["severity"] == DiagnosticSeverity.ERROR.value
        assert lsp["code"] == "TEST_001"
        assert "range" in lsp
    
    def test_diagnostic_to_string_without_context(self):
        diag = Diagnostic(
            message="Test error",
            source_range=SourceRange(Position(0, 0), Position(0, 5)),
            code="TEST_001"
        )
        output = diag.to_string(include_context=False)
        
        assert "Test error" in output
        assert "error" in output
        assert "line 1" in output
    
    def test_diagnostic_with_context(self):
        source = "hello world"
        diag = Diagnostic(
            message="Test error",
            source_range=SourceRange(Position(0, 0), Position(0, 5))
        )
        output = diag.to_string(source_text=source, include_context=True)
        
        assert "hello world" in output
        assert "^" in output  # Pointer


class TestDiagnosticCollector:
    """Test DiagnosticCollector class."""
    
    def test_add_diagnostic(self):
        collector = DiagnosticCollector()
        diag = collector.add_error(
            "Test error",
            SourceRange(Position(0, 0), Position(0, 5)),
            "TEST_001"
        )
        
        assert len(collector.diagnostics) == 1
        assert collector.diagnostics[0] == diag
    
    def test_add_multiple_diagnostics(self):
        collector = DiagnosticCollector()
        collector.add_error("Error 1", SourceRange(Position(0, 0), Position(0, 5)))
        collector.add_warning("Warning 1", SourceRange(Position(1, 0), Position(1, 5)))
        collector.add_info("Info 1", SourceRange(Position(2, 0), Position(2, 5)))
        
        assert len(collector.diagnostics) == 3
        assert collector.has_errors()
        assert collector.has_warnings()
    
    def test_error_counting(self):
        collector = DiagnosticCollector()
        collector.add_error("Error 1", SourceRange(Position(0, 0), Position(0, 5)))
        collector.add_error("Error 2", SourceRange(Position(1, 0), Position(1, 5)))
        collector.add_warning("Warning 1", SourceRange(Position(2, 0), Position(2, 5)))
        
        assert collector.error_count() == 2
        assert collector.warning_count() == 1
    
    def test_parse_suppression(self):
        collector = DiagnosticCollector()
        suppression = collector.parse_suppression(
            "@suppress TEST_001, TEST_002",
            SourceRange(Position(0, 0), Position(0, 30))
        )
        
        assert suppression is not None
        assert "TEST_001" in suppression.suppressed_codes
        assert "TEST_002" in suppression.suppressed_codes
    
    def test_suppression_filters_diagnostics(self):
        collector = DiagnosticCollector()
        
        # Add suppression for line 0
        collector.parse_suppression(
            "@suppress TEST_001",
            SourceRange(Position(0, 0), Position(0, 20))
        )
        
        # Add diagnostic on same line
        collector.add_error(
            "Test error",
            SourceRange(Position(0, 25), Position(0, 30)),
            code="TEST_001"
        )
        
        # Should be filtered out
        filtered = collector.get_filtered_diagnostics()
        assert len(filtered) == 0
    
    def test_wildcard_suppression(self):
        collector = DiagnosticCollector()
        
        # Add wildcard suppression
        collector.parse_suppression(
            "@suppress *",
            SourceRange(Position(0, 0), Position(0, 15))
        )
        
        # Add various diagnostics on same line
        collector.add_error("Error", SourceRange(Position(0, 20), Position(0, 25)), code="ANY_001")
        collector.add_warning("Warning", SourceRange(Position(0, 20), Position(0, 25)), code="ANY_002")
        
        # Both should be filtered
        filtered = collector.get_filtered_diagnostics()
        assert len(filtered) == 0
    
    def test_to_lsp(self):
        collector = DiagnosticCollector()
        collector.add_error("Error", SourceRange(Position(0, 0), Position(0, 5)))
        
        lsp = collector.to_lsp()
        assert len(lsp) == 1
        assert lsp[0]["message"] == "Error"
    
    def test_format_all(self):
        collector = DiagnosticCollector()
        collector.add_error("Error", SourceRange(Position(0, 0), Position(0, 5)))
        
        formatted = collector.format_all()
        assert "1 diagnostic" in formatted
        assert "Error" in formatted


class TestSuppressionComment:
    """Test SuppressionComment class."""
    
    def test_suppresses_exact_code(self):
        suppression = SuppressionComment(
            suppressed_codes=["TEST_001"],
            source_range=SourceRange(Position(0, 0), Position(0, 30))
        )
        
        assert suppression.suppresses("TEST_001")
        assert not suppression.suppresses("TEST_002")
    
    def test_suppresses_multiple_codes(self):
        suppression = SuppressionComment(
            suppressed_codes=["TEST_001", "TEST_002"],
            source_range=SourceRange(Position(0, 0), Position(0, 40))
        )
        
        assert suppression.suppresses("TEST_001")
        assert suppression.suppresses("TEST_002")
        assert not suppression.suppresses("TEST_003")
    
    def test_suppresses_wildcard(self):
        suppression = SuppressionComment(
            suppressed_codes=["*"],
            source_range=SourceRange(Position(0, 0), Position(0, 20))
        )
        
        assert suppression.suppresses("ANY_CODE")
        assert suppression.suppresses("TEST_001")
    
    def test_suppresses_none_code(self):
        suppression = SuppressionComment(
            suppressed_codes=["TEST_001"],
            source_range=SourceRange(Position(0, 0), Position(0, 30))
        )
        
        assert not suppression.suppresses(None)


class TestDiagnosticSeverities:
    """Test different diagnostic severity levels."""
    
    def test_error_severity(self):
        diag = Diagnostic(
            message="Error",
            source_range=SourceRange(Position(0, 0), Position(0, 5)),
            severity=DiagnosticSeverity.ERROR
        )
        assert diag.severity == DiagnosticSeverity.ERROR
    
    def test_warning_severity(self):
        diag = Diagnostic(
            message="Warning",
            source_range=SourceRange(Position(0, 0), Position(0, 5)),
            severity=DiagnosticSeverity.WARNING
        )
        assert diag.severity == DiagnosticSeverity.WARNING
    
    def test_info_severity(self):
        diag = Diagnostic(
            message="Info",
            source_range=SourceRange(Position(0, 0), Position(0, 5)),
            severity=DiagnosticSeverity.INFORMATION
        )
        assert diag.severity == DiagnosticSeverity.INFORMATION
    
    def test_hint_severity(self):
        diag = Diagnostic(
            message="Hint",
            source_range=SourceRange(Position(0, 0), Position(0, 5)),
            severity=DiagnosticSeverity.HINT
        )
        assert diag.severity == DiagnosticSeverity.HINT
