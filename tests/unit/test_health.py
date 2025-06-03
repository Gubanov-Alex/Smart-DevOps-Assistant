"""Basic health check tests to ensure CI pipeline works."""
import sys
from typing import Any, Dict

import pytest


def test_python_version() -> None:
    """Test Python version compatibility."""
    assert sys.version_info >= (3, 12), "Python 3.12+ required"


def test_imports() -> None:
    """Test critical imports work."""
    try:
        import fastapi  # noqa: F401
        import pydantic  # noqa: F401
        import sqlalchemy  # noqa: F401
        import torch  # noqa: F401

        assert True
    except ImportError as e:
        pytest.fail(f"Critical import failed: {e}")


class TestHealthEndpoint:
    """Health endpoint tests."""

    def test_health_check_structure(self) -> None:
        """Test health check response structure."""
        # Minimal test until actual FastAPI app is implemented
        health_response: Dict[str, Any] = {
            "status": "healthy",
            "timestamp": "2024-01-15T10:30:00Z",
            "version": "0.1.0",
        }

        assert "status" in health_response
        assert "timestamp" in health_response
        assert health_response["status"] in ["healthy", "unhealthy"]


@pytest.mark.asyncio
async def test_async_functionality() -> None:
    """Test async functionality works."""

    async def dummy_async() -> str:
        return "async_works"

    result = await dummy_async()
    assert result == "async_works"
