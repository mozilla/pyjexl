import operator


class Operator(object):
    __slots__ = ('symbol', 'precedence', 'evaluate', '_evaluate_lazy')

    def __init__(self, symbol, precedence, evaluate, evaluate_lazy=False):
        """Operator definition.

        If evaluate_lazy is set to True, the `evaluate()` method will receive
        it's parameters as a lambda expression that needs to be called to
        receive the value of the expression. Otherwise, the values will
        already be evaluated.
        """
        self.symbol = symbol
        self.precedence = precedence
        self.evaluate = evaluate
        self._evaluate_lazy = evaluate_lazy

    def do_evaluate(self, *args):
        if self._evaluate_lazy:
            return self.evaluate(*args)
        return self.evaluate(*(arg() for arg in args))

    def __repr__(self):
        return 'Operator({})'.format(repr(self.symbol))


default_binary_operators = {
    '+': Operator('+', 30, operator.add),
    '-': Operator('-', 30, operator.sub),
    '*': Operator('*', 40, operator.mul),
    '//': Operator('//', 40, operator.floordiv),
    '/': Operator('/', 40, operator.truediv),
    '%': Operator('%', 50, operator.mod),
    '^': Operator('^', 50, operator.pow),
    '==': Operator('==', 20, operator.eq),
    '!=': Operator('!=', 20, operator.ne),
    '>=': Operator('>=', 20, operator.ge),
    '>': Operator('>', 20, operator.gt),
    '<=': Operator('<=', 20, operator.le),
    '<': Operator('<', 20, operator.lt),
    '&&': Operator('&&', 10, lambda a, b: a() and b(), evaluate_lazy=True),
    '||': Operator('||', 10, lambda a, b: a() or b(), evaluate_lazy=True),
    'in': Operator('in', 20, lambda a, b: a in b),
}


default_unary_operators = {
    '!': Operator('!', 1000, operator.not_),
}
