# Temple Backlog

## Current Status

The Temple project is executing a **Typed DSL Compiler MVP** (8-week effort) after completing architectural decision-making (see `archive/33_decision_snapshot.md`).

### Active Work Items (Production MVP)

The following 4 items form the critical path for the typed DSL compiler:

1. **[archive/34_typed_dsl_parser.md](archive/34_typed_dsl_parser.md)** — Parser & AST Construction (2 weeks)
   - Status: ✅ `complete`
   - Deliverables: Tokenizer, parser, AST nodes with position tracking
   - Completed: 2026-01-09

2. **[archive/35_typed_dsl_type_system.md](archive/35_typed_dsl_type_system.md)** — Type System (1.5 weeks)
   - Status: ✅ `complete`
   - Deliverables: Type checker, schema validation, constraint checking
   - Completed: 2026-01-09

3. **[archive/36_typed_dsl_diagnostics.md](archive/36_typed_dsl_diagnostics.md)** — Error Diagnostics & Source Mapping (1 week)
   - Status: ✅ `complete`
   - Deliverables: Diagnostic engine, source position mapping, error formatting
   - Completed: 2026-01-09

4. **[archive/37_typed_dsl_serializers.md](archive/37_typed_dsl_serializers.md)** — Multi-Format Serializers (2 weeks)
   - Status: ✅ `complete`
   - Deliverables: JSON, Markdown, HTML, YAML serializers with type coercion
   - Completed: 2026-01-09

**Timeline**: 6.5 weeks development + 1.5 weeks integration/testing = **8 weeks total**

---

## Archive

The `archive/` folder contains:

- **Spike items** (30-33): Completed spike work and architectural decision documentation
  - `archive/30_typed_dsl_prototype.md` — Proof-of-concept typed DSL implementation
  - `archive/32_spikes_docs_and_hooks.md` — Archived (spike docs overhead)
  - `archive/33_decision_snapshot.md` — Architectural decision, risk analysis, future epics

- **Obsolete items** (01-29): Old prototype work superseded by typed DSL approach
  - Original research phase: items 01-03 (DSL syntax, query language, data parsers)
  - First-generation prototype: items 04-28 (untyped parser, rendering engine, etc.)
  - These describe the "pass-through renderer" approach which was evaluated and rejected in favor of typed DSL

### Future Epics (Documented in archive/33_decision_snapshot.md)

After the MVP is complete:

1. **Template Validation & Linting** — LSP integration, live diagnostics in editors
2. **Query Language** — JMESPath support, schema-aware query validation
3. **User-Defined Functions** — Template reusability, custom operators

### Post-MVP Work: Temple-Linter Integration (Items 42-47)

Following completion of the typed DSL compiler MVP (items 34-37) and documentation (items 38-41), the next phase integrates temple core functionality into temple-linter:

5. **[42_integrate_temple_core_dependency.md](42_integrate_temple_core_dependency.md)** — Add temple as dependency (2 hours)
   - Status: 🔄 `not_started`
   - Priority: HIGH
   - Deliverables: Update pyproject.toml, verify imports, update dev setup docs

6. **[43_implement_template_syntax_validation.md](43_implement_template_syntax_validation.md)** — Parser integration (8 hours)
   - Status: 🔄 `not_started`
   - Priority: HIGH
   - Depends on: #42
   - Deliverables: Replace TemplateLinter stub with real parser, detect syntax errors

7. **[44_implement_semantic_validation.md](44_implement_semantic_validation.md)** — Type checker integration (12 hours)
   - Status: 🔄 `not_started`
   - Priority: HIGH
   - Depends on: #42, #43
   - Deliverables: Schema loading, undefined variable detection, type mismatch checking

8. **[45_implement_lsp_language_features.md](45_implement_lsp_language_features.md)** — IDE features (16 hours)
   - Status: 🔄 `not_started`
   - Priority: MEDIUM
   - Depends on: #42, #43, #44
   - Deliverables: Completions, hover, go-to-definition, find references, rename

9. **[46_integration_and_performance_tests.md](46_integration_and_performance_tests.md)** — E2E testing (10 hours)
   - Status: 🔄 `not_started`
   - Priority: MEDIUM
   - Depends on: #42, #43, #44, #45
   - Deliverables: Integration tests, performance benchmarks, regression tests

10. **[47_documentation_updates_for_core_integration.md](47_documentation_updates_for_core_integration.md)** — Docs (6 hours)
    - Status: 🔄 `not_started`
    - Priority: MEDIUM
    - Depends on: #42, #43, #44, #45
    - Deliverables: Updated README, architecture docs, user guide, API reference, migration guide

