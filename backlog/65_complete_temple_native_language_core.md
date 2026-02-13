---
title: "Complete Temple Native Language Core for MVP Templates"
id: 65
status: testing
state_reason: null
priority: high
complexity: high
estimated_hours: 24
actual_hours: 6
completed_date: null
related_commit: []
test_results: "27 parser/integration tests pass, 16 type-checker tests pass, 63 serializer tests pass; new MVP language-core test suite added."
dependencies:
  - "[[archive/64_fix_linter_packaging_entrypoints.md]]"
  - "[[54_complete_temple_native.md]]"
related_backlog:
  - "54_complete_temple_native.md"
related_spike: []
notes: |
  Focuses on missing language constructs required by documented examples and benchmark fixtures.
  Implemented Set AST support with runtime assignment semantics and type-checker binding support.
  Added canonical `elif` parsing while preserving `else if` compatibility.
  Added expression evaluation support for list literals and boolean/comparison operators.
  Updated serializer variable lookup/evaluation paths to use shared expression evaluation semantics.
  Added focused MVP language-core regression tests.
---

## Goal

Implement the missing Temple-native language features required for a usable MVP template authoring experience: `{% set %}`, canonical `elif`, list literals, and minimal expression/operator support used by official examples.

## Background

The parser/type/eval stack exists, but key constructs in docs and fixtures are currently unsupported or partially ignored. This creates a mismatch between advertised syntax and runtime capability.

## Tasks

1. **Add missing grammar and AST coverage**
   - Implement AST representation and transform logic for `{% set %}`
   - Normalize `elif` handling to match canonical syntax
   - Add list literal parsing support

2. **Expand expression support for MVP**
   - Support minimal boolean/comparison operators needed by examples
   - Ensure evaluator and type-checker handle supported constructs consistently

3. **Wire feature behavior into rendering pipeline**
   - Ensure parser output is consumed by typed evaluation and serializers without silent drops

4. **Update and expand tests**
   - Add parser/evaluator tests for new constructs
   - Add regression tests using representative templates currently failing semantics

## Deliverables

- Updates to grammar, parser transformer, and AST models
- Updates to evaluator and type-checker for new constructs
- Expanded tests across parser, integration, and example fixtures

## Acceptance Criteria

- [ ] `{% set %}` statements are parsed and evaluated with defined scoping rules
- [ ] `elif` syntax is supported in canonical form and validated
- [ ] List literals parse and evaluate correctly
- [ ] Official template examples avoid unsupported syntax for MVP surface area
- [ ] New and existing language-core tests pass
