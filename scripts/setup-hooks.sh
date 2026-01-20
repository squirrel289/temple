#!/usr/bin/env bash
set -euo pipefail

# setup-hooks.sh
# Unified helper for local hook setup and optional global installation.
# Supports: --global, --force, --no-deps

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

usage() {
  cat <<EOF
Usage: $0 [--global] [--force] [--no-deps]

Install and configure repository hooks.

Options:
  --global   Install hooks into your global git template directory so new clones receive them automatically.
  --force    Overwrite existing global template hooks when using --global.
  --no-deps  Do NOT install CI dependencies (installer installs deps by default).
  -h, --help Show this help message
EOF
}

GLOBAL=0
FORCE=0
INSTALL_DEPS=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) GLOBAL=1; shift ;;
    --force) FORCE=1; shift ;;
    --no-deps) INSTALL_DEPS=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 2 ;;
  esac
done

if [[ $GLOBAL -eq 1 ]]; then
  TARGET_DIR="$HOME/.git-templates/hooks"
  echo "Installing hooks to global git template: $TARGET_DIR"
  mkdir -p "$TARGET_DIR"
  if [[ -d .githooks && -n "$(ls -A .githooks)" ]]; then
    if [[ $FORCE -eq 1 ]]; then
      rm -rf "$TARGET_DIR"/*
    fi
    # Prefer using pre-commit for global installs so hooks are managed consistently.
    if command -v pre-commit >/dev/null 2>&1; then
      echo "Using pre-commit to initialize global template and install hooks"
      pre-commit init-templatedir "$HOME/.git-templates" || true
      # Copy repo config into the template so pre-commit knows which hooks to install
      if [[ -f .pre-commit-config.yaml ]]; then
        cp .pre-commit-config.yaml "$TARGET_DIR/.pre-commit-config.yaml" || true
      fi
      pre-commit install --install-hooks --template-dir "$HOME/.git-templates" || true
      git config --global init.templateDir "$HOME/.git-templates"
      echo "Global pre-commit hooks installed into $TARGET_DIR. New clones will receive hooks."
      echo "(Existing repositories must run 'git init' or re-clone to pick up the template.)"
    else
      # Fallback: copy raw hook scripts if pre-commit isn't available
      cp -R .githooks/* "$TARGET_DIR/"
      chmod +x "$TARGET_DIR"/* || true
      git config --global init.templateDir "$HOME/.git-templates"
      echo "Global git hooks installed (raw scripts) into $TARGET_DIR."
      echo "Consider installing 'pre-commit' (brew install pre-commit) for managed hooks."
    fi
  else
    echo "No hooks found in .githooks/ to install." >&2
    exit 1
  fi
  exit 0
fi

# Local setup: create .hooks-venv and install tooling, then register pre-commit hooks
HOOKS_VENV="$REPO_ROOT/.hooks-venv"
if [[ -d "$HOOKS_VENV" ]]; then
  echo ".hooks-venv already exists; using existing environment"
else
  echo "Creating .hooks-venv..."
  if command -v python >/dev/null 2>&1; then
    PYTHON=python
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
  else
    echo "python not found in PATH; cannot create venv." >&2
    exit 2
  fi
  "$PYTHON" -m venv "$HOOKS_VENV"
fi

echo "Upgrading pip and installing tools into .hooks-venv"
"$HOOKS_VENV/bin/python" -m pip install --upgrade pip
"$HOOKS_VENV/bin/python" -m pip install pre-commit ruff

echo "Installing pre-commit hooks using the venv's pre-commit binary"
"$HOOKS_VENV/bin/pre-commit" install || true

# Optionally install CI dependencies used by shared scripts
if [[ $INSTALL_DEPS -eq 1 ]]; then
  echo "Installing CI dependencies into $HOOKS_VENV via shared scripts"
  PATH="$HOOKS_VENV/bin:$PATH" INSTALL_DEPS=1 bash -c "bash scripts/ci/tests.sh --install-deps-only && bash scripts/ci/docs_build.sh --install-deps-only && bash scripts/ci/benchmarks_quick.sh --install-deps-only" || true
  echo "CI dependencies installed into $HOOKS_VENV (best-effort)."
fi

cat <<'EOF'
Setup complete.
- To activate the venv: `source .hooks-venv/bin/activate`
- To run hooks manually: `.hooks-venv/bin/pre-commit run --all-files`
EOF

exit 0
