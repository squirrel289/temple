#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

PYTEST="$(command -v pytest || true)"
if [ -z "$PYTEST" ]; then
  echo "pytest not found on PATH; ensure .ci-venv is active or run ./scripts/setup-hooks.sh" >&2
  exit 1
fi

echo "Running quick benchmark validation tests"
$PYTEST -q \
  temple/tests/test_benchmarks.py::test_bench_real_small \
  temple/tests/test_benchmarks.py::test_bench_real_medium \
  temple/tests/test_benchmarks.py::test_bench_real_large \
  --maxfail=1 --disable-warnings

exit 0
