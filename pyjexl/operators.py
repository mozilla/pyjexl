import operator


class Operator(object):
    __slots__ = ('symbol', 'precedence', 'evaluate')

    def __init__(self, symbol, precedence, evaluate):
        self.symbol = symbol
        self.precedence = precedence
        self.evaluate = evaluate

    def __repr__(self):
        return 'Operator({})'.format(repr(self.symbol))


binary_operators = {
    '+': Operator('+', 30, operator.add),
    '-': Operator('-', 30, operator.sub),
    '*': Operator('*', 40, operator.mul),
    '/': Operator('/', 40, operator.truediv),

    '==': Operator('==', 20, operator.eq),
}
