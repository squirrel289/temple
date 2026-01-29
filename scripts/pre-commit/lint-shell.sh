#!/usr/bin/env bash
set -euo pipefail

# Lint all shell scripts in repository using `bash -n`.
# Excludes files in .git and known binary paths.

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "Running bash -n on repository shell scripts..."

failed=0
while IFS= read -r -d $'\0' file; do
  # Skip files that are not regular files
  if [ ! -f "$file" ]; then
    continue
  fi
  printf "Checking %s... " "$file"
  if bash -n "$file" 2>/tmp/bashlint_err; then
    printf "ok\n"
  else
    printf "ERROR\n"
    cat /tmp/bashlint_err
    failed=1
  fi
done < <(find . -path './.git' -prune -o -type f -name '*.sh' -print0)

rm -f /tmp/bashlint_err

if [ "$failed" -ne 0 ]; then
  echo "One or more shell scripts failed bash -n checks."
  exit 2
fi

echo "All shell scripts passed bash -n checks."
exit 0
