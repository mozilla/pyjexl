from collections import namedtuple

from parsimonious import Grammar, NodeVisitor


jexl_grammar = Grammar(r"""
    expression = unary_expression / binary_expression / value

    unary_expression = unary_op value
    unary_op = "!"

    binary_expression = value (_ binary_op _ value)+
    binary_op = (
        "+" /
        "-" /
        "*" /
        "/" /
        "//" /
        "%" /
        "^" /
        "&&" /
        "||" /
        "==" /
        "!=" /
        ">" /
        ">=" /
        "<" /
        "<=" /
        "in"
    )

    value = boolean / string / numeric / ("(" _ expression _ ")")
    boolean = "true" / "false"
    string = ("\"" ~r"[^\"]*" "\"") / ("'" ~r"[^']*" "'")
    numeric = "-"? number ("." number)?

    number = ~r"[0-9]+"
    _ = " "*
""")


class JEXLVisitor(NodeVisitor):
    grammar = jexl_grammar

    def visit_expression(self, node, children):
        (expression,) = children
        return expression

    def visit_binary_expression(self, node, children):
        pieces = [children[0]]
        for op_value in node.children[1].children:
            binary_op = self.visit(op_value.children[1])
            value = self.visit(op_value.children[3])
            pieces.append(binary_op)
            pieces.append(value)

        (left, operator, right) = pieces
        return BinaryOperator(operator=operator, left=left, right=right)

    def visit_binary_op(self, node, children):
        return node.text

    def visit_value(self, node, children):
        if children[0] == '(':
            (left_paren, _, expression, _, right_paren) = children
            return expression
        else:
            (value,) = children
            return value

    def visit_numeric(self, node, children):
        return Literal(float(node.text))

    def generic_visit(self, node, visited_children):
        return visited_children or node


BinaryOperator = namedtuple('BinaryOperator', ('operator', 'left', 'right'))
Literal = namedtuple('Literal', ('value',))
