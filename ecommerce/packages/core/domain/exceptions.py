class DomainError(Exception):
    """Base class for domain-level errors."""


class StockInsufficient(DomainError):
    """Raised when product stock cannot satisfy requested quantity."""


class NotFound(DomainError):
    """Raised when an entity is not found."""


class Unauthorized(DomainError):
    """Raised when an operation is not authorized."""


class ValidationError(DomainError):
    """Raised when business validation fails."""
