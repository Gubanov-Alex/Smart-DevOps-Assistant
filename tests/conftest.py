"""Pytest configuration and shared fixtures."""
import asyncio
from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db_session() -> AsyncMock:
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_redis() -> MagicMock:
    """Mock Redis client."""
    return MagicMock()


@pytest.fixture
def sample_log_data() -> dict:
    """Sample log data for testing."""
    return {
        "timestamp": "2024-01-15T10:30:00Z",
        "level": "ERROR",
        "message": "Database connection failed",
        "service": "api",
        "trace_id": "abc123",
    }
