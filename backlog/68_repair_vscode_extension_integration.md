---
title: "Repair VS Code Extension Build and Integration"
id: 68
status: not_started
state_reason: null
priority: medium
complexity: medium
estimated_hours: 10
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[67_fix_lsp_base_diagnostics_transport.md]]"
related_backlog:
  - "45_implement_lsp_language_features.md"
related_spike: []
notes: |
  Focuses on TypeScript compile stability and removing dead/duplicated request paths.
---

## Goal

Make `vscode-temple-linter` compile cleanly and interoperate predictably with the Python LSP server by removing invalid/duplicated connection code and fixing current TypeScript errors.

## Background

The extension currently fails strict TypeScript compile and contains mixed connection patterns that increase runtime ambiguity.

## Tasks

1. **Fix compile-time TypeScript errors**
   - Resolve `LspDiagnostic['code']` typing issue and any dependent errors

2. **Remove dead or duplicate connection wiring**
   - Keep a single authoritative request/notification path for extension-server interactions

3. **Harden request handlers and diagnostics mapping**
   - Validate payload shapes and maintain stable conversion behavior

4. **Add extension-level validation checks**
   - Add minimal smoke checks for compile + lint + request handler behavior

## Deliverables

- Updated `vscode-temple-linter/src/extension.ts`
- Supporting TypeScript config/package script adjustments if needed
- Added/updated checks for extension build stability

## Acceptance Criteria

- [ ] `npm run compile` succeeds without TypeScript errors
- [ ] `npm run lint` passes
- [ ] Base diagnostics request handler remains functional
- [ ] Extension code no longer contains duplicate connection setup paths
