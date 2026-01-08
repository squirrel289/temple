import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from temple_linter.base_format_linter import BaseFormatLinter, strip_temple_extension, VSCODE_PASSTHROUGH


@pytest.fixture()
def linter():
    return BaseFormatLinter()


def test_detect_by_extension_json(linter):
    assert linter.detect_base_format("config.json", "{}") == "json"


def test_detect_by_extension_yaml(linter):
    assert linter.detect_base_format("config.yaml", "key: value") == "yaml"


def test_detect_by_content_html(linter):
    html = "<!DOCTYPE html><html><body></body></html>"
    assert linter.detect_base_format(None, html) == "html"


def test_detect_by_content_xml(linter):
    xml = "<?xml version='1.0'?><root></root>"
    assert linter.detect_base_format(None, xml) == "xml"


def test_detect_markdown(linter):
    md = "# Title\n- item"
    assert linter.detect_base_format("README", md) == "md"


def test_detect_toml(linter):
    toml = "[tool]\nname='app'"
    assert linter.detect_base_format("pyproject", toml) == "toml"


def test_detect_fallback_txt(linter):
    # Unknown content and extension now triggers VS Code passthrough
    assert linter.detect_base_format("notes.unknown", "just text") == VSCODE_PASSTHROUGH


def test_lint_base_format_returns_diagnostics(linter):
    diagnostics = linter.lint_base_format("Hello {% if user %}{{ user.name }}{% endif %}")
    assert isinstance(diagnostics, list)
    assert diagnostics[0]["base_format"] == VSCODE_PASSTHROUGH


def test_strip_temple_extension_tmpl():
    assert strip_temple_extension("config.json.tmpl") == "config.json"


def test_strip_temple_extension_template():
    assert strip_temple_extension("README.md.template") == "README.md"


def test_strip_temple_extension_no_suffix():
    assert strip_temple_extension("plain_file") == "plain_file"


def test_strip_temple_extension_case_insensitive():
    assert strip_temple_extension("config.TMPL") == "config"


def test_strip_temple_extension_none():
    assert strip_temple_extension(None) is None


def test_detect_fallback_to_passthrough(linter):
    # Unknown content and no extension should trigger passthrough
    assert linter.detect_base_format("unknown", "random text") == VSCODE_PASSTHROUGH


def test_strip_custom_extensions():
    # Test with custom temple extensions
    custom_exts = [".tpl", ".jinja", ".tmpl"]
    assert strip_temple_extension("config.json.tpl", custom_exts) == "config.json"
    assert strip_temple_extension("template.md.jinja", custom_exts) == "template.md"
    assert strip_temple_extension("data.tmpl", custom_exts) == "data"


def test_strip_empty_extensions():
    # Empty extensions list should not strip anything
    assert strip_temple_extension("config.json.tmpl", []) == "config.json.tmpl"


def test_strip_none_extensions_uses_defaults():
    # None extensions should use defaults
    assert strip_temple_extension("config.json.tmpl", None) == "config.json"
    assert strip_temple_extension("data.template", None) == "data"


def test_strip_custom_case_insensitive():
    # Custom extensions should be case-insensitive
    custom_exts = [".TPL"]
    assert strip_temple_extension("config.json.tpl", custom_exts) == "config.json"
    assert strip_temple_extension("config.json.TPL", custom_exts) == "config.json"

