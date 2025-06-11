"""Тесты для доменных сущностей - Fixed version."""

import datetime
from uuid import UUID

import pytest

from app.domain.entities import LogEntry, LogLevel


class TestLogLevel:
    """Тесты для перечисления LogLevel."""

    def test_log_level_values(self):
        """Проверка значений перечисления LogLevel."""
        assert LogLevel.DEBUG.value == "debug"
        assert LogLevel.INFO.value == "info"
        assert LogLevel.WARNING.value == "warning"
        assert LogLevel.ERROR.value == "error"
        assert LogLevel.CRITICAL.value == "critical"

    def test_log_level_display_names(self):
        """Проверка display_name свойства."""
        assert LogLevel.DEBUG.display_name == "Debug"
        assert LogLevel.INFO.display_name == "Info"
        assert LogLevel.WARNING.display_name == "Warning"
        assert LogLevel.ERROR.display_name == "Error"
        assert LogLevel.CRITICAL.display_name == "Critical"

    def test_log_level_numeric_levels(self):
        """Проверка numeric_level свойства."""
        assert LogLevel.DEBUG.numeric_level == 10
        assert LogLevel.INFO.numeric_level == 20
        assert LogLevel.WARNING.numeric_level == 30
        assert LogLevel.ERROR.numeric_level == 40
        assert LogLevel.CRITICAL.numeric_level == 50

    def test_log_level_comparison(self):
        """Проверка сравнения уровней логирования."""
        # Используем numeric_level для сравнения
        assert LogLevel.DEBUG.numeric_level < LogLevel.INFO.numeric_level
        assert LogLevel.INFO.numeric_level < LogLevel.WARNING.numeric_level
        assert LogLevel.WARNING.numeric_level < LogLevel.ERROR.numeric_level
        assert LogLevel.ERROR.numeric_level < LogLevel.CRITICAL.numeric_level

    def test_log_level_is_error_level(self):
        """Проверка метода is_error_level."""
        assert not LogLevel.DEBUG.is_error_level()
        assert not LogLevel.INFO.is_error_level()
        assert not LogLevel.WARNING.is_error_level()
        assert LogLevel.ERROR.is_error_level()
        assert LogLevel.CRITICAL.is_error_level()


class TestLogEntry:
    """Тесты для класса LogEntry."""

    @pytest.fixture
    def log_entry(self):
        """Создание тестового объекта LogEntry."""
        return LogEntry(
            message="Test log message",
            timestamp=datetime.datetime(2024, 1, 1, 12, 0, 0),
            level=LogLevel.INFO,
            source="test_source",
            metadata={"key": "value"},
        )

    def test_log_entry_creation(self, log_entry):
        """Проверка создания объекта LogEntry."""
        assert log_entry.message == "Test log message"
        assert log_entry.timestamp == datetime.datetime(2024, 1, 1, 12, 0, 0)
        assert log_entry.level == LogLevel.INFO
        assert log_entry.source == "test_source"
        assert isinstance(log_entry.id, UUID)
        assert log_entry.metadata == {"key": "value"}

    def test_is_error_level(self):
        """Проверка метода is_error_level."""
        # Проверка неошибочных уровней
        log_debug = LogEntry(
            message="Debug", timestamp=datetime.datetime.now(), level=LogLevel.DEBUG, source="test"
        )
        log_info = LogEntry(
            message="Info", timestamp=datetime.datetime.now(), level=LogLevel.INFO, source="test"
        )
        log_warning = LogEntry(
            message="Warning",
            timestamp=datetime.datetime.now(),
            level=LogLevel.WARNING,
            source="test",
        )

        # Проверка ошибочных уровней
        log_error = LogEntry(
            message="Error", timestamp=datetime.datetime.now(), level=LogLevel.ERROR, source="test"
        )
        log_critical = LogEntry(
            message="Critical",
            timestamp=datetime.datetime.now(),
            level=LogLevel.CRITICAL,
            source="test",
        )

        assert not log_debug.is_error_level()
        assert not log_info.is_error_level()
        assert not log_warning.is_error_level()
        assert log_error.is_error_level()
        assert log_critical.is_error_level()
