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

3. **[36_typed_dsl_diagnostics.md](36_typed_dsl_diagnostics.md)** — Error Diagnostics & Source Mapping (1 week)
   - Status: `ready` (depends on 34, 35)
   - Deliverables: Diagnostic engine, source position mapping, error formatting
   - Key: Actionable error messages with source context

4. **[37_typed_dsl_serializers.md](37_typed_dsl_serializers.md)** — Multi-Format Serializers (2 weeks)
   - Status: `ready` (depends on 34, 35, 36)
   - Deliverables: JSON, Markdown, HTML, YAML serializers
   - Key: Valid output generation per format specifications

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

---

## Structure

```
backlog/
├── README.md                          (this file)
├── temple.md                          (project vision & scope)
├── 34_typed_dsl_parser.md            (active: parser & AST)
├── 35_typed_dsl_type_system.md       (active: type system)
├── 36_typed_dsl_diagnostics.md       (active: diagnostics)
├── 37_typed_dsl_serializers.md       (active: output generation)
└── archive/
    ├── 30_typed_dsl_prototype.md     (spike: reference implementation)
    ├── 32_spikes_docs_and_hooks.md   (spike: archived)
    ├── 33_decision_snapshot.md       (decision: why typed DSL, risks, future work)
    └── 01-29_*.md                    (obsolete: old prototype approach)
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

| Item | Title | Status | Effort | Blocker |
|------|-------|--------|--------|---------|
| 34 | Parser & AST | ready | 2w | None — **Start immediately** |
| 35 | Type System | ready | 1.5w | 34 |
| 36 | Diagnostics | ready | 1w | 34, 35 |
| 37 | Serializers | ready | 2w | 34, 35, 36 |
| **MVP Total** | | | **8w** | |

---

Last updated: 2026-01-09
