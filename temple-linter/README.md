# temple-linter

Language Server Protocol (LSP) implementation for template-aware linting and diagnostics. Strips template tokens to enable base format validation while maintaining accurate error positions.

## Features

- **Template Tokenization**: Configurable delimiter support (default: `{% %}`, `{{ }}`, `{# #}`)
- **Template Linting**: Validates template syntax (unclosed blocks, invalid statements)
- **Base Format Delegation**: Strips templates and delegates to format-specific linters
- **Position Mapping**: Maps diagnostics from cleaned content back to original template positions
- **LSP Server**: Full Language Server Protocol implementation for editor integration
- **Format Detection**: Auto-detects base format (JSON, HTML, YAML, Markdown, etc.)

## Installation

```bash
cd temple-linter
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### As LSP Server

Start the LSP server for editor integration:

```bash
python -m temple_linter.lsp_server
```

Configure your editor to use this as the language server for `.tmpl` and `.template` files.

### As CLI Tool

Lint a template file:

```bash
python -m temple_linter.linter --lint --input "{% if user %}{{ user.name }}{% endif %}"
```

Strip template tokens:

```bash
python -m temple_linter.template_preprocessing --strip --input "{% if x %}hello{% endif %}"
```

## Architecture

See [`../vscode-temple-linter/ARCHITECTURE.md`](../vscode-temple-linter/ARCHITECTURE.md) for integration architecture with VS Code.

## Testing

```bash
pytest tests/
```

## Custom Delimiters

Configure custom delimiters to avoid conflicts with your output format:

```python
from temple_linter.template_tokenizer import temple_tokenizer

delimiters = {
    "statement": ("<<", ">>"),
    "expression": ("<:", ":>"),
    "comment": ("<#", "#>")
}

tokens = list(temple_tokenizer(text, delimiters))
```

## LSP Protocol Extensions

### Custom Requests

- `temple/requestBaseDiagnostics`: Request diagnostics for cleaned base format
  - **Params**: `{ uri: string, content: string }`
  - **Returns**: `{ diagnostics: Diagnostic[] }`

### Custom Notifications

- `temple/createVirtualDocument`: Notify client of cleaned content for virtual document
  - **Params**: `{ uri: string, content: string, originalUri: string }`

## Dependencies

- `pygls>=1.0.0` - Language Server Protocol implementation

## Development Status

**Active Development** - Core functionality is implemented and tested. See [`../ARCHITECTURE_ANALYSIS.md`](../ARCHITECTURE_ANALYSIS.md) for refactoring roadmap and improvement opportunities.
