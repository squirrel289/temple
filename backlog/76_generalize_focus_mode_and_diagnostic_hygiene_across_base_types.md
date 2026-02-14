---
title: "Generalize focus mode and diagnostic hygiene across base types"
id: 76
status: not_started
state_reason: null
priority: high
complexity: medium
estimated_hours: 12
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[archive/74_implement_base_lint_strategy_resolver_and_capability_registry.md]]"
  - "[[archive/75_implement_collocated_mirror_ghost_files_and_diagnostic_remap.md]]"
related_backlog:
  - "archive/69_align_docs_linting_and_vscode_workflow.md"
related_spike: []
notes: |
  Focus mode must apply to all base languages and avoid penalizing template
  control syntax while preserving meaningful base-language diagnostics.
---

## Goal

Provide cross-language focus mode and diagnostics hygiene controls that suppress noise from template syntax while preserving actionable base-language linting.

## Background

Current markdown examples show false positives from templating constructs, duplicated diagnostics, and low-clarity parse errors with internal token labels.

## Tasks

1. **Generalize focus mode**
   - Replace markdown-specific focus controls with base-language-agnostic setting.
   - Define consistent behavior for line elision/replacement and position mapping.

2. **Diagnostic deduplication and normalization**
   - Deduplicate repeated diagnostics from base + temple channels.
   - Normalize parser/token errors into user-facing messages with literal expected tokens.

3. **Position quality improvements**
   - Improve mismatch/unterminated-token positioning heuristics.
   - Add guardrails against line-1/col-1 fallback spam.

4. **Tests**
   - Add unit and integration tests for false-positive suppression, dedupe, and message clarity.

## Deliverables

- New generalized focus mode setting and behavior docs.
- Diagnostic dedupe/normalization implementation.
- Expanded diagnostics test suite.

## Acceptance Criteria

- [ ] Focus mode works across all base types (not markdown-only).
- [ ] Duplicate diagnostics are eliminated for same source/code/range/message.
- [ ] Invalid token errors avoid internal grammar token names when possible.
- [ ] Position mapping significantly reduces incorrect line/column fallback.
