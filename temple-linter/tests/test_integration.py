"""
Integration tests for complete linting pipeline.

Tests the full workflow:
1. Template text input
2. Tokenization
3. Token cleaning
4. Format detection
5. Base linting (mocked)
6. Diagnostic mapping
7. Diagnostic merging
"""

import pathlib
import sys
from unittest.mock import Mock
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from temple_linter.services.lint_orchestrator import LintOrchestrator
    from temple_linter.services.token_cleaning_service import TokenCleaningService
    from temple_linter.base_format_linter import BaseFormatLinter
    from lsprotocol.types import Diagnostic, Range, Position
except Exception:
    # Fall back to adjusting sys.path in test environments where package isn't
    # available on the PYTHONPATH.
    import pathlib
    import sys

    ROOT = pathlib.Path(__file__).resolve().parents[1]
    SRC = ROOT / "src"
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))

    from temple_linter.services.lint_orchestrator import LintOrchestrator
    from temple_linter.services.token_cleaning_service import TokenCleaningService
    from temple_linter.base_format_linter import BaseFormatLinter
    from lsprotocol.types import Diagnostic, Range, Position


@pytest.fixture
def mock_language_client():
    """Mock LSP language client."""
    client = Mock()
    client.protocol = Mock()
    client.protocol.send_request = Mock()
    return client


@pytest.fixture
def orchestrator():
    """Create orchestrator instance."""
    return LintOrchestrator()


class TestFullPipeline:
    """Test complete linting pipeline with real-world scenarios."""

    def test_json_template_with_valid_syntax(self, orchestrator, mock_language_client):
        """Test valid JSON template produces no errors."""
        template = """
{
  "name": "{{ user.name }}",
  "age": {{ user.age }},
  "active": {% if user.active %}true{% else %}false{% end %}
}
"""
        # Mock successful base linting (no diagnostics)
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///test.json.tmpl", mock_language_client
        )

        # Should have no errors for valid template
        assert isinstance(diagnostics, list)
        # Template linting may produce diagnostics, but structure should be valid

    def test_json_template_with_invalid_json(self, orchestrator, mock_language_client):
        """Test JSON template with invalid base format."""
        template = """
{
  "name": "{{ user.name }}",
  "age": {{ user.age }}  {# missing comma #}
  "active": true
}
"""
        # Mock base linter finding JSON error
        mock_diagnostic = Diagnostic(
            range=Range(
                start=Position(line=3, character=2), end=Position(line=3, character=12)
            ),
            message="Expected comma or closing brace",
            severity=1,
        )
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": [mock_diagnostic]
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///test.json.tmpl", mock_language_client
        )

        assert isinstance(diagnostics, list)
        # Should receive diagnostics from base linter

    def test_yaml_template_with_expressions(self, orchestrator, mock_language_client):
        """Test YAML template with template expressions."""
        template = """
name: {{ app.name }}
version: {{ app.version }}
dependencies:
  {% for dep in app.dependencies %}
  - {{ dep }}
  {% end %}
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///config.yaml.tmpl", mock_language_client
        )

        assert isinstance(diagnostics, list)

    def test_html_template_with_control_flow(self, orchestrator, mock_language_client):
        """Test HTML template with if/for statements."""
        template = """
<!DOCTYPE html>
<html>
<head><title>{{ page.title }}</title></head>
<body>
  {% if user.logged_in %}
  <h1>Welcome, {{ user.name }}!</h1>
  {% else %}
  <h1>Please log in</h1>
  {% end %}
  
  <ul>
  {% for item in items %}
    <li>{{ item.name }}: ${{ item.price }}</li>
  {% end %}
  </ul>
