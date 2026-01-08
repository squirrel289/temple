# Temple: Meta-Templating System

## Vision

A developer-friendly, tree-based meta-templating system for structured data (JSON, XML, YAML, TOML, and future formats) that enables authoring templates in the target output format (Markdown, HTML, JSON, etc.) with:
- Lightweight, consistent logic DSL overlays
- Pluggable data format parsers and schema validators
- Unified query engine for all object models
- Schema-aware, query-validating, and output-linting at author time
- Real-time feedback and best-effort rendering with clear error messaging

## Essense
Once you abstract away the query engine, data structure type, templating tokens, output format, and linter—removing ASTs, schemas, and external dependencies—the **core purpose** of this system is:

**Declarative, logic-driven transformation of structured data into text, with a consistent, extensible authoring experience.**

What remains at the core:
- **A framework for expressing how to map, traverse, and render data into text.**
- **A minimal, composable logic language for describing transformations.**
- **A mechanism for binding data to template logic and emitting output.**

**In essence:**  
It is a universal, format-agnostic engine for declaratively describing and executing data-to-text transformations, with a focus on author experience, extensibility, and validation.

**The irreducible core:**
- **Template logic language** (how to express mapping, looping, conditionals, and function calls)
- **Transformation engine** (how to apply logic to data and produce output)
- **Extensibility hooks** (how to add new logic, functions, or integrations)

Everything else—ASTs, schemas, linters, query engines, etc.—are implementation details or optional enhancements. The heart is the ability to declaratively describe and execute transformations from structured data to text.

## Core Capabilities
1. **Tree-based templating logic**
2. **Lightweight DSLs**
   - Templating logic overlays (loops, conditionals, includes, user-defined functions)
   - Object-model querying (dot notation, JMESPath, etc.)
   - Pluggable data format parsers (JSON, XML, YAML, TOML, ...)
3. **Dev-time validation**
   - Template syntax linting
   - Query validation against input schema (JSON Schema, XML Schema, etc.)
   - Output format linting (markdownlint, htmlhint, JSON Schema, etc.)
4. **Post-rendering feedback**
   - Rendered document or best-effort output with error annotations
   - Clear, actionable error messaging

## User Story

As a template author, I want to write templates in the target output format using standard linters for that format, so I get real-time feedback. The templating DSL overlays the target format and must validate against it. The logic DSL is consistent across all formats, and insertion tokens may be format-specific, but logic is always the same. The system should support any structured data format (JSON, XML, YAML, TOML, etc.) via pluggable parsers and schema validators.

## Roadmap
- [ ] Define template DSL syntax and logic primitives (including user-defined functions)
- [ ] Design query language and schema validation integration (supporting multiple data formats)
- [ ] Build pluggable data format parsers and schema validators
- [ ] Build template parser and linter
- [ ] Integrate output format linters
- [ ] Implement rendering engine (object model input → output format)
- [ ] Error reporting and best-effort rendering
- [ ] CLI and/or editor integration for real-time feedback

## Structure
- `src/`: Source code
- `tests/`: Unit tests

## Setup
Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests
Add your tests in the `tests/` directory and run them with your preferred test runner.


---

## Current Status

Temple is in **specification phase**. The `docs/` directory contains authoritative specifications for the system architecture, DSL syntax, query language, and error reporting strategy. Reference implementations in `src/` demonstrate the concepts but are not production-ready.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the complete architecture specification and [`../ARCHITECTURE_ANALYSIS.md`](../ARCHITECTURE_ANALYSIS.md) for implementation roadmap and work items.