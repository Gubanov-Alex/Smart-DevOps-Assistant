"""Domain entities for Smart DevOps Assistant."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class LogLevel(Enum):
    """Log severity levels with enhanced functionality."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return self.value.title()

    @property
    def numeric_level(self) -> int:
        """Numeric representation for sorting/comparison."""
        levels = {
            self.DEBUG: 10,
            self.INFO: 20,
            self.WARNING: 30,
            self.ERROR: 40,
            self.CRITICAL: 50,
        }
        return levels[self]

    def is_error_level(self) -> bool:
        """Check if this level indicates an error condition."""
        return self in (self.ERROR, self.CRITICAL)


class IncidentSeverity(Enum):
    """Incident severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return self.value.title()

    @property
    def numeric_priority(self) -> int:
        """Numeric priority for sorting."""
        priorities = {
            self.LOW: 1,
            self.MEDIUM: 2,
            self.HIGH: 3,
            self.CRITICAL: 4,
        }
        return priorities[self]


class IncidentStatus(Enum):
    """Incident status states."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return self.value.replace("_", " ").title()

    def is_active(self) -> bool:
        """Check if incident is still active."""
        return self in (self.OPEN, self.IN_PROGRESS)


class ModelStatus(Enum):
    """ML Model status states."""

    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"

    @property
    def display_name(self) -> str:
        """Human-readable display name."""
        return self.value.title()

    def is_active(self) -> bool:
        """Check if model is actively used."""
        return self == self.DEPLOYED


@dataclass(frozen=True)
class LogEntry:
    """Core log entry entity."""

    message: str
    timestamp: datetime
    level: LogLevel
    source: str
    id: UUID = field(default_factory=uuid4)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_error_level(self) -> bool:
        """Check if log indicates an error condition."""
        return self.level.is_error_level()


@dataclass
class Incident:
    """Incident entity for tracking issues."""

    title: str
    description: str
    severity: IncidentSeverity
    source: str
    id: UUID = field(default_factory=uuid4)
    status: IncidentStatus = field(default=IncidentStatus.OPEN)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    related_logs: List[UUID] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def resolve(self, resolved_by: Optional[str] = None) -> None:
        """Mark incident as resolved."""
        self.status = IncidentStatus.RESOLVED
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if resolved_by:
            self.metadata["resolved_by"] = resolved_by

    def assign(self, assignee: str) -> None:
        """Assign incident to someone."""
        self.assigned_to = assignee
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str) -> None:
        """Add a tag to incident."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def add_related_log(self, log_id: UUID) -> None:
        """Associate a log entry with this incident."""
        if log_id not in self.related_logs:
            self.related_logs.append(log_id)
            self.updated_at = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        """Check if incident is still active."""
        return self.status.is_active()

    @property
    def resolution_time_minutes(self) -> Optional[int]:
        """Calculate resolution time in minutes."""
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
            return int(delta.total_seconds() / 60)
        return None


@dataclass
class MLModel:
    """ML Model entity for tracking trained models."""

    name: str
    model_type: str
    version: str
    id: UUID = field(default_factory=uuid4)
    status: ModelStatus = field(default=ModelStatus.TRAINING)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deployed_at: Optional[datetime] = None
    accuracy: Optional[float] = None
    training_duration_minutes: Optional[int] = None
    model_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def deploy(self, deployment_path: str) -> None:
        """Mark model as deployed."""
        self.status = ModelStatus.DEPLOYED
        self.deployed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.model_path = deployment_path

    def complete_training(self, accuracy: float, duration_minutes: int) -> None:
        """Mark training as completed."""
        self.status = ModelStatus.TRAINED
        self.accuracy = accuracy
        self.training_duration_minutes = duration_minutes
        self.updated_at = datetime.utcnow()

    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """Update model performance metrics."""
        self.metrics.update(metrics)
        self.updated_at = datetime.utcnow()

    def deprecate(self) -> None:
        """Mark model as deprecated."""
        self.status = ModelStatus.DEPRECATED
        self.updated_at = datetime.utcnow()

    @property
    def is_ready_for_deployment(self) -> bool:
        """Check if model is trained and ready for deployment."""
        return self.status == ModelStatus.TRAINED and self.accuracy is not None

    @property
    def is_deployed(self) -> bool:
        """Check if model is currently deployed."""
        return self.status == ModelStatus.DEPLOYED
