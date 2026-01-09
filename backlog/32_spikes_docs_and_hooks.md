---
title: "32_spikes_docs_and_hooks"
status: proposed
priority: Low
complexity: Low
estimated_effort: 3 days
dependencies:
  - [[30_typed_dsl_prototype.md]]
  - [[31_constraint_driven_templates.md]]
---

# 32 — Docs, Examples & Extensibility Hooks for Spikes

Goal
----
Provide consistent documentation, runnable examples, and well-defined extension points for each spike, to make future exploration and handoff straightforward.

Deliverables
----------
- `docs/spikes/` directory with per-spike README files and API notes
- Example templates (runnable) for each spike under `examples/` subfolders
- A short README describing extension hook interfaces (validator plugin, serializer adapter, include resolver, AST plugin)

Acceptance criteria
-------------------
- Each spike directory contains a `README.md` with quick start instructions and a runnable example
- Extension points are documented with example function signatures and expected behaviors

Tasks
-----
1. Create `docs/spikes/` and add per-spike README files.
2. Add example `README.md` in each `examples/` subfolder for the spikes.
3. Document minimal extension APIs in a single doc under `docs/spikes/hooks.md`.
