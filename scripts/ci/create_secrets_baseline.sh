#!/usr/bin/env bash
set -euo pipefail

# Create a detect-secrets baseline for the repo.
# Usage: ./scripts/ci/create_secrets_baseline.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../" && pwd)"

# Reuse shared readiness check
if [ -f "$ROOT_DIR/scripts/ci/venv_utils.sh" ]; then
  . "$ROOT_DIR/scripts/ci/venv_utils.sh"
fi

if ! ensure_ci_venv_ready; then
  print_ci_venv_instructions || true
  exit 1
fi

OUT="$ROOT_DIR/.secrets.baseline"
echo "Scanning repository and writing baseline to $OUT"
detect-secrets scan > "$OUT"

echo
echo "Baseline written to $OUT"
echo "Review the baseline and commit it to allow approved findings to pass detect-secrets checks." 
echo "Example: git add .secrets.baseline && git commit -m 'chore(secrets): add detect-secrets baseline'"
