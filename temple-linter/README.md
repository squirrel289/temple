# Temple Linter

A Language Server Protocol (LSP) server for linting templated files. Validates both template syntax (DSL tokens) and base format (JSON, YAML, HTML, etc.) by delegating to VS Code's native linters.

## Features

✨ **Template-Aware Linting**: Validates template syntax while preserving base format structure  
🔍 **Format Detection**: Automatic detection of JSON, YAML, HTML, XML, TOML, Markdown  
🚀 **Performance**: Regex pattern caching provides 10x+ speedup for batch processing  
🎨 **Configurable**: Custom temple file extensions via VS Code settings  
🔌 **VS Code Integration**: Seamless integration with VS Code's native linters  
📊 **Complete Diagnostics**: Combines template and base format diagnostics with accurate position mapping

## Quick Start

```bash
# Install Python package
cd temple-linter
pip install -r requirements.txt
pip install -e .

# Install VS Code extension
cd ../vscode-temple-linter
npm install
npm run compile
# Press F5 in VS Code to launch Extension Development Host
```

## Architecture

The linter uses a service-oriented architecture following the Single Responsibility Principle:

### Workflow

```
Template File (.tmpl)
        │
        ▼
┌───────────────────────────────────┐
│  1. Template Linting              │  Validates {% %}, {{ }}, {# #}
│     (TemplateLinter)               │
└───────────────┬───────────────────┘
                ▼
┌───────────────────────────────────┐
│  2. Token Cleaning                 │  Strips DSL tokens
│     (TokenCleaningService)         │
└───────────────┬───────────────────┘
                ▼
┌───────────────────────────────────┐
│  3. Format Detection               │  Detects JSON/YAML/HTML/etc.
│     (BaseFormatLinter)             │
└───────────────┬───────────────────┘
                ▼
┌───────────────────────────────────┐
│  4. Base Linting                   │  Delegates to VS Code linters
│     (BaseLintingService)           │
└───────────────┬───────────────────┘
                ▼
┌───────────────────────────────────┐
│  5. Diagnostic Mapping             │  Maps positions back
│     (DiagnosticMappingService)     │
└───────────────┬───────────────────┘
                ▼
┌───────────────────────────────────┐
│  6. Merge & Publish                │  Combined diagnostics to editor
│     (LintOrchestrator)             │
└───────────────────────────────────┘
```

## Usage

### Writing Templates

Temple uses Jinja-like syntax by default:

| Token Type  | Syntax             | Purpose                    |
|-------------|--------------------|----------------------------|
| Statement   | `{% if x %}...`    | Control flow logic         |
| Expression  | `{{ variable }}`   | Variable insertion         |
| Comment     | `{# note #}`       | Template comments          |

### Examples

#### JSON Template (`config.json.tmpl`)

```json
{
  "name": "{{ project.name }}",
  "version": "{{ project.version }}",
  "dependencies": {
    {% for dep, ver in project.deps.items() %}
    "{{ dep }}": "{{ ver }}"{% if not loop.last %},{% endif %}
    {% endfor %}
  }
}
```

#### YAML Template (`docker-compose.yaml.tmpl`)

```yaml
version: {{ docker.version }}
services:
  {% for service in services %}
  {{ service.name }}:
    image: {{ service.image }}
    ports:
      {% for port in service.ports %}
      - "{{ port }}"
      {% endfor %}
  {% endfor %}
```

#### HTML Template (`page.html.tmpl`)

```html
<!DOCTYPE html>
<html lang="{{ site.lang }}">
<head>
    <title>{{ page.title }}</title>
</head>
<body>
    {% if user.authenticated %}
    <h1>Welcome, {{ user.name }}!</h1>
    {% else %}
    <a href="/login">Log in</a>
    {% endif %}
</body>
</html>
```

## Configuration

### VS Code Settings

Configure in `.vscode/settings.json`:

```json
{
  "temple.fileExtensions": [".tmpl", ".template", ".tpl", ".jinja"],
  "python.defaultInterpreterPath": "/path/to/python"
}
```

### Custom Delimiters

Future support for custom delimiters via config:

```yaml
# .temple.yaml (planned)
delimiters:
  statement: ["<<", ">>"]
  expression: ["<:", ":>"]
  comment: ["<#", "#>"]
```

## Supported Formats

| Format   | Extensions          | Detection Heuristics        |
|----------|---------------------|------------------------------|
| JSON     | `.json`             | Starts with `{` or `[`       |
| YAML     | `.yaml`, `.yml`     | Contains `: ` patterns       |
| HTML     | `.html`             | `<!DOCTYPE>`, `<html>`       |
| XML      | `.xml`              | `<?xml version`              |
| TOML     | `.toml`             | Starts with `[section]`      |
| Markdown | `.md`               | Starts with `#` headers      |

**Unknown formats** automatically pass through to VS Code for auto-detection (VS Code Passthrough mode).

## Development

### Running Tests

```bash
# All tests (49 tests)
pytest tests/ -v

# Specific test suites
pytest tests/test_tokenizer.py -v          # Token parsing
pytest tests/test_preprocessing.py -v      # Token stripping
pytest tests/test_base_format_linter.py -v # Format detection
pytest tests/test_integration.py -v        # Full pipeline

# With coverage
pytest tests/ --cov=temple_linter --cov-report=html
```

### Test Structure

```
tests/
├── test_tokenizer.py           # Token parsing (10 tests)
├── test_preprocessing.py       # Token stripping (4 tests)
├── test_base_format_linter.py  # Format detection (18 tests)
├── test_diagnostics.py         # Diagnostic mapping (1 test)
├── test_linter.py              # Template linting (1 test)
├── test_integration.py         # Full pipeline (15 tests)
└── fixtures/                   # Real-world templates
    ├── valid_package.json.tmpl
    ├── valid_docker_compose.yaml.tmpl
    ├── valid_page.html.tmpl
    └── valid_README.md.tmpl
```

