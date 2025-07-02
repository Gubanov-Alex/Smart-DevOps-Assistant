"""SQLAlchemy models for Smart DevOps Assistant.

This module contains all database models using SQLAlchemy ORM with full
async support and proper typing. Models are designed to support high-throughput
log ingestion and ML model lifecycle management.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# Base class for all models
Base = declarative_base()


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


class LogEntry(Base):
    """Log entry model for storing and indexing application logs.

    Optimized for high-throughput ingestion with proper indexing
    for time-based queries and full-text search capabilities.
    """

    __tablename__ = "log_entries"

    # Primary key and identification
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique log entry identifier",
    )

    # Core log data
    message: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Raw log message content"
    )
    level: Mapped[LogLevel] = mapped_column(
        String(20), nullable=False, index=True, comment="Log severity level"
    )
    source: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="Source system or service name"
    )

    # Timestamp information
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        server_default=func.now(),
        comment="Log entry timestamp",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    # Structured extra_data (renamed to avoid SQLAlchemy reserved word)
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional structured log extra_data"
    )

    # Performance tracking
    processing_time_ms: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Log processing time in milliseconds"
    )

    # ML analysis results
    classification_confidence: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="ML classification confidence score"
    )
    anomaly_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Anomaly detection score"
    )

    # Relationships
    incidents: Mapped[List["Incident"]] = relationship(
        "Incident",
        secondary="incident_logs",
        back_populates="related_logs",
        lazy="selectin",
    )

    # Database constraints and indexes
    __table_args__ = (
        Index("idx_log_timestamp_level", "timestamp", "level"),
        Index("idx_log_source_timestamp", "source", "timestamp"),
        Index("idx_log_created_at", "created_at"),
        CheckConstraint(
            "classification_confidence >= 0 AND classification_confidence <= 1",
            name="check_classification_confidence_range",
        ),
        CheckConstraint(
            "anomaly_score >= 0 AND anomaly_score <= 1",
            name="check_anomaly_score_range",
        ),
        {"comment": "Application log entries with ML analysis results"},
    )

    def __repr__(self) -> str:
        return f"<LogEntry(id={self.id}, level={self.level}, source={self.source})>"


class Incident(Base):
    """Incident tracking model for managing system issues.

    Supports full incident lifecycle management with proper
    audit trail and relationship tracking.
    """

    __tablename__ = "incidents"

    # Primary key and identification
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique incident identifier",
    )

    # Core incident data
    title: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Incident title/summary"
    )
    description: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Detailed incident description"
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        String(20), nullable=False, index=True, comment="Incident severity level"
    )
    status: Mapped[IncidentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=IncidentStatus.OPEN,
        index=True,
        comment="Current incident status",
    )
    source: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Source system where incident originated",
    )

    # Timestamp tracking
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
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

    # Assignment and ownership
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Person or team assigned to incident",
    )

    # Categorization and extra_data (renamed to avoid SQLAlchemy reserved word)
    tags: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, comment="Incident categorization tags"
    )
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional incident extra_data"
    )

    # Performance metrics
    resolution_time_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Time to resolution in minutes"
    )

    # AI analysis results
    priority_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="AI-calculated priority score"
    )

    # Relationships
    related_logs: Mapped[List[LogEntry]] = relationship(
        "LogEntry",
        secondary="incident_logs",
        back_populates="incidents",
        lazy="selectin",
    )

    # Database constraints and indexes
    __table_args__ = (
        Index("idx_incident_status_severity", "status", "severity"),
        Index("idx_incident_created_at", "created_at"),
        Index("idx_incident_assigned_to", "assigned_to"),
        CheckConstraint(
            "priority_score >= 0 AND priority_score <= 1",
            name="check_priority_score_range",
        ),
        {"comment": "System incidents with full lifecycle tracking"},
    )

    def __repr__(self) -> str:
        return (
            f"<Incident(id={self.id}, severity={self.severity}, status={self.status})>"
        )


class MLModel(Base):
    """ML model registry for tracking trained models and their lifecycle.

    Supports model versioning, performance tracking, and deployment
    status management for production ML systems.
    """

    __tablename__ = "ml_models"

    # Primary key and identification
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique model identifier",
    )

    # Model identification
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, comment="Model name/identifier"
    )
    version: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Model version string"
    )
    model_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of ML model (classifier, detector, etc.)",
    )

    # Model status and lifecycle
    status: Mapped[ModelStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ModelStatus.TRAINING,
        index=True,
        comment="Current model status",
    )

    # Timestamp tracking
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

    # Training information
    training_dataset_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Size of training dataset"
    )
    training_duration_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Training duration in minutes"
    )

    # Model artifacts and configuration
    model_path: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Path to model file/artifact"
    )
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Model configuration parameters"
    )
    extra_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional model extra_data"
    )

    # Deployment information
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether model is currently active",
    )
    deployment_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Deployment configuration"
    )

    # Database constraints and indexes
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_name_version"),
        Index("idx_model_type_status", "model_type", "status"),
        Index("idx_model_created_at", "created_at"),
        Index("idx_model_is_active", "is_active"),
        CheckConstraint("accuracy >= 0 AND accuracy <= 1", name="check_accuracy_range"),
        CheckConstraint(
            "precision >= 0 AND precision <= 1", name="check_precision_range"
        ),
        CheckConstraint("recall >= 0 AND recall <= 1", name="check_recall_range"),
        CheckConstraint("f1_score >= 0 AND f1_score <= 1", name="check_f1_score_range"),
        {"comment": "ML model registry with performance tracking"},
    )

    def __repr__(self) -> str:
        return (
            f"<MLModel(name={self.name}, version={self.version}, status={self.status})>"
        )


# Association table for many-to-many relationship between incidents and logs
from sqlalchemy import Column, Table

incident_logs = Table(
    "incident_logs",
    Base.metadata,
    Column(
        "incident_id", UUID(as_uuid=True), ForeignKey("incidents.id"), primary_key=True
    ),
    Column(
        "log_id", UUID(as_uuid=True), ForeignKey("log_entries.id"), primary_key=True
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Association creation timestamp",
    ),
    Index("idx_incident_logs_incident", "incident_id"),
    Index("idx_incident_logs_log", "log_id"),
    comment="Association between incidents and related log entries",
)


# Export all models for easy importing
__all__ = [
    "Base",
    "LogLevel",
    "IncidentSeverity",
    "IncidentStatus",
    "ModelStatus",
    "LogEntry",
    "Incident",
    "MLModel",
    "incident_logs",
]