**Temple-Linter Integration Timeline**: 54 hours (≈7 days) for complete temple core integration

---

## Structure

```
backlog/
├── README.md                                    (this file)
├── temple.md                                    (project vision & scope)
├── 42_integrate_temple_core_dependency.md      (temple-linter: add dependency)
├── 43_implement_template_syntax_validation.md  (temple-linter: parser integration)
├── 44_implement_semantic_validation.md         (temple-linter: type checker)
├── 45_implement_lsp_language_features.md       (temple-linter: IDE features)
├── 46_integration_and_performance_tests.md     (temple-linter: testing)
├── 47_documentation_updates_for_core_integration.md (temple-linter: docs)
└── archive/
    ├── 30_typed_dsl_prototype.md               (spike: reference implementation)
    ├── 32_spikes_docs_and_hooks.md             (spike: archived)
    ├── 33_decision_snapshot.md                 (decision: why typed DSL)
    ├── 34_typed_dsl_parser.md                  (completed: parser & AST)
    ├── 35_typed_dsl_type_system.md             (completed: type system)
    ├── 36_typed_dsl_diagnostics.md             (completed: diagnostics)
    ├── 37_typed_dsl_serializers.md             (completed: serializers)
    ├── 38_integration_and_e2e_tests.md         (completed: testing)
    ├── 39_performance_benchmarks.md            (completed: benchmarks)
    ├── 40_ci_integration_and_docs.md           (completed: CI/docs)
    ├── 41_canonical_examples_and_docs.md       (completed: examples)
    └── 01-29_*.md                              (obsolete: old prototype)
```

---

## Key References

- **Architecture**: [temple/docs/ARCHITECTURE.md](../temple/docs/ARCHITECTURE.md)
- **Typed DSL Decision**: [archive/33_decision_snapshot.md](archive/33_decision_snapshot.md)
- **Spike Reference**: [archive/30_typed_dsl_prototype.md](archive/30_typed_dsl_prototype.md)
- **Project Vision**: [temple.md](temple.md)

---

## How to Use This Backlog

1. **For Item 34 (start now)**:
   - Read: [34_typed_dsl_parser.md](34_typed_dsl_parser.md) for detailed tasks and acceptance criteria
   - Reference: `archive/30_typed_dsl_prototype.md` for Lark grammar and tokenizer patterns
   - Create: `temple/src/temple/compiler/` directory structure

2. **For Items 35-37** (after 34 completes):
   - Each item depends on the previous one's AST output
   - Follow acceptance criteria and key features sections
   - Add tests incrementally as you build

3. **For Understanding Context**:
   - Why typed DSL?: Read `archive/33_decision_snapshot.md` executive summary
   - What was considered?: See obsolete items in `archive/` (research phase)
   - Project goals?: See [temple.md](temple.md) and `temple/docs/ARCHITECTURE.md`

---

## Status Summary

### Typed DSL Compiler MVP (Completed)

| Item | Title | Status | Effort | Completed |
|------|-------|--------|--------|-----------|
| 34 | Parser & AST | ✅ complete | 2w | 2026-01-09 |
| 35 | Type System | ✅ complete | 1.5w | 2026-01-09 |
| 36 | Diagnostics | ✅ complete | 1w | 2026-01-09 |
| 37 | Serializers | ✅ complete | 2w | 2026-01-09 |
| 38 | Integration Tests | ✅ complete | 1w | 2026-01-11 |
| 39 | Benchmarks | ✅ complete | 1w | 2026-01-11 |
| 40 | CI & Docs | ✅ complete | 1w | 2026-01-13 |
| 41 | Examples & Docs | ✅ complete | 1w | 2026-01-15 |
| **MVP Total** | | ✅ | **10w** | |

### Temple-Linter Integration (Not Started)

| Item | Title | Status | Effort | Blocker |
|------|-------|--------|--------|---------|
| 42 | Core Dependency | 🔄 not_started | 2h | None |
| 43 | Syntax Validation | 🔄 not_started | 8h | #42 |
| 44 | Semantic Validation | 🔄 not_started | 12h | #42, #43 |
| 45 | LSP Features | 🔄 not_started | 16h | #42, #43, #44 |
| 46 | Integration Tests | 🔄 not_started | 10h | #42-#45 |
| 47 | Documentation | 🔄 not_started | 6h | #42-#45 |
| **Linter Total** | | 🔄 | **54h (~7d)** | |

---

Last updated: 2026-01-09
