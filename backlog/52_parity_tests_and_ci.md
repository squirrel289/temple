---
title: Parity Tests & CI for Native vs Adapter
id: 52
status: proposed
related_commit:
  - 6d8c044 # docs(adr): clarify market role and adapter architecture (ADR-003); add adapter spec; archive backlog/48_jinja_integration.md
  - 1008bbc  # chore(ci): update workflows and contributing with shared CI scripts
  - 067a1ac  # chore: workspace/backlog updates to support parity and CI readiness
dependencies:
  - "[[54_complete_temple_native.md]]"
  - "[[56_jinja2_adapter_prototype.md]]"
estimated_hours: 16
priority: medium
---

## Goal

Create a suite of parity tests and CI checks that validate that Temple-native behavior and adapter behavior (Jinja2 adapter) produce consistent diagnostics for a shared set of template fixtures.

## Deliverables

- `tests/parity/` fixtures and test harness
- CI workflow that runs parity suite on PRs
- Triage checklist for resolving parity mismatches

## Acceptance Criteria

- CI runs parity tests; mismatches report clear diffs
- Parity suite included in repository and documented
