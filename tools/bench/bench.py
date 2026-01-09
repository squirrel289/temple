"""Simple benchmark harness for Temple renderer.

Usage: python tools/bench/bench.py [reps]

Runs a few representative workloads (small/medium/large) using the
existing `temple` parser + renderer and prints wall-clock timings.
This is intended as a repeatable baseline for comparing PoCs.
"""
import sys
import time
import tracemalloc
import statistics
from pathlib import Path
import resource

from temple.lark_parser import parse_template
from temple.typed_renderer import evaluate_ast


BASE = Path(__file__).parents[2] / "examples" / "dsl_examples"


def load_template(name: str) -> str:
    p = BASE / name
    return p.read_text()


def make_large_template(unit: str, repeat: int) -> str:
    # repeat a small unit many times to create a larger template
    return "".join(unit for _ in range(repeat))


def stats_from_samples(samples):
    if not samples:
        return {}
    s = sorted(samples)
    mean = statistics.mean(s)
    stdev = statistics.stdev(s) if len(s) > 1 else 0.0
    return {
        "mean": mean,
        "stdev": stdev,
        "min": s[0],
        "max": s[-1],
        "p50": s[int(0.50 * (len(s) - 1))],
        "p90": s[int(0.90 * (len(s) - 1))],
        "p95": s[int(0.95 * (len(s) - 1))],
        "p99": s[int(0.99 * (len(s) - 1))],
        "count": len(s),
    }


def time_render(text: str, ctx: dict, includes=None, reps: int = 100, parse_once: bool = True):
    # Measure parse time (optionally once) and per-iteration render times.
    parse_times = []
    render_samples = []
    cpu_samples = []

    if parse_once:
        t0 = time.perf_counter()
        root = parse_template(text)
        t1 = time.perf_counter()
        parse_times.append(t1 - t0)
    else:
        root = None

    # warmup
    if root is None:
        root = parse_template(text)
    evaluate_ast(root, ctx, includes=includes)

    # Start tracemalloc to capture peak Python memory during the batch
    tracemalloc.start()
    mem_before = tracemalloc.get_traced_memory()[0]
    rusage_before = resource.getrusage(resource.RUSAGE_SELF)
    cpu_before = time.process_time()
    wall0 = time.perf_counter()

    for _ in range(reps):
        if not parse_once:
            t0 = time.perf_counter()
            root = parse_template(text)
            t1 = time.perf_counter()
            parse_times.append(t1 - t0)
        t0 = time.perf_counter()
        cpu0 = time.process_time()
        evaluate_ast(root, ctx, includes=includes)
        cpu1 = time.process_time()
        t1 = time.perf_counter()
        render_samples.append(t1 - t0)
        cpu_samples.append(cpu1 - cpu0)

    wall1 = time.perf_counter()
    cpu_after = time.process_time()
    rusage_after = resource.getrusage(resource.RUSAGE_SELF)
    mem_curr, mem_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_wall = wall1 - wall0
    total_cpu = cpu_after - cpu_before

    stats = {
        "parse": stats_from_samples(parse_times),
        "render": stats_from_samples(render_samples),
        "cpu_render": stats_from_samples(cpu_samples),
        "wall_total": total_wall,
        "cpu_total": total_cpu,
        "mem_peak_bytes": mem_peak,
        "rusage_maxrss": rusage_after.ru_maxrss - rusage_before.ru_maxrss,
    }
    return stats


def main():
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 200

    ctx = {
        "user": {
            "name": "Alice",
            "age": 30,
            "active": True,
            "skills": ["python", "lark"],
            "jobs": [{"title": "Engineer", "company": "Acme"}],
        },
        "items": list(range(10)),
    }

    small = load_template("md_positive.md.tmpl")
    # also provide real-world templates
    real_small = (BASE / "bench" / "real_small.md.tmpl").read_text()
    real_medium = (BASE / "bench" / "real_medium.md.tmpl").read_text()
    real_large = (BASE / "bench" / "real_large.html.tmpl").read_text()
    # load includes from includes/ dir
    inc_dir = BASE / "includes"
    includes = {}
    if inc_dir.exists():
        for p in inc_dir.glob("*.tmpl"):
            includes[p.stem] = parse_template(p.read_text())
    med_unit = "- {{ x }}\n"
    med = "{% for x in items %}" + med_unit + "{% endfor %}"
    large = make_large_template(med_unit, 1000)

    print(f"Benchmarking with reps={reps}\n")

    s_small = time_render(small, ctx, includes=includes, reps=reps, parse_once=True)
    print("small template:")
    print(f"  op_count: {s_small['render']['count']}")
    print(f"  mean: {s_small['render']['mean']*1000:.3f} ms/op")
    print(f"  p95: {s_small['render']['p95']*1000:.3f} ms/op, p99: {s_small['render']['p99']*1000:.3f} ms/op")
    print(f"  mem_peak: {s_small['mem_peak_bytes']} bytes, rusage_delta_maxrss: {s_small['rusage_maxrss']}")

    s_med = time_render(med, ctx, includes=includes, reps=reps, parse_once=True)
    print("\nmedium template (loop 10):")
    print(f"  mean: {s_med['render']['mean']*1000:.3f} ms/op")
    print(f"  p95: {s_med['render']['p95']*1000:.3f} ms/op, p99: {s_med['render']['p99']*1000:.3f} ms/op")
    print(f"  cpu_mean: {s_med['cpu_render']['mean']*1000:.3f} ms/op")

    s_large = time_render(large, ctx, includes=includes, reps=max(10, reps//10), parse_once=True)
    print("\nlarge template (~1000 lines):")
    print(f"  mean: {s_large['render']['mean']*1000:.3f} ms/op")
    print(f"  p95: {s_large['render']['p95']*1000:.3f} ms/op, p99: {s_large['render']['p99']*1000:.3f} ms/op")
    print(f"  total_wall: {s_large['wall_total']:.3f}s, cpu_total: {s_large['cpu_total']:.3f}s")
    print(f"  mem_peak: {s_large['mem_peak_bytes']} bytes, rusage_delta_maxrss: {s_large['rusage_maxrss']}")

    # Real-world templates
    print("\nreal_small template:")
    rs_small = time_render(real_small, ctx, includes=includes, reps=reps, parse_once=True)
    print(f"  mean: {rs_small['render']['mean']*1000:.3f} ms/op, p95: {rs_small['render']['p95']*1000:.3f} ms/op")

    print("\nreal_medium template:")
    rs_med = time_render(real_medium, ctx, includes=includes, reps=reps, parse_once=True)
    print(f"  mean: {rs_med['render']['mean']*1000:.3f} ms/op, p95: {rs_med['render']['p95']*1000:.3f} ms/op")

    # For real_large create a larger context
    big_items = []
    for i in range(200):
        big_items.append({
            "title": f"Item {i}",
            "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "tags": [f"tag{j}" for j in range(5)],
        })
    big_ctx = dict(ctx)
    big_ctx["items"] = big_items
    print("\nreal_large template (~200 items):")
    rs_large = time_render(real_large, big_ctx, includes=includes, reps=max(10, reps//10), parse_once=True)
    print(f"  mean: {rs_large['render']['mean']*1000:.3f} ms/op, p95: {rs_large['render']['p95']*1000:.3f} ms/op")


if __name__ == "__main__":
    main()
