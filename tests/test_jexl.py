import pytest
import hypothesis

from pyjexl.analysis import JEXLAnalyzer
from pyjexl.exceptions import MissingTransformError, ParseError
from pyjexl.jexl import JEXL


@pytest.fixture(scope="module")
def jexl():
    """Return an instance of the JEXL class. Useful when tests are
    repeated with hypothesis since only one instance of JEXL is created
    once."""
    return JEXL()


def test_it_works(jexl):
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


def test_validate():
    jexl = JEXL()
    jexl.add_transform('foo', lambda x: x + 1)
    assert list(jexl.validate('5+6|foo')) == []

    errors = list(jexl.validate('5+6|bar'))
    assert len(errors) == 1
    assert 'bar' in errors[0]

    errors = list(jexl.validate('1+'))
    assert errors == ['Could not parse expression: 1+']

    errors = list(jexl.validate('"\n"'))
    assert errors == ['Could not parse expression: "\n"']


JEXL_ALPHABET = hypothesis.strategies.characters(whitelist_categories=(
    # Letters
    'Lu', 'Ll',
    # Numbers
    'Nd', 'No',
    # Spaces
    'Zs', 'Zl', 'Zp',
), whitelist_characters=[
    '\t', '\n', '\r', ' ',
    '$', '|', '+', '/',
    '(', ')', '{', '}', '[', ']',
    "'", '"', ',', ':', '?',
])


@hypothesis.given(hypothesis.strategies.text(JEXL_ALPHABET))
@hypothesis.settings(max_examples=500)
def test_validate_never_throws(jexl, s):
    errors = list(jexl.validate(s))
    assert isinstance(errors, list)

    # '{{' and '}}' are vanishingly rare sequences when generating
    # by-character the way we do. Artificially increase coverage of
    # these important sequences by explicitly generating them based on
    # single-character '{' and '}'.
    #
    # FIXME: figure out how to randomly generate a sequence of tokens
    # instead of characters.
    errors = list(jexl.validate(s.replace('{', '{{').replace('}', '}}')))
    assert isinstance(errors, list)


def test_validate_simple_equality():
    jexl = JEXL()
    errors = list(jexl.validate('FOO_BAR ==12345'))
    assert errors == []


class SumIntAnalyzer(JEXLAnalyzer):
    """Test analyzer that sums up all integers in a statement."""
    def generic_visit(self, expression):
        children = list(expression.children)
        if children:
            return sum(self.visit(child) for child in children)
        else:
            return 0

    def visit_Literal(self, literal):
        if isinstance(literal.value, int):
            return literal.value
        else:
            return 0


def test_analysis():
    jexl = JEXL()
    assert jexl.analyze('1+(2*3)|concat(4)', SumIntAnalyzer) == 10
