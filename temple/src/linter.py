"""
temple/linter.py
Linter for template syntax and logic errors.
"""

from typing import List, Dict, Optional
from .parser import TemplateParser, TemplateToken


class LintError:
    def __init__(self, message: str, token: Optional[TemplateToken] = None):
        self.message = message
        self.token = token

    def __repr__(self):
        loc = f" @ {self.token.start}-{self.token.end}" if self.token else ""
        return f"LintError: {self.message}{loc}"


class TemplateLinter:
    """
    Lints template syntax and logic errors only.
    For base format linting, use temple-linter and import temple.src.template_preprocessing.
    """

    def __init__(self, delimiters: Optional[Dict[str, str]] = None):
        self.parser = TemplateParser(delimiters)

    def lint(self, template: str) -> List[LintError]:
        tokens = self.parser.parse(template)
        errors: List[LintError] = []
        stack: List[str] = []
        # Syntax checks for statements
        for t in tokens:
            if t.type == "statement":
                stmt = t.value.split()
                if not stmt:
                    errors.append(LintError("Empty statement block", t))
                    continue
                if stmt[0] in {"if", "for", "function"}:
                    stack.append(stmt[0])
                elif stmt[0] in {"endif", "endfor", "endfunction"}:
                    if not stack or not stmt[0][3:] == stack[-1]:
                        errors.append(LintError(f"Unmatched {stmt[0]}", t))
                    else:
                        stack.pop()
                elif stmt[0] == "elif" and (not stack or stack[-1] != "if"):
                    errors.append(LintError("'elif' outside of 'if' block", t))
                elif stmt[0] == "else" and (not stack or stack[-1] != "if"):
                    errors.append(LintError("'else' outside of 'if' block", t))
            elif t.type == "expression":
                # Basic logic: check for empty expressions
                if not t.value:
                    errors.append(LintError("Empty expression block", t))
        if stack:
            errors.append(LintError(f"Unclosed block(s): {', '.join(stack)}"))
        return errors


# Example usage:
if __name__ == "__main__":
    linter = TemplateLinter()
    valid = """
    {% if user.name %}
    ## {{ user.name }}
    {% endif %}
    {% for job in user.jobs %}
    ### {{ job.title }} at {{ job.company }}
    - {{ job.start }} - {{ job.end }}
    {% endfor %}
    """
    invalid = """
    {% if user.name %}
    ## {{ user.name }}
    {% for job in user.jobs %}
    ### {{ job.title }} at {{ job.company }}
    - {{ job.start }} - {{ job.end }}
    {% endfor %}
    """  # missing endif
    print("Valid template lint results:")
    for err in linter.lint(valid):
        print(err)
    print("\nInvalid template lint results:")
    for err in linter.lint(invalid):
        print(err)
