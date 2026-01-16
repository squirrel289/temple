"""
temple.compiler.serializers.base
Abstract serializer interface for multi-format output.

Serializers convert type-checked AST + input data into formatted output
(JSON, Markdown, HTML, YAML, etc.), respecting type annotations and producing valid output.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from temple.typed_ast import Block, Text, Expression, If, For, Include
# Alias the core AST node type for type hints used in serializers.
# Importing as `ASTNode` keeps existing type hints stable and avoids
# NameError during test collection when annotations are evaluated.
from temple.typed_ast import Node as ASTNode
from temple.diagnostics import SourceRange
from temple.compiler.types import BaseType


class SerializationError(Exception):
    """Error during serialization process."""
    def __init__(self, message: str, source_range: Optional[SourceRange] = None):
        self.message = message
        self.source_range = source_range
        super().__init__(f"{message}" + (f" at {source_range}" if source_range else ""))


class SerializationContext:
    """Context for tracking serialization state and scope."""
    
    def __init__(self, data: Dict[str, Any], schema: Optional[BaseType] = None):
        """
        Initialize serialization context.
        
        Args:
            data: Input data to serialize against (variables)
            schema: Optional type schema for validation during serialization
        """
        self.data = data
        self.schema = schema
        self.variables: Dict[str, Any] = {}
        self.scope_stack = [self.data]
    
    def get_variable(self, path: str) -> Any:
        """
        Get variable value by dot-notation path (e.g., 'user.name').
        
        Args:
            path: Dot-notation variable path
            
        Returns:
            Value if found, None otherwise
            
        Raises:
            SerializationError: If path is invalid
        """
        parts = path.split('.')
        value = self.scope_stack[-1]  # Current scope
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, (list, tuple)):
                try:
                    idx = int(part)
                    value = value[idx]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        
        return value
    
    def push_scope(self, data: Any) -> None:
        """Push new scope onto stack."""
        self.scope_stack.append(data)
    
    def pop_scope(self) -> None:
        """Pop scope from stack."""
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
    
    @property
    def current_scope(self) -> Any:
        """Get current scope data."""
        return self.scope_stack[-1]


class Serializer(ABC):
    """Abstract base class for format-specific serializers."""
    
    def __init__(self, pretty: bool = True, strict: bool = False):
        """
        Initialize serializer.
        
        Args:
            pretty: Enable pretty-printing/formatting
            strict: Enforce strict format validation
        """
        self.pretty = pretty
        self.strict = strict
    
    @abstractmethod
    def serialize(self, ast: ASTNode, data: Dict[str, Any]) -> str:
        """
        Serialize AST with input data into formatted output.
        
        Args:
            ast: Type-checked AST to serialize
            data: Input data (variables) for template
            
        Returns:
            Formatted output string
            
        Raises:
            SerializationError: If serialization fails
        """
        pass
    
    @abstractmethod
    def evaluate(self, node: ASTNode, context: SerializationContext) -> Any:
        """
        Recursively evaluate AST node to produce intermediate representation.
        
        Args:
            node: AST node to evaluate
            context: Serialization context with current scope
            
        Returns:
            Evaluated value (format-specific)
            
        Raises:
            SerializationError: If evaluation fails
        """
        pass
    
    @abstractmethod
    def format_value(self, value: Any) -> str:
        """
        Format evaluated value into string for output format.
        
        Args:
            value: Evaluated value (may be Python type or intermediate representation)
            
        Returns:
            Formatted string for output
        """
        pass
    
    def _escape_special_chars(self, text: str) -> str:
        """Escape special characters for output format (override in subclasses)."""
        return text
    
    def _type_coerce(self, value: Any, target_type: Optional[BaseType]) -> Any:
        """
        Coerce value to target type if schema provided.
        
        Args:
            value: Value to coerce
            target_type: Target type from schema
            
        Returns:
            Coerced value
        """
        if target_type is None or value is None:
            return value
        
        # Basic type coercion (can be extended)
        type_name = target_type.__class__.__name__
        
        if type_name == "StringType" and not isinstance(value, str):
            return str(value)
        elif type_name == "NumberType" and isinstance(value, str):
            try:
                return float(value) if '.' in value else int(value)
            except ValueError:
                return value
        elif type_name == "BooleanType" and isinstance(value, (int, str)):
            return bool(int(value)) if isinstance(value, str) else bool(value)
        
        return value