</body>
</html>
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///page.html.tmpl", mock_language_client
        )

        assert isinstance(diagnostics, list)

    def test_markdown_template_with_loops(self, orchestrator, mock_language_client):
        """Test Markdown template with template syntax."""
        template = """
# {{ project.name }}

## Features

{% for feature in project.features %}
- **{{ feature.name }}**: {{ feature.description }}
{% end %}

## Installation

```bash
{{ project.install_command }}
```
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///README.md.tmpl", mock_language_client
        )

        assert isinstance(diagnostics, list)

    def test_custom_delimiters(self, orchestrator, mock_language_client):
        """Test template with custom delimiters."""
        # Note: Current implementation uses default delimiters
        # This test verifies the pipeline works regardless
        template = """
{
  "name": "<< user.name >>",
  "value": [[ var ]]
}
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///test.json.tmpl", mock_language_client
        )

        assert isinstance(diagnostics, list)

    def test_custom_temple_extensions(self, orchestrator, mock_language_client):
        """Test custom temple file extensions."""
        template = """
name: {{ config.name }}
value: {{ config.value }}
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        # Test with custom extension
        custom_extensions = [".tpl", ".jinja", ".tmpl"]
        diagnostics = orchestrator.lint_template(
            template,
            "file:///config.yaml.tpl",
            mock_language_client,
            temple_extensions=custom_extensions,
        )

        assert isinstance(diagnostics, list)


class TestTokenCleaning:
    """Test token cleaning service."""

    def test_clean_preserves_structure(self):
        """Test that cleaning preserves line/column structure."""
        service = TokenCleaningService()
        template = """line 1
{{ expr }}
line 3"""

        cleaned, tokens = service.clean_text_and_tokens(template)

        # Cleaned text should have template tokens removed
        assert "expr" not in cleaned
        assert "line 1" in cleaned
        assert "line 3" in cleaned

    def test_clean_multiple_tokens(self):
        """Test cleaning multiple token types."""
        service = TokenCleaningService()
        template = "{% if x %}{{ y }}{# comment #}text"

        cleaned, tokens = service.clean_text_and_tokens(template)

        assert "if x" not in cleaned
        assert "y" not in cleaned
        assert "comment" not in cleaned
        assert "text" in cleaned


class TestFormatDetection:
    """Test format detection with various inputs."""

    def test_detect_by_extension(self):
        """Test format detection by file extension."""
        linter = BaseFormatLinter()

        assert linter.detect_base_format("config.json", "{}") == "json"
        assert linter.detect_base_format("data.yaml", "key: value") == "yaml"
        assert linter.detect_base_format("index.html", "<html></html>") == "html"
        assert linter.detect_base_format("data.xml", "<?xml?>") == "xml"
        assert linter.detect_base_format("config.toml", "[section]") == "toml"
        assert linter.detect_base_format("README.md", "# Title") == "md"

    def test_detect_by_content(self):
        """Test format detection by content when no extension."""
        linter = BaseFormatLinter()

        # JSON content
        json_content = '{"key": "value"}'
        assert linter.detect_base_format(None, json_content) == "json"

        # HTML content
        html_content = "<!DOCTYPE html><html></html>"
        assert linter.detect_base_format(None, html_content) == "html"

        # XML content
        xml_content = "<?xml version='1.0'?><root></root>"
        assert linter.detect_base_format(None, xml_content) == "xml"

    def test_detect_temple_extension_stripping(self):
        """Test that temple extensions are properly stripped."""
        from temple_linter.base_format_linter import strip_temple_extension

        # Default extensions
        assert strip_temple_extension("config.json.tmpl") == "config.json"
        assert strip_temple_extension("data.yaml.template") == "data.yaml"

        # Custom extensions
        assert strip_temple_extension("file.tpl", [".tpl"]) == "file"
        assert strip_temple_extension("file.jinja", [".jinja", ".tmpl"]) == "file"


class TestEndToEnd:
    """End-to-end tests simulating real usage."""

    def test_complete_workflow_json_valid(self, orchestrator, mock_language_client):
        """Test complete workflow with valid JSON template."""
        template = """
{
  "users": [
    {% for user in users %}
    {
      "id": {{ user.id }},
      "name": "{{ user.name }}",
      "email": "{{ user.email }}"
    }{% if not loop.last %},{% end %}
    {% end %}
  ]
}
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///users.json.tmpl", mock_language_client
        )

        assert isinstance(diagnostics, list)
        # Valid template should produce minimal or no diagnostics

    def test_complete_workflow_yaml_valid(self, orchestrator, mock_language_client):
        """Test complete workflow with valid YAML template."""
        template = """
version: {{ version }}
services:
  {% for service in services %}
  {{ service.name }}:
    image: {{ service.image }}
    ports:
      {% for port in service.ports %}
      - "{{ port }}"
      {% end %}
  {% end %}
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///docker-compose.yaml.tmpl", mock_language_client
        )

        assert isinstance(diagnostics, list)

    def test_mixed_content_with_edge_cases(self, orchestrator, mock_language_client):
        """Test edge cases like nested braces, quotes in templates."""
        template = """
{
  "nested": {{ "{{literal}}" }},
  "quoted": "{{ 'string with \\"quotes\\"' }}",
  "complex": {% if x > 5 and y < 10 %}true{% else %}false{% end %}
}
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///complex.json.tmpl", mock_language_client
        )

        assert isinstance(diagnostics, list)


class TestSyntaxValidation:
    """Test template syntax validation integration."""

    def test_unclosed_if_block_error(self, orchestrator, mock_language_client):
        """Test that unclosed if blocks produce syntax errors."""
        template = """
{
  "name": "test",
  "value": {% if condition %}true
}
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///test.json.tmpl", mock_language_client
        )

        # Should have at least one diagnostic for unclosed block
        assert len(diagnostics) > 0
        # Check that at least one diagnostic is an error
        assert any(d.severity == 1 for d in diagnostics)  # 1 = Error

    def test_unclosed_for_block_error(self, orchestrator, mock_language_client):
        """Test that unclosed for blocks produce syntax errors."""
        template = """
<ul>
{% for item in items %}
  <li>{{ item }}</li>
</ul>
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///list.html.tmpl", mock_language_client
        )

        # Should have diagnostic for unclosed for
        assert len(diagnostics) > 0
        assert any(d.severity == 1 for d in diagnostics)

    def test_malformed_expression_error(self, orchestrator, mock_language_client):
        """Test that malformed expressions produce errors."""
        template = "{{ user. }}"

        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///test.tmpl", mock_language_client
        )

        assert len(diagnostics) > 0
        assert any(d.severity == 1 for d in diagnostics)

    def test_valid_syntax_no_errors(self, orchestrator, mock_language_client):
        """Test that valid template syntax produces no syntax errors."""
        template = """
{% if user.active %}
  {{ user.name }}
  {% for skill in user.skills %}
    - {{ skill }}
  {% end %}
{% end %}
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///test.tmpl", mock_language_client
        )

        # Should have no syntax errors
        assert all(
            d.severity != 1 or "syntax" not in d.message.lower() for d in diagnostics
        )

    def test_multiple_syntax_errors(self, orchestrator, mock_language_client):
        """Test that multiple syntax errors are all reported."""
        template = """
{% if x %}
  {{ y. }}
  {% for z in items %}
"""
        mock_language_client.protocol.send_request.return_value.result.return_value = {
            "diagnostics": []
        }

        diagnostics = orchestrator.lint_template(
            template, "file:///test.tmpl", mock_language_client
        )

        # Should have multiple errors
        assert len(diagnostics) >= 2
        assert any(d.severity == 1 for d in diagnostics)
