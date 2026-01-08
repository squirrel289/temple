import unittest
from src.base_format_linter import BaseFormatLinter


class TestBaseFormatLinter(unittest.TestCase):
    def test_strip_template_tokens(self):
        linter = BaseFormatLinter()
        text = "Hello {% if user %}{{ user.name }}{% endif %} World"
        base = linter.lint_base_format(text)
        self.assertIsInstance(base, list)


if __name__ == "__main__":
    unittest.main()