### Project Structure

```
temple-linter/
├── src/temple_linter/
│   ├── lsp_server.py                  # LSP entry point
│   ├── linter.py                      # Template syntax linter
│   ├── template_tokenizer.py         # Tokenization with caching
│   ├── template_preprocessing.py     # Token stripping with caching
│   ├── template_mapping.py           # Position utilities
│   ├── base_format_linter.py         # Format detection registry
│   ├── diagnostics.py                # Diagnostic utilities
│   └── services/
│       ├── lint_orchestrator.py           # Workflow coordinator
│       ├── token_cleaning_service.py      # Token cleaning
│       ├── base_linting_service.py        # VS Code delegation
│       └── diagnostic_mapping_service.py  # Position mapping
├── tests/                             # 49 tests
├── docs/
│   ├── ARCHITECTURE.md               # Architecture overview
│   ├── EXTENDING.md                  # Extension guide
│   └── api/                          # Sphinx documentation
├── requirements.txt
└── README.md
```

## Performance

### Regex Caching

Compiled regex patterns are cached using `functools.lru_cache`:

- **Cache size**: 128 patterns (configurable)
- **Cache key**: Delimiter configuration tuple
- **Performance**: 10x+ speedup for batch processing
- **Memory**: Minimal (patterns are small)

### Benchmarks

| Operation                | Time (uncached) | Time (cached) | Speedup |
|--------------------------|-----------------|---------------|---------|
| Tokenize 1000 files      | ~2.5s           | ~0.2s         | 12.5x   |
| Strip tokens 1000 files  | ~1.8s           | ~0.15s        | 12x     |

## Extending

### Adding Custom Format Detectors

Create a detector implementing the `FormatDetector` protocol:

```python
from temple_linter.base_format_linter import FormatDetector, registry

class CustomFormatDetector(FormatDetector):
    def matches(self, filename, content):
        """Return confidence score 0.0-1.0"""
        if filename and filename.endswith('.custom'):
            return 1.0  # Extension match
        if content.startswith('CUSTOM:'):
            return 0.8  # Content heuristic
        return 0.0
    
    def format_name(self):
        return "custom"

# Register with priority (higher = checked first)
registry.register(CustomFormatDetector(), priority=85)
```

See [docs/EXTENDING.md](docs/EXTENDING.md) for complete guide.

## Troubleshooting

### LSP Server Not Starting

**Check Python path:**
```bash
# Verify Python version
python --version  # Should be 3.8+

# Check installed packages
pip list | grep temple-linter
```

**Check VS Code Output:**
- View → Output → Select "Temple LSP" from dropdown
- Look for startup messages or errors

### Diagnostics Not Appearing

1. **Verify file extension**: Must match `temple.fileExtensions` setting
2. **Check LSP connection**: Look for "Temple LSP" client in VS Code
3. **Test with known-good template**: Use examples from `tests/fixtures/`

### Wrong Diagnostic Positions

- **Preserve line structure**: Avoid multiple tokens per line where possible
- **Check token cleaning**: Run `python -m temple_linter.template_preprocessing --strip --input "text"`
- **Enable debug logging**: Set `TEMPLE_LINTER_DEBUG=1` environment variable

### Format Not Detected

1. **Use explicit extension**: `file.json.tmpl` instead of `file.tmpl`
2. **Check detector priorities**: See `base_format_linter.py` registry
3. **Fallback to passthrough**: Unknown formats auto-delegate to VS Code

## API Documentation

Full API documentation generated with Sphinx:

```bash
cd docs
make html
open _build/html/index.html
```

Or view online: [docs/api/](docs/api/)

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Add tests: `pytest tests/test_my_feature.py -v`
4. Ensure all tests pass: `pytest tests/ -v`
5. Update documentation
6. Submit pull request

### Code Standards

- **Type hints**: Required for public APIs
- **Docstrings**: Google style (parsed by Sphinx napoleon)
- **Tests**: Minimum 80% coverage for new code
- **Formatting**: Follow existing patterns (PEP 8)

## License

MIT License - See [LICENSE](LICENSE) file for details

## Related Projects

- **temple/** - Core rendering engine (separate component)
- **vscode-temple-linter/** - VS Code extension companion
- **Temple Language Spec** - See `../temple/docs/syntax_spec.md`

## Credits

Built with:
- [pygls](https://github.com/openlawlibrary/pygls) - LSP framework
- [lsprotocol](https://github.com/microsoft/lsprotocol) - LSP types
- [pytest](https://pytest.org/) - Testing framework
- [Sphinx](https://www.sphinx-doc.org/) - Documentation

## Status

**Version**: 0.1.0-alpha  
**Stability**: Alpha - Core functionality complete

### Completed Features

- ✅ LSP server with service architecture
- ✅ Template tokenization with regex caching
- ✅ Token cleaning and preprocessing
- ✅ Format detection with VS Code passthrough
- ✅ Base linting delegation
- ✅ Diagnostic position mapping
- ✅ Diagnostic merging and publishing
- ✅ Configurable temple extensions
- ✅ 49 tests passing (unit + integration)
- ✅ API documentation (Sphinx)
- ✅ Real-world template examples

### Roadmap

- [ ] Custom delimiter configuration via files
- [ ] Template syntax validation improvements
- [ ] Query language integration (JMESPath)
- [ ] Schema validation support
- [ ] Performance profiling and optimization
- [ ] VS Code extension marketplace publication

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Tests**: `pytest tests/ -v`
- **Examples**: `tests/fixtures/`
