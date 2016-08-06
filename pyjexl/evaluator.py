from collections.abc import MutableMapping

from pyjexl.exceptions import MissingTransformError


class Context(MutableMapping):
    def __init__(self, context_data=None):
        self.data = context_data or {}
        self.relative_value = {}

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def with_relative(self, relative_value):
        new_context = Context(self.data)
        new_context.relative_value = relative_value
        return new_context


class Evaluator(object):
    def __init__(self, jexl_config):
        self.config = jexl_config

    def evaluate(self, expression, context=None):
        method = getattr(self, 'visit_' + type(expression).__name__, self.generic_visit)
        context = context or Context()
        return method(expression, context)

    def visit_BinaryExpression(self, exp, context):
        left = self.evaluate(exp.left, context)
        right = self.evaluate(exp.right, context)
        return exp.operator.evaluate(left, right)

    def visit_UnaryExpression(self, exp, context):
        right = self.evaluate(exp.right, context)
        return exp.operator.evaluate(right)

    def visit_Literal(self, literal, context):
        return literal.value

    def visit_Identifier(self, identifier, context):
        if identifier.relative:
            subject = context.relative_value
        elif identifier.subject:
            subject = self.evaluate(identifier.subject, context)
        else:
            subject = context

        return subject.get(identifier.value, None)

    def visit_ObjectLiteral(self, object_literal, context):
        return {
            key: self.evaluate(value, context)
            for key, value in object_literal.value.items()
        }

    def visit_ArrayLiteral(self, array_literal, context):
        return [self.evaluate(value, context) for value in array_literal.value]

    def visit_Transform(self, transform, context):
        try:
            transform_func = self.config.transforms[transform.name]
        except KeyError:
            raise MissingTransformError(
                'No transform found with the name "{name}"'.format(name=transform.name)
            )

        args = [self.evaluate(arg) for arg in transform.args]
        return transform_func(self.evaluate(transform.subject, context), *args)

    def visit_FilterExpression(self, filter_expression, context):
        values = self.evaluate(filter_expression.subject, context)
        if filter_expression.relative:
            return [
                value for value in values
                if self.evaluate(filter_expression.expression, context.with_relative(value))
            ]
        else:
            filter_value = self.evaluate(filter_expression.expression, context)
            if filter_value is True:
                return values
            elif filter_value is False:
                return None
            else:
                try:
                    return values[filter_value]
                except (IndexError, KeyError):
                    return None

    def visit_ConditionalExpression(self, conditional, context):
        if self.evaluate(conditional.test, context):
            return self.evaluate(conditional.consequent, context)
        else:
            return self.evaluate(conditional.alternate, context)

    def generic_visit(self, expression, context):
        raise ValueError('Could not evaluate expression: ' + repr(expression))
