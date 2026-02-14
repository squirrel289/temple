---
title: "Fix ASV workflow execution context for benchmarks and publish"
id: 71
status: not_started
state_reason: null
priority: high
complexity: low
estimated_hours: 3
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[archive/39_performance_benchmarks.md]]"
  - "[[archive/57_fix_ci_workflow_wiring.md]]"
related_backlog: []
related_spike: []
notes: |
  Created from validated code review feedback in session
  rollout-2026-02-13T18-06-30-019c5941-80d2-7d03-a17d-e45bf33ca0ae.
  ASV commands in benchmarks workflow currently execute from repo root while
  ASV configuration lives at temple/asv.conf.json.
---

## Goal

Make benchmark and publish workflow steps run ASV with the correct configuration context so scheduled/manual benchmark runs are reliable.

## Background

The workflow invokes `python -m asv` without explicitly setting `working-directory: temple` or passing `--config temple/asv.conf.json`. Since `asv.conf.json` exists only in `temple/`, this can cause config resolution failures depending on runner context.

## Tasks

1. **Choose one deterministic ASV config strategy**
   - Preferred: run ASV steps with `working-directory: temple`.
   - ~~Alternative: keep root working directory and pass explicit config path to all ASV commands~~.

2. **Update benchmark workflow**
   - Modify `.github/workflows/benchmarks.yml` ASV update/run/publish steps to use the chosen strategy consistently.
   - Ensure result/html output paths remain aligned with existing artifact upload paths.

3. **Validate path interactions**
   - Confirm machine config script and result directory assumptions still hold after workflow change.
   - Verify no mismatch between env vars and effective ASV output location.

4. **Add workflow verification evidence**
   - Capture command/output evidence from local simulation using `act` and/or CI run in `test_results`.

## Deliverables

- Updated `.github/workflows/benchmarks.yml` with deterministic ASV config resolution.
- Validation notes confirming benchmark and publish steps find config and produce artifacts at expected paths.

## Acceptance Criteria

- [ ] `asv update`, `asv run`, and `asv publish` use a context that always resolves `temple/asv.conf.json`.
- [ ] Benchmark results and HTML publish artifacts are generated in expected directories.
- [ ] Workflow remains valid YAML and runs without ASV config/path errors.
