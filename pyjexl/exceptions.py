class JexlException(Exception):
    """Base class for all pyjexl exceptions."""


class EvaluationError(JexlException):
    """An error during evaluation of a parsed expression."""


class MissingTransformError(EvaluationError):
    """An unregistered transform was used."""
