"""
temple/parser.py
Template parser for base formats (Markdown, HTML, JSON) with DSL overlays.

NOTE: This is a REFERENCE IMPLEMENTATION for specification purposes.
The authoritative implementation is in temple-linter/src/temple_linter/template_tokenizer.py
which uses (line, col) tuples for better error reporting.

TODO: Unify token models across temple and temple-linter
See ARCHITECTURE_ANALYSIS.md Work Item #3
"""

import re
from typing import List, Dict, Optional


class TemplateToken:
    def __init__(self, type_: str, value: str, start: int, end: int):
        self.type = type_  # 'base', 'statement', 'expression', 'comment'
        self.value = value
        self.start = start
        self.end = end

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
        """Tokenize template into base and DSL logic tokens."""
        tokens: List[TemplateToken] = []
        pos = 0
        while pos < len(template):
            # Find next DSL token
            matches = [
                (typ, pat.search(template, pos)) for typ, pat in self.patterns.items()
            ]
            matches = [(typ, m) for typ, m in matches if m]
            if not matches:
                tokens.append(TemplateToken("base", template[pos:], pos, len(template)))
                break
            # Find earliest match
            typ, m = min(matches, key=lambda x: x[1].start())
            if m.start() > pos:
                tokens.append(
                    TemplateToken("base", template[pos : m.start()], pos, m.start())
                )
            tokens.append(TemplateToken(typ, m.group(1).strip(), m.start(), m.end()))
            pos = m.end()
        return tokens

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
