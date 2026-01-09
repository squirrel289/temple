Bench harness and CI integration
--------------------------------

Run local benchmarks (pytest-benchmark):

```bash
# from repo root, using project's venv
python -m pip install -r requirements.txt
python -m pip install pytest-benchmark
pytest -q temple/tests/test_benchmarks.py
```

Run the standalone harness for richer stats:

```bash
python tools/bench/bench.py 200
```

ASV scaffolding is available in `asv.conf.json` and `asv_benchmarks/`.

Versioning & migration notes
---------------------------

CI runs (ASV and `pytest-benchmark`) are published to GitHub Pages under timestamped directories so historical HTML and raw results are preserved. The publisher copies results into `asv_publish/<TIMESTAMP>/html` and `asv_publish/<TIMESTAMP>/raw` (and `asv_publish/<TIMESTAMP>/bench` for pytest-benchmark JSON).

This layout makes it easy to migrate runs to S3 later: you can `aws s3 sync asv_publish s3://<bucket>/asv --delete` to copy the whole history, or sync individual timestamps.

Recommended migration steps when ready:

1. Ensure CI stores full `asv_results` and published HTML under `asv_publish/<TIMESTAMP>/` (current workflow does this).
2. Use `aws s3 sync asv_publish/ s3://my-bucket/asv/ --acl private` to copy historical runs.
3. Optionally enable S3 lifecycle rules and CloudFront distribution for caching and custom domains.

To run ASV (install `asv` first):

```bash
pip install asv
asv quickstart  # optional interactive setup
asv run
```

CI: The workflow `.github/workflows/benchmarks.yml` runs `pytest-benchmark` weekly and uploads results as artifacts.
Benchmark harness for Temple

Run `tools/bench/bench.py` to collect simple wall-clock timings for the
current Python renderer. The script measures three workloads:

- small: an existing example template
- medium: a small loop rendering 10 items
- large: repeated small unit to generate ~1000 lines

Usage:

```sh
python tools/bench/bench.py [reps]
```

`reps` controls how many render iterations to average (default 200).

Use this as a simple baseline before building alternative PoCs (Rust/Cython).

Details collected:

- wall-clock mean, min, max, p50/p90/p95/p99
- CPU process time per-op mean and percentiles
- Peak Python memory (via `tracemalloc`) during the batch
- delta `ru_maxrss` measured via `resource.getrusage`

