"""
Temple LSP Server - Thin adapter for Language Server Protocol

This server delegates all linting logic to service classes following
Single Responsibility Principle. See services/ directory for implementation.
"""
from pygls.lsp.server import LanguageServer
from pygls.lsp.client import LanguageClient
from lsprotocol.types import (
    InitializeParams,
    InitializeResult,
    TextDocumentSyncKind,
    Diagnostic,
)
from lsprotocol.types import (
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_SAVE,
    INITIALIZE,
)
from lsprotocol.types import (
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    DidSaveTextDocumentParams,
    PublishDiagnosticsParams,
)
import logging
from typing import List
from temple_linter.services.lint_orchestrator import LintOrchestrator


class TempleLinterServer(LanguageServer):
    """LSP server for temple template linting."""
    
    def __init__(self):
        super().__init__("temple-linter", "v1")
        self.logger = logging.getLogger(__name__)
        self.orchestrator = LintOrchestrator(logger=self.logger)


ls = TempleLinterServer()
lc = LanguageClient("temple-linter-client", "v1")


@ls.feature(INITIALIZE)
def on_initialize(ls: TempleLinterServer, params: InitializeParams):
    from lsprotocol.types import ServerCapabilities

    return InitializeResult(
        capabilities=ServerCapabilities(
            text_document_sync=TextDocumentSyncKind.Incremental,
            experimental={"temple/baseLint": True},
        )
    )


@ls.feature(TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: TempleLinterServer, params: DidOpenTextDocumentParams):
    """Handle document open event."""
    text_doc = params.text_document
    diagnostics: List[Diagnostic] = ls.orchestrator.lint_template(
        text_doc.text, text_doc.uri, lc
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
    diagnostics = ls.orchestrator.lint_template(text_doc.source, text_doc.uri, lc)
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
    diagnostics = ls.orchestrator.lint_template(text_doc.source, text_doc.uri, lc)
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(
            uri=text_doc.uri,
            diagnostics=diagnostics,
        )
    )


if __name__ == "__main__":
    import sys
    import os

    print("[Temple LSP][DEBUG] sys.executable:", sys.executable, flush=True)
    print("[Temple LSP][DEBUG] PATH:", os.environ.get("PATH"), flush=True)
    print("[Temple LSP][DEBUG] VIRTUAL_ENV:", os.environ.get("VIRTUAL_ENV"), flush=True)
    print("[Temple LSP][DEBUG] PYTHONPATH:", os.environ.get("PYTHONPATH"), flush=True)
    ls.start_io()
