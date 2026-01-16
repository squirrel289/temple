import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from temple_linter.template_preprocessing import (
    strip_template_tokens,
    _compile_strip_pattern,
)


def test_strip_default_delimiters():
    text = "Hello {% if user %}{{ user.name }}{% end %}"
    result = strip_template_tokens(text)
    assert result == "Hello "


def test_strip_custom_delimiters():
    text = "Hello << if user >><: user.name :><< end >>"
    delims = {
        "statement": ("<<", ">>"),
        "expression": ("<:", ":>"),
        "comment": ("<#", "#>"),
    }
    result = strip_template_tokens(text, delimiters=delims)
    assert result == "Hello "


def test_strip_with_replacement():
    text = "Hello {% if user %}{{ user.name }}{% end %}"
    result = strip_template_tokens(text, replace_with="[REDACTED]")
    assert result == "Hello [REDACTED][REDACTED][REDACTED]"


def test_pattern_caching():
    """Test that regex patterns are cached for same delimiter configuration."""
    # Clear cache to start fresh
    _compile_strip_pattern.cache_clear()
    assert _compile_strip_pattern.cache_info().hits == 0
    assert _compile_strip_pattern.cache_info().misses == 0

    # First call with default delimiters - cache miss
    text1 = "{{ x }}"
    result1 = strip_template_tokens(text1)
    assert result1 == ""
    assert _compile_strip_pattern.cache_info().misses == 1
    assert _compile_strip_pattern.cache_info().hits == 0

    # Second call with same delimiters - cache hit
    text2 = "{% if y %}{% end %}"
    result2 = strip_template_tokens(text2)
    assert result2 == ""
    assert _compile_strip_pattern.cache_info().hits == 1
    assert _compile_strip_pattern.cache_info().misses == 1

    # Third call with custom delimiters - cache miss
    custom_delims = {
        "statement": ("<<", ">>"),
        "expression": ("<:", ":>"),
        "comment": ("<#", "#>"),
    }
    text3 = "<: foo :>"
    result3 = strip_template_tokens(text3, delimiters=custom_delims)
    assert result3 == ""
    assert _compile_strip_pattern.cache_info().misses == 2
    assert _compile_strip_pattern.cache_info().hits == 1

    # Fourth call with custom delimiters again - cache hit
    text4 = "<< bar >>"
    result4 = strip_template_tokens(text4, delimiters=custom_delims)
    assert result4 == ""
    assert _compile_strip_pattern.cache_info().hits == 2
    assert _compile_strip_pattern.cache_info().misses == 2

    # Fifth call back to default delimiters - cache hit (pattern still cached)
    text5 = "{{ x }}"
    result5 = strip_template_tokens(text5)
    assert result5 == ""
    assert _compile_strip_pattern.cache_info().hits == 3
    assert _compile_strip_pattern.cache_info().misses == 2
