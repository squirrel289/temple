#!/usr/bin/env bash
set -euo pipefail

# Build docs for pre-push checks. Assumes `sphinx-build` is on PATH.

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

SPHINX="$(command -v sphinx-build || true)"
if [ -z "$SPHINX" ]; then
  echo "sphinx-build not found on PATH; ensure .ci-venv is active or run ./scripts/setup-hooks.sh" >&2
  exit 1
fi

echo "Building Sphinx documentation (quick)"
$SPHINX -b html --keep-going temple-linter/docs temple-linter/docs/_build/html

exit 0
