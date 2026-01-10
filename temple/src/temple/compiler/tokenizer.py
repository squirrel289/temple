"""
temple.compiler.tokenizer
Lexical analysis with position tracking for typed template DSL.

Tokenizes template content into:
- Text: Raw content outside DSL tokens
- Statement: {% ... %} control flow
- Expression: {{ ... }} variable insertion
- Comment: {# ... #} (ignored)
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List, Iterator
import re


class TokenType(Enum):
    """Token type enumeration."""
    TEXT = "text"
    STATEMENT = "statement"  # {% ... %}
    EXPRESSION = "expression"  # {{ ... }}
    COMMENT = "comment"  # {# ... #}
    EOF = "eof"


@dataclass
class Token:
    """Single lexical token with position information."""
    type: TokenType
    value: str  # Content (stripped of delimiters for statements/expressions)
    raw: str  # Raw content including delimiters
    start_line: int
    start_col: int
    end_line: int
    end_col: int

    def __repr__(self) -> str:
        return f"Token({self.type.value}, {self.value!r}, ({self.start_line},{self.start_col})-({self.end_line},{self.end_col}))"


class Tokenizer:
    """Lexer for typed template DSL with configurable delimiters."""

    def __init__(
        self,
        delimiters: Optional[Dict[str, Tuple[str, str]]] = None,
    ):
        """Initialize tokenizer with optional custom delimiters.
        
        Args:
            delimiters: Dict mapping token type to (start, end) delimiters.
                Default: {
                    'statement': ('{%', '%}'),
                    'expression': ('{{', '}}'),
                    'comment': ('{#', '#}'),
                }
        """
        self.delimiters = delimiters or {
            "statement": ("{%", "%}"),
            "expression": ("{{", "}}"),
            "comment": ("{#", "#}"),
        }
        self._build_pattern()

    def _build_pattern(self) -> None:
        """Build compiled regex pattern for all token types."""
        patterns = []
        for token_type, (start, end) in self.delimiters.items():
            escaped_start = re.escape(start)
            escaped_end = re.escape(end)
            # Use non-greedy match: start.*?end
            pattern = f"(?P<{token_type}>{escaped_start}.*?{escaped_end})"
            patterns.append(pattern)
        
        # Combine all patterns with alternation
        combined = "|".join(patterns)
        self.pattern = re.compile(combined, re.DOTALL)

    def tokenize(self, text: str) -> List[Token]:
        """Tokenize template text. Returns list of tokens in order."""
        tokens = []
        pos = 0
        line = 0
        col = 0

        while pos < len(text):
            # Find next token
            match = self.pattern.search(text, pos)
            
            if not match:
                # Remaining text is plain text
                if pos < len(text):
                    raw_text = text[pos:]
                    tokens.append(
                        Token(
                            type=TokenType.TEXT,
                            value=raw_text,
                            raw=raw_text,
                            start_line=line,
                            start_col=col,
                            end_line=line + raw_text.count("\n"),
                            end_col=self._advance_col(raw_text, col),
                        )
                    )
                break

            # Text before token
            if match.start() > pos:
                text_before = text[pos : match.start()]
                tokens.append(
                    Token(
                        type=TokenType.TEXT,
                        value=text_before,
                        raw=text_before,
                        start_line=line,
                        start_col=col,
                        end_line=line + text_before.count("\n"),
                        end_col=self._advance_col(text_before, col),
                    )
                )
                line, col = self._advance(line, col, text_before)

            # Process matched token
            raw_token = match.group(0)
            token_start_line = line
            token_start_col = col

            # Determine token type
            token_type = None
            token_value = None
            for ttype in self.delimiters.keys():
                if match.group(ttype):
                    token_type = TokenType(ttype)
                    start_delim, end_delim = self.delimiters[ttype]
                    # Strip delimiters and whitespace
                    token_value = raw_token[len(start_delim) : -len(end_delim)].strip()
                    break

            if token_type:
                tokens.append(
                    Token(
                        type=token_type,
                        value=token_value,
                        raw=raw_token,
                        start_line=token_start_line,
                        start_col=token_start_col,
                        end_line=token_start_line + raw_token.count("\n"),
                        end_col=self._advance_col(raw_token, token_start_col),
                    )
                )

            # Advance position
            line, col = self._advance(line, col, raw_token)
            pos = match.end()

        return tokens

    @staticmethod
    def _advance(line: int, col: int, text: str) -> Tuple[int, int]:
        """Advance line/col by text content."""
        for char in text:
            if char == "\n":
                line += 1
                col = 0
            else:
                col += 1
        return line, col

    @staticmethod
    def _advance_col(text: str, start_col: int) -> int:
        """Get ending column after text (assume no newlines crossed)."""
        # If text has newlines, this won't work correctly
        # Use _advance() instead for general case
        lines = text.split("\n")
        if len(lines) > 1:
            # Text has newlines; end col is length of last line
            return len(lines[-1])
        return start_col + len(text)


def tokenize(
    text: str,
    delimiters: Optional[Dict[str, Tuple[str, str]]] = None,
) -> List[Token]:
    """Convenience function to tokenize template text."""
    tokenizer = Tokenizer(delimiters)
    return tokenizer.tokenize(text)
