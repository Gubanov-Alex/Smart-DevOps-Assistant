"""Repository interfaces using Protocol pattern."""

from typing import List, Optional, Protocol
from uuid import UUID

from app.domain.entities import Incident, IncidentSeverity, LogEntry, MLModel


class ILogRepository(Protocol):
    """Log repository interface."""

    async def save(self, log: LogEntry) -> None:
        """Save a log entry."""
        ...

    async def find_by_id(self, log_id: UUID) -> Optional[LogEntry]:
        """Find log entry by ID."""
        ...

    async def find_by_source(self, source: str, limit: int = 100) -> List[LogEntry]:
        """Find log entries by source system."""
        ...

    async def find_critical_logs(self, since_minutes: int = 60) -> List[LogEntry]:
        """Find critical logs within time period."""
        ...


class IIncidentRepository(Protocol):
    """Incident repository interface."""

    async def save(self, incident: Incident) -> None:
        """Save an incident."""
        ...

    async def find_by_id(self, incident_id: UUID) -> Optional[Incident]:
        """Find incident by ID."""
        ...

    async def find_open_incidents(self) -> List[Incident]:
        """Find all open incidents."""
        ...

    async def find_by_severity(self, severity: IncidentSeverity) -> List[Incident]:
        """Find incidents by severity level."""
        ...


class IMLModelRepository(Protocol):
    """ML Model repository interface."""

    async def save(self, model: MLModel) -> None:
        """Save a model."""
        ...

    async def find_by_name_and_version(self, name: str, version: str) -> Optional[MLModel]:
        """Find model by name and version."""
        ...

    async def find_latest_ready(self, model_type: str) -> Optional[MLModel]:
        """Find latest ready model of given type."""
        ...

    async def find_all_versions(self, name: str) -> List[MLModel]:
        """Find all versions of a model."""
        ...

    async def get_by_id(self, model_id: UUID) -> Optional[MLModel]:
        """Get model by ID."""
        ...

    async def get_active_models(self) -> List[MLModel]:
        """Get all active models."""
        ...
