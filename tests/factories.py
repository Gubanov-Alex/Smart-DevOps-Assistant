"""Test data factories and utilities for repository testing."""

import random
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from faker import Faker

from app.domain.entities import Incident as IncidentEntity
from app.domain.entities import (
    IncidentSeverity,
    IncidentStatus,
)
from app.domain.entities import LogEntry as LogEntryEntity
from app.domain.entities import (
    LogLevel,
)
from app.domain.entities import MLModel as MLModelEntity
from app.domain.entities import (
    ModelStatus,
)

fake = Faker()


class LogEntryFactory:
    """Factory for creating LogEntry test data."""

    @staticmethod
    def create(
        message: Optional[str] = None,
        level: Optional[LogLevel] = None,
        source: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> LogEntryEntity:
        """Create a LogEntry entity with optional overrides."""
        return LogEntryEntity(
            id=uuid4(),
            message=message or fake.sentence(),
            level=level or random.choice(list(LogLevel)),
            source=source or fake.word(),
            timestamp=timestamp or fake.date_time_this_year(),
            metadata=metadata or {"test": fake.word()},
        )

    @staticmethod
    def create_batch(
        count: int = 10, level: Optional[LogLevel] = None, source: Optional[str] = None
    ) -> List[LogEntryEntity]:
        """Create a batch of LogEntry entities."""
        return [
            LogEntryFactory.create(level=level, source=source) for _ in range(count)
        ]

    @staticmethod
    def create_critical_logs(count: int = 5) -> List[LogEntryEntity]:
        """Create critical log entries for testing."""
        return [
            LogEntryFactory.create(
                level=LogLevel.CRITICAL,
                message=f"Critical error {i}: {fake.sentence()}",
                timestamp=datetime.utcnow() - timedelta(minutes=random.randint(1, 60)),
            )
            for i in range(count)
        ]


class IncidentFactory:
    """Factory for creating Incident test data."""

    @staticmethod
    def create(
        title: Optional[str] = None,
        description: Optional[str] = None,
        severity: Optional[IncidentSeverity] = None,
        status: Optional[IncidentStatus] = None,
        source: Optional[str] = None,
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
    ) -> IncidentEntity:
        """Create an Incident entity with optional overrides."""
        return IncidentEntity(
            id=uuid4(),
            title=title or fake.sentence(),
            description=description or fake.text(),
            severity=severity or random.choice(list(IncidentSeverity)),
            status=status or random.choice(list(IncidentStatus)),
            source=source or fake.word(),
            created_at=fake.date_time_this_year(),
            updated_at=fake.date_time_this_year(),
            resolved_at=None,
            assigned_to=assigned_to or fake.name(),
            tags=tags or [fake.word(), fake.word()],
            related_logs=[],
            metadata=metadata or {"test": fake.word()},
        )

    @staticmethod
    def create_open_incidents(count: int = 3) -> List[IncidentEntity]:
        """Create open incidents for testing."""
        return [
            IncidentFactory.create(
                status=random.choice([IncidentStatus.OPEN, IncidentStatus.IN_PROGRESS]),
                severity=random.choice(
                    [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]
                ),
            )
            for _ in range(count)
        ]

    @staticmethod
    def create_critical_incident() -> IncidentEntity:
        """Create a critical incident for testing."""
        return IncidentFactory.create(
            title="Critical System Failure",
            description="Multiple services are down",
            severity=IncidentSeverity.CRITICAL,
            status=IncidentStatus.OPEN,
            source="monitoring_system",
            tags=["critical", "system", "downtime"],
        )

    @staticmethod
    def create_resolved_incident() -> IncidentEntity:
        """Create a resolved incident for testing."""
        resolved_time = fake.date_time_this_month()
        return IncidentEntity(
            id=uuid4(),
            title="Resolved Database Issue",
            description="Database connection pool exhausted",
            severity=IncidentSeverity.MEDIUM,
            status=IncidentStatus.RESOLVED,
            source="database",
            created_at=resolved_time - timedelta(hours=2),
            updated_at=resolved_time,
            resolved_at=resolved_time,
            assigned_to="db_team",
            tags=["database", "resolved"],
            related_logs=[],
            metadata={"resolution_notes": "Increased connection pool size"},
        )


class MLModelFactory:
    """Factory for creating MLModel test data."""

    @staticmethod
    def create(
        name: Optional[str] = None,
        version: Optional[str] = None,
        model_type: Optional[str] = None,
        status: Optional[ModelStatus] = None,
        accuracy: Optional[float] = None,
        f1_score: Optional[float] = None,
        is_active: Optional[bool] = None,
        metadata: Optional[dict] = None,
    ) -> MLModelEntity:
        """Create an MLModel entity with optional overrides."""
        return MLModelEntity(
            id=uuid4(),
            name=name or f"model_{fake.word()}",
            version=version
            or f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            model_type=model_type
            or random.choice(["classifier", "regressor", "detector"]),
            status=status or random.choice(list(ModelStatus)),
            created_at=fake.date_time_this_year(),
            updated_at=fake.date_time_this_year(),
            trained_at=fake.date_time_this_year(),
            deployed_at=None,
            accuracy=accuracy or round(random.uniform(0.8, 0.99), 3),
            precision=round(random.uniform(0.8, 0.99), 3),
            recall=round(random.uniform(0.8, 0.99), 3),
            f1_score=f1_score or round(random.uniform(0.8, 0.99), 3),
            training_dataset_size=random.randint(1000, 100000),
            training_duration_minutes=random.randint(30, 480),
            model_path=f"/models/{fake.word()}.pkl",
            config={"param1": "value1", "param2": "value2"},
            metadata=metadata or {"test": fake.word()},
            is_active=is_active if is_active is not None else True,
            deployment_config={"env": "staging"},
        )

    @staticmethod
    def create_deployed_model() -> MLModelEntity:
        """Create a deployed model for testing."""
        deployed_time = fake.date_time_this_month()
        return MLModelEntity(
            id=uuid4(),
            name="production_classifier",
            version="2.1.0",
            model_type="classifier",
            status=ModelStatus.DEPLOYED,
            created_at=deployed_time - timedelta(days=7),
            updated_at=deployed_time,
            trained_at=deployed_time - timedelta(days=1),
            deployed_at=deployed_time,
            accuracy=0.95,
            precision=0.93,
            recall=0.92,
            f1_score=0.94,
            training_dataset_size=50000,
            training_duration_minutes=240,
            model_path="/models/production_classifier_v2.1.0.pkl",
            config={"learning_rate": 0.001, "batch_size": 32},
            metadata={"deployment_notes": "Production deployment successful"},
            is_active=True,
            deployment_config={"env": "production", "replicas": 3},
        )

    @staticmethod
    def create_model_versions(
        base_name: str = "test_model", count: int = 3
    ) -> List[MLModelEntity]:
        """Create multiple versions of the same model."""
        return [
            MLModelFactory.create(
                name=base_name,
                version=f"{i + 1}.0.0",
                accuracy=0.8 + (i * 0.05),  # Improving accuracy with versions
                status=ModelStatus.READY if i < count - 1 else ModelStatus.DEPLOYED,
            )
            for i in range(count)
        ]

    @staticmethod
    def create_training_model() -> MLModelEntity:
        """Create a model in training status."""
        return MLModelFactory.create(
            name="training_model",
            version="1.0.0",
            status=ModelStatus.TRAINING,
            accuracy=None,  # No accuracy yet
            f1_score=None,
            trained_at=None,
            deployed_at=None,
            metadata={"training_started": datetime.utcnow().isoformat()},
        )


class TestDataHelper:
    """Helper class for complex test data scenarios."""

    @staticmethod
    def create_incident_with_related_logs(
        log_count: int = 5,
    ) -> tuple[IncidentEntity, List[LogEntryEntity]]:
        """Create an incident with related log entries."""
        logs = LogEntryFactory.create_batch(
            count=log_count, level=LogLevel.ERROR, source="api_service"
        )

        incident = IncidentFactory.create(
            title="API Service Errors",
            description="Multiple API errors detected",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.OPEN,
            source="api_service",
            related_logs=[log.id for log in logs],
        )

        return incident, logs

    @staticmethod
    def create_model_lifecycle_scenario() -> List[MLModelEntity]:
        """Create models representing a complete lifecycle scenario."""
        base_time = datetime.utcnow()

        models = []

        # Old deprecated model
        old_model = MLModelFactory.create(
            name="log_classifier",
            version="1.0.0",
            status=ModelStatus.DEPRECATED,
            accuracy=0.85,
            is_active=False,
            metadata={"deprecated_reason": "Low accuracy"},
        )
        old_model.deployed_at = base_time - timedelta(days=30)
        models.append(old_model)

        # Current production model
        prod_model = MLModelFactory.create(
            name="log_classifier",
            version="2.0.0",
            status=ModelStatus.DEPLOYED,
            accuracy=0.92,
            is_active=True,
        )
        prod_model.deployed_at = base_time - timedelta(days=7)
        models.append(prod_model)

        # New model in training
        training_model = MLModelFactory.create(
            name="log_classifier",
            version="3.0.0",
            status=ModelStatus.TRAINING,
            accuracy=None,
            trained_at=None,
            deployed_at=None,
        )
        models.append(training_model)

        return models

    @staticmethod
    def create_performance_test_data(
        incident_count: int = 100, model_count: int = 50
    ) -> tuple[List[IncidentEntity], List[MLModelEntity]]:
        """Create large datasets for performance testing."""
        incidents = []
        models = []

        # Create incidents with varied characteristics
        for i in range(incident_count):
            incident = IncidentFactory.create(
                severity=random.choice(list(IncidentSeverity)),
                status=random.choice(list(IncidentStatus)),
                source=f"service_{i % 10}",  # 10 different services
                assigned_to=f"team_{i % 5}",  # 5 different teams
            )
            incidents.append(incident)

        # Create models with different types and performance metrics
        model_types = ["classifier", "regressor", "detector", "anomaly_detector"]
        for i in range(model_count):
            model = MLModelFactory.create(
                name=f"model_{i}",
                model_type=random.choice(model_types),
                status=random.choice(list(ModelStatus)),
                accuracy=round(random.uniform(0.7, 0.99), 3),
                f1_score=round(random.uniform(0.7, 0.99), 3),
                is_active=random.choice([True, False]),
            )
            models.append(model)

        return incidents, models


# Assertion helpers for testing
class AssertionHelpers:
    """Helper functions for common test assertions."""

    @staticmethod
    def assert_incident_equals(
        actual: IncidentEntity,
        expected: IncidentEntity,
        ignore_timestamps: bool = False,
    ) -> None:
        """Assert that two incidents are equal."""
        assert actual.id == expected.id
        assert actual.title == expected.title
        assert actual.description == expected.description
        assert actual.severity == expected.severity
        assert actual.status == expected.status
        assert actual.source == expected.source
        assert actual.assigned_to == expected.assigned_to
        assert actual.tags == expected.tags
        assert actual.metadata == expected.metadata

        if not ignore_timestamps:
            assert actual.created_at == expected.created_at
            assert actual.updated_at == expected.updated_at
            assert actual.resolved_at == expected.resolved_at

    @staticmethod
    def assert_model_equals(
        actual: MLModelEntity, expected: MLModelEntity, ignore_timestamps: bool = False
    ) -> None:
        """Assert that two ML models are equal."""
        assert actual.id == expected.id
        assert actual.name == expected.name
        assert actual.version == expected.version
        assert actual.model_type == expected.model_type
        assert actual.status == expected.status
        assert actual.accuracy == expected.accuracy
        assert actual.f1_score == expected.f1_score
        assert actual.is_active == expected.is_active
        assert actual.metadata == expected.metadata

        if not ignore_timestamps:
            assert actual.created_at == expected.created_at
            assert actual.updated_at == expected.updated_at
            assert actual.trained_at == expected.trained_at
            assert actual.deployed_at == expected.deployed_at

    @staticmethod
    def assert_repository_statistics(
        stats: dict, expected_keys: List[str], min_total: int = 0
    ) -> None:
        """Assert that repository statistics have expected structure."""
        for key in expected_keys:
            assert key in stats, f"Missing key: {key}"

        if "total_incidents" in stats:
            assert stats["total_incidents"] >= min_total

        if "total_active_models" in stats:
            assert stats["total_active_models"] >= min_total

        assert "timestamp" in stats
        assert isinstance(stats["timestamp"], str)


# Mock data builders for complex scenarios
class MockDataBuilder:
    """Builder pattern for creating complex mock data scenarios."""

    def __init__(self):
        self.incidents = []
        self.models = []
        self.logs = []

    def with_critical_incidents(self, count: int = 3):
        """Add critical incidents to the scenario."""
        for _ in range(count):
            self.incidents.append(IncidentFactory.create_critical_incident())
        return self

    def with_model_versions(self, base_name: str, count: int = 3):
        """Add multiple versions of a model."""
        self.models.extend(MLModelFactory.create_model_versions(base_name, count))
        return self

    def with_error_logs(self, count: int = 10):
        """Add error logs to the scenario."""
        self.logs.extend(LogEntryFactory.create_batch(count, level=LogLevel.ERROR))
        return self

    def build(self) -> dict:
        """Build the complete mock data scenario."""
        return {"incidents": self.incidents, "models": self.models, "logs": self.logs}
