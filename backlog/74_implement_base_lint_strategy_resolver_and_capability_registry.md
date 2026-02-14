---
title: "Implement base-lint strategy resolver and capability registry"
id: 74
status: not_started
state_reason: null
priority: critical
complexity: high
estimated_hours: 14
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[73_lock_base_lint_strategy_and_publish_adr_005.md]]"
related_backlog:
  - "archive/67_fix_lsp_base_diagnostics_transport.md"
related_spike: []
notes: |
  Introduce a single strategy resolver for base linting: embedded, virtual,
  mirror-file. Include mode setting and capability registry extension points.
---

## Goal

Add a deterministic strategy resolver that selects `embedded`, `virtual`, or `mirror-file` based on configuration and discovered capabilities, with `auto` as default.

## Background

Current behavior is fragmented across extension/linter boundaries and does not consistently represent how a base linter should be invoked for each file type or host extension capability.

## Tasks

1. **Add mode and resolver contracts**
   - Add settings for strategy mode (`auto|embedded|vscode`) and diagnostics logging level.
   - Add resolver contract and tests for precedence and fallbacks.

2. **Add capability registry**
   - Define adapter capability metadata and registration points.
   - Support explicit capability declaration first, runtime probing only as fallback.

3. **Wire resolver through extension and linter boundaries**
   - Route base lint requests through resolver-selected strategy.
   - Emit structured trace events for chosen strategy and fallback reason.

4. **Regression tests**
   - Unit tests for resolver decisions and mode behavior.
   - Integration tests for strategy selection across at least markdown/json fixtures.

## Deliverables

- Strategy resolver implementation in extension + linter path.
- Capability registry abstraction and tests.
- New settings documented in extension README.

## Acceptance Criteria

- [ ] `auto` mode selects the highest available strategy by precedence.
- [ ] Explicit mode honors user selection with clear fallback diagnostics when unsupported.
- [ ] Strategy decision is test-covered and observable in logs.
- [ ] No regressions in existing Temple diagnostics pipeline.
