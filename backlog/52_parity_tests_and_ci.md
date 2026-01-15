---
title: Parity Tests & CI for Native vs Adapter
id: 52
status: proposed
related_commit:
  - 6d8c044
dependencies:
  - "[[49_complete_temple_native.md]]"
  - "[[51_jinja2_adapter_prototype.md]]"
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
