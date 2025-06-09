"""Log-related domain events."""

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID, uuid4

from app.domain.entities import LogLevel
from app.domain.value_objects import AnomalyScore
from app.events.base import DomainEvent


@dataclass(frozen=True)
class LogEntryCreated(DomainEvent):
    """Event fired when a new log entry is created."""

    log_id: UUID
    message: str
    level: LogLevel
    source: str
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Set aggregate_id to log_id for logical grouping."""
        object.__setattr__(self, "aggregate_id", self.log_id)
        super().__post_init__()


@dataclass(frozen=True)
class LogClassificationCompleted(DomainEvent):
    """Event fired when log classification is completed."""

    log_id: UUID
    predicted_level: LogLevel
    confidence: float
    model_version: str
    processing_time_ms: int

    def __post_init__(self) -> None:
        """Set aggregate_id to log_id for logical grouping."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.processing_time_ms < 0:
            raise ValueError("Processing time cannot be negative")

        object.__setattr__(self, "aggregate_id", self.log_id)
        super().__post_init__()


@dataclass(frozen=True)
class AnomalyDetected(DomainEvent):
    """Event fired when anomaly is detected in logs."""

    source: str
    anomaly_score: AnomalyScore
    detection_method: str
    severity: str
    affected_logs: List[UUID] = field(default_factory=list)
    aggregate_root_id: Optional[UUID] = None

    def __post_init__(self) -> None:
        """Validate and set aggregate_id."""
        # Use explicit aggregate_root_id if provided, otherwise first affected log, or generate new
        if self.aggregate_root_id:
            aggregate_id = self.aggregate_root_id
        elif self.affected_logs:
            aggregate_id = self.affected_logs[0]
        else:
            aggregate_id = uuid4()

        object.__setattr__(self, "aggregate_id", aggregate_id)
        super().__post_init__()


@dataclass(frozen=True)
class LogPatternIdentified(DomainEvent):
    """Event fired when a log pattern is identified."""

    pattern_id: str
    pattern_description: str
    frequency_per_hour: int
    detection_method: str
    affected_sources: List[str] = field(default_factory=list)
    sample_log_ids: List[UUID] = field(default_factory=list)
    aggregate_root_id: Optional[UUID] = None

    def __post_init__(self) -> None:
        """Validate and set aggregate_id."""
        if self.frequency_per_hour < 0:
            raise ValueError("Frequency cannot be negative")

        # Use explicit aggregate_root_id if provided, otherwise first sample log, or generate new
        if self.aggregate_root_id:
            aggregate_id = self.aggregate_root_id
        elif self.sample_log_ids:
            aggregate_id = self.sample_log_ids[0]
        else:
            aggregate_id = uuid4()

        object.__setattr__(self, "aggregate_id", aggregate_id)
        super().__post_init__()
