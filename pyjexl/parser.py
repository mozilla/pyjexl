from parsimonious import Grammar, NodeVisitor

from pyjexl.operators import binary_operators, Operator, unary_operators


def operator_pattern(operators):
    """Generate a grammar rule to match a dict of operators."""
    operator_literals = ['"{}"'.format(op.symbol) for op in operators]
    return ' / '.join(operator_literals)


jexl_grammar = Grammar(r"""
    expression = binary_expression / value
    subexpression = "(" _ expression _ ")"

    unary_expression = unary_op _ value
    unary_op = {unary_op_pattern}

    binary_expression = value (_ binary_op _ value)+
    binary_op = {binary_op_pattern}

    value = (
        boolean / string / numeric / unary_expression / subexpression /
        object_literal / array_literal
    )

    object_literal = "{{" _ object_key_value_list? _ "}}"
    object_key_value_list = object_key_value (_ "," _ object_key_value)*
    object_key_value = identifier _ ":" _ expression

    array_literal = "[" _ array_value_list? _ "]"
    array_value_list = expression (_ "," _ expression)*

    identifier = ~r"[a-zA-Z_\$][a-zA-Z0-9_\$]*"

    boolean = "true" / "false"
    string = ("\"" ~r"[^\"]*" "\"") / ("'" ~r"[^']*" "'")
    numeric = "-"? number ("." number)?

    number = ~r"[0-9]+"
    _ = " "*
""".format(
    binary_op_pattern=operator_pattern(binary_operators.values()),
    unary_op_pattern=operator_pattern(unary_operators.values())
))


class JEXLVisitor(NodeVisitor):
    grammar = jexl_grammar

    def visit_expression(self, node, children):
        (expression,) = children
        return expression

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
        # from JEXL's parser code for handle binary operators.
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

    def visit_binary_op(self, node, children):
        return binary_operators[node.text]

    def visit_unary_expression(self, node, children):
        (operator, _, value) = children
        return UnaryExpression(operator=operator, right=value)

    def visit_unary_op(self, node, children):
        return unary_operators[node.text]

    def visit_value(self, node, children):
        if children[0] == '(':
            (left_paren, _, expression, _, right_paren) = children
            return expression
        else:
            (value,) = children
            return value

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

    def visit_array_value_list(self, node, children):
        values = [children[0]]
        for (_, comma, _, value) in children[1]:
            values.append(value)

        return values

    def visit_identifier(self, node, children):
        return Identifier(value=node.text)

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
        return Literal(node.text[1:-1])

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

    def root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.root()


class BinaryExpression(Node):
    fields = ['operator', 'left', 'right']


class UnaryExpression(Node):
    fields = ['operator', 'right']


class Literal(Node):
    fields = ['value']


class Identifier(Node):
    fields = ['value', 'from']


class ObjectLiteral(Node):
    fields = ['value']


class ArrayLiteral(Node):
    fields = ['value']
