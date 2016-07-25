import operator
from collections import OrderedDict


class Operator(object):
    __slots__ = ('symbol', 'precedence', 'evaluate')

    def __init__(self, symbol, precedence, evaluate):
        self.symbol = symbol
        self.precedence = precedence
        self.evaluate = evaluate

    def __repr__(self):
        return 'Operator({})'.format(repr(self.symbol))


# Operators need to be stored in order so that operators sharing a
# prefix are resolved correctly during parsing. If > is before >=, for
# example, > will match first even if the operator is actually >=.
binary_operators = OrderedDict([
    ('+', Operator('+', 30, operator.add)),
    ('-', Operator('-', 30, operator.sub)),
    ('*', Operator('*', 40, operator.mul)),
    ('//', Operator('//', 40, operator.floordiv)),
    ('/', Operator('/', 40, operator.truediv)),
    ('%', Operator('%', 50, operator.mod)),
    ('^', Operator('^', 50, operator.pow)),
    ('==', Operator('==', 20, operator.eq)),
    ('!=', Operator('!=', 20, operator.ne)),
    ('>=', Operator('>=', 20, operator.ge)),
    ('>', Operator('>', 20, operator.gt)),
    ('<=', Operator('<=', 20, operator.le)),
    ('<', Operator('<', 20, operator.lt)),
    ('&&', Operator('&&', 10, lambda a, b: a and b)),
    ('||', Operator('||', 10, lambda a, b: a or b)),
    ('in', Operator('in', 20, lambda a, b: a in b)),
])


unary_operators = OrderedDict([
    ('!', Operator('!', 1000, operator.not_)),
])


operators = OrderedDict()
operators.update(binary_operators)
operators.update(unary_operators)
