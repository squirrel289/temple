# Temple Linter - VS Code Extension

Language support for Temple templated files with integrated linting and diagnostics.

## Features

- **Syntax Highlighting**: Template-aware syntax highlighting for `.tmpl` and `.template` files
- **Intelligent Linting**: Validates both template syntax and base format
- **Format Detection**: Auto-detects JSON, YAML, HTML, XML, TOML, Markdown
- **Native Linter Integration**: Delegates to VS Code's built-in linters
- **Configurable Extensions**: Customize recognized temple file extensions
- **Real-time Diagnostics**: Instant feedback as you type

## Installation

### From Source

1. **Install Python LSP Server:**
   ```bash
   cd ../temple-linter
   pip install -r requirements.txt
   pip install -e .
   ```

2. **Build Extension:**
   ```bash
   npm install
   npm run compile
   ```

3. **Run in Development:**
   - Press `F5` in VS Code to launch Extension Development Host
   - Open a `.tmpl` file to activate

4. **Package for Installation:**
   ```bash
   npm install -g vsce
   vsce package
   # Install the generated .vsix file
   ```

## Configuration

### Settings

Configure in `.vscode/settings.json` or User Settings:

```json
{
  "temple.fileExtensions": [".tmpl", ".template", ".tpl", ".jinja"],
  "python.defaultInterpreterPath": "/path/to/python"
}
```

### Settings Reference

| Setting                        | Type     | Default                | Description                          |
|--------------------------------|----------|------------------------|--------------------------------------|
| `temple.fileExtensions`        | array    | `[".tmpl", ".template"]` | File extensions treated as templates |
| `python.defaultInterpreterPath`| string   | `"python"`             | Path to Python interpreter           |

## Usage

### Creating Template Files

Create files with `.tmpl` or `.template` extensions:

- `config.json.tmpl` - JSON template
- `app.yaml.tmpl` - YAML template  
- `index.html.tmpl` - HTML template
- `README.md.tmpl` - Markdown template

### Template Syntax

Temple uses Jinja-like syntax:

```
{% if condition %}...{% end %}   # Statements
{{ variable }}                      # Expressions
{# comment #}                       # Comments
```

### Example: JSON Template

Create `package.json.tmpl`:

```json
{
  "name": "{{ project.name }}",
  "version": "{{ project.version }}",
  "dependencies": {
    {% for dep, ver in project.deps.items() %}
    "{{ dep }}": "{{ ver }}"{% if not loop.last %},{% end %}
    {% end %}
  }
}
```

The extension will:
1. ✅ Validate template syntax (`{% %}`, `{{ }}` matching)
2. ✅ Strip template tokens
3. ✅ Validate JSON structure
4. ✅ Show combined diagnostics

### Example: YAML Template

Create `config.yaml.tmpl`:

```yaml
database:
  host: {{ db.host }}
  port: {{ db.port }}
  credentials:
    username: {{ db.user }}
    password: {{ db.password }}
servers:
  {% for server in servers %}
  - name: {{ server.name }}
    url: {{ server.url }}
  {% end %}
```

## Supported Formats

| Format   | Extensions          | Linter Integration        |
|----------|---------------------|---------------------------|
| JSON     | `.json`             | VS Code JSON Schema       |
| YAML     | `.yaml`, `.yml`     | YAML Language Support     |
| HTML     | `.html`             | VS Code HTML              |
| XML      | `.xml`              | XML Language Support      |
| TOML     | `.toml`             | Even Better TOML          |
| Markdown | `.md`               | VS Code Markdown          |

Unknown formats automatically pass through to VS Code for detection.

## Features in Detail

### Template Linting

Validates template-specific syntax:
- Unclosed blocks: `{% if %}` without `{% end %}`
- Invalid statements: `{% invalid %}`
- Malformed expressions: `{{ unclosed`
- Mismatched delimiters

### Base Format Linting

Delegates to native VS Code linters:
- JSON: Validates JSON schema, detects syntax errors
- YAML: Validates YAML structure, indentation
- HTML: Validates HTML5 standards, accessibility
- XML: Validates well-formedness
- And more...

### Diagnostic Position Mapping

Accurately maps diagnostics from cleaned content back to original template:

