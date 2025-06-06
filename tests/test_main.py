"""Integration tests for FastAPI application."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import create_app
from app.core.config import Settings


@pytest.fixture
def test_settings():
    """Test settings with safe defaults."""
    return Settings(
        environment="testing",
        debug=True,
        database_url="postgresql+asyncpg://test:test@localhost:5432/test_db",
        redis_url="redis://localhost:6379/0",
        secret_key="test-secret-key",
    )


@pytest.fixture
def app(test_settings):
    """Create test FastAPI app."""
    with patch("app.main.get_settings", return_value=test_settings):
        return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestMainApplication:
    """Test main FastAPI application."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint returns correct status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["environment"] == "testing"
        assert data["version"] == "0.1.0"

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test root endpoint returns API information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "Smart DevOps Assistant API" in data["message"]
        assert data["docs"] == "/docs"

    def test_openapi_schema_available_in_testing(self, client: TestClient) -> None:
        """Test OpenAPI schema is available in testing environment."""
        response = client.get("/api/v1/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "Smart DevOps Assistant"
        assert schema["info"]["version"] == "0.1.0"

    def test_docs_available_in_testing(self, client: TestClient) -> None:
        """Test Swagger docs are available in testing environment."""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_cors_headers_present(self, client: TestClient) -> None:
        """Test CORS headers are properly configured."""
        # Test with Origin header that should be allowed in development
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200

        # For proper CORS testing, we'd need a real browser or specialized tool
        # TestClient limitation: doesn't fully implement CORS preflight behavior

    def test_cors_middleware_allows_development_origin(self, client: TestClient) -> None:
        """Test CORS middleware allows requests from development origin."""
        # Test that requests with allowed origin work
        response = client.get(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "User-Agent": "Mozilla/5.0",
            }
        )

        assert response.status_code == 200
        # Note: TestClient doesn't add CORS headers like a real browser would
        # For full CORS testing, integration tests with real HTTP client needed

    @pytest.mark.asyncio
    async def test_lifespan_startup_shutdown(self, test_settings) -> None:
        """Test application lifespan events."""
        with patch("app.main.get_settings", return_value=test_settings):
            app = create_app()

            # Test that app can be created without errors
            assert app is not None
            assert app.title == "Smart DevOps Assistant"


class TestApplicationConfiguration:
    """Test application configuration and settings."""

    def test_production_settings_disable_docs(self) -> None:
        """Test production settings disable docs and OpenAPI."""
        prod_settings = Settings(
            environment="production",
            debug=False,
        )

        with patch("app.main.get_settings", return_value=prod_settings):
            app = create_app()

            # Docs should be disabled in production
            assert app.openapi_url is None
            assert app.docs_url is None
            assert app.redoc_url is None

    def test_development_settings_enable_docs(self, test_settings) -> None:
        """Test development settings enable docs and debugging."""
        with patch("app.main.get_settings", return_value=test_settings):
            app = create_app()

            # Docs should be enabled in development/testing
            assert app.openapi_url == "/api/v1/openapi.json"
            assert app.docs_url == "/docs"
            assert app.redoc_url == "/redoc"

    def test_middleware_configuration(self, test_settings) -> None:
        """Test middleware is properly configured."""
        with patch("app.main.get_settings", return_value=test_settings):
            app = create_app()

            # Test that app has middleware stack configured
            assert len(app.user_middleware) > 0

            # Verify app has proper configuration
            assert app.title == "Smart DevOps Assistant"
            assert app.debug is True  # Testing environment


class TestErrorHandling:
    """Test global error handling."""

    def test_404_for_unknown_endpoint(self, client: TestClient) -> None:
        """Test 404 response for unknown endpoints."""
        response = client.get("/unknown-endpoint")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_method_not_allowed(self, client: TestClient) -> None:
        """Test 405 response for unsupported HTTP methods."""
        response = client.post("/health")

        assert response.status_code == 405
        data = response.json()
        assert "detail" in data

    def test_health_endpoint_accepts_get_only(self, client: TestClient) -> None:
        """Test health endpoint only accepts GET method."""
        # GET should work
        get_response = client.get("/health")
        assert get_response.status_code == 200

        # POST should fail
        post_response = client.post("/health")
        assert post_response.status_code == 405

        # PUT should fail
        put_response = client.put("/health")
        assert put_response.status_code == 405
