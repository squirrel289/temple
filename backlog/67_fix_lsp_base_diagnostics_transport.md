---
title: "Fix LSP Base Diagnostics Transport Wiring"
id: 67
status: testing
state_reason: null
priority: high
complexity: medium
estimated_hours: 12
actual_hours: 5
completed_date: null
related_commit: []
test_results: "31 temple-linter transport/integration tests pass (test_lsp_transport_wiring, test_base_linting_service, test_integration, test_lsp_entrypoint). Ruff passes on updated transport files."
dependencies:
  - "[[66_integrate_semantic_validation_in_temple_linter.md]]"
related_backlog:
  - "45_implement_lsp_language_features.md"
related_spike: []
notes: |
  Corrects server-client transport assumptions so base-linter delegation works in real LSP sessions.
  Replaced unbound LanguageClient singleton usage with active server-session transport wiring.
  BaseLintingService now resolves protocol transport from either callable server protocol() or client protocol attribute.
  Added transport-specific tests for success and graceful fallback when protocol transport is unavailable.
---

## Goal

Refactor `temple-linter` LSP request/response wiring so base diagnostics delegation uses the active LSP transport instead of an unbound client object.

## Background

The current server path relies on a standalone `LanguageClient` instance, which is not guaranteed to be connected to the session transport. This makes base-diagnostic delegation fragile or non-functional in production use.

## Tasks

1. **Redesign delegation contract for pygls session context**
   - Use server/session primitives compatible with request-response calls
   - Remove unbound client singleton assumptions

2. **Update orchestrator interfaces**
   - Pass request-capable session context explicitly
   - Preserve graceful degradation behavior if client capability is absent

3. **Add runtime and integration tests**
   - Verify delegation request dispatch and response handling
   - Verify fallback behavior on client request failure

## Deliverables

- Updated LSP server wiring in `temple-linter/src/temple_linter/lsp_server.py`
- Updated orchestrator/base-linting service interfaces
- Tests covering transport success/failure paths

## Acceptance Criteria

- [ ] Base diagnostics request path works in active LSP session context
- [ ] Failures are logged and degraded gracefully without crashes
- [ ] Existing diagnostics publishing behavior remains intact
- [ ] Integration tests pass for request transport flows
