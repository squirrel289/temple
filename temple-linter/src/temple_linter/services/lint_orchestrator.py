"""
LintOrchestrator - Coordinates all linting services
"""
import logging
from typing import List
from pygls.lsp.client import LanguageClient
from lsprotocol.types import Diagnostic
from temple_linter.linter import TemplateLinter
from temple_linter.services.token_cleaning_service import TokenCleaningService
from temple_linter.services.base_linting_service import BaseLintingService
from temple_linter.services.diagnostic_mapping_service import DiagnosticMappingService


class LintOrchestrator:
    """
    Orchestrates the complete linting workflow for templated files.
    
    Workflow:
    1. Template linting (syntax and logic validation)
    2. Token cleaning (strip DSL tokens)
    3. Base linting (delegate to native linters)
    4. Diagnostic mapping (map positions back to original)
    5. Merge all diagnostics
    
    This orchestrator coordinates services following Single Responsibility Principle:
    - TemplateLinter: Validates template syntax
    - TokenCleaningService: Strips DSL tokens
    - BaseLintingService: Delegates to native linters
    - DiagnosticMappingService: Maps positions
    """
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.template_linter = TemplateLinter()
        self.token_cleaning_service = TokenCleaningService()
        self.base_linting_service = BaseLintingService(logger=self.logger)
        self.diagnostic_mapping_service = DiagnosticMappingService(logger=self.logger)
    
    def lint_template(
        self,
        text: str,
        uri: str,
        language_client: LanguageClient
    ) -> List[Diagnostic]:
        """
        Execute complete linting workflow for a templated file.
        
        Args:
            text: Template content
            uri: Document URI
            language_client: LSP client for base linting delegation
            
        Returns:
            Combined list of template and base format diagnostics
        """
        # 1. Template linting
        template_diagnostics = self._lint_template_syntax(text)
        
        # 2. Token cleaning
        cleaned_text, text_tokens = self.token_cleaning_service.clean_text_and_tokens(text)
        
        # 3. Base linting
        base_diagnostics = self.base_linting_service.request_base_diagnostics(
            language_client, cleaned_text, uri
        )
        
        # 4. Diagnostic mapping
        mapped_base_diagnostics = self.diagnostic_mapping_service.map_diagnostics(
            base_diagnostics, text_tokens
        )
        
        # 5. Merge diagnostics
        all_diagnostics = template_diagnostics + mapped_base_diagnostics
        
        return all_diagnostics
    
    def _lint_template_syntax(self, text: str) -> List[Diagnostic]:
        """Lint template syntax and logic."""
        diagnostics_data = self.template_linter.lint(text)
        return [Diagnostic(**d) for d in diagnostics_data]
