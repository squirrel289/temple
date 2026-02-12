#!/usr/bin/env bash
set -euo pipefail

# Run pytest for affected Python modules (pre-commit) or all tests (scheduled/push).
ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
  echo "python not found in PATH; skipping test checks (allowing commit)." >&2
  exit 0
fi

# If no filenames are provided, decide based on context.
if [[ "$#" -eq 0 ]]; then
  if [[ "${GITHUB_EVENT_NAME:-}" == "pull_request" ]]; then
    echo "CI PR detected; running affected tests only."
    base_ref="${GITHUB_BASE_REF:-}"
    if [[ -z "$base_ref" ]]; then
      echo "GITHUB_BASE_REF not set; falling back to full test run."
      "$PYTHON" -m pytest tests/ -v --tb=short
      exit 0
    fi

    # Ensure base ref is available for diff
    git fetch --no-tags --depth=1 origin "$base_ref":"refs/remotes/origin/$base_ref" >/dev/null 2>&1 || true
    diff_base="origin/$base_ref"

    mapfile -t files < <(git diff --name-only "$diff_base"...HEAD -- '*.py' || true)
    if [[ ${#files[@]} -eq 0 ]]; then
      echo "No Python changes detected; skipping pytest checks."
      exit 0
    fi

    # Convert changed files into patterns for pytest -k
    patterns=()
    for f in "${files[@]}"; do
      base="$(basename "$f" .py)"
      patterns+=("$base")
    done

    uniq_patterns=$(printf "%s\n" "${patterns[@]}" | awk '!seen[$0]++')
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
    exit 0
  fi

  echo "Non-PR run detected; running full test suite."
  "$PYTHON" -m pytest tests/ -v --tb=short
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

