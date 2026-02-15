"""TokenCleaningService - Strips template tokens for base format linting."""

from __future__ import annotations

from temple.template_spans import TemplateLineMetadata, build_template_metadata
from temple.template_tokenizer import Token
from temple.whitespace_control import apply_left_trim, trim_leading_whitespace

from .base_cleaning_contract import BaseCleaningContract
from .base_cleaning_policies import apply_markdown_policy


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
        delimiters: dict[str, tuple[str, str]] | None = None,
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
        contract = self.clean_for_base_lint(text, format_hint, delimiters)
        return contract.cleaned_text, []

    def clean_for_base_lint(
        self,
        text: str,
        format_hint: str | None = None,
        delimiters: dict[str, tuple[str, str]] | None = None,
    ) -> BaseCleaningContract:
        """Produce canonical base-cleaning contract for adapter-specific policies."""
        token_spans, line_metadata = build_template_metadata(
            text,
            delimiters=delimiters,
        )

        cleaned_chars: list[str] = []
        trim_next_text_left = False
        for token_span in token_spans:
            token = token_span.token
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

        cleaned_text = self._normalize_template_only_lines(
            "".join(cleaned_chars),
            line_metadata,
        )
        contract = BaseCleaningContract(
            original_text=text,
            cleaned_text=cleaned_text,
            token_spans=tuple(token_spans),
            line_metadata=tuple(line_metadata),
        )

        normalized_hint = (format_hint or "").strip().lower()
        if normalized_hint in {"md", "markdown"}:
            contract = apply_markdown_policy(contract)
        return contract

    @staticmethod
    def _normalize_template_only_lines(
        cleaned_text: str,
        line_metadata: list[TemplateLineMetadata],
    ) -> str:
        """Convert template-only lines to truly blank lines for base linters.

        Masking keeps offsets useful for mixed-content lines, but markdown linters in
        particular treat whitespace-only lines as non-blank. For lines that consist of
        only template tags and whitespace, collapse content to just the original line
        ending so base linting sees an actual blank separator.
        """
        cleaned_lines = cleaned_text.splitlines(keepends=True)
        if len(line_metadata) != len(cleaned_lines):
            return cleaned_text

        normalized: list[str] = []
        for meta, cleaned_line in zip(line_metadata, cleaned_lines):
            if not meta.is_template_only:
                normalized.append(cleaned_line)
                continue
            normalized.append(meta.line_ending)

        return "".join(normalized)
