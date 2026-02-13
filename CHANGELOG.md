# Changelog

All notable changes to this repository will be documented in this file.

## [Unreleased]

### Added
- VS Code extension packaging guardrails (`activationEvents`, package-content checks, CI `vsce ls` validation).
- Schema-backed semantic linting coverage for undefined variables, missing properties, and type mismatches.
- LSP smoke tests covering initialization, diagnostics publishing, completion, hover, definition, references, and rename.
- Stable editor-facing settings contract for semantic schema/context configuration.
- Repository-level MIT `LICENSE`.

### Changed
- Temple type checker now initializes variable/type bindings from schema definitions (not only runtime context).
- VS Code extension now reads `temple.semanticSchemaPath` and `temple.semanticContext`, resolves schema paths, and passes them to LSP initialization.
- LSP server now supports `semanticSchemaPath` as the canonical initialization key (with `schemaPath` compatibility fallback).

