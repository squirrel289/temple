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
    Position,
    Range,
)
import logging
from typing import List, Dict, Tuple, Optional
from temple_linter.linter import TemplateLinter
from temple_linter.template_preprocessing import strip_template_tokens
from temple_linter.template_tokenizer import temple_tokenizer, Token


class TempleLinterServer(LanguageServer):
    def __init__(self):
        super().__init__()  # pyright: ignore[reportCallIssue, reportUnknownMemberType]
        self.logger = logging.getLogger(__name__)


ls = TempleLinterServer()
# TODO: LanguageClient is created but never connected. Either:
#   1. Remove if unused, OR
#   2. Initialize connection to VS Code extension, OR
#   3. Pass as parameter instead of global variable
# See ARCHITECTURE_ANALYSIS.md Work Item #1 for refactoring plan
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
    text_doc = params.text_document
    diagnostics: List[Diagnostic] = lint_template(text_doc.text, text_doc.uri, lc)
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(
            uri=text_doc.uri,
            diagnostics=diagnostics,
        )
    )


@ls.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: TempleLinterServer, params: DidChangeTextDocumentParams):
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = lint_template(text_doc.source, text_doc.uri, lc)
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(
            uri=text_doc.uri,
            diagnostics=diagnostics,
        )
    )


@ls.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: TempleLinterServer, params: DidSaveTextDocumentParams):
    text_doc = ls.workspace.get_text_document(params.text_document.uri)
    diagnostics = lint_template(text_doc.source, text_doc.uri, lc)
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(
            uri=text_doc.uri,
            diagnostics=diagnostics,
        )
    )


# Custom method for base lint delegation using VS Code extension proxy
@ls.thread()
def request_base_lint(
    lc: LanguageClient, cleaned_text: str, original_uri: str
) -> List[Diagnostic]:
    """
    Request base diagnostics from the VS Code extension (proxy) using a custom request.
    Sends the cleaned content and URI, receives base diagnostics.
    """
    try:
        # Send a custom request to the VS Code extension
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
        logging.getLogger(__name__).error(f"Error requesting base diagnostics: {e}")
        return []


def lint_template(text: str, uri: str, lc: LanguageClient) -> List[Diagnostic]:
    # 1. Template linting using TemplateLinter class
    linter = TemplateLinter()
    template_diagnostics: List[Diagnostic] = [
        Diagnostic(**d) for d in linter.lint(text)
    ]

    # 2. Strip template tokens and collect text tokens for mapping
    cleaned_text, text_tokens = clean_text_and_tokens(text)

    # 3. Delegate base linting to client via LSP
    base_diagnostics: List[Diagnostic] = request_base_lint(lc, cleaned_text, uri)

    # 4. Map base diagnostics back to original document
    mapped_base_diagnostics: List[Diagnostic] = []
    for diag in base_diagnostics:
        mapped_diag = map_diagnostic_to_original(diag, text_tokens)
        if mapped_diag:
            mapped_base_diagnostics.append(mapped_diag)

    # 5. Merge diagnostics
    diagnostics: List[Diagnostic] = template_diagnostics + mapped_base_diagnostics
    return diagnostics


def clean_text_and_tokens(
    text: str,
) -> Tuple[str, List[Token]]:
    """
    Returns cleaned_text and a list of Token objects for mapping.
    """
    text_tokens: list[Token] = []
    cleaned_chars: list[str] = []
    for token in temple_tokenizer(text):
        if token.type == "text":
            text_tokens.append(token)
            cleaned_chars.append(token.value)
    cleaned_text = "".join(cleaned_chars)
    return cleaned_text, text_tokens


def map_diagnostic_to_original(
    diagnostic: Diagnostic,
    text_tokens: List[Token],
) -> Optional[Diagnostic]:
    import copy

    try:
        diag = copy.deepcopy(diagnostic)
        start = diag.range.start
        end = diag.range.end
        orig_start = _map_cleaned_pos_to_original(start, text_tokens)
        orig_end = _map_cleaned_pos_to_original(end, text_tokens)
        diag.range = Range(start=orig_start, end=orig_end)
        return diag
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Failed to map diagnostic: {diagnostic}, error: {e}"
        )
        return None


def _map_cleaned_pos_to_original(pos: Position, text_tokens: List[Token]) -> Position:
    # Convert (line, character) to offset in cleaned text
    cleaned_offset = _flatten_position(pos, text_tokens)
    offset = 0
    for token in text_tokens:
        token_len = len(token.value)
        if offset <= cleaned_offset < offset + token_len:
            offset_in_token = cleaned_offset - offset
            orig_line, orig_col = _advance_by_offset(
                token.start, token.value, offset_in_token
            )
            return Position(line=orig_line, character=orig_col)
        offset += token_len
    return pos


def _flatten_position(pos: Position, text_tokens: List[Token]) -> int:
    # Convert (line, character) to offset in cleaned text
    cleaned_text = "".join(token.value for token in text_tokens)
    lines = cleaned_text.splitlines(keepends=True)

    # Sum lengths of all lines before target line
    offset = sum(len(lines[i]) for i in range(min(pos.line, len(lines))))

    # Add character offset within the target line
    offset += pos.character

    return offset


def _advance_by_offset(
    start: Tuple[int, int], value: str, offset: int
) -> Tuple[int, int]:
    """Advance (line, col) by offset chars in value."""
    line, col = start
    # Get the substring up to the offset
    substr = value[:offset]
    # Split into lines, keeping line endings
    lines = substr.splitlines(keepends=True)
    if not lines:
        return (line, col)
    if len(lines) == 1:
        # No newlines encountered
        return (line, col + len(lines[0]))
    # Multiple lines: advance line by number of newlines, col is length of last line after last newline
    line += len(lines) - 1
    last_line = lines[-1]
    # If last_line ends with a newline, col should be 0
    if last_line.endswith("\n") or last_line.endswith("\r"):
        col = 0
    else:
        col = len(last_line)
    return (line, col)


if __name__ == "__main__":
    import sys
    import os

    print("[Temple LSP][DEBUG] sys.executable:", sys.executable, flush=True)
    print("[Temple LSP][DEBUG] PATH:", os.environ.get("PATH"), flush=True)
    print("[Temple LSP][DEBUG] VIRTUAL_ENV:", os.environ.get("VIRTUAL_ENV"), flush=True)
    print("[Temple LSP][DEBUG] PYTHONPATH:", os.environ.get("PYTHONPATH"), flush=True)
    ls.start_io()
