"""
temple.compiler.type_checker
Type checking and semantic analysis for typed templates.

Walks AST, assigns types, validates against schema.
"""

from typing import Dict, Any, Optional, List
from temple.typed_ast import Node as ASTNode, Block, Text, Expression, If, For, Include

# Note: FunctionDef and FunctionCall not yet in typed_ast - need to add or remove usage
from .types import (
    BaseType,
    StringType,
    NumberType,
    BooleanType,
    NullType,
    ArrayType,
    ObjectType,
    AnyType,
    infer_type_from_value,
)
from .schema import Schema
from .type_errors import TypeErrorCollector, TypeErrorKind


class TypeEnvironment:
    """Manages variable bindings and types during type checking."""

    def __init__(self, parent: Optional["TypeEnvironment"] = None):
        self.parent = parent
        self.bindings: Dict[str, BaseType] = {}

    def bind(self, name: str, type_: BaseType):
        """Bind a variable name to a type in this scope."""
        self.bindings[name] = type_

    def lookup(self, name: str) -> Optional[BaseType]:
        """Look up a variable's type, checking parent scopes."""
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def get_all_names(self) -> List[str]:
        """Get all variable names in scope."""
        names = list(self.bindings.keys())
        if self.parent:
            names.extend(self.parent.get_all_names())
        return names

    def child_scope(self) -> "TypeEnvironment":
        """Create a child scope."""
        return TypeEnvironment(parent=self)


