from pyjexl.operators import binary_operators
from pyjexl.parser import BinaryOperator, JEXLVisitor, Literal


def op(operator):
    return binary_operators[operator]


def test_literal():
    assert JEXLVisitor().parse('1') == Literal(1.0)


def test_binary_expression():
    assert JEXLVisitor().parse('1+2') == BinaryOperator(
        operator=op('+'),
        left=Literal(1),
        right=Literal(2)
    )


def test_binary_expression_priority_right():
    assert JEXLVisitor().parse('2+3*4') == BinaryOperator(
        operator=op('+'),
        left=Literal(2),
        right=BinaryOperator(
            operator=op('*'),
            left=Literal(3),
            right=Literal(4),
        )
    )


def test_binary_expression_priority_left():
    assert JEXLVisitor().parse('2*3+4') == BinaryOperator(
        operator=op('+'),
        left=BinaryOperator(
            operator=op('*'),
            left=Literal(2),
            right=Literal(3),
        ),
        right=4
    )
