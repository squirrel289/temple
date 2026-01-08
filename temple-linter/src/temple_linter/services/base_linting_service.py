"""
BaseLintingService - Delegates linting to VS Code's native linters
"""
import logging
from typing import List
from pygls.lsp.client import LanguageClient
from lsprotocol.types import Diagnostic


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
        original_uri: str
    ) -> List[Diagnostic]:
        """
        Request base format diagnostics from VS Code extension.
        
        Args:
            lc: Language client for communication
            cleaned_text: Template content with DSL tokens stripped
            original_uri: URI of the original document
            
        Returns:
            List of diagnostics from base format linters
        """
        try:
            # Send custom request to VS Code extension
            result = lc.protocol.send_request(
                "temple/requestBaseDiagnostics",
                {"uri": original_uri, "content": cleaned_text},
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
