"""Shared test fixtures and configuration."""

from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def sample_log_data() -> Dict[str, Any]:
    """Sample log data for testing."""
    return {
        "timestamp": "2024-01-01T00:00:00Z",
        "level": "INFO",
        "message": "Test log message",
        "service": "test-service",
        "trace_id": "trace-123",
        "user_id": "user-456",
        "request_id": "req-789",
        "duration": 0.123,
        "status_code": 200,
        "method": "GET",
        "path": "/api/test",
        "ip": "127.0.0.1",
        "user_agent": "test-agent/1.0",
    }


@pytest.fixture
async def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    from unittest.mock import MagicMock

    redis_mock = MagicMock()
    redis_mock.ping.return_value = True
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    return redis_mock


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure anyio backend for async tests."""
    return "asyncio"


# Test configuration
pytest_plugins = [
    "pytest_asyncio",
    "pytest_benchmark",
]
