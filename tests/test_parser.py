from pyjexl.operators import operators
from pyjexl.parser import (
    ArrayLiteral,
    BinaryExpression,
    ConditionalExpression,
    Identifier,
    JEXLVisitor,
    Literal,
    ObjectLiteral,
    Transform,
    UnaryExpression,
    FilterExpression
)


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


def test_object_literal():
    assert JEXLVisitor().parse('{foo: "bar", tek: 1+2}') == ObjectLiteral({
        'foo': Literal('bar'),
        'tek': BinaryExpression(
            operator=op('+'),
            left=Literal(1),
            right=Literal(2)
        )
    })


def test_nested_object_literals():
    assert JEXLVisitor().parse('{foo: {bar: "tek"}}') == ObjectLiteral({
        'foo': ObjectLiteral({
            'bar': Literal('tek')
        })
    })


def test_empty_object_literals():
    assert JEXLVisitor().parse('{}') == ObjectLiteral({})


def test_array_literals():
    assert JEXLVisitor().parse('["foo", 1+2]') == ArrayLiteral([
        Literal('foo'),
        BinaryExpression(
            operator=op('+'),
            left=Literal(1),
            right=Literal(2)
        )
    ])


def test_nexted_array_literals():
    assert JEXLVisitor().parse('["foo", ["bar", "tek"]]') == ArrayLiteral([
        Literal('foo'),
        ArrayLiteral([
            Literal('bar'),
            Literal('tek')
        ])
    ])


def test_empty_array_literals():
    assert JEXLVisitor().parse('[]') == ArrayLiteral([])


def test_chained_identifiers():
    assert JEXLVisitor().parse('foo.bar.baz + 1') == BinaryExpression(
        operator=op('+'),
        left=Identifier(
            'baz',
            subject=Identifier(
                'bar',
                subject=Identifier('foo')
            )
        ),
        right=Literal(1)
    )


def test_transforms():
    assert JEXLVisitor().parse('foo|tr1|tr2.baz|tr3({bar:"tek"})') == Transform(
        name='tr3',
        args=[ObjectLiteral({
            'bar': Literal('tek')
        })],
        subject=Identifier(
            'baz',
            subject=Transform(
                name='tr2',
                args=[],
                subject=Transform(
                    name='tr1',
                    args=[],
                    subject=Identifier('foo')
                )
            )
        )
    )


def test_transforms_multiple_arguments():
    assert JEXLVisitor().parse('foo|bar("tek", 5, true)') == Transform(
        name='bar',
        args=[
            Literal('tek'),
            Literal(5),
            Literal(True)
        ],
        subject=Identifier('foo')
    )


def test_filters():
    assert JEXLVisitor().parse('foo[1][.bar[0]=="tek"].baz') == Identifier(
        value='baz',
        subject=FilterExpression(
            relative=True,
            expression=BinaryExpression(
                operator=op('=='),
                left=FilterExpression(
                    relative=False,
                    expression=Literal(0),
                    subject=Identifier('bar', relative=True)
                ),
                right=Literal('tek')
            ),
            subject=FilterExpression(
                relative=False,
                expression=Literal(1),
                subject=Identifier('foo')
            )
        )
    )


def test_attribute_all_operands():
    assert JEXLVisitor().parse('"foo".length + {foo: "bar"}.foo') == BinaryExpression(
        operator=op('+'),
        left=Identifier('length', subject=Literal('foo')),
        right=Identifier(
            value='foo',
            subject=ObjectLiteral({
                'foo': Literal('bar')
            })
        )
    )


def test_attribute_subexpression():
    assert JEXLVisitor().parse('("foo" + "bar").length') == Identifier(
        value='length',
        subject=BinaryExpression(
            operator=op('+'),
            left=Literal('foo'),
            right=Literal('bar')
        )
    )


def test_attribute_array():
    assert JEXLVisitor().parse('["foo", "bar"].length') == Identifier(
        value='length',
        subject=ArrayLiteral([
            Literal('foo'),
            Literal('bar')
        ])
    )


def test_ternary_expression():
    assert JEXLVisitor().parse('foo ? 1 : 0') == ConditionalExpression(
        test=Identifier('foo'),
        consequent=Literal(1),
        alternate=Literal(0)
    )


def test_nested_grouped_ternary_expression():
    assert JEXLVisitor().parse('foo ? (bar ? 1 : 2) : 3') == ConditionalExpression(
        test=Identifier('foo'),
        consequent=ConditionalExpression(
            test=Identifier('bar'),
            consequent=Literal(1),
            alternate=Literal(2)
        ),
        alternate=Literal(3)
    )


def test_nested_non_grouped_ternary_expression():
    assert JEXLVisitor().parse('foo ? bar ? 1 : 2 : 3') == ConditionalExpression(
        test=Identifier('foo'),
        consequent=ConditionalExpression(
            test=Identifier('bar'),
            consequent=Literal(1),
            alternate=Literal(2)
        ),
        alternate=Literal(3)
    )


def test_object_ternary_expression():
    assert JEXLVisitor().parse('foo ? {bar: "tek"} : "baz"') == ConditionalExpression(
        test=Identifier('foo'),
        consequent=ObjectLiteral({
            'bar': Literal('tek')
        }),
        alternate=Literal('baz')
    )


def test_complex_binary_operator_balancing():
    assert JEXLVisitor().parse('a.b == c.d') == BinaryExpression(
        operator=op('=='),
        left=Identifier('b', subject=Identifier('a')),
        right=Identifier('d', subject=Identifier('c'))
    )
