import unittest
from src.linter import TemplateLinter


class TestTemplateLinter(unittest.TestCase):
    def test_lint_empty(self):
        linter = TemplateLinter()
        diagnostics = linter.lint("")
        self.assertEqual(diagnostics, [])


if __name__ == "__main__":
    unittest.main()
