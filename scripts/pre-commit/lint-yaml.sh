#!/usr/bin/env bash
set -euo pipefail

# Run yamllint across repository YAML files.
ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "Running yamllint via uv..."

targets=("$@")
if [ "${#targets[@]}" -eq 0 ]; then
  while IFS= read -r file; do
    targets+=("$file")
  done < <(git ls-files '*.yml' '*.yaml')
fi

if [ "${#targets[@]}" -eq 0 ]; then
  echo "No YAML files found to lint."
  exit 0
fi

workflow_targets=()
default_targets=()

for target in "${targets[@]}"; do
  case "$target" in
    .github/workflows|.github/workflows/*)
      workflow_targets+=("$target")
      ;;
    *)
      default_targets+=("$target")
      ;;
  esac
done

if [ "${#workflow_targets[@]}" -gt 0 ]; then
  uv tool run yamllint -c .github/workflows/.yamllint "${workflow_targets[@]}"
fi

if [ "${#default_targets[@]}" -gt 0 ]; then
  uv tool run yamllint -c .yamllint "${default_targets[@]}"
fi
