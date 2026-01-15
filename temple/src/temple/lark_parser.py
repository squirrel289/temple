from lark import Lark, Transformer, v_args
from lark.exceptions import UnexpectedInput, UnexpectedToken, UnexpectedCharacters
from typing import Any, Tuple, List
import re

from .typed_ast import Block, Text, Expression, If, For, Include
from .diagnostics import Diagnostic, DiagnosticSeverity, DiagnosticCollector, Position, SourceRange

GRAMMAR_PATH = __file__.rsplit("/", 1)[0] + "/typed_grammar.lark"


def validate_expression_syntax(expr: str) -> Tuple[bool, str]:
    """Validate expression syntax (dot notation, identifiers).
    
    Returns:
        (is_valid, error_message)
    """
    if not expr or expr.isspace():
        return True, ""  # Empty expressions are allowed
    
    # Check for trailing dot
    if expr.endswith('.'):
        return False, "Expression ends with trailing dot"
    
    # Check for leading dot
    if expr.startswith('.'):
        return False, "Expression starts with leading dot"
    
    # Check for consecutive dots
    if '..' in expr:
        return False, "Expression contains consecutive dots"
    
    # Check for empty segments between dots
    parts = expr.split('.')
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            return False, f"Expression has empty segment at position {i}"
        
        # Each part should be a valid identifier (alphanumeric + underscore) or array index
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', part) and not part.isdigit():
            return False, f"Invalid identifier '{part}' in expression"
    
    return True, ""


class ToTypedAST(Transformer):
    def text(self, items):
        (t,) = items
        return Text(str(t))

    def expression(self, items):
        (tok,) = items
        # tok is like '{{ user.name }}' -> strip braces
        s = str(tok)
        inner = s.lstrip('{').lstrip('{').rstrip('}').rstrip('}').strip()
        
        # Validate expression syntax
        is_valid, error_msg = validate_expression_syntax(inner)
        if not is_valid:
            # Store validation error for later collection
            # We'll collect these in parse_with_diagnostics
            expr_node = Expression(inner)
            expr_node._validation_error = error_msg
            return expr_node
        
        return Expression(inner)

    def if_block(self, items):
        # items: OPEN_IF token, body, optional else_if_chain (list), optional (OPEN_ELSE, block), OPEN_END token
        open_if = items[0]
        s = str(open_if)
        # crude parse: find 'if' and take remainder before '%}'
        cond = s.split('if', 1)[1].rsplit('%', 1)[0].strip()
        body = items[1]
        idx = 2
        elif_parts = []
        else_body = None

        # optional else_if_chain -> transformer returns a list of (cond, body)
        if idx < len(items) and isinstance(items[idx], list):
            elif_parts = items[idx]
            idx += 1

        # optional OPEN_ELSE followed by else body
        # Check if next item is a token (OPEN_ELSE), skip it and get the Block after
        if idx < len(items):
            next_item = items[idx]
            # If it's a string token (OPEN_ELSE or OPEN_END)
            if isinstance(next_item, str):
                # Check if it's OPEN_ELSE
                if 'else' in str(next_item).lower() and 'if' not in str(next_item).lower():
                    idx += 1  # Skip OPEN_ELSE
                    # Next should be the else body Block
                    if idx < len(items) and isinstance(items[idx], Block):
                        else_body = items[idx]
                        idx += 1
            # If it's a Block directly (shouldn't happen with current grammar, but be defensive)
            elif isinstance(next_item, Block):
                else_body = next_item
                idx += 1

        # Validate OPEN_END token
        if idx < len(items):
            end_token = items[idx]
            # end_token should be the OPEN_END string; no validation needed since grammar ensures it

        return If(cond, body, elif_parts if elif_parts else None, else_body)

    def else_if_chain(self, items):
        # items: OPEN_ELSE_IF, block, OPEN_ELSE_IF, block, ...
        parts = []
        i = 0
        while i < len(items):
            open_tok = items[i]
            body = items[i + 1] if i + 1 < len(items) else None
            s = str(open_tok)
            # Extract condition from `{% else if <condition> %}`
            cond = s.split('if', 1)[1].rsplit('%', 1)[0].strip()
            parts.append((cond, body))
            i += 2
        return parts

    def for_block(self, items):
        open_for = items[0]
        s = str(open_for)
        # crude parse: 'for var in iterable' extract var and iterable
        inner = s.lstrip('{').lstrip('%').rstrip('%').rstrip('}').strip()
        # inner like 'for x in items'
        parts = inner.split()
        try:
            idx_for = parts.index('for')
        except ValueError:
            idx_for = 0
        # find 'in'
        if 'in' in parts:
            i = parts.index('in')
            var = parts[idx_for + 1]
            iterable = parts[i + 1]
        else:
            var = parts[idx_for + 1] if len(parts) > idx_for + 1 else ''
            iterable = parts[idx_for + 2] if len(parts) > idx_for + 2 else ''
        body = items[1]
        # Validate OPEN_END token (items[2])
        return For(var, iterable, body)

    def include(self, items):
        (tok,) = items
        s = str(tok)
        # crude parse: find the quoted name inside include tag
        # e.g. "{% include 'footer' %}" or {% include "footer" %}
        import re

        m = re.search(r"include\s+['\"]([^'\"]+)['\"]", s)
        name = m.group(1) if m else s
        return Include(name)

    def block(self, items):
        nodes = []
        for it in items:
            if it is None:
                continue
            nodes.append(it)
        return Block(nodes)

    def NAME_PATH(self, tk):
        return tk.value

    def NAME(self, tk):
        return tk.value

    def TEXT(self, tk):
        return tk.value


