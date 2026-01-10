"""
temple.compiler.parser
Parser: transforms tokenized input into typed template AST.

Implements recursive descent parser with error recovery and position tracking.
"""

from typing import List, Optional, Dict, Tuple
from temple.compiler.tokenizer import Token, TokenType, tokenize, Tokenizer
from temple.compiler.ast_nodes import (
    ASTNode,
    Position,
    SourceRange,
    Text,
    Expression,
    If,
    For,
    Include,
    Block,
)


class ParseError(Exception):
    """Parser error with position information."""

    def __init__(self, message: str, token: Optional[Token] = None):
        self.message = message
        self.token = token
        if token:
            super().__init__(f"{message} at ({token.start_line}, {token.start_col})")
        else:
            super().__init__(message)


class TypedTemplateParser:
    """Recursive descent parser for typed template DSL."""

    def __init__(self, delimiters: Optional[Dict[str, Tuple[str, str]]] = None):
        """Initialize parser with optional custom delimiters."""
        self.delimiters = delimiters
        self.tokens = []
        self.pos = 0
        self.errors = []

    def parse(self, text: str) -> Tuple[List[ASTNode], List[ParseError]]:
        """Parse template text into AST. Returns (ast_nodes, errors).
        
        Errors are collected (no exception on first error) for best-effort parsing.
        """
        self.errors = []
        self.pos = 0
        
        # Tokenize input
        tokenizer = Tokenizer(self.delimiters)
        self.tokens = tokenizer.tokenize(text)
        
        # Parse tokens into AST
        try:
            nodes = self._parse_body(end_tokens=None)
            return nodes, self.errors
        except ParseError as e:
            self.errors.append(e)
            return [], self.errors

    def _current_token(self) -> Optional[Token]:
        """Get current token without consuming it."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _peek_token(self, offset: int = 1) -> Optional[Token]:
        """Peek ahead by offset tokens."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def _consume(self) -> Optional[Token]:
        """Consume and return current token."""
        token = self._current_token()
        if token:
            self.pos += 1
        return token

    def _expect(self, token_type: TokenType, expected_value: Optional[str] = None) -> Token:
        """Consume token of given type, raise error if mismatch."""
        token = self._current_token()
        if not token:
            raise ParseError(f"Expected {token_type.value}, got EOF")
        if token.type != token_type:
            raise ParseError(f"Expected {token_type.value}, got {token.type.value}", token)
        if expected_value and token.value != expected_value:
            raise ParseError(
                f"Expected {expected_value!r}, got {token.value!r}", token
            )
        return self._consume()

    def _parse_body(self, end_tokens: Optional[List[str]] = None) -> List[ASTNode]:
        """Parse body until end_token or EOF. Returns list of AST nodes."""
        nodes = []
        end_tokens = end_tokens or []

        while self._current_token():
            token = self._current_token()

            # Check for end condition
            if token.type == TokenType.STATEMENT:
                # Check if this is an end statement
                for end_token in end_tokens:
                    if token.value.startswith(end_token):
                        return nodes

            if token.type == TokenType.TEXT:
                node = self._parse_text()
                nodes.append(node)
            elif token.type == TokenType.EXPRESSION:
                node = self._parse_expression()
                nodes.append(node)
            elif token.type == TokenType.STATEMENT:
                node = self._parse_statement()
                if node:
                    nodes.append(node)
            elif token.type == TokenType.COMMENT:
                # Skip comments
                self._consume()
            else:
                # Skip unknown token
                self._consume()

        return nodes

    def _parse_text(self) -> Text:
        """Parse text token."""
        token = self._expect(TokenType.TEXT)
        return Text(
            value=token.value,
            source_range=SourceRange(
                start=Position(token.start_line, token.start_col),
                end=Position(token.end_line, token.end_col),
            ),
        )

    def _parse_expression(self) -> Expression:
        """Parse {{ expression }}."""
        token = self._expect(TokenType.EXPRESSION)
        return Expression(
            value=token.value,
            source_range=SourceRange(
                start=Position(token.start_line, token.start_col),
                end=Position(token.end_line, token.end_col),
            ),
        )

    def _parse_statement(self) -> Optional[ASTNode]:
        """Parse {% statement %}. Dispatches to specific statement type."""
        token = self._current_token()
        if not token or token.type != TokenType.STATEMENT:
            return None

        # Determine statement type from first word
        parts = token.value.split(None, 1)  # Split on first whitespace
        if not parts:
            self._consume()
            return None

        keyword = parts[0]

        if keyword == "if":
            return self._parse_if()
        elif keyword == "for":
            return self._parse_for()
        elif keyword == "include":
            return self._parse_include()
        elif keyword == "block":
            return self._parse_block()
        elif keyword in ("endif", "endfor", "endblock", "endfunction"):
            # End markers should be handled by caller
            return None
        else:
            # Unknown statement; skip it
            self._consume()
            return None

    def _parse_if(self) -> If:
        """Parse {% if condition %} ... {% elif %} ... {% else %} ... {% endif %}."""
        if_token = self._expect(TokenType.STATEMENT)
        if_start = Position(if_token.start_line, if_token.start_col)

        # Extract condition from "if <condition>"
        condition = if_token.value[2:].strip()

        # Parse body until elif/else/endif
        body = self._parse_body(end_tokens=["elif", "else", "endif"])

        # Parse elif parts
        elif_parts = []
        while self._current_token() and self._current_token().type == TokenType.STATEMENT:
            token = self._current_token()
            if token.value.startswith("elif"):
                self._consume()
                elif_condition = token.value[4:].strip()
                elif_body = self._parse_body(end_tokens=["elif", "else", "endif"])
                elif_parts.append((elif_condition, elif_body))
            else:
                break

        # Parse else
        else_body = None
        if self._current_token() and self._current_token().type == TokenType.STATEMENT:
            token = self._current_token()
            if token.value == "else":
                self._consume()
                else_body = self._parse_body(end_tokens=["endif"])

        # Expect endif
        endif_token = self._expect(TokenType.STATEMENT, "endif")
        endif_end = Position(endif_token.end_line, endif_token.end_col)

        return If(
            condition=condition,
            body=body,
            elif_parts=elif_parts if elif_parts else None,
            else_body=else_body,
            source_range=SourceRange(start=if_start, end=endif_end),
        )

    def _parse_for(self) -> For:
        """Parse {% for var in iterable %} ... {% endfor %}."""
        for_token = self._expect(TokenType.STATEMENT)
        for_start = Position(for_token.start_line, for_token.start_col)

        # Extract "var in iterable" from "for <var> in <iterable>"
        parts = for_token.value[3:].strip().split(" in ", 1)
        if len(parts) != 2:
            raise ParseError(f"Invalid for syntax: {for_token.value!r}", for_token)

        var = parts[0].strip()
        iterable = parts[1].strip()

        # Parse body until endfor
        body = self._parse_body(end_tokens=["endfor"])

        # Expect endfor
        endfor_token = self._expect(TokenType.STATEMENT, "endfor")
        endfor_end = Position(endfor_token.end_line, endfor_token.end_col)

        return For(
            var=var,
            iterable=iterable,
            body=body,
            source_range=SourceRange(start=for_start, end=endfor_end),
        )

    def _parse_include(self) -> Include:
        """Parse {% include "path" %}."""
        include_token = self._expect(TokenType.STATEMENT)
        start = Position(include_token.start_line, include_token.start_col)
        end = Position(include_token.end_line, include_token.end_col)

        # Extract path from "include <path>"
        # Path is typically quoted: "file.tmpl" or 'file.tmpl'
        content = include_token.value[7:].strip()  # Remove "include"

        # Strip quotes if present
        if (content.startswith('"') and content.endswith('"')) or \
           (content.startswith("'") and content.endswith("'")):
            path = content[1:-1]
        else:
            path = content

        return Include(path=path, source_range=SourceRange(start=start, end=end))

    def _parse_block(self) -> Block:
        """Parse {% block name %} ... {% endblock %}."""
        block_token = self._expect(TokenType.STATEMENT)
        block_start = Position(block_token.start_line, block_token.start_col)

        # Extract name from "block <name>"
        name = block_token.value[5:].strip()

        # Parse body until endblock
        body = self._parse_body(end_tokens=["endblock"])

        # Expect endblock
        endblock_token = self._expect(TokenType.STATEMENT, "endblock")
        endblock_end = Position(endblock_token.end_line, endblock_token.end_col)

        return Block(
            name=name,
            body=body,
            source_range=SourceRange(start=block_start, end=endblock_end),
        )


def parse(
    text: str,
    delimiters: Optional[Dict[str, Tuple[str, str]]] = None,
) -> Tuple[List[ASTNode], List[ParseError]]:
    """Convenience function to parse template text into AST."""
    parser = TypedTemplateParser(delimiters)
    return parser.parse(text)
