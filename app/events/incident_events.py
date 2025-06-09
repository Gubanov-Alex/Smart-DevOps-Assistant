"""Incident-related domain events."""

from dataclasses import dataclass
from uuid import UUID

from app.domain.entities import IncidentSeverity
from app.events.base import DomainEvent


@dataclass(frozen=True)
class IncidentCreated(DomainEvent):
    """Event fired when a new incident is created."""

    incident_id: UUID
    title: str
    description: str
    severity: IncidentSeverity
    source: str
    auto_created: bool = False

    def __post_init__(self) -> None:
        """Set aggregate_id to incident_id for logical grouping."""
        object.__setattr__(self, "aggregate_id", self.incident_id)
        super().__post_init__()


@dataclass(frozen=True)
class IncidentResolved(DomainEvent):
    """Event fired when an incident is resolved."""

    incident_id: UUID
    resolved_by: str
    resolution_time_minutes: int
    resolution_notes: str = ""

    def __post_init__(self) -> None:
        """Set aggregate_id to incident_id for logical grouping."""
        object.__setattr__(self, "aggregate_id", self.incident_id)
        super().__post_init__()


@dataclass(frozen=True)
class IncidentEscalated(DomainEvent):
    """Event fired when an incident is escalated."""

    incident_id: UUID
    escalated_to: str
    escalation_reason: str
    previous_severity: IncidentSeverity
    new_severity: IncidentSeverity

    def __post_init__(self) -> None:
        """Set aggregate_id to incident_id for logical grouping."""
        object.__setattr__(self, "aggregate_id", self.incident_id)
        super().__post_init__()


@dataclass(frozen=True)
class IncidentSlaBreached(DomainEvent):
    """Event fired when incident SLA is breached."""

    incident_id: UUID
    sla_type: str
    target_minutes: int
    actual_minutes: int
    breach_severity: str

    def __post_init__(self) -> None:
        """Set aggregate_id to incident_id for logical grouping."""
        object.__setattr__(self, "aggregate_id", self.incident_id)
        super().__post_init__()