def get_parser() -> Lark:
    with open(GRAMMAR_PATH, "r") as f:
        grammar = f.read()
    return Lark(grammar, start="start", parser="lalr")


def parse_template(text: str) -> Block:
    """Parse template text and return AST.
    
    Args:
        text: Template source text
        
    Returns:
        Parsed Block AST
        
    Raises:
        UnexpectedInput: On syntax errors (use parse_with_diagnostics for error collection)
    """
    parser = get_parser()
    tree = parser.parse(text)
    transformer = ToTypedAST()
    res = transformer.transform(tree)
    # Unwrap top-level Tree that contains a single Block
    try:
        from lark import Tree
        if isinstance(res, Tree) and len(res.children) == 1 and isinstance(res.children[0], Block):
            return res.children[0]
    except Exception:
        pass
    return res


def parse_with_diagnostics(text: str) -> Tuple[Block, List[Diagnostic]]:
    """Parse template text and collect diagnostics.
    
    Args:
        text: Template source text
        
    Returns:
        Tuple of (AST, diagnostics list). AST may be partial if errors occurred.
        
    Example:
        >>> ast, diagnostics = parse_with_diagnostics("{% if x %}{{ user.name }}")
        >>> len(diagnostics) > 0  # Missing {% end %}
        True
    """
    collector = DiagnosticCollector()
    ast = None
    
    # First, scan for expression syntax errors directly from text
    # This allows us to catch them even if parsing fails
    import re
    expr_pattern = r'\{\{(.*?)\}\}'
    for match in re.finditer(expr_pattern, text, re.DOTALL):
        expr_text = match.group(1).strip()
        is_valid, error_msg = validate_expression_syntax(expr_text)
        if not is_valid:
            # Calculate position
            start_offset = match.start()
            lines_before = text[:start_offset].count('\n')
            line_start = text.rfind('\n', 0, start_offset) + 1
            col = start_offset - line_start
            
            collector.add_error(
                f"Invalid expression syntax: {error_msg}",
                SourceRange(Position(lines_before, col), Position(lines_before, col + len(match.group()))),
                code="INVALID_EXPRESSION"
            )
    
    try:
        ast = parse_template(text)
        return ast, collector.diagnostics
    except UnexpectedToken as e:
        # Extract position from Lark exception
        line = e.line - 1  # Lark uses 1-indexed, convert to 0-indexed
        column = e.column - 1 if e.column else 0
        
        # Build helpful error message
        expected = ', '.join(e.expected) if e.expected else 'valid token'
        message = f"Unexpected token '{e.token}'. Expected {expected}"
        
        source_range = SourceRange(
            Position(line, column),
            Position(line, column + len(str(e.token)))
        )
        
        collector.add_error(message, source_range, code="UNEXPECTED_TOKEN")
        
        # Return partial AST (empty block)
        return Block([]), collector.diagnostics
        
    except UnexpectedCharacters as e:
        line = e.line - 1
        column = e.column - 1 if e.column else 0
        
        message = f"Unexpected character at position {line + 1}:{column + 1}"
        if e.allowed:
            message += f". Expected one of: {', '.join(e.allowed)}"
        
        source_range = SourceRange(
            Position(line, column),
            Position(line, column + 1)
        )
        
        collector.add_error(message, source_range, code="UNEXPECTED_CHARACTER")
        return Block([]), collector.diagnostics
        
    except UnexpectedInput as e:
        # Generic parse error
        line = getattr(e, 'line', 1) - 1
        column = getattr(e, 'column', 1) - 1
        
        message = f"Syntax error: {str(e)}"
        source_range = SourceRange(
            Position(line, column),
            Position(line, column + 1)
        )
        
        collector.add_error(message, source_range, code="SYNTAX_ERROR")
        return Block([]), collector.diagnostics
        
    except Exception as e:
        # Catch-all for unexpected errors
        message = f"Parser error: {str(e)}"
        source_range = SourceRange(Position(0, 0), Position(0, 0))
        collector.add_error(message, source_range, code="PARSER_ERROR")
        return Block([]), collector.diagnostics


__all__ = ["parse_template", "parse_with_diagnostics", "get_parser"]
