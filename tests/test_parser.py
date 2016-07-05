from pyjexl.parser import BinaryOperator, JEXLVisitor, Literal


def test_literal():
    assert JEXLVisitor().parse('1') == Literal(1.0)


def test_binary_expression():
    assert JEXLVisitor().parse('1+2') == BinaryOperator(
        operator='+',
        left=Literal(1),
        right=Literal(2)
    )
