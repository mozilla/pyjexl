from parsimonious import Grammar, NodeVisitor

from pyjexl.operators import binary_operators, Operator


def operator_pattern(operators):
    """Generate a grammar rule to match a dict of operators."""
    operator_literals = ['"{}"'.format(op.symbol) for op in operators]
    return ' / '.join(operator_literals)


jexl_grammar = Grammar(r"""
    expression = unary_expression / binary_expression / value

    unary_expression = unary_op value
    unary_op = "!"

    binary_expression = value (_ binary_op _ value)+
    binary_op = {binary_op_pattern}

    value = boolean / string / numeric / ("(" _ expression _ ")")
    boolean = "true" / "false"
    string = ("\"" ~r"[^\"]*" "\"") / ("'" ~r"[^']*" "'")
    numeric = "-"? number ("." number)?

    number = ~r"[0-9]+"
    _ = " "*
""".format(
    binary_op_pattern=operator_pattern(binary_operators.values())
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

    def visit_value(self, node, children):
        if children[0] == '(':
            (left_paren, _, expression, _, right_paren) = children
            return expression
        else:
            (value,) = children
            return value

    def visit_numeric(self, node, children):
        number_type = float if '.' in node.text else int
        return Literal(number_type(node.text))

    def generic_visit(self, node, visited_children):
        return visited_children or node


class Node(object):
    __slots__ = ('parent',)

    def __init__(self, parent=None):
        self.parent = parent

    def root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.root()


class BinaryExpression(Node):
    __slots__ = ('operator', 'left', 'right', 'parent')

    def __init__(self, operator, left=None, right=None, parent=None):
        super().__init__(parent=parent)
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self):
        return 'BinaryExpression(operator={operator}, left={left}, right={right})'.format(
            operator=repr(self.operator),
            left=repr(self.left),
            right=repr(self.right)
        )

    def __eq__(self, other):
        return (
            isinstance(other, BinaryExpression)
            and self.operator == other.operator
            and self.left == other.left
            and self.right == other.right
        )


class Literal(Node):
    __slots__ = ('value',)

    def __init__(self, value, parent=None):
        super().__init__(parent=parent)
        self.value = value

    def __repr__(self):
        return 'Literal({})'.format(repr(self.value))

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value
