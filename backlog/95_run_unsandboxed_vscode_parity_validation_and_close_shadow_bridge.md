---
title: "Run unsandboxed VS Code parity validation and close shadow-bridge release gate"
id: 95
status: not_started
state_reason: null
priority: high
complexity: medium
estimated_hours: 6
actual_hours: null
completed_date: null
related_commit: []
test_results: null
dependencies:
  - "[[88_validate_diagnostics_pipeline_and_prepare_patch_release.md]]"
  - "[[89_implement_projection_snapshots_for_shadow_bridge.md]]"
  - "[[90_implement_shadow_document_lifecycle_and_diagnostic_ownership.md]]"
  - "[[91_proxy_base_language_lsp_features_with_edit_safety.md]]"
  - "[[92_add_templated_format_language_ids_and_generated_grammars.md]]"
  - "[[93_harden_transport_timeouts_and_watched_files_noise.md]]"
  - "[[94_define_parity_matrix_and_pr_scope_for_shadow_bridge_rollout.md]]"
related_backlog: []
related_spike: []
notes: |
  2026-02-16: Created to track the remaining release-gate activity that cannot
  be completed in the current sandbox due VS Code host SIGABRT during
  integration execution.
---

## Goal

Complete final host-level parity validation and release gating for the
shadow-bridge rollout.

## Background

Local compile/lint and Python test suites pass, but `npm --prefix
vscode-temple-linter run test:integration` still terminates with `SIGABRT` in
this sandboxed environment. Release confidence requires running the same matrix
in an unsandboxed IDE/CI host and capturing objective evidence.

## Explicit Target Extension Matrix

1. `vscode.markdown-language-features`
2. `DavidAnson.vscode-markdownlint`
3. `vscode.json-language-features`
4. `redhat.vscode-yaml`
5. `vscode.html-language-features`
6. `redhat.vscode-xml`
7. `tamasfe.even-better-toml`

## Tasks

1. **Run integration in unsandboxed host**
   - Execute `npm --prefix vscode-temple-linter run test:integration` in local
     IDE host or CI runner without sandbox SIGABRT.
   - Archive logs/artifacts for pass/fail triage.

2. **Manual smoke parity checks**
   - Validate `examples/templates/bench/real_small.md.tmpl` end-to-end:
     completion, hover, definition, references, symbols, rename, formatting,
     semantic tokens.
   - Confirm no `.temple-base-lint/*` diagnostics appear in Problems pane.

3. **Finalize PR/review loop**
   - Process review feedback and update statuses for work items 89-94.
   - Close release gate notes in 88 and 94.

## Deliverables

- Unsandboxed integration evidence logs.
- Manual parity checklist with pass/fail per target extension.
- Updated work-item statuses ready for final archival.

## Acceptance Criteria

- [ ] Integration suite passes in unsandboxed VS Code host.
- [ ] No mirror URI diagnostics appear in Problems pane during smoke tests.
- [ ] Target extension matrix has pass/fail evidence attached.
- [ ] Work items 88-94 are finalized with release-gate disposition.
