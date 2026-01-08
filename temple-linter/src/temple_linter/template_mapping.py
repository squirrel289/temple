"""
template_mapping.py
Map positions between preprocessed and original template files for diagnostics.
"""

from typing import Dict, Any, Tuple, Optional
import re


class TemplateMapping:
    def __init__(
        self, text: str, delimiters: Optional[Dict[str, Tuple[str, str]]] = None
    ):
        self.text = text
        self.delimiters = delimiters or {
            "statement": ("{%", "%}"),
            "expression": ("{{", "}}"),
            "comment": ("{#", "#}"),
        }
        self._build_mapping()

    def _build_mapping(self):
        """
        Build a mapping from preprocessed positions to original template positions.
        """
        self.mapping: list[
            tuple[int, Optional[int]]
        ] = []  # List of (orig_pos, pre_pos)
        orig_pos = 0
        pre_pos = 0
        text = self.text
        # Build regex for all template tokens
        patterns = [
            re.escape(start) + r".*?" + re.escape(end)
            for start, end in self.delimiters.values()
        ]
        combined_pattern = "|".join(patterns)
        token_regex = re.compile(combined_pattern, re.DOTALL)
        for match in token_regex.finditer(text):
            # Map all non-token regions
            while orig_pos < match.start():
                self.mapping.append((orig_pos, pre_pos))
                orig_pos += 1
                pre_pos += 1
            # Map token region (removed in preprocessing)
            for i in range(match.start(), match.end()):
                self.mapping.append((i, None))  # None means not present in preprocessed
            orig_pos = match.end()
        # Map remaining text
        while orig_pos < len(text):
            self.mapping.append((orig_pos, pre_pos))
            orig_pos += 1
            pre_pos += 1

    def pre_to_orig(self, pre_pos: int) -> int:
        """
        Map a position in preprocessed text to original template position.
        """
        for orig, pre in self.mapping:
            if pre == pre_pos:
                return orig
        return -1  # Not found

    def orig_to_pre(self, orig_pos: int) -> int:
        """
        Map a position in original template to preprocessed text position.
        """
        for orig, pre in self.mapping:
            if orig == orig_pos:
                return pre if pre is not None else -1
        return -1

    def map_diagnostic(self, diag: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a diagnostic from preprocessed to original template positions.
        """
        if "pos" in diag:
            orig_pos = self.pre_to_orig(diag["pos"])
            diag["orig_pos"] = orig_pos
        if "line" in diag:
            # Optionally map line numbers if needed
            pass
        return diag
