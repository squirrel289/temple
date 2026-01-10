---
title: Performance Benchmarks and Profiling
id: 39
status: open
related_commits: []
estimated_hours: 16
priority: medium
---

## Goal

Measure and improve performance for tokenizer, type checker, and serializers using benchmarks and profiling.

## Tasks

- Add benchmark harness using `asv` or `pytest-benchmark` under `asv/benchmarks/` and/or `benchmarks/`.
- Create representative large templates and datasets to simulate real workloads.
- Run profiling to identify hotspots and propose targeted optimizations.
- Record baseline results and add instructions to reproduce locally.

## Acceptance Criteria

- Benchmarks runnable with `asv run` or `pytest --benchmark-only` and outputs stored under `asv/` or `benchmarks/results/`.
- A short optimization plan is captured if hotspots are found.

## Notes

- Use the existing `.venv_asv_test` virtualenv for consistent environment.
