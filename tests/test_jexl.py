import pytest

from pyjexl.exceptions import MissingTransformError, ParseError
from pyjexl.jexl import JEXL


def test_it_works():
    assert JEXL().evaluate('1 + 1') == 2


def test_parse_error():
    jexl = JEXL()
    with pytest.raises(ParseError):
        jexl.evaluate('this is ( invalid + =s')


def test_add_transform():
    jexl = JEXL()
    jexl.add_transform('foo', lambda x: x + 2)
    assert jexl.evaluate('4|foo') == 6


def test_remove_transform():
    jexl = JEXL()
    jexl.add_transform('foo', lambda x: x)
    assert jexl.evaluate('4|foo') == 4

    jexl.remove_transform('foo')
    with pytest.raises(MissingTransformError):
        jexl.evaluate('4|foo')


def test_transform_decorator_explicit_name():
    jexl = JEXL()

    @jexl.transform(name='new_name')
    def old_name(x):
        return x + 2

    assert jexl.evaluate('3|new_name') == 5
    with pytest.raises(MissingTransformError):
        jexl.evaluate('3|old_name')


def test_transform_decorator_using_function_name():
    jexl = JEXL()

    @jexl.transform()
    def old_name(x):
        return x + 2

    assert jexl.evaluate('3|old_name') == 5


def test_add_custom_binary_operator():
    jexl = JEXL()
    jexl.add_binary_operator('=', 20, lambda x, y: (x + y) / 2)
    assert jexl.evaluate('2 = 4') == 3


def test_remove_binary_operator():
    jexl = JEXL()
    jexl.remove_binary_operator('+')
    with pytest.raises(ParseError):
        jexl.evaluate('2 + 4')


def test_binary_operator_precedence():
    jexl = JEXL()
    jexl.add_binary_operator('=', 50, lambda x, y: x + y)
    jexl.add_binary_operator('@', 100, lambda x, y: x / y)

    assert jexl.evaluate('(3 = 6) @ 3') == 3
    assert jexl.evaluate('3 = 6 @ 3') == 5


def test_add_custom_unary_operator():
    jexl = JEXL()
    jexl.add_unary_operator('=', lambda x: x + 5)
    assert jexl.evaluate('=5') == 10


def test_remove_unary_operator():
    jexl = JEXL()
    jexl.remove_unary_operator('!')
    with pytest.raises(ParseError):
        jexl.evaluate('!true')


def test_grammar_invalidation():
    """
    Ensure that the grammar object doesn't get stale when operators
    change.
    """
    jexl = JEXL()
    jexl.add_unary_operator('=', lambda x: x + 5)
    assert jexl.evaluate('=5') == 10

    jexl.remove_unary_operator('=')
    with pytest.raises(ParseError):
        jexl.evaluate('=5')
