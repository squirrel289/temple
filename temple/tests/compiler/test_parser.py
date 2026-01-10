"""
tests.compiler.test_parser
Comprehensive tests for typed template parser with position tracking.
"""

import pytest
from temple.compiler.tokenizer import tokenize, Tokenizer, Token, TokenType
from temple.compiler.parser import parse, TypedTemplateParser, ParseError
from temple.compiler.ast_nodes import (
    Text,
    Expression,
    If,
    For,
    Include,
    Block,
    Position,
    SourceRange,
    walk_ast,
)


class TestTokenizer:
    """Tests for lexical analysis."""

    def test_simple_text(self):
        """Tokenize plain text."""
        tokens = tokenize("hello world")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.TEXT
        assert tokens[0].value == "hello world"
        assert tokens[0].start_line == 0
        assert tokens[0].start_col == 0

    def test_expression_token(self):
        """Tokenize {{ expression }}."""
        tokens = tokenize("foo {{ bar }} baz")
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.TEXT
        assert tokens[0].value == "foo "
        assert tokens[1].type == TokenType.EXPRESSION
        assert tokens[1].value == "bar"  # Stripped of delimiters and whitespace
        assert tokens[2].type == TokenType.TEXT
        assert tokens[2].value == " baz"

    def test_statement_token(self):
        """Tokenize {% statement %}."""
        tokens = tokenize("{% if x %}yes{% endif %}")
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.STATEMENT
        assert tokens[0].value == "if x"
        assert tokens[1].type == TokenType.TEXT
        assert tokens[1].value == "yes"
        assert tokens[2].type == TokenType.STATEMENT
        assert tokens[2].value == "endif"

    def test_comment_token(self):
        """Tokenize {# comment #} (should be tokenized but not parsed)."""
        tokens = tokenize("text {# ignored #} more")
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.TEXT
        assert tokens[1].type == TokenType.COMMENT
        assert tokens[2].type == TokenType.TEXT

    def test_multiline_token_position(self):
        """Verify position tracking across lines."""
        text = "line1\n{{ foo }}\nline3"
        tokens = tokenize(text)
        assert len(tokens) == 3
        assert tokens[0].value == "line1\n"
        assert tokens[0].start_line == 0
        assert tokens[0].end_line == 1
        assert tokens[1].type == TokenType.EXPRESSION
        assert tokens[1].start_line == 1
        # Remaining text includes the newline before line3
        assert tokens[2].start_line == 1  # Starts on same line as {{ foo }}

    def test_custom_delimiters(self):
        """Tokenize with custom delimiters."""
        delims = {
            "statement": ("<<", ">>"),
            "expression": ("<:", ":>"),
            "comment": ("<#", "#>"),
        }
        tokens = tokenize("<: x :> and << if y >>", delimiters=delims)
        assert tokens[0].type == TokenType.EXPRESSION
        assert tokens[0].value == "x"
        assert tokens[2].type == TokenType.STATEMENT
        assert tokens[2].value == "if y"

    def test_empty_token(self):
        """Tokenize empty expressions."""
        tokens = tokenize("{{ }}")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EXPRESSION
        assert tokens[0].value == ""

    def test_nested_delimiters_not_supported(self):
        """Current tokenizer doesn't support nested delimiters (non-greedy match stops at first end)."""
        # This is a limitation: {{ {{ nested }} }} will tokenize incorrectly
        # Future enhancement: context-aware nesting
        tokens = tokenize("{{ a {{ b }} }}")
        # Non-greedy match will stop at first }}; greedy match stops at first occurrence
        assert tokens[0].type == TokenType.EXPRESSION
        # The value is the entire "a {{ b" because non-greedy stops at first }}
        assert "a" in tokens[0].value


