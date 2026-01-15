---
title: Implement Adapter Interface & SDK
id: 55
status: proposed
related_commit:
  - 6d8c044  # added ADAPTER_SPEC.md and ADR-003
dependencies:
  - "[[003-market-role-and-adapter-architecture.md]]"
estimated_hours: 24
priority: high
---

## Goal

Design and implement the concrete adapter SDK in `temple/sdk/adapter.py` and document the adapter contract. Provide reference types (`AdapterParseResult`, `IR` nodes, `Diagnostic`) and unit tests for the adapter interfaces.

## Deliverables

- `temple/sdk/adapter.py` with typed Python interfaces
- Unit tests validating `parse_to_ir` and `source_map` behaviors
- Example usage docs and API docs in `temple/docs/ADAPTER_SPEC.md`

## Acceptance Criteria

- Adapter interfaces are type-annotated and importable
- Tests pass validating sample parse results and diagnostic shapes
- Documentation added linking to ADR-003
