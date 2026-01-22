#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

HOOKS_VENV="$(pwd)/.ci-venv"
if [[ -d "$HOOKS_VENV" && -x "$HOOKS_VENV/bin/python" ]]; then
  echo "Using hooks venv: $HOOKS_VENV"
  export PATH="$HOOKS_VENV/bin:$PATH"
fi

echo "1/2: Running benchmark validations (subset)."
./scripts/ci/benchmarks_quick.sh

echo "2/2: Building docs (Sphinx)."
./scripts/ci/docs_build.sh

exit 0
