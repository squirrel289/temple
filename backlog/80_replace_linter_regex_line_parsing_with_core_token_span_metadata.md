---
title: "Replace linter regex line parsing with core token-span metadata"
id: 80
status: not_started
state_reason: null
priority: high
complexity: high
estimated_hours: 10
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[79_audit_cross_layer_dry_and_grammar_anchoring.md]]"
  - "[[78_add_author_controlled_whitespace_trim_tokens.md]]"
related_backlog:
  - "archive/24_optimize_base_linting_diagnostics.md"
related_spike:
  - "79_audit_cross_layer_dry_and_grammar_anchoring.md"
notes: |
  Finding: token_cleaning_service still uses local inline-template regex to
  classify template-only/mixed lines and perform replacements.
---

## Goal

Eliminate linter-local template-structure regex parsing by using core tokenizer-derived token-span metadata.

## Background

`token_cleaning_service.py` currently combines tokenizer output with direct regex passes. This duplicates syntax knowledge and risks divergence from trim-aware grammar semantics.

## Tasks

1. Add a core utility that returns per-line template span classification and line metadata.
2. Refactor `TokenCleaningService` to consume that utility instead of `_INLINE_TEMPLATE_TOKEN_RE` structural matching.
3. Preserve markdown policy behavior while removing duplicated parsing logic.
4. Expand tests for trim markers, mixed lines, and template-only lines.

## Deliverables

- Core token-span metadata helper in `temple`.
- Refactored `temple-linter` cleaner without structure regex coupling.
- Regression tests covering previous false-positive scenarios.

## Acceptance Criteria

- [ ] `TokenCleaningService` no longer uses regex to detect template tags for structure decisions.
- [ ] Trim-marker behavior remains correct and test-covered.
- [ ] Existing cleaning-focused integration tests pass.
