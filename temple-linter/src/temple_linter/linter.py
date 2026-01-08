"""
linter.py
Core linting logic for templated files.
"""

from typing import List, Dict, Any


class TemplateLinter:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def lint(self, text: str) -> List[Dict[str, Any]]:
        """
        Lint the given templated text and return diagnostics.
        """
        # Placeholder: integrate with temple for preprocessing
        # and with base format linters
        diagnostics: List[Dict[str, Any]] = []
        # ... linting logic ...
        return diagnostics


# CLI entry point for LSP server usage
if __name__ == "__main__":
    import argparse
    import sys
    import json

    parser = argparse.ArgumentParser(description="Temple Linter CLI")
    parser.add_argument("--lint", action="store_true", help="Run linter")
    parser.add_argument("--input", type=str, help="Input text to lint")
    parser.add_argument(
        "--delegate-base-lint",
        action="store_true",
        help="Delegate base linting to caller",
    )
    parser.add_argument(
        "--filename", type=str, help="Filename for base format detection", default=None
    )
    args = parser.parse_args()

    if args.lint and args.input is not None:
        linter = TemplateLinter()
        template_diags = linter.lint(args.input)
        cleaned_text = args.input  # Replace with actual template stripping if needed
        if args.delegate_base_lint:
            # Emit base lint request
            print(
                json.dumps(
                    {
                        "template_diagnostics": template_diags,
                        "base_lint_request": {
                            "text": cleaned_text,
                            "filename": args.filename,
                        },
                    }
                )
            )
            # Read base diagnostics from stdin (as JSON)
            try:
                base_diags = json.loads(sys.stdin.read())
            except Exception:
                base_diags = []
            # Merge and output
            print(json.dumps(template_diags + base_diags))
            sys.exit(0)
        else:
            # Run base linting in-process (if implemented)
            print(json.dumps(template_diags))
            sys.exit(0)
    else:
        print(json.dumps([]))
        sys.exit(0)
