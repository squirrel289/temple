# Contributing to Temple

Welcome! This guide walks you through the Temple development workflow, including CI integration and test execution.

## Development Setup

### Local Environment
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/temple.git
   cd temple
   ```

2. Install dependencies for core and linter (Python 3.8+):
   ```bash
   # Core temple package
   cd temple && pip install -e . && cd ..
   
   # Linter (depends on core)
   cd temple-linter && pip install -r requirements.txt && cd ..
   
   # VS Code extension (Node.js 16+)
   cd vscode-temple-linter && npm install && npm run compile && cd ..
   ```

3. Verify installation:
   ```bash
   pytest temple/tests/ -v
   pytest temple-linter/tests/ -v
   ```

### Install Git hooks (recommended)

After cloning the repository, enable the repository-tracked git hooks so you get the pre-push checks locally:

```bash
cd temple
./scripts/install-hooks.sh
```

The install script sets `core.hooksPath` to the tracked `.githooks/` directory. The recommended way to enable hooks for all future clones on your machine is to install them into your global git template directory (instructions below). This avoids needing repository-specific commit markers.


## CI/Workflow Overview

Temple uses **four primary GitHub Actions workflows** to validate code:

### 1. **tests.yml** — Python Tests (on push & PR)
- **Runs**: `pytest` across Python 3.10, 3.11
- **Scope**: `temple/` and `temple-linter/` packages
- **Trigger**: Push to `main`, pull requests to `main`
- **Status Badge**: Appears in PR checks

**Local equivalent:**
```bash
cd temple && pytest tests/ -v
cd ../temple-linter && pytest tests/ -v
```

### 2. **docs.yml** — Documentation Build (on push & PR)
- **Runs**:
  - Sphinx build for `temple-linter/docs/` (with `-W` strict mode)
  - Sphinx linkcheck for broken external URLs
  - Verification of core `temple/docs/` markdown files
- **Trigger**: Push to `main`, pull requests to `main`
- **Note**: Core docs (Markdown) are verified to exist; Sphinx is used for linter autodoc.

**Local equivalent:**
```bash
cd temple-linter/docs && sphinx-build -b html -W . _build/html
cd temple-linter/docs && sphinx-build -b linkcheck . _build/linkcheck
```

### 3. **benchmarks.yml** — Performance Regression Gate (on PR only)
- **Runs**: `asv continuous` to detect performance regressions
- **Threshold**: Fails if any benchmark regresses >10% (configurable in `asv.conf.json`)
- **Trigger**: Pull requests to `main` only (not on push)
- **Execution**: Runs from `temple/` subdirectory; uses shared machine config script

**Local equivalent:**
```bash
cd temple && asv continuous origin/main HEAD
```

### 4. **asv_publish.yml** — Benchmark Results Publish (scheduled weekly)
- **Runs**: Full ASV benchmark suite; publishes results to GitHub Pages
- **Trigger**: Scheduled for Wednesday 02:00 UTC (or manual dispatch)
- **Output**: Benchmark history at `https://yourusername.github.io/temple/benchmarks/`

## Continuous Integration Details

### Python Test Matrix
- **Versions**: Python 3.10, 3.11
- **Platforms**: Ubuntu Latest (Linux)
- **Dependencies**: Installed from `requirements.txt` and `setup.py`

### ASV (Airspeed Velocity) Configuration
- **Location**: `temple/asv.conf.json`
- **Key Settings**:
  - `repo: ".."` — Relative path for CI portability
  - `branches: ["main"]` — Track main branch only
  - `build_cache_size: 8` — Limit build artifacts
  - `default_benchmark_mode: "whole"` — Full benchmark runs
  - `min_run_count: 5` — Minimum iterations per benchmark

### Machine Identity (CI Only)
- **Purpose**: Ensure consistent benchmark measurements across CI runs
- **Setup Script**: `.github/scripts/configure_asv_machine.sh`
- **Config File**: `asv/machines/ci_machine.json`
- **Behavior**: 
  - Maps CI hostname to stable machine name (e.g., `gh-ubuntu-x64`)
  - Creates `~/.asv-machine.json` for ASV discovery
  - Registers `asv/results/{machine_name}/machine.json` for historical tracking

## Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code is tested locally: `pytest temple/tests/ -v && pytest temple-linter/tests/ -v`
- [ ] No lint errors (if linters configured)
- [ ] Documentation is updated if behavior changes
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with `main`

## Troubleshooting CI Failures

