#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

# Ensure CI virtualenv is activated so linters are run from `.ci-venv`.
# This provides consistent tool versions in CI and locally.
if [ -f "$ROOT_DIR/scripts/ci/venv_utils.sh" ]; then
	# shellcheck disable=SC1090
	. "$ROOT_DIR/scripts/ci/venv_utils.sh"
	if ! ensure_ci_venv_ready; then
		echo "CI virtualenv not found or not ready. See scripts/ci/venv_utils.sh for instructions." >&2
		print_ci_venv_instructions || true
		exit 1
	fi
fi

echo "Running python linter (ruff)..."
ruff check

exit 0