class TypeChecker:
    """Type checker for templates."""

    def __init__(self, schema: Optional[Schema] = None, data: Optional[Any] = None):
        self.schema = schema
        self.data = data
        self.errors = TypeErrorCollector()

        # Initialize root environment with data types
        self.root_env = TypeEnvironment()
        if data is not None:
            self._initialize_data_types(data)

    def _initialize_data_types(self, data: Any, prefix: str = ""):
        """Initialize type environment from input data."""
        if isinstance(data, dict):
            for key, value in data.items():
                var_name = f"{prefix}.{key}" if prefix else key
                inferred_type = infer_type_from_value(value)
                self.root_env.bind(var_name, inferred_type)

                # Recursively add nested properties for objects
                if isinstance(value, dict):
                    self._initialize_data_types(value, var_name)

    def check(self, ast: ASTNode) -> bool:
        """
        Type check an AST node.

        Returns:
            True if no errors, False if errors were found.
        """
        self._check_node(ast, self.root_env)
        return not self.errors.has_errors()

    def _check_node(self, node: ASTNode, env: TypeEnvironment) -> BaseType:
        """
        Check a node and return its type.

        This is the main dispatch method for type checking.
        """
        if isinstance(node, Text):
            return self._check_text(node, env)
        elif isinstance(node, Expression):
            return self._check_expression(node, env)
        elif isinstance(node, If):
            return self._check_if(node, env)
        elif isinstance(node, For):
            return self._check_for(node, env)
        elif isinstance(node, Include):
            return self._check_include(node, env)
        elif isinstance(node, Block):
            return self._check_block(node, env)
        elif isinstance(node, FunctionDef):
            return self._check_function_def(node, env)
        elif isinstance(node, FunctionCall):
            return self._check_function_call(node, env)
        elif isinstance(node, list):
            # List of nodes - check each
            for child in node:
                self._check_node(child, env)
            return AnyType()
        else:
            # Unknown node type
            return AnyType()

    def _check_text(self, node: Text, env: TypeEnvironment) -> BaseType:
        """Check a text node (always valid)."""
        return StringType()

    def _check_expression(self, node: Expression, env: TypeEnvironment) -> BaseType:
        """Check an expression node."""
        # Parse the expression value to extract variable path
        # For now, support simple dot notation: "var.prop.subprop"
        var_path = node.expr.strip()

        # Handle simple variable lookup
        if "." not in var_path:
            var_type = env.lookup(var_path)
            if var_type is None:
                self.errors.add_undefined_variable(
                    source_range=node.source_range,
                    var_name=var_path,
                    available_vars=env.get_all_names(),
                )
                return AnyType()
            return var_type

        # Handle property access: "obj.prop"
        parts = var_path.split(".")
        current_type = env.lookup(parts[0])

        if current_type is None:
            self.errors.add_undefined_variable(
                source_range=node.source_range,
                var_name=parts[0],
                available_vars=env.get_all_names(),
            )
            return AnyType()

        # Walk the property path
        for i, prop in enumerate(parts[1:], 1):
            if isinstance(current_type, ObjectType):
                if prop not in current_type.properties:
                    self.errors.add_missing_property(
                        source_range=node.source_range,
                        property_name=prop,
                        object_type=".".join(parts[:i]),
                        available_properties=list(current_type.properties.keys()),
                    )
                    return AnyType()
                current_type = current_type.properties[prop]
            else:
                # Not an object, can't access property
                self.errors.add_error(
                    kind=TypeErrorKind.TYPE_MISMATCH,
                    message=f"Cannot access property '{prop}' on non-object type",
                    source_range=node.source_range,
                    expected_type="object",
                    actual_type=type(current_type).__name__,
                )
                return AnyType()

        return current_type

    def _check_if(self, node: If, env: TypeEnvironment) -> BaseType:
        """Check an if statement."""
        # Check condition expression
        condition_type = self._check_expression(
            Expression(expr=node.condition, source_range=node.source_range), env
        )

        # Condition should be boolean or truthy
        # For now, accept any type (JavaScript-like truthiness)

        # Check body
        for child in node.body:
            self._check_node(child, env)

        # Check elif parts
        for elif_cond, elif_body in node.else_if_parts:
            self._check_expression(
                Expression(expr=elif_cond, source_range=node.source_range), env
            )
            for child in elif_body.nodes if isinstance(elif_body, Block) else elif_body:
                self._check_node(child, env)

        # Check else body
        if node.else_body:
            for child in node.else_body.nodes:
                self._check_node(child, env)

        return AnyType()

    def _check_for(self, node: For, env: TypeEnvironment) -> BaseType:
        """Check a for loop."""
        # Check iterable expression
        iterable_expr = Expression(expr=node.iterable, source_range=node.source_range)
        iterable_type = self._check_expression(iterable_expr, env)

        # Iterable should be an array
        if not isinstance(iterable_type, ArrayType) and not isinstance(
            iterable_type, AnyType
        ):
            self.errors.add_error(
                kind=TypeErrorKind.TYPE_MISMATCH,
                message=f"Cannot iterate over non-array type",
                source_range=node.source_range,
                expected_type="array",
                actual_type=type(iterable_type).__name__,
                suggestion="Use an array or check the variable type",
            )
            item_type = AnyType()
        else:
            item_type = (
                iterable_type.item_type
                if isinstance(iterable_type, ArrayType)
                else AnyType()
            )

        # Create child scope with loop variable
        loop_env = env.child_scope()
        loop_env.bind(node.var, item_type)

        # Check body in loop scope
        for child in node.body.nodes:
            self._check_node(child, loop_env)

        return AnyType()

    def _check_include(self, node: Include, env: TypeEnvironment) -> BaseType:
        """Check an include statement."""
        # For now, just verify the path is a string
        # Full implementation would load and type-check the included template
        return AnyType()

    def _check_block(self, node: Block, env: TypeEnvironment) -> BaseType:
        """Check a block definition."""
        # Check body
        for child in node.body:
            self._check_node(child, env)
        return AnyType()

    def _check_function_def(self, node: FunctionDef, env: TypeEnvironment) -> BaseType:
        """Check a function definition."""
        # Create child scope for function body
        func_env = env.child_scope()

        # Bind function arguments (types unknown for now)
        for arg in node.args:
            func_env.bind(arg, AnyType())

        # Check function body
        for child in node.body:
            self._check_node(child, func_env)

        return AnyType()

    def _check_function_call(
        self, node: FunctionCall, env: TypeEnvironment
    ) -> BaseType:
        """Check a function call."""
        # Check arguments
        for arg in node.args:
            self._check_expression(
                Expression(value=arg, source_range=node.source_range), env
            )

        return AnyType()

    def validate_output_schema(self, ast: ASTNode) -> bool:
        """
        Validate that the template output will match the schema.

        This is a simplified check - full implementation would
        simulate rendering to determine output structure.
        """
        if not self.schema:
            return True

        # For now, just run type checking
        return self.check(ast)
