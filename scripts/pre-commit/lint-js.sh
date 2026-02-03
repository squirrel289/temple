#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

# Ensure CI venv is available if helper exists
if [ -f "$ROOT_DIR/scripts/ci/venv_utils.sh" ]; then
  . "$ROOT_DIR/scripts/ci/venv_utils.sh"
fi

if ! ensure_ci_venv_ready; then
  print_ci_venv_instructions || true
  exit 1
fi

echo "Running ESLint (vscode-temple-linter)..."
npm --prefix vscode-temple-linter run lint -- --max-warnings=0

exit 0
