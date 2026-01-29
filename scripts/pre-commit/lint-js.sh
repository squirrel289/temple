#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

# Activate CI virtualenv if available to ensure consistent environment
if [ -f "$ROOT_DIR/scripts/ci/venv_utils.sh" ]; then
	# shellcheck disable=SC1090
	. "$ROOT_DIR/scripts/ci/venv_utils.sh"
	ensure_ci_venv_ready || true
fi

echo "Running ESLint (vscode-temple-linter)..."
npm --prefix vscode-temple-linter run lint -- --max-warnings=0

exit 0
