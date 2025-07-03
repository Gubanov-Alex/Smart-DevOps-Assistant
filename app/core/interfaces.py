"""Core interfaces for ML services using a Protocol pattern."""

from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID

from app.domain.entities import LogEntry, LogLevel
from app.domain.value_objects import AnomalyScore


class ILogClassifier(Protocol):
    """Interface for log classification services."""

    async def classify(self, logs: List[str]) -> List[LogLevel]:
        """Classify log messages and return predicted levels.

        Args:
            logs: List of raw log messages

        Returns:
            List of predicted LogLevel enums
        """
        ...

    async def classify_single(self, log_message: str) -> LogLevel:
        """Classify a single log message."""
        ...

    async def get_confidence(self, log_message: str, predicted_level: LogLevel) -> float:
        """Get a confidence score for prediction."""
        ...

    async def health_check(self) -> bool:
        """Check if the classifier is healthy and ready."""
        ...


class IAnomalyDetector(Protocol):
    """Interface for anomaly detection services."""

    async def detect(self, metrics: List[float]) -> List[AnomalyScore]:
        """Detect anomalies in metric values.

        Args:
            metrics: List of metric values to analyze

        Returns:
            List of AnomalyScore objects
        """
        ...

    async def detect_logs(self, logs: List[LogEntry]) -> List[AnomalyScore]:
        """Detect anomalies in log patterns."""
        ...

    async def update_baseline(self, metrics: List[float]) -> None:
        """Update baseline metrics for anomaly detection."""
        ...

    async def health_check(self) -> bool:
        """Check detector health."""
        ...


class IModelRegistry(Protocol):
    """Interface for ML model registry."""

    async def save_model(self, model: Any, name: str, version: str, metadata: Dict[str, Any]) -> UUID:
        """Save a trained model to registry.

        Args:
            model: The trained model object
            name: Model name
            version: Model version
            metadata: Additional model metadata

        Returns:
            Model UUID
        """
        ...

    async def load_model(self, name: str, version: Optional[str] = None) -> Any:
        """Load model from the registry.

        Args:
            name: Model name
            version: Specific version (latest if None)

        Returns:
            Loaded model object
        """
        ...

    async def list_versions(self, name: str) -> List[str]:
        """List all versions of a model."""
        ...

    async def delete_model(self, name: str, version: str) -> bool:
        """Delete a model version."""
        ...

    async def get_model_metadata(self, name: str, version: str) -> Dict[str, Any]:
        """Get model metadata."""
        ...


class IIncidentAnalyzer(Protocol):
    """Interface for incident analysis services."""

    async def analyze_incident_pattern(self, logs: List[LogEntry]) -> Dict[str, Any]:
        """Analyze incident patterns from logs.

        Returns:
            Analysis results with root cause suggestions
        """
        ...

    async def predict_incident_severity(self, logs: List[LogEntry]) -> float:
        """Predict incident severity based on logs."""
        ...

    async def suggest_resolution(self, incident_description: str) -> List[str]:
        """Suggest resolution steps for incident."""
        ...
