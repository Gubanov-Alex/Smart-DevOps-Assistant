"""Event handlers for domain events."""

from typing import Protocol

import structlog

from app.events.base import DomainEvent
from app.events.incident_events import IncidentCreated, IncidentResolved
from app.events.log_events import AnomalyDetected, LogEntryCreated
from app.events.ml_events import ModelDeployed, ModelTrainingCompleted

logger = structlog.get_logger()


class IEventHandler(Protocol):
    """Event handler interface."""

    async def handle(self, event: DomainEvent) -> None:
        """Handle domain event."""
        ...


class LogEventHandlers:
    """Handlers for log-related events."""

    async def handle_log_created(self, event: LogEntryCreated) -> None:
        """Handle log entry creation."""
        logger.info(
            "Log entry created",
            log_id=str(event.log_id),
            level=event.level.display_name,
            source=event.source,
        )

    async def handle_anomaly_detected(self, event: AnomalyDetected) -> None:
        """Handle anomaly detection."""
        logger.warning(
            "Anomaly detected",
            source=event.source,
            score=event.anomaly_score.value,
            affected_logs=len(event.affected_logs),
        )


class IncidentEventHandlers:
    """Handlers for incident-related events."""

    async def handle_incident_created(self, event: IncidentCreated) -> None:
        """Handle incident creation."""
        logger.info(
            "Incident created",
            incident_id=str(event.incident_id),
            title=event.title,
            severity=event.severity.display_name,
            auto_created=event.auto_created,
        )

    async def handle_incident_resolved(self, event: IncidentResolved) -> None:
        """Handle incident resolution."""
        logger.info(
            "Incident resolved",
            incident_id=str(event.incident_id),
            resolved_by=event.resolved_by,
            resolution_time=event.resolution_time_minutes,
        )


class MLEventHandlers:
    """Handlers for ML-related events."""

    async def handle_training_completed(self, event: ModelTrainingCompleted) -> None:
        """Handle model training completion."""
        logger.info(
            "Model training completed",
            model_id=str(event.model_id),
            model_name=event.model_name,
            accuracy=event.accuracy,
            duration=event.training_duration_minutes,
        )

    async def handle_model_deployed(self, event: ModelDeployed) -> None:
        """Handle model deployment."""
        logger.info(
            "Model deployed",
            model_id=str(event.model_id),
            model_name=event.model_name,
            version=event.version,
            environment=event.deployment_environment,
        )
