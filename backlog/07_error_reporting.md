---
title: "Error Reporting and Best-Effort Rendering"
status: not_started
priority: HIGH
complexity: Medium
estimated_effort: 1 week
dependencies: ["04_template_parser_linter.md", "06_rendering_engine.md"]
related_backlog: ["12_diagnostics_mapping.md", "13_combine_template_and_base_diagnostics.md"]
related_commit: null
---
# Error Reporting and Best-Effort Rendering

## Goal
Design and implement error reporting and annotation for best-effort rendering, providing actionable feedback for template, query, and output issues.

## Deliverables
- Error reporting module
- Annotation strategy for rendered output
- Example error messages and annotated outputs
- Integration with CLI/editor feedback

## Acceptance Criteria
- Errors are reported at each stage (template, query, output)
- Best-effort rendering produces as much valid output as possible
- Error annotations are clear and non-intrusive
- Example workflows demonstrate error handling
