import ast

from parsimonious import Grammar, NodeVisitor

from pyjexl.exceptions import InvalidOperatorError
from pyjexl.operators import Operator


def operator_pattern(operators):
    """Generate a grammar rule to match a dict of operators."""
    # Sort operators and reverse them so that operators sharing a prefix
    # always have the shortest forms last. Otherwise, the shorter forms
    # will match operators early, i.e. `<` will match `<=` and ignore
    # the `=`, causing a parse error.
    operators = sorted(operators, key=lambda op: op.symbol, reverse=True)
    operator_literals = ['"{}"'.format(op.symbol) for op in operators]
    return ' / '.join(operator_literals)


def jexl_grammar(jexl_config):
    return Grammar(r"""
        expression = (
            _ (conditional_expression / binary_expression / unary_expression / complex_value) _
        )

        conditional_expression = (
            conditional_test _ "?" _ expression _ ":" _ expression
        )
        conditional_test = (binary_expression / unary_expression / complex_value)

        binary_expression = binary_operand (_ binary_operator _ binary_operand)+
        binary_operator = {binary_op_pattern}
        binary_operand = (unary_expression / complex_value)

        unary_expression = unary_operator _ unary_operand
        unary_operator = {unary_op_pattern}
        unary_operand = (unary_expression / complex_value)

        complex_value = value (transform / attribute / filter_expression)*

        transform = "|" identifier transform_arguments?
        transform_arguments = "(" _ value_list _ ")"

        attribute = "." identifier

        filter_expression = "[" _ expression _ "]"

        value = (
            boolean / string / numeric / subexpression / object_literal /
            array_literal / identifier / relative_identifier
        )

        subexpression = "(" _ expression _ ")"

        object_literal = "{{" _ object_key_value_list? _ "}}"
        object_key_value_list = object_key_value (_ "," _ object_key_value)*
        object_key_value = identifier _ ":" _ expression

        array_literal = "[" _ value_list? _ "]"
        value_list = expression (_ "," _ expression)*

        identifier = ~r"[a-zA-Z_\$][a-zA-Z0-9_\$]*"
        relative_identifier = "." identifier

        boolean = "true" / "false"
        string = ~"\"[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*\""is /
                 ~"'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'"is
        numeric = "-"? number ("." number)?

        number = ~r"[0-9]+"

        _ = ~r"\s*"
    """.format(
        binary_op_pattern=operator_pattern(jexl_config.binary_operators.values()),
        unary_op_pattern=operator_pattern(jexl_config.unary_operators.values())
    ))


class Parser(NodeVisitor):
    def __init__(self, jexl_config):
        self.config = jexl_config
        self._relative = 0

    def visit_expression(self, node, children):
        return children[1][0]

    def visit_subexpression(self, node, children):
        (left_paren, _, expression, _, right_paren) = children
        return expression

    def visit_binary_expression(self, node, children):
        pieces = [children[0]]
        for op_value in node.children[1].children:
            op_symbol = self.visit(op_value.children[1])
            value = self.visit(op_value.children[3])
            pieces.append(op_symbol)
            pieces.append(value)

        # Build a tree of binary operators based on precedence. Adapted
        # from JEXL's parser code for handling binary operators.
        cursor = pieces.pop(0)
        for piece in pieces:
            if not isinstance(piece, Operator):
                cursor.right = piece
                piece.parent = cursor
                cursor = piece
                continue

            # Parents are always operators
            parent = cursor.parent
            while parent is not None and parent.operator.precedence >= piece.precedence:
                cursor = parent
                parent = cursor.parent

            node = BinaryExpression(operator=piece, left=cursor, parent=parent)
            cursor.parent = node
            if parent is not None:
                parent.right = node
            cursor = node

        return cursor.root()

    def visit_conditional_expression(self, node, children):
        (test, _, question, _, consequent, _, colon, _, alternate) = children
        return ConditionalExpression(test=test, consequent=consequent, alternate=alternate)

    def visit_conditional_test(self, node, children):
        return children[0]

    def visit_binary_operator(self, node, children):
        try:
            return self.config.binary_operators[node.text]
        except KeyError as err:
            raise InvalidOperatorError(node.text) from err

    def visit_binary_operand(self, node, children):
        return children[0]

    def visit_unary_expression(self, node, children):
        (operator, _, value) = children
        return UnaryExpression(operator=operator, right=value)

    def visit_unary_operator(self, node, children):
        try:
            return self.config.unary_operators[node.text]
        except KeyError as err:
            raise InvalidOperatorError(node.text) from err

    def visit_unary_operand(self, node, children):
        return children[0]

    def visit_object_literal(self, node, children):
        (left_brace, _, value, _, right_brace) = children

        return ObjectLiteral(value=value[0] if isinstance(value, list) else {})

    def visit_object_key_value_list(self, node, children):
        key_values = [children[0]]
        for (_, comma, _, key_value) in children[1]:
            key_values.append(key_value)

        return {identifier.value: value for identifier, value in key_values}

    def visit_object_key_value(self, node, children):
        (identifier, _, colon, _, value) = children
        return (identifier, value)

    def visit_array_literal(self, node, children):
        (left_bracket, _, value, _, right_bracket) = children
        return ArrayLiteral(value=value[0] if isinstance(value, list) else [])

    def visit_value_list(self, node, children):
        values = [children[0]]
        for (_, comma, _, value) in children[1]:
            values.append(value)

        return values

    def visit_complex_value(self, node, children):
        (value, modifiers) = children

        current = value
        for (modifier,) in modifiers:
            modifier.subject = current
            current = modifier

        return current

    def visit_attribute(self, node, children):
        (dot, identifier) = children
        return identifier

    def visit_transform(self, node, children):
        (bar, identifier, arguments) = children
        transform = Transform(name=identifier.value, args=[])

        try:
            transform.args = arguments[0]
        except (IndexError, TypeError):
            pass

        return transform

    def visit_transform_arguments(self, node, children):
        (left_paren, _, values, _, right_paren) = children
        return values

    def visit_filter_expression(self, node, children):
        (left_bracket, _, expression, _, right_bracket) = children
        return FilterExpression(expression=expression, relative=expression.contains_relative())

    def visit_identifier(self, node, children):
        return Identifier(value=node.text, relative=False)

    def visit_relative_identifier(self, node, children):
        (dot, identifier) = children
        identifier.relative = True
        return identifier

    def visit_value(self, node, children):
        return children[0]

    def visit_boolean(self, node, children):
        if node.text == 'true':
            return Literal(True)
        elif node.text == 'false':
            return Literal(False)
        else:
            raise ValueError('Could not parse boolean: ' + node.text)

    def visit_numeric(self, node, children):
        number_type = float if '.' in node.text else int
        return Literal(number_type(node.text))

    def visit_string(self, node, children):
        return Literal(ast.literal_eval(node.text))

    def generic_visit(self, node, visited_children):
        return visited_children or node


