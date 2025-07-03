"""Smoke test to ensure basic imports work."""


def test_basic_imports():
    """Test that basic imports work."""
    # Test config
    from app.core.config import get_settings

    settings = get_settings()
    assert settings is not None

    # Test events
    from app.events.event_bus import EventBus

    bus = EventBus()
    assert bus is not None

    # Test models
    from app.models import LogEntry, LogLevel

    assert LogEntry is not None
    assert LogLevel is not None

    print("✅ Все базовые импорты работают")


def test_settings_fields():
    """Test Settings has required fields."""
    from app.core.config import get_settings

    settings = get_settings()

    required_fields = ["log_format", "database_url", "redis_url"]
    for field in required_fields:
        assert hasattr(settings, field), f"Поле {field} отсутствует в Settings"

    print("✅ Все обязательные поля присутствуют в Settings")
