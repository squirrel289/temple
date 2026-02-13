"""Tests for the Jinja2 adapter prototype."""

import pytest

pytest.importorskip("jinja2")

from temple.adapters.jinja2_adapter import Jinja2Adapter


def test_parse_to_ir_and_list_filters() -> None:
    adapter = Jinja2Adapter()
    result = adapter.parse_to_ir("{{ users | map('name') | join(', ') }}")

    assert result.diagnostics == ()
    assert adapter.list_used_filters(result.ir) == ["map", "join"]
    assert len(result.source_map) >= 1


def test_parse_to_ir_handles_control_flow_and_set() -> None:
    adapter = Jinja2Adapter()
    template = """
{% set is_active = user.active %}
{% if is_active %}
  {% for item in items %}
    {{ item.name }}
  {% endfor %}
{% endif %}
"""
    result = adapter.parse_to_ir(template)
    typed = adapter.to_typed_block(result.ir)

    assert len(typed.nodes) >= 2


def test_parse_to_ir_reports_syntax_errors_with_range() -> None:
    adapter = Jinja2Adapter()
    result = adapter.parse_to_ir("{% if user.active %}hello")

    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag.code == "jinja2.syntax_error"
    assert diag.source_range.start.line >= 0


def test_semantic_diagnostics_reports_undefined_or_missing_fields() -> None:
    adapter = Jinja2Adapter()
    diagnostics = adapter.semantic_diagnostics(
        "{{ user.missing }}",
        data={"user": {"name": "Ada"}},
    )

    assert diagnostics
    assert diagnostics[0]["code"] in {"missing_property", "undefined_variable"}
