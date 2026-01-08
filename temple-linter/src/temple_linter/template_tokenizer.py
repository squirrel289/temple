from typing import Iterator, Optional, Tuple, Literal

TokenType = Literal["text", "statement", "expression", "comment"]


class Token:
    def __init__(
        self,
        raw_token: str,
        start: Tuple[int, int],
        delimiters: Optional[dict[TokenType, tuple[str, str]]] = None,
    ):
        self.raw_token = raw_token
        self.start = start
        self.delimiters = delimiters or {
            "statement": ("{%", "%}"),
            "expression": ("{{", "}}"),
            "comment": ("{#", "#}"),
        }
        self.type, self.value, self.delimiter_start, self.delimiter_end = (
            self._parse_type_and_value()
        )
        self.end = self._compute_end()

    def _parse_type_and_value(self):
        for ttype, (start_delim, end_delim) in self.delimiters.items():
            if self.raw_token.startswith(start_delim) and self.raw_token.endswith(
                end_delim
            ):
                value = self.raw_token[len(start_delim) : -len(end_delim)].strip()
                return ttype, value, start_delim, end_delim
        # Default to text
        return "text", self.raw_token, None, None

    def _compute_end(self):
        line, col = self.start
        for c in self.raw_token:
            if c == "\n":
                line += 1
                col = 0
            else:
                col += 1
        return (line, col)

    def __repr__(self):
        return f"Token(type={self.type!r}, value={self.value!r}, start={self.start}, end={self.end}, delimiters=({self.delimiter_start!r},{self.delimiter_end!r}))"


def temple_tokenizer(
    text: str,
    delimiters: Optional[dict[TokenType, tuple[str, str]]] = None,
) -> Iterator[Token]:
    """
    Yields Token objects for text, statement, expression, and comment regions.
    Supports custom delimiters.
    
    TODO: Add regex pattern caching for performance (recompiles on every call)
    See ARCHITECTURE_ANALYSIS.md Work Item #4 for implementation plan
    """
    import re

    # Default delimiters (Jinja-like)
    delims = delimiters or {
        "statement": ("{%", "%}"),
        "expression": ("{{", "}}"),
        "comment": ("{#", "#}"),
    }
    # Build regex pattern with capture groups for each token type
    pattern_parts: list[str] = []
    for ttype, (start, end) in delims.items():
        pattern_parts.append(f"(?P<{ttype}>{re.escape(start)}.*?{re.escape(end)})")
    combined_pattern = "|".join(pattern_parts)
    token_pattern = re.compile(combined_pattern, re.DOTALL)
    pos = 0
    line = 0
    col = 0
    while pos < len(text):
        m = token_pattern.search(text, pos)
        if not m:
            # Remaining text is plain text
            value = text[pos:]
            if value:
                yield Token(value, (line, col), delimiters)
            break
        # Text before token
        if m.start() > pos:
            value = text[pos : m.start()]
            yield Token(value, (line, col), delimiters)
            line, col = _advance((line, col), value)
        # Token itself
        for ttype in delims.keys():
            if m.group(ttype):
                raw_token = m.group(ttype)
                yield Token(raw_token, (line, col), delimiters)
                line, col = _advance((line, col), raw_token)
                break
        pos = m.end()


def _advance(start: Tuple[int, int], value: str) -> Tuple[int, int]:
    """Advance (line, col) by value."""
    line, col = start
    for c in value:
        if c == "\n":
            line += 1
            col = 0
        else:
            col += 1
    return (line, col)
