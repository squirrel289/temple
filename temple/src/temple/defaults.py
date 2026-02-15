"""Shared Temple defaults used across tokenizer/parser/linter integrations."""

from __future__ import annotations

from typing import Final

DEFAULT_TEMPLATE_DELIMITERS: Final[dict[str, tuple[str, str]]] = {
    "statement": ("{%", "%}"),
    "expression": ("{{", "}}"),
    "comment": ("{#", "#}"),
}

DEFAULT_TEMPLE_EXTENSIONS: Final[tuple[str, ...]] = (".tmpl", ".template")
