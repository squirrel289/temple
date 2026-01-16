#!/usr/bin/env bash
set -euo pipefail

# Opt-in dependency installation
# Usage: export INSTALL_DEPS=1 || pass --with-deps or --install-deps-only
INSTALL_DEPS=${INSTALL_DEPS:-0}
INSTALL_ONLY=0
while [[ $# -gt 0 ]]; do
	case "$1" in
		--with-deps)
			INSTALL_DEPS=1
			shift
			;;
		--install-deps-only)
			INSTALL_DEPS=1
			INSTALL_ONLY=1
			shift
			;;
		*)
			echo "Unknown arg: $1" >&2
			exit 2
			;;
	esac
done

# Install dependencies only when opted-in
if [[ "$INSTALL_DEPS" -eq 1 ]]; then
	python -m pip install --upgrade pip
	python -m pip install -r scripts/ci/requirements-tests.txt
	if [[ "$INSTALL_ONLY" -eq 1 ]]; then
		echo "Installed test dependencies only."
		exit 0
	fi
fi

# Run tests (assumes dependencies are present if required)
python -m pytest temple/tests -q --ignore=temple/tests/test_benchmarks.py
