---
title: CI Jobs and Documentation Build
id: 40
status: open
related_commits: []
estimated_hours: 12
priority: high
---

## Goal

Add continuous integration workflows to run unit tests, E2E tests, benchmarks, and documentation builds on pull requests.

## Tasks

- Add GitHub Actions workflows: `ci/tests.yml`, `ci/benchmarks.yml`, `ci/docs.yml` (or consolidate into a matrix job).
- Ensure Python environment setup aligns with `.venv_asv_test` and pins a supported Python version.
- Add a docs build step that generates HTML from `docs/` and checks for broken links.
- Gate merges on successful test and docs checks.

## Acceptance Criteria

- Pull requests trigger CI; unit tests and docs build run and report status.
- A minimal `ci/` workflow checked in and referenced in contributor docs.