class NodeMeta(type):
    """
    Metaclass for making AST nodes. Handles adding the Node's custom
    fields to __slots__ and ensures every Node has a parent field.
    """
    def __new__(meta, classname, bases, classdict):
        if 'parent' not in classdict['fields']:
            classdict['fields'].append('parent')
        classdict.update({
            '__slots__': classdict['fields'],
        })
        return type.__new__(meta, classname, bases, classdict)


class Node(object, metaclass=NodeMeta):
    """
    Base class for AST Nodes.

    Nodes are like mutable namedtuples. Each node type should declare a
    fields attribute on the class that lists the desired attributes for
    the class.
    """
    fields = []

    def __init__(self, *args, **kwargs):
        """
        Accepts values for this node's fields as both positional (in the
        order defined in self.fields) and keyword arguments.
        """
        for index, field in enumerate(self.fields):
            if len(args) > index:
                setattr(self, field, args[index])
            else:
                setattr(self, field, kwargs.get(field, None))

    def __repr__(self):
        kwargs = [
            '='.join([field, repr(getattr(self, field))])
            for field in self.fields if field != 'parent'
        ]

        return '{name}({kwargs})'.format(
            name=type(self).__name__,
            kwargs=', '.join(kwargs)
        )

    def __eq__(self, other):
        return isinstance(other, type(self)) and all(
            getattr(self, field) == getattr(other, field)
            for field in self.fields if field != 'parent'
        )

    @property
    def children(self):
        return iter(())

    def root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.root()

    def contains_relative(self):
        children_relative = any(
            child.contains_relative() for child in self.children if child is not None
        )
        return getattr(self, 'relative', children_relative)


class BinaryExpression(Node):
    fields = ['operator', 'left', 'right']

    @property
    def children(self):
        yield self.left
        yield self.right


class UnaryExpression(Node):
    fields = ['operator', 'right']

    @property
    def children(self):
        yield self.right


class Literal(Node):
    fields = ['value']


class Identifier(Node):
    fields = ['value', 'subject', 'relative']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('relative', False)
        super().__init__(*args, **kwargs)

    @property
    def children(self):
        if self.subject is not None:
            yield self.subject


class ObjectLiteral(Node):
    fields = ['value']


class ArrayLiteral(Node):
    fields = ['value']


class Transform(Node):
    fields = ['name', 'args', 'subject']

    @property
    def children(self):
        yield self.subject
        yield from self.args


class FilterExpression(Node):
    fields = ['expression', 'subject', 'relative']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('relative', False)
        super().__init__(*args, **kwargs)

    @property
    def children(self):
        yield self.expression
        yield self.subject

    def contains_relative(self):
        return self.subject.contains_relative()


class ConditionalExpression(Node):
    fields = ['test', 'consequent', 'alternate']

    @property
    def children(self):
        yield self.test
        yield self.consequent
        yield self.alternate
