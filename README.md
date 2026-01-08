# Temple: Meta-Templating System

A universal, format-agnostic meta-templating system for declaratively transforming structured data into text with real-time validation and developer tooling.

## 🏗️ Monorepo Structure

This repository contains three interconnected components:

### 1. **temple/** - Core Templating Engine (Specification Phase)
The heart of the Temple system: template DSL parser, query engine, rendering engine, and schema validation.

- **Language**: Python 3.8+
- **Status**: Architecture & specification phase
- **Key Features**:
  - Pluggable data format parsers (JSON, XML, YAML, TOML)
  - Unified query engine (dot notation, JMESPath)
  - Configurable delimiters for template DSL
  - Schema-aware query validation

📖 **Documentation**: [temple/docs/ARCHITECTURE.md](temple/docs/ARCHITECTURE.md)

### 2. **temple-linter/** - LSP Server & Template Linting (Active Development)
Language Server Protocol (LSP) implementation for template-aware linting and diagnostics.

- **Language**: Python 3.8+
- **Status**: Active development
- **Key Features**:
  - Template tokenization with configurable delimiters
  - Strips templates for base format validation
  - LSP integration for editor support
  - Position-accurate diagnostic mapping

📖 **Documentation**: [temple-linter/README.md](temple-linter/README.md)

### 3. **vscode-temple-linter/** - VS Code Extension (TypeScript)
Visual Studio Code extension providing real-time linting via LSP proxy to native VS Code linters.

- **Language**: TypeScript / Node.js
- **Status**: Functional prototype
- **Key Features**:
  - Virtual document provider for cleaned templates
  - LSP proxy to VS Code's native linters
  - Language support for `.tmpl`, `.template` files

📖 **Documentation**: [vscode-temple-linter/ARCHITECTURE.md](vscode-temple-linter/ARCHITECTURE.md)

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** (for `temple` and `temple-linter`)
- **Node.js 14+** (for `vscode-temple-linter`)
- **VS Code** (optional, for extension development)

### Setup Each Component

#### 1. temple (Core Engine)
```bash
cd temple
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

#### 2. temple-linter (LSP Server)
```bash
cd temple-linter
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/
```

#### 3. vscode-temple-linter (Extension)
```bash
cd vscode-temple-linter
npm install
npm run compile

# For development
npm run watch
```

## 🎯 Core Concepts

### Configurable Delimiters
Templates support custom delimiters to avoid conflicts with output formats:

```yaml
# Default: {% %}, {{ }}, {# #}
temple:
  statement_start: "<<"
  statement_end: ">>"
  expression_start: "<:"
  expression_end: ":>"
```

### Template Example
```markdown
# Resume
{% if user.name %}
## {{ user.name }}
{% endif %}

{% for job in user.jobs %}
### {{ job.title }} at {{ job.company }}
{% endfor %}
```

### Supported Output Formats
- Markdown (`.md`)
- HTML (`.html`)
- JSON (`.json`)
- XML (`.xml`)
- Any text-based format

## 🧪 Testing

Run tests for each component:

```bash
# temple
cd temple && pytest tests/

# temple-linter
cd temple-linter && pytest tests/

# vscode-temple-linter
cd vscode-temple-linter && npm test
```

## 📦 Dependency Isolation

Each subproject maintains its own isolated environment:
- **Python projects**: Use dedicated `.venv/` directories
- **Node.js project**: Uses local `node_modules/`
- **No cross-contamination**: Dependencies are scoped per component

## 🗺️ Development Workflow

### Multi-Root Workspace
Open `temple.code-workspace` in VS Code for optimal development experience. This configures:
- Separate workspace folders for each component
- Language-specific settings per folder
- Integrated terminal contexts

### Making Changes

1. **Specification changes** → Update `temple/docs/*.md`
2. **Tokenization/parsing** → Modify `temple-linter/src/`
3. **Editor integration** → Update `vscode-temple-linter/src/`
4. **Cross-component changes** → Update all affected components in same commit

### Commit Guidelines

Create atomic, logical commits:
- **feat**: New features
- **fix**: Bug fixes
- **docs**: Documentation only
- **refactor**: Code restructuring without behavior change
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

Example:
```bash
git commit -m "feat(temple-linter): add support for custom delimiters"
git commit -m "docs(temple): document query validation architecture"
```

## 🏛️ Architecture Philosophy

**The irreducible core:**
> Declarative, logic-driven transformation of structured data into text with a consistent, extensible authoring experience.

Temple abstracts away:
- Data structure types (JSON, XML, YAML, TOML)
- Query engines and AST implementations
- Output formats and their linters
- Editor/IDE integration details

What remains:
- **Template logic language** (expressing mapping, looping, conditionals)
- **Transformation engine** (applying logic to data)
- **Extensibility hooks** (adding new logic, functions, integrations)

## 📄 License

[Add your license here]

## 🤝 Contributing

Contributions welcome! Please read each component's documentation before making changes:
- Understand the delimiter system (configurable tokens)
- Follow position tracking conventions (line, col tuples)
- Write tests before implementing features
- Consider cross-component impacts

## 🔗 Links

- **Specification Docs**: [temple/docs/](temple/docs/)
- **Issue Tracker**: [Add your issue tracker URL]
- **Discussion Forum**: [Add your discussion forum URL]

---

**Status**: Early development - specifications are stable, implementation is ongoing.
