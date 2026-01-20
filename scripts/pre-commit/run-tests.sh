#!/usr/bin/env bash
set -euo pipefail

# Run pytest for affected Python modules derived from filenames passed by pre-commit.

PYTHON=python
if [[ -x "$(pwd)/.ci-venv/bin/python" ]]; then
  PYTHON="$(pwd)/.ci-venv/bin/python"
else
  if command -v python >/dev/null 2>&1; then
    PYTHON=python
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
  else
    echo "python not found in PATH; skipping test checks (allowing commit)." >&2
    exit 0
  fi
fi

# If pre-commit passes no filenames, exit successfully
if [[ "$#" -eq 0 ]]; then
  echo "No files provided; skipping pytest checks."
  exit 0
fi

# Collect Python files from args
files=()
for f in "$@"; do
  case "$f" in
    *.py) files+=("$f") ;;
  esac
done

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No Python files; skipping pytest checks."
  exit 0
fi

# Build pytest -k pattern from basenames (without extension)
patterns=()
for f in "${files[@]}"; do
  base="$(basename "$f" .py)"
  patterns+=("$base")
done

# Deduplicate patterns
uniq_patterns=$(printf "%s
" "${patterns[@]}" | awk '!seen[$0]++')

K_EXPR=""
while IFS= read -r p; do
  if [[ -z "$K_EXPR" ]]; then
    K_EXPR="$p"
  else
    K_EXPR="$K_EXPR or $p"
  fi
done <<< "$uniq_patterns"

echo "Running pytest for changed modules: $K_EXPR"
"$PYTHON" -m pytest -q -k "$K_EXPR" --maxfail=1 --disable-warnings

