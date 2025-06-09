"""Тесты для событий логов."""

from uuid import uuid4

import pytest

from app.domain.entities import LogLevel
from app.domain.value_objects import AnomalyScore
from app.events.log_events import (
    AnomalyDetected,
    LogClassificationCompleted,
    LogEntryCreated,
    LogPatternIdentified,
)


class TestLogEvents:
    """Тесты для событий связанных с логами."""

    def test_log_entry_created_event(self):
        """Тест события создания лог-записи."""
        log_id = uuid4()

        event = LogEntryCreated(
            aggregate_id=log_id,  # Use log_id as aggregate_id
            log_id=log_id,
            message="Test log message",
            level=LogLevel.ERROR,
            source="test-service",
            tags=["test", "error"],
        )

        assert event.aggregate_id == log_id  # Should match since __post_init__ sets it to log_id
        assert event.log_id == log_id
        assert event.message == "Test log message"
        assert event.level == LogLevel.ERROR
        assert event.source == "test-service"
        assert event.tags == ["test", "error"]
        assert event.event_type == "LogEntryCreated"

    def test_log_classification_completed_event(self):
        """Тест события завершения классификации лога."""
        log_id = uuid4()

        event = LogClassificationCompleted(
            aggregate_id=log_id,  # Use log_id as aggregate_id
            log_id=log_id,
            predicted_level=LogLevel.WARNING,
            confidence=0.95,
            model_version="v1.2.3",
            processing_time_ms=150,
        )

        assert event.aggregate_id == log_id  # Should match since __post_init__ sets it to log_id
        assert event.log_id == log_id
        assert event.predicted_level == LogLevel.WARNING
        assert event.confidence == 0.95
        assert event.model_version == "v1.2.3"
        assert event.processing_time_ms == 150
        assert event.event_type == "LogClassificationCompleted"

    def test_anomaly_detected_event(self):
        """Тест события обнаружения аномалии."""
        log_ids = [uuid4(), uuid4()]
        first_log_id = log_ids[0]
        anomaly_score = AnomalyScore(value=0.9, confidence=0.85)

        event = AnomalyDetected(
            aggregate_id=first_log_id,  # Use first log as aggregate_id
            source="api-service",
            anomaly_score=anomaly_score,
            affected_logs=log_ids,
            detection_method="ml_model",
            severity="high",
        )

        assert (
            event.aggregate_id == first_log_id
        )  # Should match since __post_init__ uses first affected log
        assert event.source == "api-service"
        assert event.anomaly_score == anomaly_score
        assert event.affected_logs == log_ids
        assert event.detection_method == "ml_model"
        assert event.severity == "high"
        assert event.event_type == "AnomalyDetected"

    def test_log_pattern_identified_event(self):
        """Тест события идентификации паттерна в логах."""
        sample_logs = [uuid4(), uuid4(), uuid4()]
        first_log_id = sample_logs[0]

        event = LogPatternIdentified(
            aggregate_id=first_log_id,  # Use first sample log as aggregate_id
            pattern_id="conn_timeout_pattern",
            pattern_description="Connection timeout errors",
            frequency_per_hour=25,
            detection_method="pattern_matching",  # Add required field
            affected_sources=["api-gateway", "auth-service"],
            sample_log_ids=sample_logs,
        )

        assert (
            event.aggregate_id == first_log_id
        )  # Should match since __post_init__ uses first sample log
        assert event.pattern_id == "conn_timeout_pattern"
        assert event.pattern_description == "Connection timeout errors"
        assert event.frequency_per_hour == 25
        assert event.detection_method == "pattern_matching"
        assert event.affected_sources == ["api-gateway", "auth-service"]
        assert event.sample_log_ids == sample_logs
        assert event.event_type == "LogPatternIdentified"

    def test_events_are_immutable(self):
        """Тест неизменяемости событий."""
        log_id = uuid4()
        event = LogEntryCreated(
            aggregate_id=log_id,
            log_id=log_id,
            message="Test",
            level=LogLevel.INFO,
            source="test",
            tags=[],
        )

        with pytest.raises(AttributeError):
            event.message = "Modified"

    def test_events_inherit_from_domain_event(self):
        """Тест что события наследуются от DomainEvent."""
        log_id1 = uuid4()
        log_id2 = uuid4()
        log_id3 = uuid4()
        log_id4 = uuid4()

        events = [
            LogEntryCreated(
                aggregate_id=log_id1,
                log_id=log_id1,
                message="Test",
                level=LogLevel.INFO,
                source="test",
                tags=[],
            ),
            LogClassificationCompleted(
                aggregate_id=log_id2,
                log_id=log_id2,
                predicted_level=LogLevel.ERROR,
                confidence=0.8,
                model_version="v1.0",
                processing_time_ms=100,
            ),
            AnomalyDetected(
                aggregate_id=log_id3,
                source="test",
                anomaly_score=AnomalyScore(value=0.8, confidence=0.9),
                affected_logs=[log_id3],
                detection_method="rule_based",
                severity="medium",
            ),
            LogPatternIdentified(
                aggregate_id=log_id4,
                pattern_id="test_pattern",
                pattern_description="Test pattern",
                frequency_per_hour=10,
                detection_method="statistical",  # Add required field
                affected_sources=["test"],
                sample_log_ids=[log_id4],
            ),
        ]

        for event in events:
            # Проверяем наличие свойств базового события
            assert hasattr(event, "event_id")
            assert hasattr(event, "occurred_at")
            assert hasattr(event, "version")
            assert hasattr(event, "event_type")
            assert hasattr(event, "metadata")
            assert hasattr(event, "event_data")
