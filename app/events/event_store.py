"""Event store implementation for domain events."""

from typing import List, Optional, Protocol
from uuid import UUID

from app.events.base import DomainEvent


class IEventStore(Protocol):
    """Event store interface."""

    async def save_events(
        self, aggregate_id: UUID, events: List[DomainEvent], expected_version: Optional[int] = None
    ) -> None:
        """Save events to the store."""
        ...

    async def get_events(
        self, aggregate_id: UUID, from_version: Optional[int] = None
    ) -> List[DomainEvent]:
        """Get events for an aggregate."""
        ...


class InMemoryEventStore:
    """In-memory implementation of event store."""

    def __init__(self) -> None:
        self._events: dict[UUID, List[DomainEvent]] = {}

    async def save_events(
        self, aggregate_id: UUID, events: List[DomainEvent], expected_version: Optional[int] = None
    ) -> None:
        """Save events to memory."""
        if aggregate_id not in self._events:
            self._events[aggregate_id] = []
        self._events[aggregate_id].extend(events)

    async def get_events(
        self, aggregate_id: UUID, from_version: Optional[int] = None
    ) -> List[DomainEvent]:
        """Get events for aggregate."""
        events = self._events.get(aggregate_id, [])
        if from_version is not None:
            return events[from_version:]
        return events.copy()
