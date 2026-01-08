"""
BaseLintingService - Delegates linting to VS Code's native linters
"""
import logging
from typing import List, Optional
from pygls.lsp.client import LanguageClient
from lsprotocol.types import Diagnostic
from temple_linter.base_format_linter import VSCODE_PASSTHROUGH, strip_temple_extension


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
        lc: LanguageClient,
        cleaned_text: str,
        original_uri: str,
        detected_format: Optional[str] = None,
        original_filename: Optional[str] = None
    ) -> List[Diagnostic]:
        """
        Request base format diagnostics from VS Code extension.
        
        Args:
            lc: Language client for communication
            cleaned_text: Template content with DSL tokens stripped
            original_uri: URI of the original document
            detected_format: Format detected by registry (or VSCODE_PASSTHROUGH)
            original_filename: Original filename for extension stripping
            
        Returns:
            List of diagnostics from base format linters
        """
        try:
            # If format is unknown, let VS Code auto-detect using stripped filename
            target_uri = original_uri
            if detected_format == VSCODE_PASSTHROUGH and original_filename:
                stripped = strip_temple_extension(original_filename)
                if stripped and stripped != original_filename:
                    # Replace filename in URI for better VS Code detection
                    import os
                    dir_uri = os.path.dirname(original_uri)
                    target_uri = f"{dir_uri}/{stripped}" if dir_uri else stripped
            
            # Send custom request to VS Code extension
            result = lc.protocol.send_request(
                "temple/requestBaseDiagnostics",
                {"uri": target_uri, "content": cleaned_text},
            ).result()
            
            diagnostics: List[Diagnostic] = result.get("diagnostics", []) if result else []
            valid_diagnostics: List[Diagnostic] = []
            
            for d in diagnostics:
                # Accept Diagnostic objects directly
                valid_diagnostics.append(d)
            
            return valid_diagnostics
        
        except Exception as e:
            # Log and return no diagnostics on error
            self.logger.error(f"Error requesting base diagnostics: {e}")
            return []
