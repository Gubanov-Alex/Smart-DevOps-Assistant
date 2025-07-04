"""Health check response schemas."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field

from app.schemas.common.base import BaseSchema


class ServiceHealth(BaseSchema):
    """Individual service health status."""

    status: str = Field(
        description="Service status", examples=["healthy", "degraded", "unhealthy"]
    )
    response_time_ms: Optional[float] = Field(
        default=None, ge=0, description="Service response time in milliseconds"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional service-specific details"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if service is unhealthy"
    )


class DatabaseHealth(ServiceHealth):
    """Database-specific health information."""

    pool_size: Optional[int] = Field(
        default=None, ge=0, description="Connection pool size"
    )
    active_connections: Optional[int] = Field(
        default=None, ge=0, description="Number of active connections"
    )
    version: Optional[str] = Field(default=None, description="Database version")


class RedisHealth(ServiceHealth):
    """Redis-specific health information."""

    memory_usage_mb: Optional[float] = Field(
        default=None, ge=0, description="Redis memory usage in MB"
    )
    connected_clients: Optional[int] = Field(
        default=None, ge=0, description="Number of connected clients"
    )
    keyspace_hits: Optional[int] = Field(
        default=None, ge=0, description="Keyspace hits counter"
    )


class MLModelsHealth(ServiceHealth):
    """ML models health information."""

    loaded_models: Optional[int] = Field(
        default=None, ge=0, description="Number of loaded models"
    )
    models_status: Optional[Dict[str, str]] = Field(
        default=None, description="Individual model statuses"
    )
    last_prediction_at: Optional[datetime] = Field(
        default=None, description="Timestamp of last prediction"
    )


class SystemMetrics(BaseSchema):
    """System performance metrics."""

    memory_usage_mb: float = Field(ge=0, description="Current memory usage in MB")
    memory_total_mb: float = Field(ge=0, description="Total available memory in MB")
    memory_percent: float = Field(ge=0, le=100, description="Memory usage percentage")
    cpu_usage_percent: float = Field(ge=0, le=100, description="CPU usage percentage")
    disk_usage_gb: float = Field(ge=0, description="Disk usage in GB")
    disk_total_gb: float = Field(ge=0, description="Total disk space in GB")
    disk_percent: float = Field(ge=0, le=100, description="Disk usage percentage")


class HealthCheckResponse(BaseSchema):
    """Comprehensive health check response."""

    status: str = Field(
        description="Overall system health status",
        examples=["healthy", "degraded", "unhealthy"],
    )
    timestamp: datetime = Field(description="Health check timestamp")
    version: str = Field(description="Application version", examples=["0.1.0", "1.2.3"])
    environment: str = Field(
        description="Environment name",
        examples=["development", "staging", "production"],
    )
    uptime_seconds: float = Field(ge=0, description="Application uptime in seconds")

    # Service dependencies
    database: DatabaseHealth = Field(description="Database health status")
    redis: RedisHealth = Field(description="Redis health status")
    ml_models: MLModelsHealth = Field(description="ML models health status")

    # System metrics
    system: SystemMetrics = Field(description="System performance metrics")

    # Request information
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")


class SimpleHealthResponse(BaseSchema):
    """Simplified health check for load balancers."""

    status: str = Field(description="Simple health status", examples=["ok", "error"])
    timestamp: datetime = Field(description="Check timestamp")
