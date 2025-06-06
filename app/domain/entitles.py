"""Domain entities for Smart DevOps Assistant."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict
from uuid import UUID, uuid4


class LogLevel(Enum):
    """Log severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


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
        return self.level in (LogLevel.ERROR, LogLevel.CRITICAL)
