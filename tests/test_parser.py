from pyjexl.operators import operators
from pyjexl.parser import BinaryExpression, JEXLVisitor, Literal, UnaryExpression


def op(operator):
    return operators[operator]


def test_literal():
    assert JEXLVisitor().parse('1') == Literal(1.0)


def test_binary_expression():
    assert JEXLVisitor().parse('1+2') == BinaryExpression(
        operator=op('+'),
        left=Literal(1),
        right=Literal(2)
    )


def test_binary_expression_priority_right():
    assert JEXLVisitor().parse('2+3*4') == BinaryExpression(
        operator=op('+'),
        left=Literal(2),
        right=BinaryExpression(
            operator=op('*'),
            left=Literal(3),
            right=Literal(4),
        )
    )


def test_binary_expression_priority_left():
    assert JEXLVisitor().parse('2*3+4') == BinaryExpression(
        operator=op('+'),
        left=BinaryExpression(
            operator=op('*'),
            left=Literal(2),
            right=Literal(3),
        ),
        right=Literal(4)
    )


def test_binary_expression_encapsulation():
    assert JEXLVisitor().parse('2+3*4==5/6-7') == BinaryExpression(
        operator=op('=='),
        left=BinaryExpression(
            operator=op('+'),
            left=Literal(2),
            right=BinaryExpression(
                operator=op('*'),
                left=Literal(3),
                right=Literal(4)
            ),
        ),
        right=BinaryExpression(
            operator=op('-'),
            left=BinaryExpression(
                operator=op('/'),
                left=Literal(5),
                right=Literal(6)
            ),
            right=Literal(7)
        )
    )


def test_unary_operator():
    assert JEXLVisitor().parse('1*!!true-2') == BinaryExpression(
        operator=op('-'),
        left=BinaryExpression(
            operator=op('*'),
            left=Literal(1),
            right=UnaryExpression(
                operator=op('!'),
                right=UnaryExpression(
                    operator=op('!'),
                    right=Literal(True)
                )
            )
        ),
        right=Literal(2)
    )


def test_subexpression():
    assert JEXLVisitor().parse('(2+3)*4') == BinaryExpression(
        operator=op('*'),
        left=BinaryExpression(
            operator=op('+'),
            left=Literal(2),
            right=Literal(3)
        ),
        right=Literal(4)
    )


def test_nested_subexpression():
    assert JEXLVisitor().parse('(4*(2+3))/5') == BinaryExpression(
        operator=op('/'),
        left=BinaryExpression(
            operator=op('*'),
            left=Literal(4),
            right=BinaryExpression(
                operator=op('+'),
                left=Literal(2),
                right=Literal(3)
            )
        ),
        right=Literal(5)
    )
