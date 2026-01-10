"""
Tests for the type checker.
"""

import pytest
from temple.compiler.type_checker import TypeChecker, TypeEnvironment
from temple.compiler.ast_nodes import (
    Text, Expression, If, For, Position, SourceRange
)
from temple.compiler.schema import object_schema
from temple.compiler.types import StringType, NumberType, ObjectType, ArrayType


class TestTypeEnvironment:
    """Test type environment."""
    
    def test_bind_and_lookup(self):
        env = TypeEnvironment()
        env.bind("x", StringType())
        
        result = env.lookup("x")
        assert isinstance(result, StringType)
    
    def test_lookup_parent_scope(self):
        parent = TypeEnvironment()
        parent.bind("x", StringType())
        
        child = parent.child_scope()
        result = child.lookup("x")
        assert isinstance(result, StringType)
    
    def test_child_scope_shadowing(self):
        parent = TypeEnvironment()
        parent.bind("x", StringType())
        
        child = parent.child_scope()
        child.bind("x", NumberType())
        
        result = child.lookup("x")
        assert isinstance(result, NumberType)


class TestTypeCheckerBasics:
    """Test basic type checking."""
    
    def test_check_text_node(self):
        checker = TypeChecker()
        node = Text("hello", SourceRange(Position(0, 0), Position(0, 5)))
        
        assert checker.check(node)
        assert not checker.errors.has_errors()
    
    def test_check_valid_expression(self):
        data = {"name": "Alice"}
        checker = TypeChecker(data=data)
        
        node = Expression("name", SourceRange(Position(0, 0), Position(0, 10)))
        assert checker.check(node)
        assert not checker.errors.has_errors()
    
    def test_check_undefined_variable(self):
        checker = TypeChecker(data={})
        
        node = Expression("undefined", SourceRange(Position(0, 0), Position(0, 15)))
        assert not checker.check(node)
        assert checker.errors.has_errors()
        
        error = checker.errors.errors[0]
        assert error.kind == "undefined_variable"
        assert "undefined" in error.message
    
    def test_check_property_access(self):
        data = {"user": {"name": "Alice"}}
        checker = TypeChecker(data=data)
        
        node = Expression("user.name", SourceRange(Position(0, 0), Position(0, 15)))
        assert checker.check(node)
        assert not checker.errors.has_errors()
    
    def test_check_missing_property(self):
        data = {"user": {"name": "Alice"}}
        checker = TypeChecker(data=data)
        
        node = Expression("user.age", SourceRange(Position(0, 0), Position(0, 15)))
        assert not checker.check(node)
        assert checker.errors.has_errors()
        
        error = checker.errors.errors[0]
        assert error.kind == "missing_property"
        assert "age" in error.message


class TestTypeCheckerControlFlow:
    """Test type checking for control flow."""
    
    def test_check_if_statement(self):
        data = {"active": True}
        checker = TypeChecker(data=data)
        
        node = If(
            condition="active",
            body=[Text("yes", SourceRange(Position(1, 0), Position(1, 3)))],
            elif_parts=[],
            else_body=None,
            source_range=SourceRange(Position(0, 0), Position(2, 10))
        )
        
        assert checker.check(node)
        assert not checker.errors.has_errors()
    
    def test_check_for_loop_with_array(self):
        data = {"items": ["a", "b", "c"]}
        checker = TypeChecker(data=data)
        
        node = For(
            var="item",
            iterable="items",
            body=[
                Expression("item", SourceRange(Position(1, 0), Position(1, 10)))
            ],
            source_range=SourceRange(Position(0, 0), Position(2, 15))
        )
        
        assert checker.check(node)
        assert not checker.errors.has_errors()
    
    def test_check_for_loop_non_array(self):
        data = {"count": 42}
        checker = TypeChecker(data=data)
        
        node = For(
            var="item",
            iterable="count",
            body=[
                Expression("item", SourceRange(Position(1, 0), Position(1, 10)))
            ],
            source_range=SourceRange(Position(0, 0), Position(2, 15))
        )
        
        assert not checker.check(node)
        assert checker.errors.has_errors()
        
        error = checker.errors.errors[0]
        assert error.kind == "type_mismatch"
        assert "iterate" in error.message.lower()
    
    def test_check_for_loop_variable_scope(self):
        data = {"items": [{"name": "Alice"}, {"name": "Bob"}]}
        checker = TypeChecker(data=data)
        
        # Loop variable should be accessible in body
        node = For(
            var="item",
            iterable="items",
            body=[
                Expression("item.name", SourceRange(Position(1, 0), Position(1, 15)))
            ],
            source_range=SourceRange(Position(0, 0), Position(2, 15))
        )
        
        assert checker.check(node)
        # Should have no errors - item.name is valid in loop scope


class TestSchemaValidation:
    """Test schema-based validation."""
    
    def test_validate_with_schema(self):
        schema = object_schema({
            "name": StringType(),
            "age": NumberType()
        })
        data = {"name": "Alice", "age": 30}
        
        checker = TypeChecker(schema=schema, data=data)
        node = Expression("name", SourceRange(Position(0, 0), Position(0, 10)))
        
        assert checker.check(node)
        assert not checker.errors.has_errors()


class TestErrorMessages:
    """Test error message generation."""
    
    def test_undefined_variable_suggestion(self):
        data = {"username": "Alice"}
        checker = TypeChecker(data=data)
        
        # Typo: "user_name" instead of "username"
        node = Expression("user_name", SourceRange(Position(0, 0), Position(0, 15)))
        checker.check(node)
        
        assert checker.errors.has_errors()
        error = checker.errors.errors[0]
        
        # Should suggest "username"
        assert error.suggestion is not None
        assert "username" in error.suggestion
    
    def test_missing_property_suggestion(self):
        data = {"user": {"username": "Alice", "email": "alice@example.com"}}
        checker = TypeChecker(data=data)
        
        # Typo: "user.emai" instead of "user.email"
        node = Expression("user.emai", SourceRange(Position(0, 0), Position(0, 15)))
        checker.check(node)
        
        assert checker.errors.has_errors()
        error = checker.errors.errors[0]
        
        # Should suggest "email"
        assert error.suggestion is not None
        assert "email" in error.suggestion.lower()
    
    def test_error_formatting(self):
        checker = TypeChecker(data={})
        node = Expression("undefined", SourceRange(Position(0, 5), Position(0, 15)))
        checker.check(node)
        
        source_text = "{{ {{ undefined }} }}"
        formatted = checker.errors.format_all(source_text)
        
        assert "TypeError" in formatted
        assert "undefined_variable" in formatted
        assert "line 1" in formatted
