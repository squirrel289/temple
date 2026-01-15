---
title: Complete Temple-native Templating & Linting
id: 54
status: proposed
related_commit:
  - 6d8c044  # docs(adr): clarify market role and adapter architecture (ADR-003); add adapter spec; archive backlog/48_jinja_integration.md
dependencies:
  - "[[19_unified_token_model.md]]"
estimated_hours: 40
priority: critical
---

## Goal

Finish the remaining Temple-native implementation work required for an initial stable release: filters (typed), `{% set %}`, list literals, `{% elif %}` grammar fix, diagnostics hardening, and test completion.

## Deliverables

- Fix `{% elif %}` grammar bug
- Implement list literals
- Implement `{% set %}` with proper scoping
- Implement `FilterAdapter` with initial core filters (`selectattr`, `map`, `join`, `default`) and typed signatures
- Add unit and integration tests; reach parity with existing test expectations
- Release notes and changelog entry

## Acceptance Criteria

- All temple-native tests pass in CI
- Filter signatures present in filter registry
- Diagnostics and source mapping validated against representative fixtures
