---
title: "Centralize temple default delimiters and extensions across layers"
id: 85
status: not_started
state_reason: null
priority: medium
complexity: medium
estimated_hours: 7
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[79_audit_cross_layer_dry_and_grammar_anchoring.md]]"
related_backlog:
  - "archive/22_configurable_temple_extensions.md"
related_spike:
  - "79_audit_cross_layer_dry_and_grammar_anchoring.md"
notes: |
  Finding: default delimiters and temple extension defaults are duplicated
  across core, linter, and VS Code extension layers.
---

## Goal

Create a single source of truth for default temple delimiters and extension values, with explicit override flow across extension/linter/core.

## Background

Multiple default declarations increase drift risk and complicate maintenance when supported suffixes or delimiter behavior evolves.

## Tasks

1. Inventory default delimiter/extension declarations and choose canonical owner(s).
2. Implement shared config export/import path (or generated artifact) for each runtime.
3. Update linter server and extension initialization to consume centralized defaults.
4. Add tests that verify parity across layers.

## Deliverables

- Centralized defaults contract for delimiters and temple extensions.
- Refactored consumers in core/linter/extension.
- Cross-layer parity tests.

## Acceptance Criteria

- [ ] Default delimiters are not hard-coded in multiple runtime modules.
- [ ] Temple extension defaults are centrally defined and consumed consistently.
- [ ] Override behavior remains supported and test-covered.
