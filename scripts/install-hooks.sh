#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

echo "Installing git hooks from .githooks/"
git config core.hooksPath .githooks
echo "Hooks installed (git config core.hooksPath set to .githooks)."
