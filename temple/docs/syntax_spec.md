# Temple DSL Syntax Specification

## 1. Syntax Overview

The Temple DSL overlays logic primitives directly onto the target output format (Markdown, HTML, JSON, etc.) using a consistent, minimal syntax. Logic tokens are designed to be ignorable by format linters, ensuring templates remain valid in their base format.

### Logic Token Format
- By default, all logic blocks use `{% ... %}` for statements and `{{ ... }}` for expressions.
- Whitespace inside tokens is ignored.
- Example: `{% if user.name %}Hello, {{ user.name }}!{% endif %}`

### User-Specified Tokens
Users may configure custom delimiters for logic blocks and statements to avoid conflicts with the target format or to match personal/team preferences.

**Configuration Example:**
```yaml
temple:
  statement_start: "::"
  statement_end: "::"
  expression_start: "<<"
  expression_end: ">>"
```

**Usage Example:**
```markdown
:: if user.name ::
Hello, << user.name >>!
:: endif ::
```

The temple system should allow these tokens to be set via configuration (YAML, JSON, CLI flags, etc.), and all logic parsing will respect the chosen delimiters.

## 2. Supported Logic Primitives
- **Variable Insertion:** `{{ variable }}`
- **Conditionals:** `{% if condition %}...{% elif condition %}...{% else %}...{% endif %}`
- **Loops:** `{% for item in collection %}...{% endfor %}`
- **Includes:** `{% include "filename.md" %}`
- **User-Defined Functions:** `{% function name(args) %}...{% endfunction %}`
- **Comments:** `{# This is a comment #}`

All primitives support custom tokens. For example, with the configuration above:
- **Variable Insertion:** `<< variable >>`
- **Conditionals:** `[[ if condition ]]...[[ elif condition ]]...[[ else ]]...[[ endif ]]`
- **Loops:** `[[ for item in collection ]]...[[ endfor ]]`
- **Includes:** `[[ include "filename.md" ]]`
- **User-Defined Functions:** `[[ function name(args) ]]...[[ endfunction ]]`
- **Comments:** `[## This is a comment ##]` (if comment tokens are also configurable)

## 3. Example Templates

### Markdown
```markdown
# Resume

{% if user.name %}
## {{ user.name }}
{% endif %}

{% for job in user.jobs %}
### {{ job.title }} at {{ job.company }}
- {{ job.start }} - {{ job.end }}
{% endfor %}
```

### HTML
```html
<html>
  <body>
    <h1>{{ user.name }}</h1>
    <ul>
      {% for skill in user.skills %}
      <li>{{ skill }}</li>
      {% endfor %}
    </ul>
  </body>
</html>
```

### JSON
```json
{
  "name": "{{ user.name }}",
  "jobs": [
    {% for job in user.jobs %}
    {
      "title": "{{ job.title }}",
      "company": "{{ job.company }}"
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  ]
}
```

## 4. User-Defined Functions

### Definition
```markdown
{% function format_date(date) %}
{{ date | date("YYYY-MM-DD") }}
{% endfunction %}
```

### Usage
```markdown
- Start Date: {{ format_date(job.start) }}
```

## 5. Acceptance Criteria Mapping
- **Readability:** DSL overlays do not break format linting; logic tokens are ignorable.
- **Consistency:** Primitives and syntax are identical across formats.
- **User Functions:** Supported via `{% function ... %}` blocks.
- **Linting:** Example templates pass format linters when logic is ignored.
