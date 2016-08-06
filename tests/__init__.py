from pyjexl.evaluator import Evaluator
from pyjexl.jexl import JEXLConfig
from pyjexl.operators import default_binary_operators, default_unary_operators
from pyjexl.parser import jexl_grammar, Parser


default_config = JEXLConfig({}, default_unary_operators, default_binary_operators)


class DefaultParser(Parser):
    grammar = jexl_grammar(default_config)

    def __init__(self, config=None):
        super().__init__(config or default_config)


class DefaultEvaluator(Evaluator):
    def __init__(self, config=None):
        super().__init__(config or default_config)
