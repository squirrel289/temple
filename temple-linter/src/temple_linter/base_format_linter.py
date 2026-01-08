"""
Base format linting integration for templated files.
Uses template_preprocessing to strip template tokens before linting.
"""

from temple_linter.template_preprocessing import strip_template_tokens
from typing import List, Dict, Any, Optional

import os

# TODO: Refactor to use registry pattern for extensibility (see ARCHITECTURE_ANALYSIS.md Work Item #2)
class BaseFormatLinter:
    def __init__(self, delimiters: Optional[Dict[str, tuple]] = None):
        self.delimiters = delimiters

    def detect_base_format(self, filename: Optional[str], text: str) -> str:
        """
        Detect the base format of a templated file using extension and content heuristics.
        Supported formats: json, yaml, html, toml, xml, md, txt
        
        TODO: Refactor using Strategy pattern with FormatDetectorRegistry
        See ARCHITECTURE_ANALYSIS.md Work Item #2 for implementation plan
        """
        if filename:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.json', '.json.tmpl', '.json.template']:
                return 'json'
            if ext in ['.yaml', '.yml', '.yaml.tmpl', '.yml.tmpl', '.yaml.template', '.yml.template']:
                return 'yaml'
            if ext in ['.html', '.htm', '.html.tmpl', '.htm.tmpl', '.html.template', '.htm.template']:
                return 'html'
            if ext in ['.toml', '.toml.tmpl', '.toml.template']:
                return 'toml'
            if ext in ['.xml', '.xml.tmpl', '.xml.template']:
                return 'xml'
            if ext in ['.md', '.markdown', '.md.tmpl', '.markdown.tmpl', '.md.template', '.markdown.template']:
                return 'md'
            if ext in ['.txt', '.text', '.txt.tmpl', '.text.tmpl', '.txt.template', '.text.template']:
                return 'txt'
        # Fallback: content-based detection
        sample = text.strip()[:1000].lower()
        if sample.startswith('{') or sample.startswith('['):
            return 'json'
        if sample.startswith('<!doctype html') or sample.startswith('<html'):
            return 'html'
        if sample.startswith('<?xml') or sample.startswith('<'):
            return 'xml'
        if sample.startswith('---') or 'yaml' in sample or ': ' in sample:
            return 'yaml'
        if '[[' in sample and ']]' in sample:
            return 'toml'
        if sample.startswith('#') or sample.startswith('##'):
            return 'md'
        return 'txt'

    def lint_base_format(self, text: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lint the base format of a templated file by stripping template tokens first.
        Returns diagnostics from the base linter (placeholder).
        """
        base_text = strip_template_tokens(text, self.delimiters)
        base_format = self.detect_base_format(filename, base_text)
        diagnostics = []
        # TODO: Integrate with actual base format linter (Markdown, HTML, JSON, etc.)
        diagnostics.append({
            'base_format': base_format,
            'info': f'Detected base format: {base_format}'
        })
        # ... base format linting logic ...
        return diagnostics