```
Original:    1: {
             2:   "name": "{{ project.name }}",
             3:   "invalid": true true
             4: }

Cleaned:     1: {
             2:   "name": "",
             3:   "invalid": true true    <-- Error here
             4: }

Diagnostic:  Line 3: Duplicate value
```

The extension correctly reports the error at line 3 in the original template.

## Extension Architecture

```
┌──────────────────────────────────────────────────┐
│              VS Code Extension                   │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  Language Client (TypeScript)              │ │
│  │  - Activates on .tmpl files                │ │
│  │  - Starts Python LSP server                │ │
│  │  - Passes configuration                    │ │
│  └──────────────┬─────────────────────────────┘ │
│                 │ LSP (JSON-RPC)                │
│                 ▼                                │
│  ┌────────────────────────────────────────────┐ │
│  │  Python LSP Server                         │ │
│  │  (temple-linter)                           │ │
│  │  - Tokenizes templates                     │ │
│  │  - Cleans DSL tokens                       │ │
│  │  - Detects format                          │ │
│  └──────────────┬─────────────────────────────┘ │
│                 │ temple/requestBaseDiagnostics │
│                 ▼                                │
│  ┌────────────────────────────────────────────┐ │
│  │  Virtual Document Provider                 │ │
│  │  - Creates temple-cleaned:// documents     │ │
│  │  - Triggers native linters                 │ │
│  │  - Collects diagnostics                    │ │
│  └──────────────┬─────────────────────────────┘ │
│                 │ Diagnostics                    │
│                 ▼                                │
│  ┌────────────────────────────────────────────┐ │
│  │  Native VS Code Linters                    │ │
│  │  (JSON, YAML, HTML, etc.)                  │ │
│  └────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

## Troubleshooting

### Extension Not Activating

**Check file extension:**
- File must end with `.tmpl` or `.template` (or custom configured extension)
- Verify `temple.fileExtensions` setting

**Check language ID:**
- Bottom-right corner of VS Code should show "Templated File"
- Click to manually select language if incorrect

### No Diagnostics Appearing

1. **Check Output Panel:**
   - View → Output → Select "Temple LSP"
   - Look for connection errors

2. **Verify Python Server:**
   ```bash
   # Test LSP server manually
   cd ../temple-linter
   python -m temple_linter.lsp_server
   ```

3. **Check Python Path:**
   - Ensure `python.defaultInterpreterPath` is correct
   - Python 3.8+ required

### Incorrect Diagnostic Positions

- **Template structure**: Keep templates line-oriented when possible
- **Debug mode**: Set `TEMPLE_LINTER_DEBUG=1` for verbose logging
- **Report issue**: Include template and diagnostic positions

### Performance Issues

- **Large files**: Consider breaking into smaller templates
- **Many templates**: Regex caching should help (automatic)
- **Disable temporarily**: Close/reopen file to restart

## Development

### Build from Source

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch mode (auto-compile)
npm run watch

# Launch Extension Development Host
# Press F5 in VS Code
```

### Project Structure

```
vscode-temple-linter/
├── src/
│   └── extension.ts          # Extension entry point
├── package.json              # Extension manifest
├── language-configuration.json # Language config
├── tsconfig.json             # TypeScript config
└── README.md
```

### Key Files

**package.json** - Extension manifest:
- Contribution points (languages, commands, settings)
- Activation events
- Language configuration

**extension.ts** - Extension logic:
- Language client setup
- LSP server configuration
- Virtual document provider
- Base diagnostics handler

## Known Limitations

- **Custom delimiters**: Not yet configurable via extension (Python-side ready)
- **Nested templates**: Complex nesting may affect position mapping
- **Binary formats**: Text-based formats only

## Roadmap

- [ ] Custom delimiter configuration UI
- [ ] Template snippets and autocomplete
- [ ] Hover documentation for template variables
- [ ] Go-to-definition for template references
- [ ] Marketplace publication

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### Testing Extension

1. Open workspace in VS Code
2. Press F5 to launch Extension Development Host
3. Create test file: `test.json.tmpl`
4. Verify linting and diagnostics

## License

MIT License - See [LICENSE](../LICENSE) file

## Related

- **temple-linter** - Python LSP server backend
- **temple** - Core rendering engine
- **Temple Docs** - See `../temple/docs/`

## Support

- **Issues**: Report on GitHub
- **Documentation**: See `../temple-linter/docs/`
- **Examples**: See `../temple-linter/tests/fixtures/`
