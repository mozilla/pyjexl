import operator


class Evaluator(object):
    operations = {
        '+': operator.add
    }

    def evaluate(self, expression):
        method = getattr(self, 'visit_' + type(expression).__name__, self.generic_visit)
        return method(expression)

    def visit_BinaryOperator(self, exp):
        left = self.evaluate(exp.left)
        right = self.evaluate(exp.right)
        return self.operations[exp.operator](left, right)

    def visit_Literal(self, literal):
        return literal.value

    def generic_visit(self, expression):
        raise ValueError('Could not evaluate expression: ' + repr(expression))
