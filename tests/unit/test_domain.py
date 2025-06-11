"""Тесты для интерфейсов репозиториев."""

from uuid import uuid4

import pytest

from app.domain.repositories import IIncidentRepository, ILogRepository, IMLModelRepository


class TestRepositoryInterfaces:
    """Тесты для интерфейсов репозиториев."""

    def test_log_repository_is_protocol(self):
        """Тест что ILogRepository является протоколом."""
        assert hasattr(ILogRepository, "__annotations__")

        # Проверяем наличие методов
        assert hasattr(ILogRepository, "save")
        assert hasattr(ILogRepository, "find_by_id")
        assert hasattr(ILogRepository, "find_by_source")
        assert hasattr(ILogRepository, "find_critical_logs")

    def test_incident_repository_is_protocol(self):
        """Тест что IIncidentRepository является протоколом."""
        assert hasattr(IIncidentRepository, "__annotations__")

        # Проверяем наличие методов
        assert hasattr(IIncidentRepository, "save")
        assert hasattr(IIncidentRepository, "find_by_id")
        assert hasattr(IIncidentRepository, "find_open_incidents")
        assert hasattr(IIncidentRepository, "find_by_severity")

    def test_ml_model_repository_is_protocol(self):
        """Тест что IMLModelRepository является протоколом."""
        assert hasattr(IMLModelRepository, "__annotations__")

        # Проверяем наличие методов
        assert hasattr(IMLModelRepository, "save")
        assert hasattr(IMLModelRepository, "find_by_name_and_version")
        assert hasattr(IMLModelRepository, "find_latest_ready")
        assert hasattr(IMLModelRepository, "find_all_versions")


class MockLogRepository:
    """Мок-реализация репозитория логов для тестирования интерфейса."""

    async def save(self, log):
        pass

    async def find_by_id(self, log_id):
        return None

    async def find_by_source(self, source, limit=100):
        return []

    async def find_critical_logs(self, since_minutes=60):
        return []


class MockIncidentRepository:
    """Мок-реализация репозитория инцидентов."""

    async def save(self, incident):
        pass

    async def find_by_id(self, incident_id):
        return None

    async def find_open_incidents(self):
        return []

    async def find_by_severity(self, severity):
        return []


class MockMLModelRepository:
    """Мок-реализация репозитория ML моделей."""

    async def save(self, model):
        pass

    async def find_by_name_and_version(self, name, version):
        return None

    async def find_latest_ready(self, model_type):
        return None

    async def find_all_versions(self, name):
        return []


class TestRepositoryImplementations:
    """Тесты для проверки соответствия интерфейсам."""

    def test_mock_log_repository_implements_interface(self):
        """Тест что мок-репозиторий логов соответствует интерфейсу."""
        repo = MockLogRepository()

        # Проверяем наличие всех методов
        assert callable(getattr(repo, "save", None))
        assert callable(getattr(repo, "find_by_id", None))
        assert callable(getattr(repo, "find_by_source", None))
        assert callable(getattr(repo, "find_critical_logs", None))

    def test_mock_incident_repository_implements_interface(self):
        """Тест что мок-репозиторий инцидентов соответствует интерфейсу."""
        repo = MockIncidentRepository()

        assert callable(getattr(repo, "save", None))
        assert callable(getattr(repo, "find_by_id", None))
        assert callable(getattr(repo, "find_open_incidents", None))
        assert callable(getattr(repo, "find_by_severity", None))

    def test_mock_ml_model_repository_implements_interface(self):
        """Тест что мок-репозиторий ML моделей соответствует интерфейсу."""
        repo = MockMLModelRepository()

        assert callable(getattr(repo, "save", None))
        assert callable(getattr(repo, "find_by_name_and_version", None))
        assert callable(getattr(repo, "find_latest_ready", None))
        assert callable(getattr(repo, "find_all_versions", None))

    @pytest.mark.asyncio
    async def test_mock_repositories_async_methods(self):
        """Тест что асинхронные методы работают корректно."""
        log_repo = MockLogRepository()
        incident_repo = MockIncidentRepository()
        ml_repo = MockMLModelRepository()

        # Тестируем асинхронные вызовы
        await log_repo.save(None)
        result = await log_repo.find_by_id(uuid4())
        assert result is None

        await incident_repo.save(None)
        incidents = await incident_repo.find_open_incidents()
        assert incidents == []

        await ml_repo.save(None)
        models = await ml_repo.find_all_versions("test")
        assert models == []
