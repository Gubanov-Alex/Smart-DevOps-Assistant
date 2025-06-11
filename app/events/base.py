"""Base domain event class."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Uses aggregate_id as the only required field to avoid dataclass inheritance issues.
    All other fields have defaults and are set in __post_init__.
    """

    aggregate_id: UUID
    event_id: UUID = field(default_factory=uuid4, init=False)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc), init=False)
    version: int = field(default=1, init=False)
    event_type: str = field(default="", init=False)
    metadata: Dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Set computed fields after initialization."""
        # Set event type from class name
        object.__setattr__(self, "event_type", self.__class__.__name__)

        # Initialize metadata if not already set
        if not hasattr(self, "_metadata_initialized"):
            object.__setattr__(self, "metadata", {})
            object.__setattr__(self, "_metadata_initialized", True)

    @property
    def event_data(self) -> Dict[str, Any]:
        """Get event data for serialization."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_id": str(self.aggregate_id),
            "occurred_at": self.occurred_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
        }
