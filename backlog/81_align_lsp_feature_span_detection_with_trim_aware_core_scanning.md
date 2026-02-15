---
title: "Align LSP feature span detection with trim-aware core scanning"
id: 81
status: not_started
state_reason: null
priority: high
complexity: medium
estimated_hours: 8
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[79_audit_cross_layer_dry_and_grammar_anchoring.md]]"
  - "[[78_add_author_controlled_whitespace_trim_tokens.md]]"
related_backlog:
  - "archive/45_implement_lsp_language_features.md"
related_spike:
  - "79_audit_cross_layer_dry_and_grammar_anchoring.md"
notes: |
  Finding: lsp_features relies on delimiter regexes that are not trim-marker
  aware and can diverge from grammar behavior.
---

## Goal

Make LSP feature span detection use shared core scanning/token utilities so completion/hover/definition behavior matches parser/tokenizer semantics.

## Background

`lsp_features.py` currently uses raw regex patterns for expressions/statements/includes. This can drift from grammar updates and trim-marker support.

## Tasks

1. Introduce or reuse core span scanning APIs for expression and statement regions.
2. Replace `_EXPR_RE` / `_STMT_RE` dependent logic in `lsp_features.py`.
3. Ensure include discovery handles trim forms and partial/unclosed tags consistently.
4. Add/extend LSP feature tests for trim and incomplete-token scenarios.

## Deliverables

- LSP feature scanning aligned to core behavior.
- Reduced regex duplication in `lsp_features.py`.
- Test coverage for trim-aware and unclosed-tag flows.

## Acceptance Criteria

- [ ] LSP feature logic no longer depends on trim-unaware raw delimiter regexes.
- [ ] Features behave consistently for `{%- ... -%}` and `{{~ ... ~}}`.
- [ ] Existing LSP feature tests pass with new coverage added.
