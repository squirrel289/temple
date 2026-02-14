---
title: "Add base-lint queueing, adaptive debounce, and observability"
id: 77
status: not_started
state_reason: null
priority: critical
complexity: high
estimated_hours: 16
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[archive/74_implement_base_lint_strategy_resolver_and_capability_registry.md]]"
  - "[[archive/75_implement_collocated_mirror_ghost_files_and_diagnostic_remap.md]]"
related_backlog:
  - "archive/46_integration_and_performance_tests.md"
related_spike: []
notes: |
  Performance and stale diagnostics are currently the major UX blocker. Add
  lightweight queueing and adaptive scheduling with configurable trace levels.
---

## Goal

Make diagnostics feel real-time and reliable by introducing queueing, cancellation, adaptive debounce, and structured observability for base lint runs.

## Background

Current latency can exceed user edit cadence, creating stale or misleading diagnostics that refer to no-longer-existing errors.

## Tasks

1. **Introduce lint task queue**
   - Add per-document queue with cancellation/coalescing of stale runs.
   - Ensure at-most-one active base lint task per document.

2. **Adaptive debounce policy**
   - Adjust debounce by file size/latency profile.
   - Reset caches on extension reload and workspace reopen.

3. **Add telemetry-like trace logs**
   - Structured log levels (`error|warn|info|debug|trace`) in settings.
   - Emit request lifecycle timing and cancellation stats.

4. **Performance tests**
   - Add synthetic editing burst tests to verify stale diagnostic suppression.
   - Set target thresholds for p50/p95 diagnostic latency.

## Deliverables

- Queue/scheduler implementation for base lint requests.
- Adaptive debounce and cancellation controls.
- Logging level configuration and timing instrumentation.

## Acceptance Criteria

- [ ] Stale diagnostics are canceled/suppressed during rapid edits.
- [ ] Diagnostic latency is materially reduced and measurable via tests/logs.
- [ ] Cache reset behavior is deterministic on extension reload.
- [ ] Log verbosity is user-configurable without noisy defaults.
