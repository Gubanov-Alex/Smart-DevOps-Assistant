"""Value objects for domain logic - Compatible with existing tests."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AnomalyScore:
    """Value object for anomaly detection scores with threshold support."""

    value: float
    confidence: float
    threshold: float = 0.7
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        """Validate score ranges."""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("Anomaly score must be between 0.0 and 1.0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

    def is_anomaly(self) -> bool:
        """Check if this represents an anomaly based on value and confidence vs threshold."""
        return self.value >= self.threshold and self.confidence >= 0.8

    def severity_level(self) -> str:
        """Calculate severity level based on anomaly score and confidence."""
        if self.value >= 0.9:
            return "critical"
        elif self.value >= 0.8:
            return "high"
        elif self.value >= 0.7:
            return "medium"
        else:
            return "normal"

    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is above threshold (0.8)."""
        return self.confidence >= 0.8

    @property
    def is_significant_anomaly(self) -> bool:
        """Check if both score and confidence are high."""
        return self.value / 100.0 >= 0.7 and self.is_high_confidence

    @property
    def risk_level(self) -> str:
        """Calculate risk level based on score and confidence."""
        if self.is_significant_anomaly:
            return "high"
        elif self.value >= 0.5 and self.confidence >= 0.6:
            return "medium"
        else:
            return "low"

    def __str__(self) -> str:
        """String representation for logging."""
        return f"AnomalyScore(value={self.value:.2f}, confidence={self.confidence:.2f}, risk={self.risk_level})"


@dataclass(frozen=True)
class MetricValue:
    """Value object for system metrics with name and validation."""

    name: str
    value: float
    unit: str
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Validate metric data."""
        if not self.name or not self.name.strip():
            raise ValueError("Metric name cannot be empty")

        # Allow negative values for certain metric types
        negative_allowed_types = ["temperature", "balance", "change", "delta", "diff", "offset"]

        if self.value < 0 and not any(
            allowed_type in self.name.lower() for allowed_type in negative_allowed_types
        ):
            raise ValueError(f"Metric '{self.name}' cannot have negative value")

    def is_percentage(self) -> bool:
        """Check if metric is a percentage."""
        return self.unit.lower() in ["percent", "percentage", "%"]

    def normalize_percentage(self) -> float:
        """Normalize percentage values or return original value for non-percentages."""
        if self.is_percentage():
            # For percentages > 1.0, normalize to decimal (150% → 1.5)
            # For percentages <= 1.0, return as-is (0.8% → 0.8)
            if self.value > 1.0:
                return self.value / 100.0
            else:
                return self.value
        else:
            # For non-percentages, return original value unchanged
            return self.value

    @property
    def is_time_based(self) -> bool:
        """Check if metric represents time."""
        return self.unit.lower() in [
            "seconds",
            "milliseconds",
            "minutes",
            "hours",
            "ms",
            "s",
            "m",
            "h",
        ]

    @property
    def is_size_based(self) -> bool:
        """Check if metric represents data size."""
        return self.unit.upper() in ["BYTES", "KB", "MB", "GB", "TB", "B"]

    def __str__(self) -> str:
        """String representation with formatting."""
        if self.is_percentage():
            return f"{self.value:.1f}%"
        elif self.is_time_based and self.value < 1 and self.unit.lower() in ["seconds", "s"]:
            return f"{self.value * 1000:.0f}ms"
        else:
            return f"{self.value}{self.unit}"


@dataclass(frozen=True)
class SourceSystem:
    """Value object representing the source of logs or metrics."""

    name: str
    environment: str
    service_type: str
    version: str = "unknown"
    region: str = "unknown"
    tags: tuple = ()

    def __post_init__(self) -> None:
        """Validate source system data."""
        if not self.name or not self.name.strip():
            raise ValueError("Source name cannot be empty")

        valid_environments = ["development", "staging", "production", "test", "local"]
        if self.environment.lower() not in valid_environments:
            raise ValueError(f"Environment must be one of: {', '.join(valid_environments)}")

        # Convert tags to tuple if it's a list
        if isinstance(self.tags, list):
            object.__setattr__(self, "tags", tuple(self.tags))

    def is_production(self) -> bool:
        """Check if this is a production system."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if this is a development system."""
        return self.environment.lower() in ["development", "dev", "local"]

    @property
    def is_staging(self) -> bool:
        """Check if this is a staging system."""
        return self.environment.lower() in ["staging", "stage", "test"]

    @property
    def fully_qualified_name(self) -> str:
        """Get fully qualified name including environment."""
        return f"{self.name}.{self.environment}"

    def full_identifier(self) -> str:
        """Generate full identifier: environment.service_type.name"""
        return f"{self.environment}.{self.service_type}.{self.name}"

    def has_tag(self, tag: str) -> bool:
        """Check if source has a specific tag."""
        return tag in self.tags

    def matches_filter(self, environment: str = None, service_type: str = None) -> bool:
        """Check if source matches given filters."""
        if environment and self.environment != environment:
            return False
        if service_type and self.service_type != service_type:
            return False
        return True

    def __str__(self) -> str:
        """String representation for logging."""
        return f"{self.name}[{self.environment}]"
