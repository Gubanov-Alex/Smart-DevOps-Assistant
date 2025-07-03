"""Mappers for converting between domain entities and SQLAlchemy models.

This module provides bidirectional mapping between domain entities and
database models, handling field name differences like metadata <-> extra_data.
"""

from typing import List

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
        return LogEntryEntity(
            id=model.id,
            message=model.message,
            level=LogLevel(model.level),
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
            level=entity.level,
            source=entity.source,
            timestamp=entity.timestamp,
            extra_data=entity.metadata,  # Map metadata to extra_data
        )

    @staticmethod
    def update_model_from_entity(model: LogEntryModel, entity: LogEntryEntity) -> None:
        """Update SQLAlchemy model from domain entity."""
        model.message = entity.message
        model.level = entity.level
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
            severity=entity.severity,
            status=entity.status,
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
        model.severity = entity.severity
        model.status = entity.status
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
        """Convert SQLAlchemy model to domain entity."""
        return MLModelEntity(
            id=model.id,
            name=model.name,
            version=model.version,
            model_type=model.model_type,
            status=ModelStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            trained_at=model.trained_at,
            deployed_at=model.deployed_at,
            accuracy=model.accuracy,
            precision=model.precision,
            recall=model.recall,
            f1_score=model.f1_score,
            training_dataset_size=model.training_dataset_size,
            training_duration_minutes=model.training_duration_minutes,
            model_path=model.model_path,
            config=model.config or {},
            metadata=model.extra_data or {},  # Map extra_data to metadata
            is_active=model.is_active,
            deployment_config=model.deployment_config or {},
        )

    @staticmethod
    def to_model(entity: MLModelEntity) -> MLModelModel:
        """Convert domain entity to SQLAlchemy model."""
        return MLModelModel(
            id=entity.id,
            name=entity.name,
            version=entity.version,
            model_type=entity.model_type,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            trained_at=entity.trained_at,
            deployed_at=entity.deployed_at,
            accuracy=entity.accuracy,
            precision=entity.precision,
            recall=entity.recall,
            f1_score=entity.f1_score,
            training_dataset_size=entity.training_dataset_size,
            training_duration_minutes=entity.training_duration_minutes,
            model_path=entity.model_path,
            config=entity.config,
            extra_data=entity.metadata,  # Map metadata to extra_data
            is_active=entity.is_active,
            deployment_config=entity.deployment_config,
        )

    @staticmethod
    def update_model_from_entity(model: MLModelModel, entity: MLModelEntity) -> None:
        """Update SQLAlchemy model from domain entity."""
        model.name = entity.name
        model.version = entity.version
        model.model_type = entity.model_type
        model.status = entity.status
        model.updated_at = entity.updated_at
        model.trained_at = entity.trained_at
        model.deployed_at = entity.deployed_at
        model.accuracy = entity.accuracy
        model.precision = entity.precision
        model.recall = entity.recall
        model.f1_score = entity.f1_score
        model.training_dataset_size = entity.training_dataset_size
        model.training_duration_minutes = entity.training_duration_minutes
        model.model_path = entity.model_path
        model.config = entity.config
        model.extra_data = entity.metadata
        model.is_active = entity.is_active
        model.deployment_config = entity.deployment_config


# Convenience functions for batch operations
def log_entities_to_models(entities: List[LogEntryEntity]) -> List[LogEntryModel]:
    """Convert list of LogEntry entities to models."""
    return [LogEntryMapper.to_model(entity) for entity in entities]


def log_models_to_entities(models: List[LogEntryModel]) -> List[LogEntryEntity]:
    """Convert list of LogEntry models to entities."""
    return [LogEntryMapper.to_entity(model) for model in models]


def incident_entities_to_models(entities: List[IncidentEntity]) -> List[IncidentModel]:
    """Convert list of Incident entities to models."""
    return [IncidentMapper.to_model(entity) for entity in entities]


def incident_models_to_entities(models: List[IncidentModel]) -> List[IncidentEntity]:
    """Convert list of Incident models to entities."""
    return [IncidentMapper.to_entity(model) for model in models]


def mlmodel_entities_to_models(entities: List[MLModelEntity]) -> List[MLModelModel]:
    """Convert list of MLModel entities to models."""
    return [MLModelMapper.to_model(entity) for entity in entities]


def mlmodel_models_to_entities(models: List[MLModelModel]) -> List[MLModelEntity]:
    """Convert list of MLModel models to entities."""
    return [MLModelMapper.to_entity(model) for model in models]


# Export mapper classes and utility functions
__all__ = [
    "LogEntryMapper",
    "IncidentMapper",
    "MLModelMapper",
    "log_entities_to_models",
    "log_models_to_entities",
    "incident_entities_to_models",
    "incident_models_to_entities",
    "mlmodel_entities_to_models",
    "mlmodel_models_to_entities",
]
