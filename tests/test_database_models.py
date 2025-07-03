"""Simple database test that should work."""

import pytest
from datetime import datetime
from app.models import LogEntry, LogLevel


class TestDatabaseSimple:
    """Simple database tests without async fixtures."""

    def test_log_entry_creation(self):
        """Test LogEntry can be created."""
        entry = LogEntry(
            message="Test message",
            level=LogLevel.INFO,
            source="test-source",
            timestamp=datetime.now()
        )
        
        assert entry.message == "Test message"
        assert entry.level == LogLevel.INFO
        assert entry.source == "test-source"
        assert entry.timestamp is not None

    def test_log_level_enum(self):
        """Test LogLevel enum values."""
        assert LogLevel.INFO is not None
        assert LogLevel.ERROR is not None
        assert LogLevel.WARNING is not None
        
        # Test enum has value attribute
        assert hasattr(LogLevel.INFO, 'value')
        assert LogLevel.INFO.value == 'INFO'
