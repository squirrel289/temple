---
title: "Define base cleaning contract and markdown policy adapter"
id: 84
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
  - "[[80_replace_linter_regex_line_parsing_with_core_token_span_metadata.md]]"
related_backlog:
  - "archive/76_generalize_focus_mode_and_diagnostic_hygiene_across_base_types.md"
related_spike:
  - "79_audit_cross_layer_dry_and_grammar_anchoring.md"
notes: |
  Finding: markdown-specific cleanup is valid adapter policy, but it should run
  on a well-defined core cleaning contract rather than ad hoc line regex passes.
---

## Goal

Define a formal base-cleaning contract (core output + metadata) and keep markdown behavior as an adapter policy module on top of that contract.

## Background

Temple should provide consistent template semantics; language-specific lint compatibility belongs to pluggable base-format adapters.

## Tasks

1. Specify contract for cleaned text and associated metadata required for adapter policies.
2. Extract markdown-specific cleanup into a distinct policy adapter boundary.
3. Ensure future base-type policies can plug in without touching core semantics.
4. Add tests asserting contract invariants and markdown policy behavior.

## Deliverables

- Contract docs and types/interfaces for base-cleaning output.
- Markdown adapter policy module using contract inputs.
- Tests for contract invariants and adapter outcomes.

## Acceptance Criteria

- [ ] Core cleaning behavior is language-agnostic and contract-driven.
- [ ] Markdown-specific behavior is isolated behind an adapter policy boundary.
- [ ] Contract + adapter tests pass and are documented for future base types.
