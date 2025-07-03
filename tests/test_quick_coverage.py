"""Fixed quick coverage tests."""

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

# Заменяем несуществующий импорт на существующий
from app.events.handlers import IncidentEventHandlers, LogEventHandlers, MLEventHandlers
from app.events.middleware import AuditMiddleware, LoggingMiddleware, MetricsMiddleware
from app.infrastructure.ml.preprocessing.text_processor import LogTextProcessor


class TestEventHandlers:
    """Tests for event handlers."""

    @pytest.mark.asyncio
    async def test_log_event_handlers(self):
        """Test LogEventHandlers."""
        handlers = LogEventHandlers()

        # Mock event
        event = MagicMock()
        event.log_id = "123"
        event.level = MagicMock()
        event.level.display_name = "ERROR"
        event.source = "test"

        # Should not crash
        await handlers.handle_log_created(event)

    @pytest.mark.asyncio
    async def test_incident_event_handlers(self):
        """Test IncidentEventHandlers."""
        handlers = IncidentEventHandlers()

        event = MagicMock()
        event.incident_id = "123"
        event.title = "Test"
        event.severity = MagicMock()
        event.severity.display_name = "HIGH"
        event.auto_created = True

        await handlers.handle_incident_created(event)

    @pytest.mark.asyncio
    async def test_ml_event_handlers(self):
        """Test MLEventHandlers."""
        handlers = MLEventHandlers()

        event = MagicMock()
        event.model_id = "123"
        event.model_name = "test-model"
        event.accuracy = 0.95
        event.training_duration_minutes = 60

        await handlers.handle_training_completed(event)


# Остальные тесты остаются без изменений...
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
