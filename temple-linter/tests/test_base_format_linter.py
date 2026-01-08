import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from temple_linter.base_format_linter import BaseFormatLinter


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
    assert linter.detect_base_format("notes.unknown", "just text") == "txt"


def test_lint_base_format_returns_diagnostics(linter):
    diagnostics = linter.lint_base_format("Hello {% if user %}{{ user.name }}{% endif %}")
    assert isinstance(diagnostics, list)
    assert diagnostics[0]["base_format"] == "txt"
