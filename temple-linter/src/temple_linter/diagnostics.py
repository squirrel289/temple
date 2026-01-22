"""
diagnostics.py
Diagnostics mapping and reporting for templated files.
"""

from typing import List, Dict, Any, Optional
from temple.diagnostics import DiagnosticCollector
from .template_mapping import TemplateMapping


def map_diagnostics(
    template_diagnostics: List[Dict[str, Any]],
    base_diagnostics: List[Dict[str, Any]],
    node_collector: Optional[DiagnosticCollector] = None,
) -> List[Dict[str, Any]]:
    """
    Map and combine diagnostics from template and base format linters.
    """
    # Map base diagnostics to original template positions if possible
    mapped_base: List[Dict[str, Any]] = []
    if base_diagnostics and "preprocessed_text" in base_diagnostics[0]:
        # Assume original_text is provided for mapping
        original_text = base_diagnostics[0]["original_text"]
        mapping = TemplateMapping(original_text)
        for diag in base_diagnostics:
            if "pos" in diag:
                orig_pos = mapping.pre_to_orig(diag["pos"])
                diag["orig_pos"] = orig_pos
            mapped_base.append(diag)
    else:
        mapped_base = base_diagnostics
    # Include diagnostics collected per-node from collector (if provided).
    node_diags: List[Dict[str, Any]] = []
    if node_collector is not None:
        raw = node_collector.diagnostics

        for d in raw:
            # If diagnostic has `to_lsp`, use it; if dict-like, use as-is.
            if hasattr(d, "to_lsp"):
                node_diags.append(d.to_lsp())
            elif isinstance(d, dict):
                node_diags.append(d)
            else:
                # Fallback to string representation
                node_diags.append({"message": str(d)})

    # Combine and return: template diagnostics first, then mapped base, then node-attached
    combined = template_diagnostics + mapped_base + node_diags
    return combined
