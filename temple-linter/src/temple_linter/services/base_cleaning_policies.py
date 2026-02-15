"""Base-cleaning policy adapters for language-specific lint compatibility."""

from __future__ import annotations

import re

from temple.template_spans import TemplateTokenSpan

from .base_cleaning_contract import BaseCleaningContract

_ATX_MULTI_SPACE_RE = re.compile(r"^(#{1,6})\s{2,}")
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")


def apply_markdown_policy(contract: BaseCleaningContract) -> BaseCleaningContract:
    """Apply markdown-specific post-processing on top of base-cleaning contract."""
    line_metadata = contract.line_metadata
    if not line_metadata:
        return contract

    template_tokens_by_line = _group_template_tokens_by_line(
        contract.token_spans,
        len(line_metadata),
    )
    cleaned_lines = contract.cleaned_text.splitlines(keepends=True)
    if len(cleaned_lines) != len(line_metadata):
        return contract

    rewritten: list[str] = []
    for line, line_info in enumerate(line_metadata):
        masked_line = cleaned_lines[line]

        if not line_info.has_template_token:
            rewritten.append(masked_line)
            continue
        if line_info.is_template_only:
            rewritten.append(masked_line)
            continue

        core_rewritten = _rewrite_markdown_mixed_line(
            contract.original_text,
            line_info.start_offset,
            line_info.end_offset,
            template_tokens_by_line.get(line, []),
        )
        core_rewritten = _MULTI_SPACE_RE.sub(" ", core_rewritten).rstrip()
        core_rewritten = _ATX_MULTI_SPACE_RE.sub(r"\1 ", core_rewritten)

        if core_rewritten.strip() == "":
            rewritten.append(line_info.line_ending)
        else:
            rewritten.append(core_rewritten + line_info.line_ending)

    return BaseCleaningContract(
        original_text=contract.original_text,
        cleaned_text="".join(rewritten),
        token_spans=contract.token_spans,
        line_metadata=contract.line_metadata,
    )


def _group_template_tokens_by_line(
    token_spans: tuple[TemplateTokenSpan, ...],
    line_count: int,
) -> dict[int, list[TemplateTokenSpan]]:
    grouped: dict[int, list[TemplateTokenSpan]] = {}
    for span in token_spans:
        if span.token.type == "text":
            continue
        start_line = max(span.token.start[0], 0)
        end_line = min(span.token.end[0], line_count - 1)
        if span.token.end[0] > span.token.start[0] and span.token.end[1] == 0:
            end_line = max(start_line, end_line - 1)
        for line in range(start_line, end_line + 1):
            grouped.setdefault(line, []).append(span)

    for spans in grouped.values():
        spans.sort(key=lambda item: item.start_offset)
    return grouped


def _rewrite_markdown_mixed_line(
    original_text: str,
    line_start: int,
    line_end: int,
    template_spans: list[TemplateTokenSpan],
) -> str:
    if not template_spans:
        return original_text[line_start:line_end]

    parts: list[str] = []
    cursor = line_start
    for span in template_spans:
        token_start = max(span.start_offset, line_start)
        token_end = min(span.end_offset, line_end)
        if token_end <= token_start:
            continue

        if cursor < token_start:
            parts.append(original_text[cursor:token_start])

        if span.token.type == "expression":
            parts.append(" lorem ")
        cursor = max(cursor, token_end)

    if cursor < line_end:
        parts.append(original_text[cursor:line_end])
    return "".join(parts)
