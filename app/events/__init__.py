"""Domain events package."""

from app.events.base import DomainEvent
from app.events.event_bus import EventBus
from app.events.event_store import IEventStore, InMemoryEventStore

# Handlers
from app.events.handlers import (
    IncidentEventHandlers,
    LogEventHandlers,
    MLEventHandlers,
)
from app.events.incident_events import (
    IncidentCreated,
    IncidentEscalated,
    IncidentResolved,
    IncidentSlaBreached,
)

# Event types
from app.events.log_events import (
    AnomalyDetected,
    LogClassificationCompleted,
    LogEntryCreated,
    LogPatternIdentified,
)

# Middleware
from app.events.middleware import (
    audit_middleware,
    logging_middleware,
    metrics_middleware,
)
from app.events.ml_events import (
    ModelDeployed,
    ModelPerformanceDegraded,
    ModelTrainingCompleted,
    ModelTrainingStarted,
)

__all__ = [
    # Base
    "DomainEvent",
    "EventBus",
    "IEventStore",
    "InMemoryEventStore",
    # Log events
    "LogEntryCreated",
    "LogClassificationCompleted",
    "AnomalyDetected",
    "LogPatternIdentified",
    # Incident events
    "IncidentCreated",
    "IncidentResolved",
    "IncidentEscalated",
    "IncidentSlaBreached",
    # ML events
    "ModelTrainingStarted",
    "ModelTrainingCompleted",
    "ModelDeployed",
    "ModelPerformanceDegraded",
    # Handlers
    "LogEventHandlers",
    "IncidentEventHandlers",
    "MLEventHandlers",
    # Middleware
    "logging_middleware",
    "metrics_middleware",
    "audit_middleware",
]
