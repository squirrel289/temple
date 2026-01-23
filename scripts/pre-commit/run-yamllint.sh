#!/usr/bin/env bash
set -euo pipefail

# Run yamllint across repository YAML files using repo config
HERE=$(dirname "$0")/..
YAMLLINT_BIN="${CI_VENV:-.ci-venv}/bin/yamllint"
if [ ! -x "$YAMLLINT_BIN" ]; then
  YAMLLINT_BIN=".ci-venv/bin/yamllint"
fi

echo "Running yamllint..."
# Collect YAML files and run yamllint. Use -z and xargs -0 for portability
files_count=$(git ls-files '*.yml' '*.yaml' | wc -l | tr -d ' ')
if [ "${files_count}" -eq 0 ]; then
  echo "No YAML files found to lint."
  exit 0
fi

# Use null-separated file list to safely handle spaces/newlines in filenames
git ls-files -z '*.yml' '*.yaml' | xargs -0 "$YAMLLINT_BIN" -c .yamllint.yml
