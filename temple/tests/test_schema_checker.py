from temple.typed_ast import ObjectNode, Expression, Array
from temple.typed_renderer import evaluate_ast
from temple.schema_checker import validate


def test_schema_missing_required_property():
    # build AST with start positions for mapping
    obj = ObjectNode([
        ("skills", Array([Expression("user.skills", start=(2, 1))], start=(2, 1)))
    ], start=(1, 0))
    ctx = {"user": {"skills": ["a", "b"]}}
    res = evaluate_ast(obj, ctx)

    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "skills": {"type": "array", "items": {"type": "string"}},
        },
    }
    diags = validate(res.ir, schema, mapping=res.mapping)
    assert any(d["path"].endswith("/name") for d in diags)


def test_schema_type_mismatch():
    obj = ObjectNode([
        ("name", Expression("user.name", start=(1, 2))),
    ], start=(1, 0))
    ctx = {"user": {"name": 123}}
    res = evaluate_ast(obj, ctx)
    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    diags = validate(res.ir, schema, mapping=res.mapping)
    assert any("expected string" in d["message"] for d in diags)
