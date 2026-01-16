#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

usage() {
	cat <<EOF
Usage: $0 [--global] [--force]

Install repository-tracked git hooks.

Options:
	--global   Install hooks into your global git template directory so new clones receive them automatically.
	--force    Overwrite existing global template hooks when using --global.
	-h, --help Show this help message
EOF
}

GLOBAL=0
FORCE=0
while [[ $# -gt 0 ]]; do
	case "$1" in
		--global) GLOBAL=1; shift ;;
		--force) FORCE=1; shift ;;
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
	echo "Hooks installed (git config core.hooksPath set to .githooks)."
fi
