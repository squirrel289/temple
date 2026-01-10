---
title: "35_typed_dsl_type_system"
status: ready
priority: High
complexity: High
estimated_effort: 1.5 weeks
dependencies:
  - [[34_typed_dsl_parser.md]]
related_backlog:
  - [[36_typed_dsl_diagnostics.md]]
  - [[37_typed_dsl_serializers.md]]
related_spike:
  - archive/30_typed_dsl_prototype.md (reference implementation)
---

# 35 — Typed DSL: Type System & Schema Validation

Goal
----
Implement a complete type system for typed templates, enabling compile-time schema validation and rejection of structurally-invalid outputs before rendering.

Deliverables
----------
- `temple/src/temple/compiler/types.py` — type system (scalars, collections, unions, references)
- `temple/src/temple/compiler/schema.py` — schema definitions (JSON Schema subset, custom schema DSL)
- `temple/src/temple/compiler/type_checker.py` — AST walker + semantic analysis + type inference
- `temple/src/temple/compiler/type_errors.py` — type error reporting with position mapping
- Unit tests covering type checking rules and schema validation
- Documentation: Type system reference and schema specification

Acceptance Criteria
------------------
- Type checker rejects templates that would produce structurally-invalid JSON/YAML/TOML
- Type errors include source position and actionable suggestions
- Schema can be declared in template (comment block) or external file
- Supports common type patterns: objects, arrays, unions, nullability, constraints
- Test coverage ≥ 85% for type system

Type System Features
-------------------
- **Base Types**: String, Number, Boolean, Null
- **Collections**: Array, Object, Tuple (fixed-size array)
- **Unions**: Optional types, discriminated unions
- **Constraints**: Min/max length, regex patterns, enums
- **References**: Named types, recursive types
- **Schema Inference**: Infer schema from data or template structure

Tasks
-----
1. Design type system and schema language (extend JSON Schema or custom DSL)
2. Implement type representations and inference engine
3. Build semantic analyzer (walks AST, assigns types, checks constraints)
4. Implement type error reporter with position mapping to template
5. Add test suite covering type rules and edge cases
6. Document type system and schema format

Notes
-----
- **Reference**: Spike 30 (`schema_checker.py`) shows basic schema validation
- **Scope**: Focus on compile-time checking; runtime type coercion handled by serializers
- **Schema Location**: Support `@schema` comment blocks and external `.schema` files
- **Integration**: Output type-decorated AST for serializers (item 37)
