#!/usr/bin/env bash
set -euo pipefail
# Check for broken links in Sphinx docs
uv pip run sphinx-build -b linkcheck -W --keep-going . _build/linkcheck || true
