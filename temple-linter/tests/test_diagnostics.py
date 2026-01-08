import unittest
from src.diagnostics import map_diagnostics


class TestDiagnostics(unittest.TestCase):
    def test_map_empty(self):
        result = map_diagnostics([], [])
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
