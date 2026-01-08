import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from temple_linter.services.base_linting_service import BaseLintingService


class _FakeResult:
    def __init__(self, payload):
        self._payload = payload

    def result(self):
        return self._payload


class _FakeProtocol:
    def __init__(self, payload):
        self.sent = []
        self._payload = payload

    def send_request(self, method, params):
        self.sent.append((method, params))
        return _FakeResult(self._payload)


class _FakeLanguageClient:
    def __init__(self, payload):
        self.protocol = _FakeProtocol(payload)


def test_request_base_diagnostics_strips_extension():
    diagnostics_payload = {
        "diagnostics": [
            {
                "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
                "message": "example",
                "source": "json",
            }
        ]
    }
    lc = _FakeLanguageClient(diagnostics_payload)
    svc = BaseLintingService()

    diagnostics = svc.request_base_diagnostics(
        lc,
        cleaned_text="{ }",
        original_uri="file:///workspace/config.json.tmpl",
        detected_format="json",
        original_filename="config.json.tmpl",
        temple_extensions=[".tmpl"],
    )

    # Request goes out with stripped temple suffix
    assert lc.protocol.sent[0][0] == "temple/requestBaseDiagnostics"
    assert lc.protocol.sent[0][1]["uri"] == "file:///workspace/config.json"
    assert "content" in lc.protocol.sent[0][1]

    # Diagnostics flow through
    assert len(diagnostics) == 1


def test_request_base_diagnostics_handles_errors_gracefully():
    class _RaisingProtocol:
        def send_request(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    class _RaisingClient:
        def __init__(self):
            self.protocol = _RaisingProtocol()

    svc = BaseLintingService()
    diagnostics = svc.request_base_diagnostics(
        _RaisingClient(),
        cleaned_text="{}",
        original_uri="file:///workspace/invalid.json.tmpl",
        detected_format="json",
        original_filename="invalid.json.tmpl",
        temple_extensions=[".tmpl"],
    )

    assert diagnostics == []
