"""TokenCleaningService - Strips template tokens for base format linting."""

from __future__ import annotations

import re

from temple.template_tokenizer import Token, temple_tokenizer
from temple.whitespace_control import apply_left_trim, trim_leading_whitespace

_INLINE_TEMPLATE_TOKEN_RE = re.compile(r"\{#.*?#\}|\{%.*?%\}|\{\{.*?\}\}")
_ATX_MULTI_SPACE_RE = re.compile(r"^(#{1,6})\s{2,}")


class TokenCleaningService:
    """
    Service responsible for stripping template tokens and tracking text positions.

    This service:
    - Tokenizes template content
    - Replaces DSL tokens with whitespace placeholders
    - Preserves line/column offsets for base-linter diagnostics
    """

    def clean_text_and_tokens(
        self,
        text: str,
        format_hint: str | None = None,
    ) -> tuple[str, list[Token]]:
        """
        Strip template tokens and return cleaned text with position tracking.

        Args:
            text: Original template content

        Returns:
            Tuple of (cleaned_text, text_tokens)
            - cleaned_text: Content with all DSL tokens removed
            - text_tokens: List of text Token objects for position mapping
        """
        cleaned_chars: list[str] = []
        trim_next_text_left = False

        for token in temple_tokenizer(text):
            if token.type == "text":
                text_value = token.value
                if trim_next_text_left:
                    text_value = trim_leading_whitespace(text_value)
                    trim_next_text_left = False
                cleaned_chars.append(text_value)
                continue

            if token.trim_left:
                apply_left_trim(cleaned_chars)

            # Keep offsets stable by masking template DSL lexemes with spaces while
            # preserving line breaks. This allows native linters to report positions
            # that map directly to the original template.
            if token.trim_left or token.trim_right:
                masked = ""
            else:
                masked = "".join(
                    ch if ch in ("\n", "\r") else " " for ch in token.raw_token
                )
            cleaned_chars.append(masked)
            if token.trim_right:
                trim_next_text_left = True

        cleaned_text = self._normalize_template_only_lines(text, "".join(cleaned_chars))
        normalized_hint = (format_hint or "").strip().lower()
        if normalized_hint in {"md", "markdown"}:
            cleaned_text = self._apply_markdown_semantic_cleanup(text, cleaned_text)
        return cleaned_text, []

    @staticmethod
    def _apply_markdown_semantic_cleanup(
        original_text: str,
        precleaned_text: str,
    ) -> str:
        """Apply markdown-specific cleanup after generic token masking.

        Rules:
        - Keep generic template-only-line normalization as the base behavior.
        - Replace expression tags with placeholder words on mixed-content lines.
        - Remove statement/comment tags on mixed-content lines.
        - Normalize heading spacing to avoid MD019 false positives.
        """
        original_lines = original_text.splitlines(keepends=True)
        precleaned_lines = precleaned_text.splitlines(keepends=True)
        if len(original_lines) != len(precleaned_lines):
            return precleaned_text

        output_lines: list[str] = []
        for original_line, masked_line in zip(original_lines, precleaned_lines):
            line_ending = ""
            core = original_line
            if core.endswith("\r\n"):
                core = core[:-2]
                line_ending = "\r\n"
            elif core.endswith("\n"):
                core = core[:-1]
                line_ending = "\n"
            elif core.endswith("\r"):
                core = core[:-1]
                line_ending = "\r"

            had_template_tag = any(tag in core for tag in ("{{", "{%", "{#"))
            if not had_template_tag:
                output_lines.append(masked_line)
                continue

            if masked_line.strip() == "":
                output_lines.append(masked_line)
                continue

            def _replace_tag(match: re.Match[str]) -> str:
                token = match.group(0)
                if token.startswith("{{"):
                    return " lorem "
                return ""

            cleaned = _INLINE_TEMPLATE_TOKEN_RE.sub(_replace_tag, core)
            cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).rstrip()
            cleaned = _ATX_MULTI_SPACE_RE.sub(r"\1 ", cleaned)

            if cleaned.strip() == "":
                output_lines.append(line_ending)
            else:
                output_lines.append(cleaned + line_ending)

        return "".join(output_lines)

    @staticmethod
    def _normalize_template_only_lines(original_text: str, cleaned_text: str) -> str:
        """Convert template-only lines to truly blank lines for base linters.

        Masking keeps offsets useful for mixed-content lines, but markdown linters in
        particular treat whitespace-only lines as non-blank. For lines that consist of
        only template tags and whitespace, collapse content to just the original line
        ending so base linting sees an actual blank separator.
        """
        original_lines = original_text.splitlines(keepends=True)
        cleaned_lines = cleaned_text.splitlines(keepends=True)
        if len(original_lines) != len(cleaned_lines):
            return cleaned_text

        normalized: list[str] = []
        for original_line, cleaned_line in zip(original_lines, cleaned_lines):
            contains_template_tag = any(tag in original_line for tag in ("{{", "{%", "{#"))
            line_without_template = _INLINE_TEMPLATE_TOKEN_RE.sub("", original_line)
            is_template_only = contains_template_tag and line_without_template.strip() == ""

            if not is_template_only:
                normalized.append(cleaned_line)
                continue

            if original_line.endswith("\r\n"):
                normalized.append("\r\n")
            elif original_line.endswith("\n"):
                normalized.append("\n")
            elif original_line.endswith("\r"):
                normalized.append("\r")
            else:
                normalized.append("")

        return "".join(normalized)
