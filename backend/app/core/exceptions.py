class OperationalDataUnavailableError(RuntimeError):
    """Raised when real operational data required for a response is unavailable."""


class ModelUnavailableError(RuntimeError):
    """Raised when a trained model is required but not loaded/configured."""


class IncompleteOperationalDataError(RuntimeError):
    """Raised when an operational record is missing required source fields."""
