import time
from temple.lark_parser import parse_template
from temple.typed_renderer import evaluate_ast


def load_template_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def bench_real_small(loops=1000):
    tpl = load_template_text("examples/bench/real_small.md.tmpl")
    root = parse_template(tpl)
    ctx = {"user": {"name": "Alice"}, "items": [{"title": f"i{i}"} for i in range(10)]}
    start = time.perf_counter()
    for _ in range(loops):
        evaluate_ast(root, ctx)
    return time.perf_counter() - start


def bench_real_large(loops=100):
    tpl = load_template_text("examples/bench/real_large.html.tmpl")
    root = parse_template(tpl)
    ctx = {"user": {"name": "Alice"}, "items": [{"title": f"i{i}"} for i in range(200)]}
    start = time.perf_counter()
    for _ in range(loops):
        evaluate_ast(root, ctx)
    return time.perf_counter() - start
