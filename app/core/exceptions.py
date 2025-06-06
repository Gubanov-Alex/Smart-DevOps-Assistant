"""Custom application exceptions with proper HTTP status codes."""
from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """Base application exception with structured error handling."""

    def __init__(
            self,
            message: str,
            status_code: int = 500,
            error_code: str = "INTERNAL_ERROR",
            details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BaseAppException):
    """Validation error exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(BaseAppException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(
            message=f"{resource} with identifier '{identifier}' not found",
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
        )


class ConflictError(BaseAppException):
    """Resource conflict exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class UnauthorizedError(BaseAppException):
    """Unauthorized access exception."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class ForbiddenError(BaseAppException):
    """Forbidden access exception."""

    def __init__(self, message: str = "Access forbidden") -> None:
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
        )


class MLModelError(BaseAppException):
    """ML model related exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="ML_MODEL_ERROR",
            details=details,
        )


class ExternalServiceError(BaseAppException):
    """External service error exception."""

    def __init__(self, service: str, message: str) -> None:
        super().__init__(
            message=f"External service '{service}' error: {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )
