from collections import namedtuple
from functools import wraps

from parsimonious.exceptions import ParseError as ParsimoniousParseError

from pyjexl.analysis import ValidatingAnalyzer
from pyjexl.evaluator import Context, Evaluator
from pyjexl.exceptions import ParseError
from pyjexl.operators import default_binary_operators, default_unary_operators, Operator
from pyjexl.parser import jexl_grammar, Parser


#: Encapsulates the variable parts of JEXL that affect parsing and
#: evaluation.
JEXLConfig = namedtuple('JEXLConfig', ['transforms', 'unary_operators', 'binary_operators'])


def invalidates_grammar(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self._grammar = None
        return func(self, *args, **kwargs)
    return wrapper


class JEXL(object):
    def __init__(self, context=None):
        self.context = Context(context or {})
        self.config = JEXLConfig(
            transforms={},
            unary_operators=default_unary_operators.copy(),
            binary_operators=default_binary_operators.copy()
        )

        self._grammar = None

    @property
    def grammar(self):
        if not self._grammar:
            self._grammar = jexl_grammar(self.config)
        return self._grammar

    @invalidates_grammar
    def add_binary_operator(self, operator, precedence, func):
        self.config.binary_operators[operator] = Operator(operator, precedence, func)

    @invalidates_grammar
    def remove_binary_operator(self, operator):
        del self.config.binary_operators[operator]

    @invalidates_grammar
    def add_unary_operator(self, operator, func):
        self.config.unary_operators[operator] = Operator(operator, 1000, func)

    @invalidates_grammar
    def remove_unary_operator(self, operator):
        del self.config.unary_operators[operator]

    def add_transform(self, name, func):
        self.config.transforms[name] = func

    def remove_transform(self, name):
        del self.config.transforms[name]

    def transform(self, name=None):
        def wrapper(func):
            self.config.transforms[name or func.__name__] = func
            return func
        return wrapper

    def parse(self, expression):
        try:
            return Parser(self.config).visit(self.grammar.parse(expression))
        except ParsimoniousParseError as err:
            raise ParseError('Could not parse expression: ' + expression) from err

    def analyze(self, expression, AnalyzerClass):
        parsed_expression = self.parse(expression)
        visitor = AnalyzerClass(self.config)
        return visitor.visit(parsed_expression)

    def validate(self, expression):
        try:
            yield from self.analyze(expression, ValidatingAnalyzer)
        except ParseError as err:
            yield str(err)

    def evaluate(self, expression, context=None):
        parsed_expression = self.parse(expression)
        context = Context(context) if context is not None else self.context
        return Evaluator(self.config).evaluate(parsed_expression, context)
