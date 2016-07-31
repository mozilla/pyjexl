class JEXLException(Exception):
    """Base class for all pyjexl exceptions."""


class EvaluationError(JEXLException):
    """An error during evaluation of a parsed expression."""


class MissingTransformError(EvaluationError):
    """An unregistered transform was used."""
