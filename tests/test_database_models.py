"""Comprehensive tests for SQLAlchemy database models.

Tests cover model creation, relationships, constraints, and database operations
with both unit and integration testing approaches.
"""

from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import db_manager
from app.models import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    LogEntry,
    LogLevel,
    MLModel,
    ModelStatus,
)


class TestLogEntryModel:
    """Test cases for LogEntry model."""

    @pytest.mark.asyncio
    async def test_create_log_entry(self, db_session: AsyncSession):
        """Test creating a basic log entry."""
        log_entry = LogEntry(
            message="Test error message",
            level=LogLevel.ERROR,
            source="test-service",
            timestamp=datetime.utcnow(),
            extra_data={"user_id": "123", "request_id": "abc-def"},
        )

        db_session.add(log_entry)
        await db_session.commit()
        await db_session.refresh(log_entry)

        assert log_entry.id is not None
        assert log_entry.message == "Test error message"
        assert log_entry.level == LogLevel.ERROR
        assert log_entry.source == "test-service"
        assert log_entry.extra_data["user_id"] == "123"
        assert log_entry.created_at is not None

    @pytest.mark.asyncio
    async def test_log_entry_with_ml_scores(self, db_session: AsyncSession):
        """Test log entry with ML analysis scores."""
        log_entry = LogEntry(
            message="Critical system failure",
            level=LogLevel.CRITICAL,
            source="database-service",
            timestamp=datetime.utcnow(),
            classification_confidence=0.95,
            anomaly_score=0.87,
            processing_time_ms=12.5,
        )

        db_session.add(log_entry)
        await db_session.commit()

        assert log_entry.classification_confidence == 0.95
        assert log_entry.anomaly_score == 0.87
        assert log_entry.processing_time_ms == 12.5

    @pytest.mark.asyncio
    async def test_log_entry_constraints(self, db_session: AsyncSession):
        """Test model constraints validation."""
        # Test invalid confidence score
        log_entry = LogEntry(
            message="Test message",
            level=LogLevel.INFO,
            source="test",
            timestamp=datetime.utcnow(),
            classification_confidence=1.5,  # Invalid: > 1.0
        )

        db_session.add(log_entry)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_log_entry_indexing(self, db_session: AsyncSession):
        """Test that indexes work properly for queries."""
        # Create multiple log entries
        entries = []
        for i in range(10):
            entry = LogEntry(
                message=f"Log message {i}",
                level=LogLevel.INFO if i % 2 == 0 else LogLevel.ERROR,
                source=f"service-{i % 3}",
                timestamp=datetime.utcnow() - timedelta(hours=i),
            )
            entries.append(entry)

        db_session.add_all(entries)
        await db_session.commit()

        # Test timestamp + level index
        result = await db_session.execute(
            select(LogEntry).where(LogEntry.level == LogLevel.ERROR).order_by(LogEntry.timestamp.desc())
        )
        error_logs = result.scalars().all()

        assert len(error_logs) == 5  # Half of the entries are ERROR level

        # Test source + timestamp index
        result = await db_session.execute(
            select(LogEntry).where(LogEntry.source == "service-1").order_by(LogEntry.timestamp.desc())
        )
        service_logs = result.scalars().all()

        assert len(service_logs) > 0


