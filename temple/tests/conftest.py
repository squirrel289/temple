import pytest

try:
    import pytest_benchmark  # type: ignore
except Exception:
    pytest.exit(
        "pytest-benchmark is required. Install it (pip install pytest-benchmark) or add it to dev requirements."
    )
