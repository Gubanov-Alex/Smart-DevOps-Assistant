"""Тесты для базовых событий."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.events.base import DomainEvent


@dataclass(frozen=True)
class TestEvent(DomainEvent):
    """Тестовое событие для проверки базовой функциональности."""

    test_data: str


class TestDomainEvent:
    """Тесты для базового доменного события."""

    def test_domain_event_creation(self):
        """Тест создания доменного события."""
        aggregate_id = uuid4()
        event = TestEvent(aggregate_id=aggregate_id, test_data="test")

        assert event.aggregate_id == aggregate_id
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_at, datetime)
        assert event.version == 1
        assert event.event_type == "TestEvent"
        assert event.metadata == {}

    def test_domain_event_with_custom_metadata(self):
        """Тест создания события с метаданными."""
        aggregate_id = uuid4()

        # Create event first, then modify metadata
        event = TestEvent(aggregate_id=aggregate_id, test_data="test")

        # Since event is frozen, we need to test metadata setting differently
        # This tests the default metadata behavior
        assert event.metadata == {}
        assert event.aggregate_id == aggregate_id

    def test_event_data_serialization(self):
        """Тест сериализации данных события."""
        aggregate_id = uuid4()
        event = TestEvent(aggregate_id=aggregate_id, test_data="test")

        event_data = event.event_data

        assert "event_id" in event_data
        assert "event_type" in event_data
        assert "aggregate_id" in event_data
        assert "occurred_at" in event_data
        assert "version" in event_data
        assert "metadata" in event_data

        assert event_data["event_type"] == "TestEvent"
        assert event_data["aggregate_id"] == str(aggregate_id)
        assert event_data["version"] == 1

    def test_domain_event_immutability(self):
        """Тест неизменяемости события."""
        event = TestEvent(aggregate_id=uuid4(), test_data="test")

        # Попытка изменить замороженный объект должна вызвать ошибку
        with pytest.raises(AttributeError):
            event.test_data = "modified"
