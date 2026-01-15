---
title: Canonical Examples & Developer Docs
id: 41
status: completed
related_commits: []
estimated_hours: 8
priority: medium
---

## Goal

Provide clear, runnable examples and developer-facing documentation for serializers and diagnostics APIs.

## Status: COMPLETED ✓

All deliverables created and integrated with existing codebase. Updated to use working dsl_examples with lark_parser/typed_renderer.

## Deliverables

### 1. DSL Examples Enhancement (`examples/dsl_examples/`)
- ✓ `sample_data.json` — Standardized input data used by all examples
- ✓ `run_example.py` — Reusable script to render all format examples (HTML, Markdown, Text, TOML)
- ✓ Utilizes existing verified templates: `html_positive.html.tmpl`, `md_positive.md.tmpl`, `text_positive.txt.tmpl`, `toml_positive.toml.tmpl`
- ✓ Uses proven working implementation: `lark_parser.parse_template()` and `typed_renderer.evaluate_ast()`
- ✓ Handles includes/ directory for headers/footers

### 2. Diagnostics API Documentation (`temple-linter/docs/diagnostics_api.md`)
- ✓ Diagnostic types: Severity levels, `Diagnostic` dataclass, `DiagnosticCollector`
- ✓ Error categories: Syntax, type, semantic errors with code examples
- ✓ Formatting: `ErrorFormatter` for human-readable messages with source context
- ✓ Diagnostic mapping: `TemplateMapping` and `DiagnosticMappingService` for LSP integration
- ✓ LSP conversion: Converting diagnostics to LSP format for IDE display
- ✓ Practical examples: Undefined variables, type mismatches, base format errors
- ✓ Error suppression syntax and acceptance criteria

### 3. Examples Quickstart Guide (`examples/README.md`)
- ✓ Directory structure overview updated to reflect dsl_examples/
- ✓ Python setup instructions
- ✓ Runnable DSL examples for all 4 formats (HTML, Markdown, Text, TOML)
- ✓ Usage instructions for run_example.py script
- ✓ Contributing guidelines for adding new examples
- ✓ Links to related projects and documentation

## Acceptance Criteria ✓

- ✓ Examples render with local commands and produce expected output
- ✓ run_example.py script works for all formats (HTML, Markdown, Text, TOML)
- ✓ sample_data.json provides standardized input data
- ✓ Examples use verified working implementation (lark_parser/typed_renderer)
- ✓ Diagnostics API documentation covers extension points and integration patterns
- ✓ Error handling and diagnostics mapping explained with practical examples
- ✓ Examples README includes contributing guidelines and setup instructions

## Implementation Notes

### Examples Organization
- Examples use existing `examples/dsl_examples/` with verified templates
- `sample_data.json` contains standardized user profile data matching test suite
- `run_example.py` script provides consistent interface for rendering all formats
- Uses `lark_parser.parse_template()` and `typed_renderer.evaluate_ast()` (proven working)
- Handles includes/ directory for template composition (headers/footers)

### Documentation Coverage
- **Diagnostics API:** 550+ lines covering error types, formatting, mapping, LSP integration, practical examples
- **Examples Guide:** Updated with dsl_examples structure, run_example.py usage, contributing guidelines

### Integration Points
- Examples/README links to `temple-linter/docs/diagnostics_api.md`
- Diagnostics docs links to Error Reporting Strategy
- All docs use consistent code block formatting and examples
- run_example.py integrates with existing test suite data model

## Files Created/Modified

### New Files
- `examples/dsl_examples/sample_data.json` — Standardized input data
- `examples/dsl_examples/run_example.py` — Reusable rendering script
- `temple-linter/docs/diagnostics_api.md` — Comprehensive diagnostics documentation

### Modified Files
- `examples/README.md` — Updated with dsl_examples structure and run_example.py usage

### Removed Files
- `examples/serializer_examples/` — Removed unverified templates in favor of working dsl_examples

## Testing

All exampl

All examples tested and verified:
```bash
# Test individual format
python examples/dsl_examples/run_example.py html
python examples/dsl_examples/run_example.py md
python examples/dsl_examples/run_example.py text
python examples/dsl_examples/run_example.py toml

# Test all formats
python examples/dsl_examples/run_example.py all

# Run full test suite
pytest temple/tests/test_example_templates.py
```

## Next Steps

- Consider adding more complex examples showcasing advanced features
- Add inline comments to existing templates explaining DSL features
- Create example-specific documentation for each format's unique capabilities
es verified:
1. Templates parse without errors
2. Serialization produces expected output matching `.output` files
3. API examples in docs are syntactically correct
4. Links between docs pages are accurate