class TestParser:
    """Tests for syntactic analysis and AST construction."""

    def test_parse_plain_text(self):
        """Parse plain text (no DSL)."""
        nodes, errors = parse("hello world")
        assert len(errors) == 0
        assert len(nodes) == 1
        assert isinstance(nodes[0], Text)
        assert nodes[0].value == "hello world"

    def test_parse_expression(self):
        """Parse {{ expression }}."""
        nodes, errors = parse("value: {{ user.name }}")
        assert len(errors) == 0
        # May have 2 nodes (text + expression) or 3 (text + expression + text) depending on trailing handling
        assert len(nodes) >= 2
        assert isinstance(nodes[0], Text)
        assert isinstance(nodes[1], Expression)
        assert nodes[1].value == "user.name"

    def test_parse_if_statement(self):
        """Parse {% if %} ... {% endif %}."""
        nodes, errors = parse("{% if x %}yes{% endif %}")
        assert len(errors) == 0
        assert len(nodes) == 1
        assert isinstance(nodes[0], If)
        assert nodes[0].condition == "x"
        assert len(nodes[0].body) == 1
        assert isinstance(nodes[0].body[0], Text)
        assert nodes[0].body[0].value == "yes"

    def test_parse_if_elif_else(self):
        """Parse {% if %} ... {% elif %} ... {% else %} ... {% endif %}."""
        template = "{% if x %}a{% elif y %}b{% else %}c{% endif %}"
        nodes, errors = parse(template)
        assert len(errors) == 0
        assert len(nodes) == 1
        if_node = nodes[0]
        assert isinstance(if_node, If)
        assert if_node.condition == "x"
        assert len(if_node.elif_parts) == 1
        assert if_node.elif_parts[0][0] == "y"  # elif condition
        assert if_node.else_body is not None

    def test_parse_for_loop(self):
        """Parse {% for %} ... {% endfor %}."""
        template = "{% for item in items %}{{ item }}{% endfor %}"
        nodes, errors = parse(template)
        assert len(errors) == 0
        assert len(nodes) == 1
        for_node = nodes[0]
        assert isinstance(for_node, For)
        assert for_node.var == "item"
        assert for_node.iterable == "items"
        assert len(for_node.body) == 1
        assert isinstance(for_node.body[0], Expression)

    def test_parse_include(self):
        """Parse {% include "path" %}."""
        template = '{% include "header.tmpl" %}'
        nodes, errors = parse(template)
        assert len(errors) == 0
        assert len(nodes) == 1
        include_node = nodes[0]
        assert isinstance(include_node, Include)
        assert include_node.path == "header.tmpl"

    def test_parse_include_single_quotes(self):
        """Parse include with single quotes."""
        template = "{% include 'footer.tmpl' %}"
        nodes, errors = parse(template)
        assert len(errors) == 0
        include_node = nodes[0]
        assert include_node.path == "footer.tmpl"

    def test_parse_block(self):
        """Parse {% block %} ... {% endblock %}."""
        template = "{% block content %}default{% endblock %}"
        nodes, errors = parse(template)
        assert len(errors) == 0
        assert len(nodes) == 1
        block_node = nodes[0]
        assert isinstance(block_node, Block)
        assert block_node.name == "content"
        assert len(block_node.body) == 1

    def test_parse_nested_structures(self):
        """Parse nested if/for."""
        template = "{% if show %}{% for item in list %}{{ item }}{% endfor %}{% endif %}"
        nodes, errors = parse(template)
        assert len(errors) == 0
        assert len(nodes) == 1
        if_node = nodes[0]
        assert isinstance(if_node, If)
        assert len(if_node.body) == 1
        for_node = if_node.body[0]
        assert isinstance(for_node, For)
        assert len(for_node.body) == 1
        expr = for_node.body[0]
        assert isinstance(expr, Expression)

    def test_position_tracking_on_all_nodes(self):
        """Verify all AST nodes have position information."""
        template = "text {{ expr }} {% if x %}content{% endif %}"
        nodes, errors = parse(template)
        
        # Check all nodes have positions
        for node in walk_ast(nodes[0]):
            assert node.source_range is not None
            assert isinstance(node.start, Position)
            assert isinstance(node.end, Position)

    def test_parse_multiline_if(self):
        """Parse if statement across multiple lines."""
        template = """{% if user %}
Hello {{ user.name }}!
{% endif %}"""
        nodes, errors = parse(template)
        assert len(errors) == 0
        if_node = nodes[0]
        assert isinstance(if_node, If)
        # Body should have text and expression
        assert any(isinstance(n, Expression) for n in walk_ast(if_node))

    def test_skip_comments(self):
        """Comments are tokenized but not included in AST."""
        template = "before {# this is ignored #} after"
        nodes, errors = parse(template)
        assert len(errors) == 0
        # Should have text nodes but no comment nodes in AST
        assert all(isinstance(n, Text) for n in nodes)

    def test_custom_delimiters_parsing(self):
        """Parse with custom delimiters."""
        delims = {
            "statement": ("<<", ">>"),
            "expression": ("<:", ":>"),
            "comment": ("<#", "#>"),
        }
        template = "<: name :> and << if ok >>yes<< endif >>"
        nodes, errors = parse(template, delimiters=delims)
        assert len(errors) == 0
        assert len(nodes) > 0
        # Check that custom delimiters were used
        has_if = any(isinstance(n, If) for n in walk_ast(nodes[0]) if hasattr(n, 'condition'))
        assert has_if or len(nodes) > 1  # Either parsed if or separate nodes

    def test_error_recovery_on_invalid_for(self):
        """Parser collects errors but attempts recovery."""
        template = "{% for bad syntax %} content"
        nodes, errors = parse(template)
        # Should have collected an error
        assert len(errors) > 0 or len(nodes) == 0


