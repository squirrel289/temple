"""
LintOrchestrator - Coordinates all linting services
"""

import logging
import os
from typing import List
from pygls.lsp.client import LanguageClient
from lsprotocol.types import Diagnostic
from temple_linter.linter import TemplateLinter
from temple_linter.base_format_linter import BaseFormatLinter
from temple_linter.services.token_cleaning_service import TokenCleaningService
from temple_linter.services.base_linting_service import BaseLintingService
from temple_linter.services.diagnostic_mapping_service import DiagnosticMappingService
from temple_linter.diagnostic_converter import temple_to_lsp_diagnostic


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
        self.format_linter = BaseFormatLinter()
        self.token_cleaning_service = TokenCleaningService()
        self.base_linting_service = BaseLintingService(logger=self.logger)
        self.diagnostic_mapping_service = DiagnosticMappingService(logger=self.logger)

    def lint_template(
        self,
        text: str,
        uri: str,
        language_client: LanguageClient,
        temple_extensions: List[str] = None,
    ) -> List[Diagnostic]:
        """
        Execute complete linting workflow for a templated file.

        Args:
            text: Template content
            uri: Document URI
            language_client: LSP client for base linting delegation
            temple_extensions: List of temple file extensions (e.g., [".tmpl", ".template"])

        Returns:
            Combined list of template and base format diagnostics
        """
        if temple_extensions is None:
            temple_extensions = [".tmpl", ".template"]

        # 1. Template linting
        template_diagnostics = self._lint_template_syntax(text)

        # 2. Token cleaning
        cleaned_text, text_tokens = self.token_cleaning_service.clean_text_and_tokens(
            text
        )

        # 3. Format detection
        filename = os.path.basename(uri) if uri else None
        detected_format = self.format_linter.detect_base_format(filename, cleaned_text)

        # 4. Base linting
        base_diagnostics = self.base_linting_service.request_base_diagnostics(
            language_client,
            cleaned_text,
            uri,
            detected_format,
            filename,
            temple_extensions,
        )

        # 5. Diagnostic mapping
        mapped_base_diagnostics = self.diagnostic_mapping_service.map_diagnostics(
            base_diagnostics, text_tokens
        )

        # 6. Merge diagnostics
        all_diagnostics = template_diagnostics + mapped_base_diagnostics

        return all_diagnostics

    def _lint_template_syntax(self, text: str) -> List[Diagnostic]:
        """
        Lint template syntax and logic.

        Converts temple core diagnostics to LSP format.

        Args:
            text: Template content

        Returns:
            List of LSP Diagnostic objects
        """
        temple_diagnostics = self.template_linter.lint(text)
        return [temple_to_lsp_diagnostic(d) for d in temple_diagnostics]
