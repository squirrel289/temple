---
title: "30_typed_dsl_prototype"
status: proposed
priority: Medium
complexity: Medium
estimated_effort: 2 weeks
dependencies:
  - [[06_rendering_engine.md]]
related_backlog:
  - [[25_expression_rendering.md]]
  - [[26_control_flow_rendering.md]]
---

# 30 — Structured / Typed Template AST (Spike)

Goal
----
Prototype a minimal structured/typed template DSL (AST-based) that enables compile-time schema checks for JSON-style outputs and produces a target-neutral IR that can be serialized by small per-target serializers.

Deliverables
----------
- `temple/src/temple/typed_ast.py` — minimal AST node types (`Text`, `Expression`, `If`, `For`, `Include`, `Block`)
- Compiler / semantics engine that evaluates the AST into a target-neutral IR
- Two lightweight serializers: JSON and Markdown (examples of per-target serializers)
- Example templates in `examples/typed/` demonstrating common patterns
- Unit tests covering AST construction, semantic evaluation, and schema validation
- Backlog doc (this file) with acceptance criteria and tasks

Acceptance criteria
-------------------
- A small sample template compiles to an IR without executing arbitrary code
- Provided schema checks can reject templates that would produce structurally-invalid JSON (e.g., mixing object/array where schema expects one)
- Serializers produce valid JSON and Markdown for the IR
- Tests demonstrating mapping from IR errors back to template node locations

Success metrics
---------------
- Prototype implements at least 6 AST node types and 2 serializers
- Unit tests + examples run locally via pytest

Tasks
-----
1. Define AST node classes and small parser helpers in `typed_ast.py`.
2. Implement a semantics engine that evaluates nodes against input data to produce IR.
3. Implement a JSON serializer and a Markdown serializer that accept the IR.
4. Add example templates to `examples/typed/` and small test harness under `temple/tests/`.
5. Add docs/usage examples and run tests.

Notes / Constraints
------------------
- Keep the prototype minimal — focus on shape validation and mapping diagnostics to AST nodes.
- Do not implement a full template parser; examples can use programmatic AST construction or a tiny hand-rolled parser for the limited syntax.