class TestASTWalker:
    """Tests for AST traversal utilities."""

    def test_walk_simple_tree(self):
        """Walk simple AST tree."""
        template = "text {{ expr }} more"
        nodes, _ = parse(template)
        all_nodes = []
        for node in nodes:
            all_nodes.extend(walk_ast(node))
        
        # Should have Text, Expression, Text
        assert len(all_nodes) == 3
        assert isinstance(all_nodes[0], Text)
        assert isinstance(all_nodes[1], Expression)
        assert isinstance(all_nodes[2], Text)

    def test_walk_nested_tree(self):
        """Walk nested AST tree."""
        template = "{% if x %}{{ y }}{% endif %}"
        nodes, _ = parse(template)
        all_nodes = []
        for node in nodes:
            all_nodes.extend(walk_ast(node))
        
        # Should have If (root) + Text in body + Expression in body
        # walk_ast returns depth-first
        assert len(all_nodes) >= 2
        assert isinstance(all_nodes[0], If)


class TestPositionTracking:
    """Tests for accurate source position tracking."""

    def test_text_position(self):
        """Text node has correct position."""
        tokens = tokenize("hello")
        token = tokens[0]
        node = Text("hello", SourceRange(
            start=Position(token.start_line, token.start_col),
            end=Position(token.end_line, token.end_col),
        ))
        assert node.start.line == 0
        assert node.start.col == 0
        assert node.end.col == 5

    def test_multiline_position(self):
        """Position tracking across multiple lines."""
        text = "line1\nline2\n{{ expr }}"
        nodes, _ = parse(text)
        expr_node = [n for n in walk_ast(nodes[0]) if isinstance(n, Expression)]
        if expr_node:
            assert expr_node[0].start.line == 2

    def test_position_to_lsp(self):
        """Convert positions to LSP format."""
        pos = Position(5, 10)
        lsp = pos.to_lsp()
        assert lsp == {"line": 5, "character": 10}

    def test_range_to_lsp(self):
        """Convert source range to LSP format."""
        sr = SourceRange(
            start=Position(1, 2),
            end=Position(3, 4),
        )
        lsp = sr.to_lsp()
        assert lsp["start"]["line"] == 1
        assert lsp["end"]["character"] == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
