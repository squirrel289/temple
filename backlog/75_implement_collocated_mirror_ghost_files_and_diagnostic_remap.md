---
title: "Implement collocated mirror ghost files and diagnostic remapping"
id: 75
status: not_started
state_reason: null
priority: high
complexity: high
estimated_hours: 16
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[74_implement_base_lint_strategy_resolver_and_capability_registry.md]]"
related_backlog:
  - "archive/67_fix_lsp_base_diagnostics_transport.md"
related_spike: []
notes: |
  Mirror-file fallback must preserve nested workspace config resolution while
  keeping ghost artifacts hidden, cleaned up, and mapped back to source URIs.
---

## Goal

Implement robust mirror-file fallback that writes collocated ghost files for base tools, remaps diagnostics back to `.tmpl` source locations, and avoids repository pollution.

## Background

Temp-directory mirrors caused incorrect ownership, stale diagnostics, missing source mapping, and config resolution mismatches for tools that read nested workspace config.

## Tasks

1. **Implement collocated ghost pathing**
   - Create deterministic hidden sibling ghost files near source templates.
   - Ensure paths are excluded from repo and hidden from normal editor flows.

2. **Map diagnostics to source document**
   - Convert base-tool diagnostics from ghost URI to original `.tmpl` URI.
   - Preserve code, severity, and message fidelity.

3. **Lifecycle + failsafe cleanup**
   - Cleanup on close/reload/deactivate.
   - Add stale ghost sweeper and startup recovery.

4. **Validation**
   - Unit tests for pathing, remap correctness, cleanup behavior.
   - Integration test validating markdownlint owner diagnostics appear only on source file.

## Deliverables

- Mirror ghost manager with cleanup strategy.
- Diagnostic remapping layer with test coverage.
- Default ignore patterns/docs for ghost paths.

## Acceptance Criteria

- [ ] Base-tool diagnostics are attached to original `.tmpl` documents, not ghost files.
- [ ] Ghost file strategy resolves nested workspace configs correctly.
- [ ] Ghost files are hidden and cleaned automatically with failsafe behavior.
- [ ] No repo pollution from ghost files in normal workflows.
