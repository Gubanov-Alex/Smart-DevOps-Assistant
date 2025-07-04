"""Mappers for converting between domain entities and SQLAlchemy models.

This module provides bidirectional mapping between domain entities and
database models, handling field name differences like metadata <-> extra_data.
"""

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
from app.models import Incident as IncidentModel
from app.models import LogEntry as LogEntryModel
from app.models import MLModel as MLModelModel


class LogEntryMapper:
    """Mapper for LogEntry domain entity <-> SQLAlchemy model."""

    @staticmethod
    def to_entity(model: LogEntryModel) -> LogEntryEntity:
        """Convert SQLAlchemy model to domain entity."""
        # Handle case-insensitive enum conversion
        level_value = model.level.upper() if model.level else "INFO"

        # Map database values to enum values
        level_mapping = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
            "CRITICAL": LogLevel.CRITICAL,
        }

        level = level_mapping.get(level_value, LogLevel.INFO)

        return LogEntryEntity(
            id=model.id,
            message=model.message,
            level=level,
            source=model.source,
            timestamp=model.timestamp,
            metadata=model.extra_data or {},  # Map extra_data to metadata
        )

    @staticmethod
    def to_model(entity: LogEntryEntity) -> LogEntryModel:
        """Convert domain entity to SQLAlchemy model."""
        return LogEntryModel(
            id=entity.id,
            message=entity.message,
            level=entity.level.value.upper(),  # Store as uppercase in DB
            source=entity.source,
            timestamp=entity.timestamp,
            extra_data=entity.metadata,  # Map metadata to extra_data
        )

    @staticmethod
    def update_model_from_entity(model: LogEntryModel, entity: LogEntryEntity) -> None:
        """Update SQLAlchemy model from domain entity."""
        model.message = entity.message
        model.level = entity.level.value.upper()  # Store as uppercase in DB
        model.source = entity.source
        model.timestamp = entity.timestamp
        model.extra_data = entity.metadata


class IncidentMapper:
    """Mapper for Incident domain entity <-> SQLAlchemy model."""

    @staticmethod
    def to_entity(model: IncidentModel) -> IncidentEntity:
        """Convert SQLAlchemy model to domain entity."""
        return IncidentEntity(
            id=model.id,
            title=model.title,
            description=model.description,
            severity=IncidentSeverity(model.severity),
            status=IncidentStatus(model.status),
            source=model.source,
            created_at=model.created_at,
            updated_at=model.updated_at,
            resolved_at=model.resolved_at,
            assigned_to=model.assigned_to,
            tags=model.tags or [],
            related_logs=(
                [log.id for log in model.related_logs] if model.related_logs else []
            ),
            metadata=model.extra_data or {},  # Map extra_data to metadata
        )

    @staticmethod
    def to_model(entity: IncidentEntity) -> IncidentModel:
        """Convert domain entity to SQLAlchemy model."""
        return IncidentModel(
            id=entity.id,
            title=entity.title,
            description=entity.description,
            severity=entity.severity.value,  # Convert enum to string
            status=entity.status.value,  # Convert enum to string
            source=entity.source,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            resolved_at=entity.resolved_at,
            assigned_to=entity.assigned_to,
            tags=entity.tags,
            extra_data=entity.metadata,  # Map metadata to extra_data
        )

    @staticmethod
    def update_model_from_entity(model: IncidentModel, entity: IncidentEntity) -> None:
        """Update SQLAlchemy model from domain entity."""
        model.title = entity.title
        model.description = entity.description
        model.severity = entity.severity.value
        model.status = entity.status.value
        model.source = entity.source
        model.updated_at = entity.updated_at
        model.resolved_at = entity.resolved_at
        model.assigned_to = entity.assigned_to
        model.tags = entity.tags
        model.extra_data = entity.metadata


class MLModelMapper:
    """Mapper for MLModel domain entity <-> SQLAlchemy model."""

    @staticmethod
    def to_entity(model: MLModelModel) -> MLModelEntity:
        """Convert SQLAlchemy model to domain entity - matching actual domain structure."""
        return MLModelEntity(
            name=model.name,
            model_type=model.model_type,
            version=model.version,
            id=model.id,
            status=ModelStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            deployed_at=model.deployed_at,
            accuracy=model.accuracy,
            training_duration_minutes=model.training_duration_minutes,
            model_path=model.model_path,
            config=model.config or {},
            metrics={
                # Map SQLAlchemy fields to metrics dict
                "precision": model.precision,
                "recall": model.recall,
                "f1_score": model.f1_score,
            },
            metadata=model.extra_data or {},
        )

    @staticmethod
    def to_model(entity: MLModelEntity) -> MLModelModel:
        """Convert domain entity to SQLAlchemy model."""
        return MLModelModel(
            id=entity.id,
            name=entity.name,
            version=entity.version,
            model_type=entity.model_type,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            trained_at=None,  # Not in domain entity
            deployed_at=entity.deployed_at,
            accuracy=entity.accuracy,
            precision=entity.metrics.get("precision"),
            recall=entity.metrics.get("recall"),
            f1_score=entity.metrics.get("f1_score"),
            training_dataset_size=None,  # Not in domain entity
            training_duration_minutes=entity.training_duration_minutes,
            model_path=entity.model_path,
            config=entity.config,
            extra_data=entity.metadata,
            is_active=True,  # Default value
            deployment_config={},  # Default value
        )

    @staticmethod
    def update_model_from_entity(model: MLModelModel, entity: MLModelEntity) -> None:
        """Update SQLAlchemy model from domain entity."""
        model.name = entity.name
        model.version = entity.version
        model.model_type = entity.model_type
        model.status = entity.status.value
        model.updated_at = entity.updated_at
        model.deployed_at = entity.deployed_at
        model.accuracy = entity.accuracy
        model.precision = entity.metrics.get("precision")
        model.recall = entity.metrics.get("recall")
        model.f1_score = entity.metrics.get("f1_score")
        model.training_duration_minutes = entity.training_duration_minutes
        model.model_path = entity.model_path
        model.config = entity.config
        model.extra_data = entity.metadata
