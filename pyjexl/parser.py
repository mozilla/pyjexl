from parsimonious import Grammar, NodeVisitor

from pyjexl.operators import binary_operators, Operator, unary_operators


def operator_pattern(operators):
    """Generate a grammar rule to match a dict of operators."""
    operator_literals = ['"{}"'.format(op.symbol) for op in operators]
    return ' / '.join(operator_literals)


jexl_grammar = Grammar(r"""
    expression = binary_expression / value

    unary_expression = unary_op _ value
    unary_op = {unary_op_pattern}

    binary_expression = value (_ binary_op _ value)+
    binary_op = {binary_op_pattern}

    value = boolean / string / numeric / unary_expression / ("(" _ expression _ ")")
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

    def generic_visit(self, node, visited_children):
        return visited_children or node


class Node(type):
    """
    Metaclass for making AST nodes.

    AST nodes are kinda like mutable namedtuples; they have a set of
    attributes that can be set positionally or by kwarg in the
    constructor, default to None, and can be compared with eachother
    easily.

    Nodes are also given an extra `parent` field, which is useful mainly
    for building binary expression trees. The parent field is ignored
    in equality testing.
    """
    def __new__(meta, classname, bases, classdict):
        classdict.setdefault('fields', [])
        classdict['fields'].append('parent')
        classdict.update({
            '__init__': meta._init,
            '__repr__': meta._repr,
            '__eq__': meta._eq,
            '__slots__': classdict['fields'],
            'root': meta.root,
        })
        return type.__new__(meta, classname, bases, classdict)

    def _init(self, *args, **kwargs):
        for index, field in enumerate(self.fields):
            if len(args) > index:
                setattr(self, field, args[index])
            else:
                setattr(self, field, kwargs.get(field, None))

    def _repr(self):
        kwargs = [
            '='.join([field, repr(getattr(self, field))])
            for field in self.fields if field != 'parent'
        ]
        return '{name}({kwargs})'.format(
            name=type(self).__name__,
            kwargs=', '.join(kwargs)
        )

    def _eq(self, other):
        return isinstance(other, type(self)) and all(
            getattr(self, field) == getattr(other, field)
            for field in self.fields if field != 'parent'
        )

    def root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.root()


class BinaryExpression(metaclass=Node):
    fields = ['operator', 'left', 'right']


class UnaryExpression(metaclass=Node):
    fields = ['operator', 'right']


class Literal(metaclass=Node):
    fields = ['value']