class TestIncidentModel:
    """Test cases for Incident model."""

    @pytest.mark.asyncio
    async def test_create_incident(self, db_session: AsyncSession):
        """Test creating a basic incident."""
        incident = Incident(
            title="Database Connection Failure",
            description="Unable to connect to primary database",
            severity=IncidentSeverity.HIGH,
            source="database-service",
            assigned_to="admin@example.com",
            tags=["database", "connectivity", "high-priority"],
            extra_data={"affected_users": 1500, "region": "us-east-1"},
        )

        db_session.add(incident)
        await db_session.commit()
        await db_session.refresh(incident)

        assert incident.id is not None
        assert incident.title == "Database Connection Failure"
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.status == IncidentStatus.OPEN  # Default status
        assert "database" in incident.tags
        assert incident.extra_data["affected_users"] == 1500
        assert incident.created_at is not None
        assert incident.updated_at is not None

    @pytest.mark.asyncio
    async def test_incident_status_management(self, db_session: AsyncSession):
        """Test incident lifecycle status changes."""
        incident = Incident(
            title="Test Incident",
            description="Test incident for status changes",
            severity=IncidentSeverity.MEDIUM,
            source="test-service",
        )

        db_session.add(incident)
        await db_session.commit()

        original_updated_at = incident.updated_at

        # Update status
        incident.status = IncidentStatus.IN_PROGRESS
        await db_session.commit()
        await db_session.refresh(incident)

        assert incident.status == IncidentStatus.IN_PROGRESS
        assert incident.updated_at > original_updated_at

        # Resolve incident
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(incident)

        assert incident.status == IncidentStatus.RESOLVED
        assert incident.resolved_at is not None

    @pytest.mark.asyncio
    async def test_incident_priority_calculation(self, db_session: AsyncSession):
        """Test AI priority score functionality."""
        incident = Incident(
            title="Critical Payment Failure",
            description="Payment processing system is down",
            severity=IncidentSeverity.CRITICAL,
            source="payment-service",
            priority_score=0.95,
        )

        db_session.add(incident)
        await db_session.commit()

        assert incident.priority_score == 0.95

    @pytest.mark.asyncio
    async def test_incident_log_relationship(self, db_session: AsyncSession):
        """Test many-to-many relationship between incidents and logs."""
        # Create log entries
        log1 = LogEntry(
            message="Payment API error",
            level=LogLevel.ERROR,
            source="payment-service",
            timestamp=datetime.utcnow(),
        )
        log2 = LogEntry(
            message="Database timeout in payment processing",
            level=LogLevel.ERROR,
            source="payment-service",
            timestamp=datetime.utcnow(),
        )

        # Create incident
        incident = Incident(
            title="Payment System Issues",
            description="Multiple payment failures detected",
            severity=IncidentSeverity.HIGH,
            source="payment-service",
        )

        db_session.add_all([log1, log2, incident])
        await db_session.commit()

        # Associate logs with incident
        incident.related_logs.extend([log1, log2])
        await db_session.commit()

        # Test relationship from incident side
        await db_session.refresh(incident)
        assert len(incident.related_logs) == 2
        assert log1 in incident.related_logs
        assert log2 in incident.related_logs

        # Test relationship from log side
        await db_session.refresh(log1)
        assert len(log1.incidents) == 1
        assert incident in log1.incidents


class TestMLModelModel:
    """Test cases for MLModel model."""

    @pytest.mark.asyncio
    async def test_create_ml_model(self, db_session: AsyncSession):
        """Test creating a basic ML model entry."""
        model = MLModel(
            name="log-classifier",
            version="1.0.0",
            model_type="classification",
            status=ModelStatus.TRAINING,
            config={"algorithm": "random_forest", "n_estimators": 100, "max_depth": 10},
            metadata={
                "training_framework": "scikit-learn",
                "python_version": "3.12",
                "feature_count": 25,
            },
        )

        db_session.add(model)
        await db_session.commit()
        await db_session.refresh(model)

        assert model.id is not None
        assert model.name == "log-classifier"
        assert model.version == "1.0.0"
        assert model.model_type == "classification"
        assert model.status == ModelStatus.TRAINING
        assert model.config["algorithm"] == "random_forest"
        assert model.is_active is False  # Default value
        assert model.created_at is not None

    @pytest.mark.asyncio
    async def test_model_versioning_constraint(self, db_session: AsyncSession):
        """Test unique constraint on model name + version."""
        model1 = MLModel(
            name="anomaly-detector",
            version="1.0.0",
            model_type="anomaly_detection",
            status=ModelStatus.TRAINED,
        )

        model2 = MLModel(
            name="anomaly-detector",
            version="1.0.0",  # Same name and version
            model_type="anomaly_detection",
            status=ModelStatus.TRAINING,
        )

        db_session.add(model1)
        await db_session.commit()

        db_session.add(model2)

        with pytest.raises(IntegrityError):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_model_performance_metrics(self, db_session: AsyncSession):
        """Test model performance tracking."""
        model = MLModel(
            name="incident-classifier",
            version="2.1.0",
            model_type="classification",
            status=ModelStatus.READY,
            accuracy=0.94,
            precision=0.92,
            recall=0.89,
            f1_score=0.905,
            training_dataset_size=50000,
            training_duration_minutes=45,
            is_active=True,
        )

        db_session.add(model)
        await db_session.commit()

        assert model.accuracy == 0.94
        assert model.precision == 0.92
        assert model.recall == 0.89
        assert model.f1_score == 0.905
        assert model.training_dataset_size == 50000
        assert model.training_duration_minutes == 45
        assert model.is_active is True

    @pytest.mark.asyncio
    async def test_model_deployment_tracking(self, db_session: AsyncSession):
        """Test model deployment status and timestamps."""
        model = MLModel(
            name="real-time-analyzer",
            version="3.0.0",
            model_type="real_time_analysis",
            status=ModelStatus.DEPLOYED,
            trained_at=datetime.utcnow() - timedelta(hours=2),
            deployed_at=datetime.utcnow() - timedelta(minutes=30),
            is_active=True,
            deployment_config={
                "endpoint": "http://ml-service:8080/predict",
                "timeout_seconds": 30,
                "batch_size": 100,
            },
        )

        db_session.add(model)
        await db_session.commit()

        assert model.status == ModelStatus.DEPLOYED
        assert model.trained_at is not None
        assert model.deployed_at is not None
        assert model.deployment_config["endpoint"] is not None
        assert model.is_active is True


