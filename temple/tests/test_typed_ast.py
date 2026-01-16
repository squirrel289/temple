import json

from temple.typed_ast import Block, Text, Expression, For
from temple.typed_renderer import evaluate_ast, json_serialize, markdown_serialize


def test_basic_expression_and_text():
    root = Block([Text("Hi "), Expression("user.name")])
    ctx = {"user": {"name": "Bob"}}
    res = evaluate_ast(root, ctx)
    assert res.ir == ["Hi ", "Bob"]
    js = json_serialize(res.ir)
    assert json.loads(js) == ["Hi ", "Bob"]


def test_for_loop_and_markdown():
    root = Block([
        Text("List:"),
        For("x", "items", Block([Text("- "), Expression("x")])),
    ])
    ctx = {"items": ["a", "b"]}
    res = evaluate_ast(root, ctx)
    # flattened list contains dash prefixes and items
    assert res.ir[0] == "List:"
    assert "a" in res.ir and "b" in res.ir
    md = markdown_serialize(res.ir)
    assert "List:" in md and "a" in md and "b" in md

# precommit test

# precommit test

# precommit test