### Test Failure
- **Check locally first**: `pytest tests/ -v` in the affected package
- **View logs**: Click "Details" on the failing check in the PR
- **Common causes**: Missing dependencies, Python version mismatch, flaky tests

### Benchmark Regression Detected
- **Understand the threshold**: Check `asv.conf.json` for `min_run_count` and comparison logic
- **Run locally**: `cd temple && asv continuous origin/main HEAD`
- **Investigate root cause**:
  - Are you caching or memoizing differently?
  - Did you change the tokenizer or rendering logic?
  - Is the machine under load (check `top` during local run)?

### Documentation Build Failure
- **Check links locally**: `cd temple-linter/docs && sphinx-build -b linkcheck . _build/linkcheck`
- **Fix broken refs**: Update `.rst` files with correct paths or disable linkcheck for external URLs
- **Verify markdown**: Core docs must exist in `temple/docs/` (currently verified only)

### Machine Config Error (Benchmarks)
- **Error**: `RuntimeError: Could not automatically resolve ASV_MACHINE`
- **Fix**: Ensure `.github/scripts/configure_asv_machine.sh` is executable and called before ASV steps
- **Verify**: Check `asv/machines/ci_machine.json` exists in the repo

## Branch Protection Rules

The `main` branch enforces:
- ✅ All PR checks must pass (tests, docs, benchmarks)
- ✅ At least 1 approving review
- ✅ Commits must be up to date before merge

## Monorepo Structure

Temple is organized as a **single-root monorepo** with three interconnected components:

```
temple/                      # Python core templating engine
├── src/temple/
│   ├── template_tokenizer.py    # Authoritative tokenizer (LRU cached)
│   ├── template_renderer.py     # Rendering engine
│   └── __init__.py              # Public exports
├── tests/test_tokenizer.py
├── docs/ARCHITECTURE.md         # Core documentation (Markdown)
└── asv.conf.json                # ASV benchmark config

temple-linter/              # LSP server for template linting
├── src/temple_linter/
│   ├── lsp_server.py            # Language Server Protocol
│   ├── template_preprocessing.py # Token stripping for base format lint
│   └── diagnostics.py           # Error mapping
├── tests/test_*.py
└── docs/                        # Sphinx documentation
    ├── conf.py
    ├── index.rst
    └── api.rst

vscode-temple-linter/       # VS Code extension (TypeScript)
├── src/extension.ts
├── package.json
└── README.md
```

**Key Convention**: All three components share the same tokenizer (`temple.template_tokenizer`). Changes to tokenizer **must** be tested across all three.

## Common Development Tasks

### Add a Unit Test
```bash
# Add test to temple/tests/test_tokenizer.py or temple-linter/tests/test_linter.py
# Run locally:
cd temple && pytest tests/test_tokenizer.py::test_my_feature -v
```

### Update Documentation
- **Core docs**: Markdown files in `temple/docs/` (ARCHITECTURE.md, syntax_spec.md, etc.)
- **Linter docs**: Sphinx `.rst` files in `temple-linter/docs/`
- **Verify**: `cd temple-linter/docs && sphinx-build -b html . _build/html`

### Run Benchmarks Locally
```bash
cd temple
asv run --skip-existing  # Run all benchmarks
asv continuous origin/main HEAD  # Compare against main branch
```

### Update Dependencies
- **Core**: Edit `temple/pyproject.toml` or `requirements.txt`
- **Linter**: Edit `temple-linter/requirements.txt`
- **Extension**: Edit `vscode-temple-linter/package.json`
- **After update**: Reinstall locally (`pip install -e .` or `npm install`)
### Install Git hooks (recommended)

After cloning the repository, enable the repository-tracked git hooks so you get the pre-push checks locally:

```bash
cd temple
./scripts/install-hooks.sh
```

The install script sets `core.hooksPath` to the tracked `.githooks/` directory. To make hooks apply for new clones on your machine, copy them into your global git template directory (see below) so you don't need per-repo configuration.

If you prefer a machine-wide setup so future clones receive hooks automatically, install the hooks into your global git template directory (one-time per machine):

```bash
mkdir -p ~/.git-templates/hooks
cp -R .githooks/* ~/.git-templates/hooks/
git config --global init.templateDir "$HOME/.git-templates"
```


## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: File an Issue with minimal reproduction
- **Security**: Please report privately to maintainers

---

**Last Updated**: Based on CI workflows (tests.yml, docs.yml, benchmarks.yml, asv_publish.yml)