class TestDatabaseQueries:
    """Test complex database queries and performance."""

    @pytest.mark.asyncio
    async def test_log_aggregation_queries(self, db_session: AsyncSession):
        """Test aggregation queries for log analytics."""
        # Create sample data
        base_time = datetime.utcnow()
        logs_data = [
            (LogLevel.INFO, "service-a", base_time),
            (LogLevel.INFO, "service-a", base_time),
            (LogLevel.ERROR, "service-a", base_time),
            (LogLevel.ERROR, "service-b", base_time),
            (LogLevel.CRITICAL, "service-b", base_time),
        ]

        for level, source, timestamp in logs_data:
            log = LogEntry(
                message=f"Log from {source}",
                level=level,
                source=source,
                timestamp=timestamp,
            )
            db_session.add(log)

        await db_session.commit()

        # Test aggregation by source and level
        result = await db_session.execute(
            select(LogEntry.source, LogEntry.level, func.count(LogEntry.id).label("count"))
            .group_by(LogEntry.source, LogEntry.level)
            .order_by(LogEntry.source, LogEntry.level)
        )

        aggregation = result.all()

        # Verify aggregation results
        assert len(aggregation) == 4  # 4 unique source+level combinations

        # Check specific counts
        service_a_info = next(
            (row for row in aggregation if row.source == "service-a" and row.level == LogLevel.INFO),
            None,
        )
        assert service_a_info is not None
        assert service_a_info.count == 2

    @pytest.mark.asyncio
    async def test_incident_analytics_queries(self, db_session: AsyncSession):
        """Test incident analytics and reporting queries."""
        # Create incidents with different severities and statuses
        incidents_data = [
            (IncidentSeverity.HIGH, IncidentStatus.OPEN),
            (IncidentSeverity.HIGH, IncidentStatus.RESOLVED),
            (IncidentSeverity.MEDIUM, IncidentStatus.OPEN),
            (IncidentSeverity.LOW, IncidentStatus.RESOLVED),
        ]

        for severity, status in incidents_data:
            incident = Incident(
                title=f"Test incident {severity.value}",
                description="Test incident description",
                severity=severity,
                status=status,
                source="test-service",
            )
            db_session.add(incident)

        await db_session.commit()

        # Query open incidents by severity
        result = await db_session.execute(
            select(Incident.severity, func.count(Incident.id).label("count"))
            .where(Incident.status == IncidentStatus.OPEN)
            .group_by(Incident.severity)
        )

        open_by_severity = result.all()

        # Should have 2 open incidents (HIGH and MEDIUM)
        assert len(open_by_severity) == 2

        high_count = next(
            (row.count for row in open_by_severity if row.severity == IncidentSeverity.HIGH),
            0,
        )
        assert high_count == 1

    @pytest.mark.asyncio
    async def test_model_registry_queries(self, db_session: AsyncSession):
        """Test ML model registry queries."""
        # Create models with different statuses
        models_data = [
            ("classifier", "1.0.0", ModelStatus.DEPLOYED, True),
            ("classifier", "1.1.0", ModelStatus.READY, False),
            ("detector", "2.0.0", ModelStatus.DEPLOYED, True),
            ("detector", "2.1.0", ModelStatus.TRAINING, False),
        ]

        for name, version, status, is_active in models_data:
            model = MLModel(
                name=name,
                version=version,
                model_type=name,
                status=status,
                is_active=is_active,
            )
            db_session.add(model)

        await db_session.commit()

        # Query active deployed models
        result = await db_session.execute(
            select(MLModel).where((MLModel.status == ModelStatus.DEPLOYED) & (MLModel.is_active.is_(True)))
        )

        active_models = result.scalars().all()
        assert len(active_models) == 2

        # Query latest version per model type
        result = await db_session.execute(
            select(MLModel.name, func.max(MLModel.version).label("latest_version")).group_by(MLModel.name)
        )

        latest_versions = result.all()
        assert len(latest_versions) == 2


# Pytest fixtures for database testing
@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for testing."""
    await db_manager.initialize()

    # Create tables for testing
    await db_manager.create_tables()

    async with db_manager.get_session() as session:
        yield session

    # Clean up after tests
    await db_manager.drop_tables()
    await db_manager.close()


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
