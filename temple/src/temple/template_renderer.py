"""
temple.template_renderer
Minimal rendering engine for Temple templates.

Provides:
- Passthrough token concatenation (text tokens only)
- Statement block validation (if/for/function nesting)
- Placeholder handling for expressions/comments
"""

from typing import List, Tuple, Optional
from temple.template_tokenizer import Token, temple_tokenizer, TokenType


class RenderError(Exception):
    """Error during template rendering."""
    pass


class BlockValidator:
    """Validates nesting of statement blocks (if/for/function)."""
    
    # Statement tokens that open/close blocks
    BLOCK_OPENS = {"if", "for", "function"}
    BLOCK_CLOSES = {"endif", "endfor", "endfunction"}
    BLOCK_PAIRS = {
        "if": "endif",
        "for": "endfor",
        "function": "endfunction",
    }
    
    def __init__(self):
        self.stack: List[Tuple[str, int, int]] = []  # (type, line, col)
    
    def validate(self, tokens: List[Token]) -> List[str]:
        """
        Validate block balance. Return list of error messages.
        
        Args:
            tokens: List of template tokens
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        for token in tokens:
            if token.type != "statement":
                continue
            
            keyword = token.value.split()[0].lower() if token.value else ""
            
            # Opening block
            if keyword in self.BLOCK_OPENS:
                self.stack.append((keyword, token.start[0], token.start[1]))
            
            # Closing block
            elif keyword in self.BLOCK_CLOSES:
                if not self.stack:
                    errors.append(
                        f"Unexpected closing block '{keyword}' at "
                        f"line {token.start[0] + 1}, col {token.start[1] + 1}"
                    )
                    continue
                
                open_type, open_line, open_col = self.stack[-1]
                expected_close = self.BLOCK_PAIRS[open_type]
                
                if keyword != expected_close:
                    errors.append(
                        f"Mismatched block: expected '{expected_close}' to close "
                        f"'{open_type}' at line {open_line + 1}, col {open_col + 1}"
                    )
                    # Don't pop; treat as unclosed so we still report it
                else:
                    self.stack.pop()
        
        # Check for unclosed blocks
        for block_type, line, col in self.stack:
            errors.append(
                f"Unclosed block '{block_type}' at line {line + 1}, col {col + 1}"
            )
        
        return errors


def render_passthrough(
    text: str,
    delimiters: Optional[dict] = None,
    validate_blocks: bool = True,
) -> Tuple[str, List[str]]:
    """
    Render template by concatenating text tokens.
    
    This is a minimal renderer that:
    - Extracts text tokens (strips DSL)
    - Validates block nesting (if/for/function)
    - Returns rendered output + validation errors
    
    Args:
        text: Template content
        delimiters: Optional custom delimiters
        validate_blocks: Whether to validate statement block nesting (default: True)
        
    Returns:
        Tuple of (rendered_output, error_messages)
    """
    tokens = list(temple_tokenizer(text, delimiters))
    errors = []
    
    # Validate block nesting
    if validate_blocks:
        validator = BlockValidator()
        errors = validator.validate(tokens)
    
    # Concatenate text tokens only (passthrough)
    output_parts = []
    for token in tokens:
        if token.type == "text":
            output_parts.append(token.value)
    
    output = "".join(output_parts)
    return output, errors


def render(
    text: str,
    data: Optional[dict] = None,
    delimiters: Optional[dict] = None,
) -> Tuple[str, List[str]]:
    """
    Render template with data.
    
    Currently implements passthrough mode (text extraction + block validation).
    Future: Implement full rendering with expression evaluation, loops, etc.
    
    Args:
        text: Template content
        data: Input data object (unused in passthrough mode)
        delimiters: Optional custom delimiters
        
    Returns:
        Tuple of (rendered_output, error_messages)
    """
    # TODO: Implement full rendering with data binding
    # For now: passthrough mode
    return render_passthrough(text, delimiters, validate_blocks=True)
