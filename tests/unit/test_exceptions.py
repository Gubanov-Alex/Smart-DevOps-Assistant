"""Тесты для пользовательских исключений."""

from app.core.exceptions import (
    BaseAppException,
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    MLModelError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


class TestExceptions:
    """Тесты для проверки пользовательских исключений."""

    def test_base_app_exception(self):
        """Проверка базового исключения."""
        exception = BaseAppException(
            message="Test error",
            status_code=500,
            error_code="TEST_ERROR",
            details={"test": "value"},
        )
        assert exception.message == "Test error"
        assert exception.status_code == 500
        assert exception.error_code == "TEST_ERROR"
        assert exception.details == {"test": "value"}

    def test_validation_error(self):
        """Проверка исключения ValidationError."""
        exception = ValidationError("Invalid data", {"field": "reason"})
        assert exception.message == "Invalid data"
        assert exception.status_code == 422
        assert exception.error_code == "VALIDATION_ERROR"
        assert exception.details == {"field": "reason"}

    def test_not_found_error(self):
        """Проверка исключения NotFoundError."""
        exception = NotFoundError("User", "123")
        assert "User with identifier '123' not found" in str(exception)
        assert exception.status_code == 404
        assert exception.error_code == "NOT_FOUND"
        assert exception.details == {"resource": "User", "identifier": "123"}

    def test_conflict_error(self):
        """Проверка исключения ConflictError."""
        exception = ConflictError("Resource already exists")
        assert exception.message == "Resource already exists"
        assert exception.status_code == 409
        assert exception.error_code == "CONFLICT"

    def test_unauthorized_error(self):
        """Проверка исключения UnauthorizedError."""
        exception = UnauthorizedError()
        assert exception.message == "Authentication required"
        assert exception.status_code == 401
        assert exception.error_code == "UNAUTHORIZED"

    def test_forbidden_error(self):
        """Проверка исключения ForbiddenError."""
        exception = ForbiddenError()
        assert exception.message == "Access forbidden"
        assert exception.status_code == 403
        assert exception.error_code == "FORBIDDEN"

    def test_ml_model_error(self):
        """Проверка исключения MLModelError."""
        exception = MLModelError("Model prediction failed")
        assert exception.message == "Model prediction failed"
        assert exception.status_code == 500
        assert exception.error_code == "ML_MODEL_ERROR"

    def test_external_service_error(self):
        """Проверка исключения ExternalServiceError."""
        exception = ExternalServiceError("API Service", "Connection timeout")
        assert "External service 'API Service' error: Connection timeout" in str(exception)
        assert exception.status_code == 502
        assert exception.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exception.details == {"service": "API Service"}
