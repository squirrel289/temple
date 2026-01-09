import time
from temple.lark_parser import parse_template
from temple.typed_renderer import evaluate_ast


def load_template_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class TemplateBenchBase:
    def setup(self):
        # load template and parse once
        self.tpl_small = load_template_text("examples/bench/real_small.md.tmpl")
        self.tpl_medium = load_template_text("examples/bench/real_medium.md.tmpl")
        self.tpl_large = load_template_text("examples/bench/real_large.html.tmpl")
        self.root_small = parse_template(self.tpl_small)
        self.root_medium = parse_template(self.tpl_medium)
        self.root_large = parse_template(self.tpl_large)
        self.ctx_small = {"user": {"name": "Alice"}, "items": [{"title": f"i{i}"} for i in range(10)]}
        self.ctx_medium = {"user": {"name": "Alice"}, "items": [{"title": f"i{i}"} for i in range(50)]}
        self.ctx_large = {"user": {"name": "Alice"}, "items": [{"title": f"i{i}"} for i in range(200)]}


class BenchTemplateSmall(TemplateBenchBase):
    def time_render_small(self, loops=1000):
        start = time.perf_counter()
        for _ in range(loops):
            evaluate_ast(self.root_small, self.ctx_small)
        return time.perf_counter() - start


class BenchTemplateMedium(TemplateBenchBase):
    def time_render_medium(self, loops=200):
        start = time.perf_counter()
        for _ in range(loops):
            evaluate_ast(self.root_medium, self.ctx_medium)
        return time.perf_counter() - start


class BenchTemplateLarge(TemplateBenchBase):
    def time_render_large(self, loops=50):
        start = time.perf_counter()
        for _ in range(loops):
            evaluate_ast(self.root_large, self.ctx_large)
        return time.perf_counter() - start
