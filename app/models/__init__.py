"""SQLAlchemy models for Smart DevOps Assistant - Fixed deprecation warnings.

This module contains all database models using SQLAlchemy ORM with full
async support and proper typing. Models are designed to support high-throughput
log ingestion and ML model lifecycle management.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Association table for many-to-many relationship between incidents and logs
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


# Base class for all models - Fixed deprecation warning
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class LogLevel(str, Enum):
    """Log level enumeration matching domain entity."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def is_error_level(self) -> bool:
        """Check if log level indicates an error condition."""
        return self in (self.ERROR, self.CRITICAL)


class IncidentSeverity(str, Enum):
    """Incident severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    """Incident status enumeration."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

    def is_active(self) -> bool:
        """Check if incident status is active."""
        return self in (self.OPEN, self.IN_PROGRESS)


class ModelStatus(str, Enum):
    """ML Model status enumeration."""

    TRAINING = "TRAINING"
    TRAINED = "TRAINED"
    VALIDATING = "VALIDATING"
    READY = "READY"
    DEPLOYED = "DEPLOYED"
    DEPRECATED = "DEPRECATED"
    FAILED = "FAILED"

    def is_production_ready(self) -> bool:
        """Check if model is ready for production deployment."""
        return self == self.DEPLOYED


# Association table for many-to-many relationship between incidents and logs
incident_logs = Table(
    "incident_logs",
    Base.metadata,
    Column(
        "incident_id", UUID(as_uuid=True), ForeignKey("incidents.id"), primary_key=True
    ),
    Column(
        "log_id", UUID(as_uuid=True), ForeignKey("log_entries.id"), primary_key=True
    ),
    Index("idx_incident_logs_incident", "incident_id"),
    Index("idx_incident_logs_log", "log_id"),
)


class LogEntry(Base):
    """Log entry model for storing and indexing application logs.

    Optimized for high-throughput ingestion with proper indexing
    for time-based queries and full-text search capabilities.
    """

    __tablename__ = "log_entries"
    __table_args__ = (
        # Indexes for high-performance queries
        Index("idx_log_entries_timestamp", "timestamp"),
        Index("idx_log_entries_level", "level"),
        Index("idx_log_entries_source", "source"),
        Index("idx_log_entries_level_timestamp", "level", "timestamp"),
        Index("idx_log_entries_source_timestamp", "source", "timestamp"),
        Index("idx_log_entries_anomaly_score", "anomaly_score"),
        # Constraints for data integrity
        CheckConstraint(
            "anomaly_score >= 0 AND anomaly_score <= 1",
            name="check_anomaly_score_range",
        ),
        CheckConstraint(
            "classification_confidence >= 0 AND classification_confidence <= 1",
            name="check_classification_confidence_range",
        ),
        {"comment": "Application log entries with ML analysis results"},
    )

    # Primary fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Raw log message content"
    )
    level: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Log severity level"
    )
    source: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Source system or service name"
    )

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Log entry timestamp",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    # Optional analysis fields
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional structured log extra_data"
    )
    processing_time_ms: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Log processing time in milliseconds"
    )
    classification_confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="ML classification confidence score"
    )
    anomaly_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Anomaly detection score"
    )

    # Relationships
    incidents: Mapped[List["Incident"]] = relationship(
        "Incident", secondary=incident_logs, back_populates="related_logs"
    )

    def __repr__(self) -> str:
        """String representation of log entry."""
        return f"<LogEntry(id={self.id}, level={self.level}, source={self.source})>"

    def is_critical(self) -> bool:
        """Check if log entry is critical level."""
        return self.level == LogLevel.CRITICAL.value

    def has_anomaly(self, threshold: float = 0.7) -> bool:
        """Check if log entry has anomaly above threshold."""
        return self.anomaly_score is not None and self.anomaly_score >= threshold


