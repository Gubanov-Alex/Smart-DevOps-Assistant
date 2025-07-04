"""Fixed ML Service tests with proper mocks."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ml_service import MLService


@pytest.fixture
def mock_dependencies():
    """Create mocked dependencies for MLService."""
    return {
        "classifier": MagicMock(),
        "detector": MagicMock(),
        "registry": MagicMock(),
        "incident_analyzer": MagicMock(),
        "event_bus": AsyncMock(),
    }


@pytest.fixture
def ml_service(mock_dependencies):
    """Create MLService with mocked dependencies."""
    return MLService(**mock_dependencies)


class TestMLServiceFixed:
    """Fixed tests for MLService."""

    def test_service_initialization(self, mock_dependencies):
        """Test MLService can be initialized with dependencies."""
        service = MLService(**mock_dependencies)
        assert service is not None
        assert service._classifier is not None
        assert service._detector is not None

    def test_service_attributes(self, ml_service):
        """Test MLService has expected attributes."""
        assert hasattr(ml_service, "_classifier")
        assert hasattr(ml_service, "_detector")
        assert hasattr(ml_service, "_registry")
        assert hasattr(ml_service, "_incident_analyzer")
        assert hasattr(ml_service, "_event_bus")
        assert hasattr(ml_service, "_stats")

    def test_service_stats_initialization(self, ml_service):
        """Test MLService stats are properly initialized."""
        stats = ml_service._stats
        assert "total_classifications" in stats
        assert "total_anomalies_detected" in stats
        assert "average_processing_time" in stats

        # Test initial values
        assert stats["total_classifications"] == 0
        assert stats["total_anomalies_detected"] == 0
        assert stats["average_processing_time"] == 0.0

    def test_service_properties(self, ml_service):
        """Test MLService properties exist."""
        # Test that service has basic attributes (without batch_size/max_sequence_length)
        assert hasattr(ml_service, "_classifier")
        assert hasattr(ml_service, "_detector")
        assert hasattr(ml_service, "_stats")
