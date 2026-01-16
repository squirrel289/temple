#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

usage() {
	cat <<EOF
Usage: $0 [--global] [--force] [--no-deps]

Install repository-tracked git hooks.

Options:
	--global   Install hooks into your global git template directory so new clones receive them automatically.
	--force    Overwrite existing global template hooks when using --global.
	--no-deps  Do NOT create the repository venv and install CI dependencies (installer installs deps by default).
	-h, --help Show this help message
EOF
}

GLOBAL=0
FORCE=0
# Install deps by default (all-or-nothing policy). Use --no-deps to opt-out.
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
	if [[ -n "$(ls -A .githooks)" ]]; then
		if [[ $FORCE -eq 1 ]]; then
			rm -rf "$TARGET_DIR"/*
		fi
		cp -R .githooks/* "$TARGET_DIR/"
		# Ensure hooks are executable
		chmod +x "$TARGET_DIR"/* || true
		git config --global init.templateDir "$HOME/.git-templates"
		echo "Global git hooks installed. New clones will receive hooks from $TARGET_DIR."
		echo "(Existing repositories must run 'git init' or re-clone to pick up the template.)"
	else
		echo "No hooks found in .githooks/ to install." >&2
		exit 1
	fi
else
	echo "Installing git hooks from .githooks/ into repository-local hooksPath"
	git config core.hooksPath .githooks
	# Ensure hooks are executable in the repository copy
	if [[ -d .githooks ]]; then
		chmod +x .githooks/* || true
	fi
	echo "Hooks installed (git config core.hooksPath set to .githooks)."
fi

# Optionally install CI dependencies used by the shared scripts
if [[ $INSTALL_DEPS -eq 1 ]]; then
	# Prefer `python`, fall back to `python3` for venv creation
	if command -v python >/dev/null 2>&1; then
		PYTHON=python
	elif command -v python3 >/dev/null 2>&1; then
		PYTHON=python3
	else
		echo "python not found in PATH; cannot install dependencies." >&2
		exit 2
	fi
	# Create a repository-scoped venv for hooks to avoid contaminating user env
	HOOKS_VENV="$REPO_ROOT/.hooks-venv"
	if [[ ! -d "$HOOKS_VENV" ]]; then
		echo "Creating hooks virtualenv at $HOOKS_VENV"
		"$PYTHON" -m venv "$HOOKS_VENV"
	fi

	# Install CI dependencies via the shared scripts in "install-deps-only" mode.
	# Invoke the scripts with the venv on PATH so `python` resolves to the venv python.
	echo "Installing CI dependencies into $HOOKS_VENV via shared scripts"
	PATH="$HOOKS_VENV/bin:$PATH" INSTALL_DEPS=1 bash -c "bash scripts/ci/tests.sh --install-deps-only && bash scripts/ci/docs_build.sh --install-deps-only && bash scripts/ci/benchmarks_quick.sh --install-deps-only"
	echo "CI dependencies installed into $HOOKS_VENV."

	# Add hooks venv to .gitignore if not present
	GITIGNORE="$REPO_ROOT/.gitignore"
	if [[ -f "$GITIGNORE" ]]; then
		if ! grep -q "^\.hooks-venv$" "$GITIGNORE"; then
			echo ".hooks-venv" >> "$GITIGNORE"
			echo "Added .hooks-venv to .gitignore"
		fi
	else
		echo ".hooks-venv" > "$GITIGNORE"
		echo "Created .gitignore and added .hooks-venv"
	fi
fi
