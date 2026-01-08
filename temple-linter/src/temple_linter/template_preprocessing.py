"""
template_preprocessing.py
Utility for stripping/replacing template tokens for base format linting.
"""

import re
from typing import Optional, Tuple, Dict


def strip_template_tokens(
    text: str,
    delimiters: Optional[Dict[str, Tuple[str, str]]] = None,
    replace_with: str = "",
) -> str:
    """
    Strips or replaces all template tokens (statements, expressions, comments) from a templated file.
    Preserves the base format structure for linting. Supports configurable delimiters.

    Args:
        text: The input templated text.
        delimiters: Optional dict specifying delimiters for 'statement', 'expression', 'comment'.
            Example: {
                'statement': ('{%','%}'),
                'expression': ('{{','}}'),
                'comment': ('{#','#}')
            }
        replace_with: String to replace template tokens with (default: '').

    Returns:
        str: Text with template tokens stripped or replaced.
    """
    # Default delimiters (Jinja-like)
    default_delims = {
        "statement": ("{%", "%}"),
        "expression": ("{{", "}}"),
        "comment": ("{#", "#}"),
    }
    delims = delimiters or default_delims
    # Build regex patterns for each token type
    patterns = [
        re.escape(start) + r".*?" + re.escape(end) for start, end in delims.values()
    ]
    combined_pattern = "|".join(patterns)
    # Replace all template tokens
    processed = re.sub(combined_pattern, replace_with, text, flags=re.DOTALL)
    return processed


# CLI entry point for LSP server usage
if __name__ == "__main__":
    import argparse
    import sys
    import json

    parser = argparse.ArgumentParser(description="Template Preprocessing CLI")
    parser.add_argument("--strip", action="store_true", help="Strip template tokens")
    parser.add_argument("--input", type=str, help="Input text to process")
    parser.add_argument(
        "--delimiters", type=str, help="Delimiters as JSON string", default=None
    )
    args = parser.parse_args()

    if args.strip and args.input is not None:
        delimiters = None
        if args.delimiters:
            delimiters = json.loads(args.delimiters)
        result = strip_template_tokens(args.input, delimiters)
        print(result)
        sys.exit(0)
    else:
        print("")
        sys.exit(0)
