from src.temple_linter.template_tokenizer import temple_tokenizer, Token


def tokens_to_tuples(
    tokens: list[Token],
) -> list[tuple[str, str, tuple[int, int], tuple[int, int]]]:
    """Helper to convert tokens to tuples for easier comparison in tests."""
    return [(t.type, t.value, t.start, t.end) for t in tokens]


def test_simple_text():
    text = "hello world"
    tokens = list(temple_tokenizer(text))
    assert tokens_to_tuples(tokens) == [("text", "hello world", (0, 0), (0, 11))]


def test_expression_token():
    text = "foo {{ bar }} baz"
    tokens = list(temple_tokenizer(text))
    assert tokens_to_tuples(tokens) == [
        ("text", "foo ", (0, 0), (0, 4)),
        ("expression", "{{ bar }}", (0, 4), (0, 13)),
        ("text", " baz", (0, 13), (0, 17)),
    ]


def test_statement_token():
    text = "{% if x %}42{% endif %}"
    tokens = list(temple_tokenizer(text))
    assert tokens_to_tuples(tokens) == [
        ("statement", "{% if x %}", (0, 0), (0, 10)),
        ("text", "42", (0, 10), (0, 12)),
        ("statement", "{% endif %}", (0, 12), (0, 23)),
    ]


def test_comment_token():
    text = "foo {# comment #} bar"
    tokens = list(temple_tokenizer(text))
    assert tokens_to_tuples(tokens) == [
        ("text", "foo ", (0, 0), (0, 4)),
        ("comment", "{# comment #}", (0, 4), (0, 17)),
        ("text", " bar", (0, 17), (0, 21)),
    ]


def test_mixed_tokens():
    text = "a{{x}}b{%y%}c{#z#}d"
    tokens = list(temple_tokenizer(text))
    assert tokens_to_tuples(tokens) == [
        ("text", "a", (0, 0), (0, 1)),
        ("expression", "{{x}}", (0, 1), (0, 6)),
        ("text", "b", (0, 6), (0, 7)),
        ("statement", "{%y%}", (0, 7), (0, 12)),
        ("text", "c", (0, 12), (0, 13)),
        ("comment", "{#z#}", (0, 13), (0, 18)),
        ("text", "d", (0, 18), (0, 19)),
    ]


def test_multiline_tokens():
    text = "foo\n{{\nbar\n}}\nbaz"
    tokens = list(temple_tokenizer(text))
    assert tokens_to_tuples(tokens) == [
        ("text", "foo\n", (0, 0), (1, 0)),
        ("expression", "{{\nbar\n}}", (1, 0), (3, 2)),
        ("text", "\nbaz", (3, 2), (4, 3)),
    ]


def test_unclosed_token():
    text = "foo {{ bar "
    tokens = list(temple_tokenizer(text))
    # Should treat the whole as text since no closing '}}'
    assert tokens_to_tuples(tokens) == [("text", "foo {{ bar ", (0, 0), (0, 12))]


def test_empty_string():
    tokens = list(temple_tokenizer(""))
    assert tokens == []


def test_only_token():
    text = "{{foo}}"
    tokens = list(temple_tokenizer(text))
    assert tokens_to_tuples(tokens) == [("expression", "{{foo}}", (0, 0), (0, 7))]
