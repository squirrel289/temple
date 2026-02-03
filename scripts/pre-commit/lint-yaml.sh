#!/usr/bin/env bash
set -euo pipefail

# Run yamllint across repository YAML files using repo config
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

YAMLLINT_BIN="$(command -v yamllint || true)"
if [ -z "$YAMLLINT_BIN" ]; then
  echo "yamllint not found on PATH; ensure .ci-venv is active or run ./scripts/setup-hooks.sh" >&2
  exit 1
fi

echo "Running yamllint..."
# Collect YAML files and run yamllint. Use -z and xargs -0 for portability
files_count=$(git ls-files '*.yml' '*.yaml' | wc -l | tr -d ' ')
if [ "${files_count}" -eq 0 ]; then
  echo "No YAML files found to lint."
  exit 0
fi

# Use null-separated file list to safely handle spaces/newlines in filenames
git ls-files -z '*.yml' '*.yaml' | xargs -0 "$YAMLLINT_BIN" -c .yamllint
