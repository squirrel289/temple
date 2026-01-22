"""
DiagnosticMappingService - Maps diagnostics from cleaned content to original positions
"""

import logging
import copy
from typing import List, Optional, Tuple
from lsprotocol.types import Diagnostic, Position, Range
from temple.template_tokenizer import Token


class DiagnosticMappingService:
    """
    Service responsible for mapping diagnostics between cleaned and original content.

    This service:
    - Maps diagnostic positions from cleaned content back to original template
    - Accounts for stripped DSL tokens in position calculations
    - Handles edge cases and errors gracefully
    """

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def map_diagnostics(
        self, diagnostics: List[Diagnostic], text_tokens: List[Token]
    ) -> List[Diagnostic]:
        """
        Map diagnostics from cleaned content to original template positions.

        Args:
            diagnostics: Diagnostics with positions in cleaned content
            text_tokens: Text tokens tracking original positions

        Returns:
            Diagnostics with positions mapped to original template
        """
        mapped_diagnostics: List[Diagnostic] = []

        for diag in diagnostics:
            mapped_diag = self._map_diagnostic(diag, text_tokens)
            if mapped_diag:
                mapped_diagnostics.append(mapped_diag)

        return mapped_diagnostics

    def _map_diagnostic(
        self, diagnostic: Diagnostic, text_tokens: List[Token]
    ) -> Optional[Diagnostic]:
        """Map a single diagnostic to original positions."""
        try:
            diag = copy.deepcopy(diagnostic)
            start = diag.range.start
            end = diag.range.end

            orig_start = self._map_position(start, text_tokens)
            orig_end = self._map_position(end, text_tokens)

            diag.range = Range(start=orig_start, end=orig_end)
            return diag

        except Exception as e:
            self.logger.error(f"Failed to map diagnostic: {diagnostic}, error: {e}")
            return None

    def _map_position(self, pos: Position, text_tokens: List[Token]) -> Position:
        """Map a position from cleaned content to original template."""
        # Convert (line, character) to offset in cleaned text
        cleaned_offset = self._position_to_offset(pos, text_tokens)

        # Find the token containing this offset
        offset = 0
        for token in text_tokens:
            token_len = len(token.value)
            if offset <= cleaned_offset < offset + token_len:
                offset_in_token = cleaned_offset - offset
                orig_line, orig_col = self._advance_by_offset(
                    token.start, token.value, offset_in_token
                )
                return Position(line=orig_line, character=orig_col)
            offset += token_len

        # Fallback: return original position
        return pos

    def _position_to_offset(self, pos: Position, text_tokens: List[Token]) -> int:
        """Convert (line, character) position to flat offset in cleaned text."""
        cleaned_text = "".join(token.value for token in text_tokens)
        lines = cleaned_text.splitlines(keepends=True)

        # Sum lengths of all lines before target line
        offset = sum(len(lines[i]) for i in range(min(pos.line, len(lines))))

        # Add character offset within the target line
        offset += pos.character

        return offset

    def _advance_by_offset(
        self, start: Tuple[int, int], value: str, offset: int
    ) -> Tuple[int, int]:
        """Advance (line, col) by offset chars in value."""
        line, col = start

        # Get the substring up to the offset
        substr = value[:offset]

        # Split into lines, keeping line endings
        lines = substr.splitlines(keepends=True)
        if not lines:
            return (line, col)

        if len(lines) == 1:
            # No newlines encountered
            return (line, col + len(lines[0]))

        # Multiple lines: advance line by number of newlines
        line += len(lines) - 1
        last_line = lines[-1]

        # If last_line ends with a newline, col should be 0
        if last_line.endswith("\n") or last_line.endswith("\r"):
            col = 0
        else:
            col = len(last_line)

        return (line, col)
