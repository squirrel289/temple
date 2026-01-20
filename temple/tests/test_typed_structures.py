from temple.typed_ast import ObjectNode, Array, Expression
from temple.typed_renderer import evaluate_ast, json_serialize


def test_object_and_array_serialization():
    obj = ObjectNode(
        [
            ("name", Expression("user.name")),
            ("skills", Array([Expression("user.skills")])),
        ]
    )
    ctx = {"user": {"name": "Alice", "skills": ["Python", "Templating"]}}
    res = evaluate_ast(obj, ctx)
    assert isinstance(res.ir, dict)
    assert res.ir["name"] == "Alice"
    assert isinstance(res.ir["skills"], list)
    assert "Python" in res.ir["skills"]
    # JSON serialize
    js = json_serialize(res.ir)
    assert "Alice" in js
