"""
BaseLintingService - Delegates linting to VS Code's native linters
"""

import logging
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

from lsprotocol.types import Diagnostic

from temple_linter.base_format_linter import strip_temple_extension


class BaseLintingService:
    """
    Service responsible for delegating base format linting to VS Code extension.

    This service:
    - Sends cleaned content to VS Code extension
    - Receives diagnostics from native linters (JSON, YAML, etc.)
    - Handles communication errors gracefully
    """

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def request_base_diagnostics(
        self,
        request_transport: Any,
        cleaned_text: str,
        original_uri: str,
        detected_format: str | None = None,
        original_filename: str | None = None,
        temple_extensions: list[str] | None = None,
    ) -> list[Diagnostic]:
        """
        Request base format diagnostics from VS Code extension.

        Args:
            request_transport: Session-bound request transport (server or client wrapper)
            cleaned_text: Template content with DSL tokens stripped
            original_uri: URI of the original document
            detected_format: Format detected by registry (or VSCODE_PASSTHROUGH)
            original_filename: Original filename for extension stripping
            temple_extensions: List of temple file extensions (e.g., [".tmpl", ".template"])

        Returns:
            List of diagnostics from base format linters
        """
        if temple_extensions is None:
            temple_extensions = [".tmpl", ".template"]

        try:
            protocol = self._resolve_protocol(request_transport)

            # Strip temple suffix from filename so the extension matches the base format
            target_uri = original_uri
            if original_filename:
                stripped = strip_temple_extension(original_filename, temple_extensions)
                if stripped and stripped != original_filename:
                    import os

                    dir_uri = os.path.dirname(original_uri)
                    target_uri = f"{dir_uri}/{stripped}" if dir_uri else stripped

            # Send custom request to VS Code extension with format hint
            result_future = protocol.send_request(
                "temple/requestBaseDiagnostics",
                {
                    "uri": target_uri,
                    "content": cleaned_text,
                    "detectedFormat": detected_format,
                },
            )
            # Keep this short so template syntax diagnostics remain responsive.
            result = result_future.result(timeout=0.5)

            # Coerce diagnostics to LSP Diagnostic objects
            raw_diagnostics = result.get("diagnostics", []) if result else []
            valid_diagnostics: list[Diagnostic] = []

            for d in raw_diagnostics:
                if isinstance(d, Diagnostic):
                    valid_diagnostics.append(d)
                elif isinstance(d, dict):
                    # Ensure minimal required fields exist for LSP Diagnostic construction
                    diag_dict = dict(d)
                    if "range" not in diag_dict or diag_dict.get("range") is None:
                        # synthesize a zero-length range at start of file
                        diag_dict["range"] = {
                            "start": {"line": 0, "character": 0},
                            "end": {"line": 0, "character": 0},
                        }
                    if "message" not in diag_dict:
                        diag_dict["message"] = ""

                    try:
                        valid_diagnostics.append(Diagnostic(**diag_dict))
                    except Exception as exc:
                        # Log and skip uncoercible diagnostics
                        self.logger.warning(
                            "Skipping invalid base diagnostic from extension: %s; error: %s",
                            diag_dict,
                            exc,
                        )
                        continue

            return valid_diagnostics

        except FutureTimeoutError:
            self.logger.warning(
                "Timed out waiting for base diagnostics from extension transport"
            )
            return []
        except Exception as e:
            # Log and return no diagnostics on error
            self.logger.error(f"Error requesting base diagnostics: {e}")
            return []

    @staticmethod
    def _resolve_protocol(request_transport: Any) -> Any:
        """Resolve pygls protocol object from either server or client transport."""
        protocol = getattr(request_transport, "protocol", None)
        if callable(protocol):
            protocol = protocol()
        if protocol is None or not hasattr(protocol, "send_request"):
            raise RuntimeError("Request transport does not provide protocol.send_request")
        return protocol
