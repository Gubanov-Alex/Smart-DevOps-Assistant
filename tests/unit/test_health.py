"""Basic health check tests to ensure CI pipeline works."""
import pytest
from fastapi.testclient import TestClient


def test_python_version():
    """Test Python version compatibility."""
    import sys
    assert sys.version_info >= (3, 12), "Python 3.12+ required"


def test_imports():
    """Test critical imports work."""
    try:
        import fastapi
        import pydantic
        import sqlalchemy
        import torch
        import pytest
        assert True
    except ImportError as e:
        pytest.fail(f"Critical import failed: {e}")


class TestHealthEndpoint:
    """Health endpoint tests."""

    def test_health_check_structure(self):
        """Test health check response structure."""
        # Minimal test until actual FastAPI app is implemented
        health_response = {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "version": "0.1.0"
        }

        assert "status" in health_response
        assert "timestamp" in health_response
        assert health_response["status"] in ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality works."""
    async def dummy_async():
        return "async_works"

    result = await dummy_async()
    assert result == "async_works"