---
title: VS Code Packaging and LSP Init Contract Hardening
id: 57
status: testing
related_commit: []
dependencies:
  - "[[45_implement_lsp_language_features.md]]"
  - "[[46_integration_and_performance_tests.md]]"
estimated_hours: 6
priority: high
---

## Goal

Harden the VS Code extension packaging and initialization contract so extension artifacts are publishable and semantic settings are reliably passed to the LSP server.

## Deliverables

- Valid extension manifest for packaging (`activationEvents`, package file list)
- CI check that validates extension packaging metadata (`vsce ls`)
- Extension settings and initialization options for:
  - `temple.semanticSchemaPath`
  - `temple.semanticContext`
- LSP server support for canonical `semanticSchemaPath` initialization option
- Smoke test coverage validating initialization + language-feature path

## Acceptance Criteria

- `npm run package:check` passes locally and in CI
- Extension settings are documented and wired through to LSP initialization
- LSP server loads schema from path option and preserves raw schema for hover docs
- Smoke tests cover completion, hover, definition, references, and rename

