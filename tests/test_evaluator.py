from builtins import str

import pytest

from pyjexl.evaluator import Context, Evaluator
from pyjexl.exceptions import MissingTransformError
from pyjexl.jexl import JEXLConfig
from pyjexl.operators import default_binary_operators, default_unary_operators

from . import DefaultEvaluator, DefaultParser


def tree(expression):
    return DefaultParser().parse(expression)


def test_literal():
    result = DefaultEvaluator().evaluate(tree('1'))
    assert result == 1.0


def test_binary_expression():
    result = DefaultEvaluator().evaluate(tree('1 + 2'))
    assert result == 3.0


def test_arithmetic():
    result = DefaultEvaluator().evaluate(tree('(2 + 3) * 4'))
    assert result == 20


def test_string_concat():
    # Because we don't have implicit type conversions like JavaScript,
    # we diverge from the original JEXL test suite and add a filter.
    config = JEXLConfig({'str': str}, default_binary_operators, default_unary_operators)
    evaluator = Evaluator(config)
    result = evaluator.evaluate(tree('"Hello" + (4+4)|str + "Wo\\"rld"'))
    assert result == 'Hello8Wo"rld'


def test_true_comparison():
    result = DefaultEvaluator().evaluate(tree('2 > 1'))
    assert result


def test_false_comparison():
    result = DefaultEvaluator().evaluate(tree('2 <= 1'))
    assert not result


def test_complex():
    result = DefaultEvaluator().evaluate(tree('"foo" && 6 >= 6 && 0 + 1 && true'))
    assert result


def test_identifier_chain():
    context = Context({'foo': {'baz': {'bar': 'tek'}}})
    result = DefaultEvaluator().evaluate(tree('foo.baz.bar'), context)
    assert result == 'tek'


def test_transforms():
    config = JEXLConfig(
        {'half': lambda x: x / 2},
        default_binary_operators,
        default_unary_operators
    )
    evaluator = Evaluator(config)
    result = evaluator.evaluate(tree('foo|half + 3'), {'foo': 10})
    assert result == 8


def test_filter_arrays():
    context = Context({
        'foo': {
            'bar': [
                {'tek': 'hello'},
                {'tek': 'baz'},
                {'tok': 'baz'}
            ]
        }
    })

    result = DefaultEvaluator().evaluate(tree('foo.bar[.tek == "baz"]'), context)
    assert result == [{'tek': 'baz'}]


def test_array_index():
    context = Context({
        'foo': {
            'bar': [
                {'tek': 'tok'},
                {'tek': 'baz'},
                {'tek': 'foz'}
            ]
        }
    })

    result = DefaultEvaluator().evaluate(tree('foo.bar[1].tek'), context)
    assert result == 'baz'


def test_filter_object_properties():
    context = Context({'foo': {'baz': {'bar': 'tek'}}})
    result = DefaultEvaluator().evaluate(tree('foo["ba" + "z"].bar'), context)
    assert result == 'tek'


def test_missing_transform_exception():
    with pytest.raises(MissingTransformError):
        DefaultEvaluator().evaluate(tree('"hello"|world'))


def test_divfloor():
    result = DefaultEvaluator().evaluate(tree('7 // 2'))
    assert result == 3


def test_object_literal():
    result = DefaultEvaluator().evaluate(tree('{foo: {bar: "tek"}}'))
    assert result == {'foo': {'bar': 'tek'}}


def test_empty_object_literal():
    result = DefaultEvaluator().evaluate(tree('{}'))
    assert result == {}


def test_transforms_multiple_arguments():
    config = JEXLConfig(
        binary_operators=default_binary_operators,
        unary_operators=default_unary_operators,
        transforms={
            'concat': lambda val, a1, a2, a3: val + ': ' + a1 + a2 + a3,
        }
    )
    evaluator = Evaluator(config)
    result = evaluator.evaluate(tree('"foo"|concat("baz", "bar", "tek")'))
    assert result == 'foo: bazbartek'


def test_object_literal_properties():
    result = DefaultEvaluator().evaluate(tree('{foo: "bar"}.foo'))
    assert result == 'bar'


def test_array_literal():
    result = DefaultEvaluator().evaluate(tree('["foo", 1+2]'))
    assert result == ['foo', 3]


def test_in_operator_string():
    result = DefaultEvaluator().evaluate(tree('"bar" in "foobartek"'))
    assert result is True

    result = DefaultEvaluator().evaluate(tree('"baz" in "foobartek"'))
    assert result is False


def test_in_operator_array():
    result = DefaultEvaluator().evaluate(tree('"bar" in ["foo","bar","tek"]'))
    assert result is True

    result = DefaultEvaluator().evaluate(tree('"baz" in ["foo","bar","tek"]'))
    assert result is False


def test_conditional_expression():
    result = DefaultEvaluator().evaluate(tree('"foo" ? 1 : 2'))
    assert result == 1

    result = DefaultEvaluator().evaluate(tree('"" ? 1 : 2'))
    assert result == 2


def test_arbitrary_whitespace():
    result = DefaultEvaluator().evaluate(tree('(\t2\n+\n3) *\n4\n\r\n'))
    assert result == 20
