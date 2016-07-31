import pytest

from pyjexl.exceptions import MissingTransformError
from pyjexl.jexl import JEXL


def test_it_works():
    assert JEXL().evaluate('1 + 1') == 2


def test_transform_pass_func():
    jexl = JEXL()
    jexl.transform('foo', lambda x: x + 2)
    assert jexl.evaluate('4|foo') == 6


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
