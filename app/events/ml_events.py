"""ML model related domain events."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID

from app.events.base import DomainEvent


@dataclass(frozen=True)
class ModelTrainingStarted(DomainEvent):
    """Event fired when model training begins."""

    model_id: UUID = field()
    model_name: str = field()
    model_type: str = field()
    training_data_size: int = field()
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    training_config: Dict[str, Any] = field(default_factory=dict)  # Добавлено

    def __post_init__(self):
        """Validate and set aggregate_id."""
        if self.training_data_size < 0:
            raise ValueError("Training data size cannot be negative")
        object.__setattr__(self, "aggregate_id", self.model_id)
        super().__post_init__()


@dataclass(frozen=True)
class ModelTrainingCompleted(DomainEvent):
    """Event fired when model training completes."""

    model_id: UUID = field()
    model_name: str = field()
    accuracy: float = field()
    training_duration_minutes: int = field()
    model_metrics: Dict[str, Any] = field(default_factory=dict)  # Добавлено

    def __post_init__(self):
        """Validate accuracy and set aggregate_id."""
        if not 0 <= self.accuracy <= 1:
            raise ValueError("Accuracy must be between 0 and 1")
        if self.training_duration_minutes < 0:
            raise ValueError("Training duration cannot be negative")
        object.__setattr__(self, "aggregate_id", self.model_id)
        super().__post_init__()


@dataclass(frozen=True)
class ModelDeployed(DomainEvent):
    """Event fired when model is deployed to production."""

    model_id: UUID = field()
    model_name: str = field()
    version: str = field()
    deployment_environment: str = field()
    previous_version: Optional[str] = field(default=None)

    def __post_init__(self):
        """Set aggregate_id."""
        object.__setattr__(self, "aggregate_id", self.model_id)
        super().__post_init__()


@dataclass(frozen=True)
class ModelPerformanceDegraded(DomainEvent):
    """Event fired when model performance degrades below threshold."""

    model_id: UUID = field()
    model_name: str = field()
    current_accuracy: float = field()
    threshold_accuracy: float = field()
    degradation_metrics: Dict[str, Any] = field(default_factory=dict)  # Добавлено

    def __post_init__(self):
        """Validate accuracies and set aggregate_id."""
        if not 0 <= self.current_accuracy <= 1:
            raise ValueError("Current accuracy must be between 0 and 1")
        if not 0 <= self.threshold_accuracy <= 1:
            raise ValueError("Threshold accuracy must be between 0 and 1")
        object.__setattr__(self, "aggregate_id", self.model_id)
        super().__post_init__()
