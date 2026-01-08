"""
temple/parser.py
Template parser for base formats (Markdown, HTML, JSON) with DSL overlays.

NOTE: This is a REFERENCE IMPLEMENTATION matching the authoritative implementation
in temple-linter/src/temple_linter/template_tokenizer.py

Token Model: Uses (line, col) tuples for positions (0-indexed)
- line: 0-indexed line number
- col: 0-indexed column number within line
- Tuples enable accurate error reporting and diagnostic mapping
"""

import re
from typing import List, Dict, Optional, Tuple


class TemplateToken:
    """
    Template token with (line, col) position tracking.
    
    Position Semantics (0-indexed):
    - line: Line number starting from 0
    - col: Column number within line starting from 0
    - Both start and end positions are inclusive
    
    Example: "foo\nbar" with token "bar" at line 1, col 0
    """
    def __init__(self, type_: str, value: str, start: Tuple[int, int], end: Tuple[int, int]):
        self.type = type_  # 'base', 'statement', 'expression', 'comment'
        self.value = value
        self.start = start  # (line, col) tuple
        self.end = end      # (line, col) tuple

    def __repr__(self):
        return f"<Token {self.type}: {self.value[:30]!r} @ {self.start}-{self.end}>"


class TemplateParser:
    def __init__(self, delimiters: Optional[Dict[str, str]] = None):
        # Default delimiters
        self.delimiters = delimiters or {
            "statement_start": "{%",
            "statement_end": "%}",
            "expression_start": "{{",
            "expression_end": "}}",
            "comment_start": "{#",
            "comment_end": "#}",
        }
        # Require all 6 delimiters to be distinct for robust parsing
        delimiter_keys = [
            "statement_start",
            "statement_end",
            "expression_start",
            "expression_end",
            "comment_start",
            "comment_end",
        ]
        values = [self.delimiters[k] for k in delimiter_keys]
        if len(set(values)) != 6:
            raise ValueError(
                "All statement, expression, and comment start/end delimiters must be distinct for correct parsing."
            )
        self._compile_patterns()

    def _compile_patterns(self):
        d = self.delimiters
        self.patterns = {
            "statement": re.compile(
                re.escape(d["statement_start"])
                + r"(.*?)"
                + re.escape(d["statement_end"]),
                re.DOTALL,
            ),
            "expression": re.compile(
                re.escape(d["expression_start"])
                + r"(.*?)"
                + re.escape(d["expression_end"]),
                re.DOTALL,
            ),
            "comment": re.compile(
                re.escape(d["comment_start"]) + r"(.*?)" + re.escape(d["comment_end"]),
                re.DOTALL,
            ),
        }

    def tokenize(self, template: str) -> List[TemplateToken]:
        """Tokenize template into base and DSL logic tokens with (line, col) positions."""
        tokens: List[TemplateToken] = []
        pos = 0
        line = 0
        col = 0
        
        while pos < len(template):
            # Find next DSL token
            matches = [
                (typ, pat.search(template, pos)) for typ, pat in self.patterns.items()
            ]
            matches = [(typ, m) for typ, m in matches if m]
            if not matches:
                # Remaining content is base text
                value = template[pos:]
                start_pos = (line, col)
                end_pos = self._advance_position((line, col), value)
                tokens.append(TemplateToken("base", value, start_pos, end_pos))
                break
            
            # Find earliest match
            typ, m = min(matches, key=lambda x: x[1].start())
            
            # Base text before DSL token
            if m.start() > pos:
                value = template[pos : m.start()]
                start_pos = (line, col)
                end_pos = self._advance_position((line, col), value)
                tokens.append(TemplateToken("base", value, start_pos, end_pos))
                line, col = end_pos
            
            # DSL token itself
            value = m.group(1).strip()
            raw_token = template[m.start() : m.end()]
            start_pos = (line, col)
            end_pos = self._advance_position((line, col), raw_token)
            tokens.append(TemplateToken(typ, value, start_pos, end_pos))
            line, col = end_pos
            pos = m.end()
            
        return tokens
    
    def _advance_position(self, start: Tuple[int, int], value: str) -> Tuple[int, int]:
        """Advance (line, col) position by processing value string."""
        line, col = start
        for c in value:
            if c == "\n":
                line += 1
                col = 0
            else:
                col += 1
        return (line, col)

    def parse(self, template: str) -> List[TemplateToken]:
        """Parse template and return token list (AST nodes)."""
        return self.tokenize(template)


# Example usage:
if __name__ == "__main__":
    parser = TemplateParser()
    example = """
    # Resume
    {% if user.name %}
    ## {{ user.name }}
    {% endif %}
    {% for job in user.jobs %}
    ### {{ job.title }} at {{ job.company }}
    - {{ job.start }} - {{ job.end }}
    {% endfor %}
    """
    tokens = parser.parse(example)
    for t in tokens:
        print(t)
