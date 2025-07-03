"""Enhanced repository interfaces with additional methods."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID

from app.domain.entities import Incident, IncidentSeverity, LogEntry, LogLevel, MLModel


class ILogRepository(Protocol):
    """Enhanced log repository interface with batch operations and filtering."""

    async def save(self, log: LogEntry) -> None:
        """Save a single log entry."""
        ...

    async def save_batch(self, logs: List[LogEntry]) -> None:
        """Save multiple log entries in batch for high-throughput ingestion."""
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

    async def find_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[LogEntry]:
        """Find logs within specific time range with pagination."""
        ...

    async def find_by_level(
        self, level: LogLevel, since_minutes: int = 60, limit: int = 1000
    ) -> List[LogEntry]:
        """Find logs by specific level within time period."""
        ...

    async def find_by_levels(
        self, levels: List[LogLevel], since_minutes: int = 60, limit: int = 1000
    ) -> List[LogEntry]:
        """Find logs by multiple levels (for critical level filtering)."""
        ...

    async def count_by_level_and_time(
        self, level: LogLevel, since_minutes: int = 60
    ) -> int:
        """Count logs by level within time period for monitoring."""
        ...

    async def find_logs_with_anomalies(
        self, threshold: float = 0.7, limit: int = 100
    ) -> List[LogEntry]:
        """Find logs with anomaly scores above threshold."""
        ...

    async def get_log_statistics(self, since_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated log statistics for monitoring dashboard."""
        ...

    async def delete_old_logs(self, older_than_days: int = 30) -> int:
        """Delete logs older than specified days (for maintenance)."""
        ...
