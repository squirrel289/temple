"""
Temple LSP Server - Thin adapter for Language Server Protocol

This server delegates all linting logic to service classes following
Single Responsibility Principle. See services/ directory for implementation.
"""

import logging
from pathlib import Path
from typing import Any

from lsprotocol.types import (
    INITIALIZE,
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_SAVE,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_PREPARE_RENAME,
    TEXT_DOCUMENT_REFERENCES,
    TEXT_DOCUMENT_RENAME,
    CompletionOptions,
    CompletionParams,
    DefinitionParams,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DidSaveTextDocumentParams,
    HoverParams,
    InitializeParams,
    InitializeResult,
    PrepareRenameParams,
    PublishDiagnosticsParams,
    ReferenceParams,
    RenameOptions,
    RenameParams,
    ServerCapabilities,
    TextDocumentSyncKind,
)
from pygls.lsp.server import LanguageServer

from temple.compiler.schema import SchemaParser

from .lsp_features import (
    TemplateCompletionProvider,
    TemplateDefinitionProvider,
    TemplateHoverProvider,
    TemplateReferenceProvider,
    TemplateRenameProvider,
)
from .services.lint_orchestrator import LintOrchestrator


class TempleLinterServer(LanguageServer):
    """LSP server for temple template linting."""

    def __init__(self) -> None:
        super().__init__("temple-linter", "v1")
        self.logger = logging.getLogger(__name__)
        self.temple_extensions = [".tmpl", ".template"]  # defaults
        self.semantic_context: dict[str, Any] | None = None
        self.semantic_schema = None
        self.semantic_schema_raw: dict[str, Any] | None = None
        self.orchestrator = LintOrchestrator(logger=self.logger)
        self.completion_provider = TemplateCompletionProvider()
        self.hover_provider = TemplateHoverProvider()
        self.definition_provider = TemplateDefinitionProvider()
        self.reference_provider = TemplateReferenceProvider()
        self.rename_provider = TemplateRenameProvider()


ls = TempleLinterServer()


@ls.feature(INITIALIZE)
def on_initialize(ls: TempleLinterServer, params: InitializeParams):
    # Extract temple extensions from initialization options if provided
    if params.initialization_options:
        init_options = params.initialization_options
        temple_exts = init_options.get("templeExtensions")
        if temple_exts and isinstance(temple_exts, list):
            ls.temple_extensions = temple_exts
            ls.logger.info(f"Temple extensions configured: {temple_exts}")

        semantic_context = init_options.get("semanticContext")
        if isinstance(semantic_context, dict):
            ls.semantic_context = semantic_context

        semantic_schema = init_options.get("semanticSchema")
        if isinstance(semantic_schema, dict):
            try:
                ls.semantic_schema = SchemaParser.from_json_schema(semantic_schema)
                ls.semantic_schema_raw = semantic_schema
            except Exception as exc:
                ls.logger.warning("Failed to parse semanticSchema init option: %s", exc)

        schema_path = init_options.get("schemaPath")
        if ls.semantic_schema is None and isinstance(schema_path, str) and schema_path:
            try:
                ls.semantic_schema = SchemaParser.from_file(schema_path)
            except Exception as exc:
                ls.logger.warning("Failed to load schemaPath init option: %s", exc)

    return InitializeResult(
        capabilities=ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.Incremental,
            completion_provider=CompletionOptions(trigger_characters=[".", "{", "%"]),
            hover_provider=True,
            definition_provider=True,
            references_provider=True,
            rename_provider=RenameOptions(prepare_provider=True),
            experimental={"temple/baseLint": True},
        )
    )


@ls.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: TempleLinterServer, params: DidOpenTextDocumentParams):
    """Handle document open event."""
    text_doc = params.text_document
    diagnostics = ls.orchestrator.lint_template(
        text_doc.text,
        text_doc.uri,
        ls,
        ls.temple_extensions,
        semantic_context=ls.semantic_context,
        semantic_schema=ls.semantic_schema,
    )
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(
            uri=text_doc.uri,
            diagnostics=diagnostics,
        )
    )


@ls.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: TempleLinterServer, params: DidChangeTextDocumentParams):
    """Handle document change event."""
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = ls.orchestrator.lint_template(
        text_doc.source,
        text_doc.uri,
        ls,
        ls.temple_extensions,
        semantic_context=ls.semantic_context,
        semantic_schema=ls.semantic_schema,
    )
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(
            uri=text_doc.uri,
            diagnostics=diagnostics,
        )
    )


@ls.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: TempleLinterServer, params: DidSaveTextDocumentParams):
    """Handle document save event."""
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = ls.orchestrator.lint_template(
        text_doc.source,
        text_doc.uri,
        ls,
        ls.temple_extensions,
        semantic_context=ls.semantic_context,
        semantic_schema=ls.semantic_schema,
    )
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(
            uri=text_doc.uri,
            diagnostics=diagnostics,
        )
    )


def main() -> int:
    """Start the Temple LSP server over stdio."""
    ls.start_io()
    return 0


@ls.feature(TEXT_DOCUMENT_COMPLETION)
def completion(ls: TempleLinterServer, params: CompletionParams):
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    return ls.completion_provider.get_completions(
        text_doc.source,
        params.position,
        schema=ls.semantic_schema,
    )


@ls.feature(TEXT_DOCUMENT_HOVER)
def hover(ls: TempleLinterServer, params: HoverParams):
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    return ls.hover_provider.get_hover(
        text_doc.source,
        params.position,
        schema=ls.semantic_schema,
        raw_schema=ls.semantic_schema_raw,
    )


@ls.feature(TEXT_DOCUMENT_DEFINITION)
def definition(ls: TempleLinterServer, params: DefinitionParams):
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    workspace_root = getattr(ls.workspace, "root_path", None)
    root_path = Path(workspace_root) if isinstance(workspace_root, str) else None
    return ls.definition_provider.get_definition(
        text_doc.source,
        params.position,
        params.text_document.uri,
        root_path,
        ls.temple_extensions,
    )


@ls.feature(TEXT_DOCUMENT_REFERENCES)
def references(ls: TempleLinterServer, params: ReferenceParams):
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    return ls.reference_provider.find_references(
        text_doc.source,
        params.position,
        params.text_document.uri,
    )


@ls.feature(TEXT_DOCUMENT_PREPARE_RENAME)
def prepare_rename(ls: TempleLinterServer, params: PrepareRenameParams):
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    return ls.rename_provider.prepare_rename(text_doc.source, params.position)


@ls.feature(TEXT_DOCUMENT_RENAME)
def rename(ls: TempleLinterServer, params: RenameParams):
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    return ls.rename_provider.rename(
        text_doc.source,
        params.position,
        params.new_name,
        params.text_document.uri,
    )


if __name__ == "__main__":
    raise SystemExit(main())
