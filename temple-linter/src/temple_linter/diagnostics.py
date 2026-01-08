"""
diagnostics.py
Diagnostics mapping and reporting for templated files.
"""

from typing import List, Dict, Any
from .template_mapping import TemplateMapping


def map_diagnostics(
    template_diagnostics: List[Dict[str, Any]], base_diagnostics: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Map and combine diagnostics from template and base format linters.
    """
    # Map base diagnostics to original template positions if possible
    mapped_base = []
    if base_diagnostics and "preprocessed_text" in base_diagnostics[0]:
        # Assume preprocessed_text and original_text are provided for mapping
        preprocessed_text = base_diagnostics[0]["preprocessed_text"]
        original_text = base_diagnostics[0]["original_text"]
        mapping = TemplateMapping(original_text)
        for diag in base_diagnostics:
            if "pos" in diag:
                orig_pos = mapping.pre_to_orig(diag["pos"])
                diag["orig_pos"] = orig_pos
            mapped_base.append(diag)
    else:
        mapped_base = base_diagnostics
    # Combine and return
    combined = template_diagnostics + mapped_base
    return combined
