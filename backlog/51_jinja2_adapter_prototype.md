---
title: Jinja2 Adapter Prototype
id: 51
status: proposed
related_commit:
  - 6d8c044  # ADAPTER_SPEC.md added
dependencies:
  - "[[50_adapter_spec_impl.md]]"
estimated_hours: 40
priority: high
---

## Goal

Build a prototype adapter `temple.adapters.jinja2` that parses templates with Jinja2, walks the Jinja2 AST, produces the Temple IR, and emits diagnostics mapped to original source ranges.

## Deliverables

- Prototype adapter module `temple/adapters/jinja2_adapter.py`
- Source mapping heuristics for Jinja2 nodes → original ranges
- Mapping for a set of built-in filters to Temple filter signatures
- Parity fixtures comparing native and adapter diagnostics

## Acceptance Criteria

- Prototype can process representative templates and produce IR
- Diagnostics for undefined variables and simple type mismatches are produced and mapped
- Adapter documented with examples
