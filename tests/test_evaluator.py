import pytest

from pyjexl.evaluator import Evaluator
from pyjexl.exceptions import MissingTransformError
from pyjexl.parser import JEXLVisitor


def tree(expression):
    return JEXLVisitor().parse(expression)


def test_literal():
    result = Evaluator().evaluate(tree('1'))
    assert result == 1.0


def test_binary_expression():
    result = Evaluator().evaluate(tree('1 + 2'))
    assert result == 3.0


def test_arithmetic():
    result = Evaluator().evaluate(tree('(2 + 3) * 4'))
    assert result == 20


def test_string_concat():
    # Because we don't have implicit type conversions like JavaScript,
    # we diverge from the original JEXL test suite and add a filter.
    evaluator = Evaluator()
    evaluator.register_transform(str)
    result = evaluator.evaluate(tree('"Hello" + (4+4)|str + "Wo\\"rld"'))
    assert result == 'Hello8Wo"rld'


def test_true_comparison():
    result = Evaluator().evaluate(tree('2 > 1'))
    assert result


def test_false_comparison():
    result = Evaluator().evaluate(tree('2 <= 1'))
    assert not result


def test_complex():
    result = Evaluator().evaluate(tree('"foo" && 6 >= 6 && 0 + 1 && true'))
    assert result


def test_identifier_chain():
    context = {'foo': {'baz': {'bar': 'tek'}}}
    result = Evaluator(context).evaluate(tree('foo.baz.bar'))
    assert result == 'tek'


def test_transforms():
    evaluator = Evaluator({'foo': 10})

    @evaluator.register_transform
    def half(val):
        return val / 2

    result = evaluator.evaluate(tree('foo|half + 3'))
    assert result == 8


def test_filter_arrays():
    evaluator = Evaluator({
        'foo': {
            'bar': [
                {'tek': 'hello'},
                {'tek': 'baz'},
                {'tok': 'baz'}
            ]
        }
    })

    result = evaluator.evaluate(tree('foo.bar[.tek == "baz"]'))
    assert result == [{'tek': 'baz'}]


def test_array_index():
    evaluator = Evaluator({
        'foo': {
            'bar': [
                {'tek': 'tok'},
                {'tek': 'baz'},
                {'tek': 'foz'}
            ]
        }
    })

    result = evaluator.evaluate(tree('foo.bar[1].tek'))
    assert result == 'baz'


def test_filter_object_properties():
    evaluator = Evaluator({'foo': {'baz': {'bar': 'tek'}}})
    result = evaluator.evaluate(tree('foo["ba" + "z"].bar'))
    assert result == 'tek'


def test_missing_transform_exception():
    with pytest.raises(MissingTransformError):
        Evaluator().evaluate(tree('"hello"|world'))


def test_divfloor():
    result = Evaluator().evaluate(tree('7 // 2'))
    assert result == 3


def test_object_literal():
    result = Evaluator().evaluate(tree('{foo: {bar: "tek"}}'))
    assert result == {'foo': {'bar': 'tek'}}


def test_empty_object_literal():
    result = Evaluator().evaluate(tree('{}'))
    assert result == {}


def test_transforms_multiple_arguments():
    evaluator = Evaluator()

    @evaluator.register_transform
    def concat(val, a1, a2, a3):
        return val + ': ' + a1 + a2 + a3

    result = evaluator.evaluate(tree('"foo"|concat("baz", "bar", "tek")'))
    assert result == 'foo: bazbartek'


def test_object_literal_properties():
    result = Evaluator().evaluate(tree('{foo: "bar"}.foo'))
    assert result == 'bar'


def test_array_literal():
    result = Evaluator().evaluate(tree('["foo", 1+2]'))
    assert result == ['foo', 3]


def test_in_operator_string():
    result = Evaluator().evaluate(tree('"bar" in "foobartek"'))
    assert result is True

    result = Evaluator().evaluate(tree('"baz" in "foobartek"'))
    assert result is False


def test_in_operator_array():
    result = Evaluator().evaluate(tree('"bar" in ["foo","bar","tek"]'))
    assert result is True

    result = Evaluator().evaluate(tree('"baz" in ["foo","bar","tek"]'))
    assert result is False


def test_conditional_expression():
    result = Evaluator().evaluate(tree('"foo" ? 1 : 2'))
    assert result == 1

    result = Evaluator().evaluate(tree('"" ? 1 : 2'))
    assert result == 2


def test_arbitrary_whitespace():
    result = Evaluator().evaluate(tree('(\t2\n+\n3) *\n4\n\r\n'))
    assert result == 20
