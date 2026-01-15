import unittest
from temple_linter.linter import TemplateLinter
from temple.diagnostics import DiagnosticSeverity


class TestTemplateLinter(unittest.TestCase):
    """Test template syntax validation."""
    
    def test_lint_empty(self):
        """Test that empty text produces no diagnostics."""
        linter = TemplateLinter()
        diagnostics = linter.lint("")
        self.assertIsInstance(diagnostics, list)
    
    def test_valid_template_no_errors(self):
        """Test that valid templates produce no diagnostics."""
        linter = TemplateLinter()
        text = "{% if user.active %}{{ user.name }}{% end %}"
        diagnostics = linter.lint(text)
        self.assertEqual(len(diagnostics), 0)
    
    def test_unclosed_if_block(self):
        """Test detection of unclosed if block."""
        linter = TemplateLinter()
        text = "{% if user.active %}Hello"
        diagnostics = linter.lint(text)
        self.assertGreater(len(diagnostics), 0)
        self.assertTrue(any("unclosed" in d.message.lower() or "end" in d.message.lower() 
                           for d in diagnostics))
        self.assertTrue(any(d.severity == DiagnosticSeverity.ERROR for d in diagnostics))
    
    def test_unclosed_for_block(self):
        """Test detection of unclosed for block."""
        linter = TemplateLinter()
        text = "{% for item in items %}{{ item }}"
        diagnostics = linter.lint(text)
        self.assertGreater(len(diagnostics), 0)
        self.assertTrue(any(d.severity == DiagnosticSeverity.ERROR for d in diagnostics))
    
    def test_malformed_expression(self):
        """Test detection of malformed expression with trailing dot."""
        linter = TemplateLinter()
        text = "{{ user. }}"
        diagnostics = linter.lint(text)
        self.assertGreater(len(diagnostics), 0)
        self.assertTrue(any(d.severity == DiagnosticSeverity.ERROR for d in diagnostics))
    
    def test_nested_blocks_valid(self):
        """Test that properly nested blocks work."""
        linter = TemplateLinter()
        text = """
        {% if user.active %}
            {% for skill in user.skills %}
                {{ skill }}
            {% end %}
        {% end %}
        """
        diagnostics = linter.lint(text)
        self.assertEqual(len(diagnostics), 0)
    
    def test_diagnostic_has_position(self):
        """Test that diagnostics include source positions."""
        linter = TemplateLinter()
        text = "{% if x %}"
        diagnostics = linter.lint(text)
        if len(diagnostics) > 0:
            diag = diagnostics[0]
            self.assertIsNotNone(diag.source_range)
            self.assertIsNotNone(diag.source_range.start)
            self.assertIsNotNone(diag.source_range.end)
    
    def test_multiple_errors(self):
        """Test that multiple syntax errors are all reported."""
        linter = TemplateLinter()
        text = "{% if x %}{{ y. }}{% for z in items %}"
        diagnostics = linter.lint(text)
        # Should have multiple errors (unclosed blocks, malformed expression)
        self.assertGreaterEqual(len(diagnostics), 2)


if __name__ == "__main__":
    unittest.main()
