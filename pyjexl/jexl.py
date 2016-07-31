from pyjexl.evaluator import Context, Evaluator
from pyjexl.parser import Parser


class JEXL(object):
    def __init__(self, context=None):
        self.context = Context(context or {})
        self.transforms = {}

    def transform(self, name=None, func=None):
        if func:
            self.transforms[name or func.__name__] = func
        else:
            def wrapper(func):
                self.transforms[name or func.__name__] = func
            return wrapper

    def evaluate(self, expression, context=None):
        context = Context(context) if context is not None else self.context
        parsed_expression = Parser().parse(expression)
        evaluator = Evaluator(self.transforms)
        return evaluator.evaluate(parsed_expression, context)
