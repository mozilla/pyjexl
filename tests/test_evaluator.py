from pyjexl.evaluator import Evaluator
from pyjexl.parser import JEXLVisitor


def tree(expression):
    return JEXLVisitor().parse(expression)


def test_literal():
    result = Evaluator().evaluate(tree('1'))
    assert result == 1.0


def test_binary_expression():
    result = Evaluator().evaluate(tree('1 + 2'))
    assert result == 3.0
