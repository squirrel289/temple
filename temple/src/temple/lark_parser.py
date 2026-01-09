from lark import Lark, Transformer, v_args
from typing import Any

from .typed_ast import Block, Text, Expression, If, For, Include

GRAMMAR_PATH = __file__.rsplit("/", 1)[0] + "/typed_grammar.lark"


class ToTypedAST(Transformer):
    def text(self, items):
        (t,) = items
        return Text(str(t))

    def expression(self, items):
        (tok,) = items
        # tok is like '{{ user.name }}' -> strip braces
        s = str(tok)
        inner = s.lstrip('{').lstrip('{').rstrip('}').rstrip('}').strip()
        return Expression(inner)

    def if_block(self, items):
        # items: OPEN_IF token, body, optional OPEN_ELSE token + else body, OPEN_ENDIF token
        # find OPEN_IF token to extract condition
        open_if = items[0]
        s = str(open_if)
        # crude parse: find 'if' and take remainder before '%}'
        cond = s.split('if', 1)[1].rsplit('%', 1)[0].strip()
        # body is next
        body = items[1]
        else_body = None
        if len(items) == 4:
            # has else: items[2] is else body
            else_body = items[2]
        return If(cond, body, else_body)

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


__all__ = ["parse_template", "get_parser"]