class Incident(Base):
    """Incident model for tracking system issues and outages.

    Designed for efficient incident management with proper relationships
    to related log entries and comprehensive metadata support.
    """

    __tablename__ = "incidents"
    __table_args__ = (
        # Indexes for efficient querying
        Index("idx_incidents_status", "status"),
        Index("idx_incidents_severity", "severity"),
        Index("idx_incidents_source", "source"),
        Index("idx_incidents_created_at", "created_at"),
        Index("idx_incidents_assigned_to", "assigned_to"),
        Index("idx_incidents_status_severity", "status", "severity"),
        Index("idx_incidents_priority_score", "priority_score"),
        # Constraints
        CheckConstraint(
            "priority_score >= 0 AND priority_score <= 1",
            name="check_priority_score_range",
        ),
        {"comment": "System incidents and issues tracking"},
    )

    # Primary fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Incident title or summary"
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Detailed incident description"
    )
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Incident severity level"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Current incident status"
    )
    source: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Source system or detector"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Incident creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Incident resolution timestamp"
    )

    # Assignment and categorization
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Assigned team or person"
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, comment="Incident tags for categorization"
    )

    # Metadata and analytics
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional incident metadata"
    )
    resolution_time_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Time to resolution in minutes"
    )
    priority_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="AI-calculated priority score"
    )

    # Relationships
    related_logs: Mapped[List[LogEntry]] = relationship(
        "LogEntry", secondary=incident_logs, back_populates="incidents"
    )

    def __repr__(self) -> str:
        """String representation of incident."""
        return f"<Incident(id={self.id}, title={self.title}, status={self.status})>"

    def is_open(self) -> bool:
        """Check if incident is in open status."""
        return self.status in [
            IncidentStatus.OPEN.value,
            IncidentStatus.IN_PROGRESS.value,
        ]

    def is_critical(self) -> bool:
        """Check if incident is critical severity."""
        return self.severity == IncidentSeverity.CRITICAL.value


class MLModel(Base):
    """ML Model metadata and lifecycle tracking.

    Stores comprehensive information about machine learning models
    including training metrics, deployment status, and versioning.
    """

    __tablename__ = "ml_models"
    __table_args__ = (
        # Indexes for model management queries
        Index("idx_ml_models_name", "name"),
        Index("idx_ml_models_version", "version"),
        Index("idx_ml_models_status", "status"),
        Index("idx_ml_models_type", "model_type"),
        Index("idx_ml_models_name_version", "name", "version"),
        Index("idx_ml_models_active", "is_active"),
        Index("idx_ml_models_deployed_at", "deployed_at"),
        Index("idx_ml_models_accuracy", "accuracy"),
        # Unique constraint for name-version combination
        UniqueConstraint("name", "version", name="uq_ml_models_name_version"),
        {"comment": "ML model metadata and lifecycle tracking"},
    )

    # Primary fields
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Model name identifier"
    )
    version: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Model version string"
    )
    model_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Type of ML model"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Current model status"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Model creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp",
    )
    trained_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Training completion timestamp"
    )
    deployed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Deployment timestamp"
    )

    # Performance metrics
    accuracy: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Model accuracy score"
    )
    precision: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Model precision score"
    )
    recall: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Model recall score"
    )
    f1_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Model F1 score"
    )

    # Training metadata
    training_dataset_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Size of training dataset"
    )
    training_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Training duration in minutes"
    )

    # Model storage and configuration
    model_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Path to model file"
    )
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Model configuration parameters"
    )
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional model metadata"
    )

    # Status fields
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether model is active"
    )
    deployment_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Deployment configuration"
    )

    def __repr__(self) -> str:
        """String representation of ML model."""
        return f"<MLModel(id={self.id}, name={self.name}, version={self.version}, status={self.status})>"

    def is_deployed(self) -> bool:
        """Check if model is deployed."""
        return self.status == ModelStatus.DEPLOYED.value

    def is_production_ready(self) -> bool:
        """Check if model is ready for production."""
        return self.status in [ModelStatus.READY.value, ModelStatus.DEPLOYED.value]

    def get_performance_summary(self) -> Dict[str, Optional[float]]:
        """Get performance metrics summary."""
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
        }
