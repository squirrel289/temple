"""
LintOrchestrator - Coordinates all linting services
"""

import logging
import os
from typing import Any

from lsprotocol.types import Diagnostic
from pygls.lsp.client import LanguageClient

from temple.diagnostics import DiagnosticCollector

from ..base_format_linter import BaseFormatLinter
from ..diagnostic_converter import temple_to_lsp_diagnostic
from ..linter import TemplateLinter
from .base_linting_service import BaseLintingService
from .diagnostic_mapping_service import DiagnosticMappingService
from .token_cleaning_service import TokenCleaningService


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

    def __init__(self, logger: logging.Logger | None = None):
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
        temple_extensions: list[str] | None = None,
        semantic_context: dict[str, Any] | None = None,
        semantic_schema: Any = None,
    ) -> list[Diagnostic]:
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
        # Create a node collector to capture per-node diagnostics during parsing
        node_collector = DiagnosticCollector()
        template_diagnostics = self._lint_template_syntax(
            text,
            node_collector,
            semantic_context=semantic_context,
            semantic_schema=semantic_schema,
        )

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

        # 6. Include node-attached diagnostics (from parser/transformation)
        node_diags: list[Diagnostic] = []
        for d in node_collector.diagnostics:
            node_diags.append(temple_to_lsp_diagnostic(d))

        # 7. Merge diagnostics
        all_diagnostics = template_diagnostics + mapped_base_diagnostics + node_diags

        # Return merged diagnostics list (template + mapped base + node-attached)
        return all_diagnostics

    def _lint_template_syntax(
        self,
        text: str,
        node_collector: DiagnosticCollector | None = None,
        semantic_context: dict[str, Any] | None = None,
        semantic_schema: Any = None,
    ) -> list[Diagnostic]:
        """
        Lint template syntax and logic.

        Converts temple core diagnostics to LSP format.

        Args:
            text: Template content

        Returns:
            List of LSP Diagnostic objects
        """
        temple_diagnostics = self.template_linter.lint(
            text,
            node_collector=node_collector,
            context=semantic_context,
            schema=semantic_schema,
        )
        return [temple_to_lsp_diagnostic(d) for d in temple_diagnostics]
