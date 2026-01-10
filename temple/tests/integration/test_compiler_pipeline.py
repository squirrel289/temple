"""
Integration tests for the typed DSL compiler pipeline.

Covers parser → type checker → serializer flows using Markdown output as a
representative end-to-end path.
"""

import pytest

from temple.compiler.ast_nodes import Block, Position, SourceRange
from temple.compiler.parser import TypedTemplateParser
from temple.compiler.type_checker import TypeChecker
from temple.compiler.serializers.markdown_serializer import MarkdownSerializer


def _make_block(nodes):
    """Wrap a list of AST nodes in a synthetic root block for serialization."""
    if not nodes:
        start = end = Position(0, 0)
    else:
        start = nodes[0].source_range.start
        end = nodes[-1].source_range.end
    return Block("root", nodes, SourceRange(start, end))


def test_markdown_pipeline_happy_path():
    """Parse, type check, and serialize a simple Markdown template end-to-end."""
    template = (
        "Hello {{ user.name }}\n"
        "{% for job in user.jobs %}- {{ job.title }} at {{ job.company }}\n"
        "{% endfor %}"
    )
    data = {
        "user": {
            "name": "Alice",
            "jobs": [
                {"title": "Engineer", "company": "Acme"},
                {"title": "Manager", "company": "Beta"},
            ],
        }
    }

    parser = TypedTemplateParser()
    ast_nodes, parse_errors = parser.parse(template)
    assert parse_errors == []

    checker = TypeChecker(data=data)
    for node in ast_nodes:
        checker.check(node)
    assert not checker.errors.has_errors()

    root = _make_block(ast_nodes)
    serializer = MarkdownSerializer(pretty=False)
    output = serializer.serialize(root, data)

    expected = "Hello Alice\n- Engineer at Acme\n- Manager at Beta\n"
    assert output == expected


def test_markdown_pipeline_reports_type_errors():
    """Pipeline surfaces type errors when accessing missing data."""
    template = "Hello {{ user.missing }}"
    data = {"user": {"name": "Alice"}}

    parser = TypedTemplateParser()
    ast_nodes, parse_errors = parser.parse(template)
    assert parse_errors == []

    checker = TypeChecker(data=data)
    for node in ast_nodes:
        checker.check(node)

    assert checker.errors.has_errors()
    # Verify error kind and message reference the missing property
    error = checker.errors.errors[0]
    assert error.kind == "missing_property"
    assert "missing" in error.message

    # Serialization should respect errors; strict mode raises on undefined variable
    root = _make_block(ast_nodes)
    serializer = MarkdownSerializer(pretty=False, strict=True)
    with pytest.raises(Exception):
        serializer.serialize(root, data)
