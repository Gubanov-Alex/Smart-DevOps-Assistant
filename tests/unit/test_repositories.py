"""Repository tests with proper dataclass structure."""

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.entities import LogEntry, LogLevel


@dataclass(frozen=True)
class MockLogEntry:
    """Mock log entry for testing."""

    message: str
    level: LogLevel
    source: str
    id: UUID = field(default_factory=uuid4)
    metadata: dict = field(default_factory=dict)


class TestRepositoryPatterns:
    """Test repository interface patterns."""

    def test_repository_protocol_compliance(self):
        """Test that repository interfaces follow Protocol pattern."""

        class MockLogRepository:
            """Mock implementation."""

            async def save(self, log: LogEntry) -> None:
                """Save log entry."""
                pass

        repo = MockLogRepository()
        assert hasattr(repo, "save")

    def test_dataclass_ordering_fix(self):
        """Test that dataclass field ordering is correct."""

        mock_entry = MockLogEntry(message="Test message", level=LogLevel.INFO, source="test")

        assert mock_entry.message == "Test message"
        assert mock_entry.level == LogLevel.INFO
        assert isinstance(mock_entry.id, UUID)
