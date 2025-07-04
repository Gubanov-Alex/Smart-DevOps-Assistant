"""Base Pydantic schemas for common data structures."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""

    created_at: datetime = Field(
        description="Creation timestamp", examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp",
        examples=["2024-01-15T12:45:00Z"],
    )


class PaginationParams(BaseSchema):
    """Pagination parameters for list endpoints."""

    page: int = Field(
        default=1, ge=1, description="Page number (1-based)", examples=[1, 2, 5]
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
        examples=[10, 20, 50],
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseSchema):
    """Generic paginated response wrapper."""

    items: List[Any] = Field(description="List of items")
    total: int = Field(ge=0, description="Total number of items")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    @classmethod
    def create(
        cls, items: List[Any], total: int, pagination: PaginationParams
    ) -> "PaginatedResponse":
        """Create paginated response from items and pagination params."""
        pages = (total + pagination.page_size - 1) // pagination.page_size

        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
            has_next=pagination.page < pages,
            has_prev=pagination.page > 1,
        )


class HealthStatus(BaseSchema):
    """Health check status response."""

    status: str = Field(
        description="Overall health status",
        examples=["healthy", "degraded", "unhealthy"],
    )
    timestamp: datetime = Field(description="Health check timestamp")
    version: str = Field(description="Application version")
    uptime_seconds: float = Field(ge=0, description="Application uptime in seconds")
    environment: str = Field(description="Environment name")

    # Service dependencies status
    database: Dict[str, Any] = Field(description="Database health status")
    redis: Dict[str, Any] = Field(description="Redis health status")
    ml_models: Dict[str, Any] = Field(description="ML models status")

    # Performance metrics
    memory_usage_mb: float = Field(ge=0, description="Memory usage in MB")
    cpu_usage_percent: float = Field(ge=0, le=100, description="CPU usage percentage")


class ErrorDetail(BaseSchema):
    """Error detail information."""

    field: Optional[str] = Field(
        default=None, description="Field that caused the error"
    )
    message: str = Field(description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")


class ErrorResponse(BaseSchema):
    """Standard error response format."""

    error: str = Field(description="Error type/code")
    message: str = Field(description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(
        default=None, description="Detailed error information"
    )
    timestamp: datetime = Field(description="Error timestamp")
    request_id: Optional[str] = Field(
        default=None, description="Request ID for tracking"
    )


class IDResponse(BaseSchema):
    """Response containing only an ID (for create operations)."""

    id: UUID = Field(description="Created resource ID")
    message: str = Field(default="Resource created successfully")


class BulkOperationResponse(BaseSchema):
    """Response for bulk operations."""

    processed: int = Field(ge=0, description="Number of processed items")
    successful: int = Field(ge=0, description="Number of successful operations")
    failed: int = Field(ge=0, description="Number of failed operations")
    errors: List[ErrorDetail] = Field(
        default_factory=list, description="Details of failed operations"
    )


class FilterParams(BaseSchema):
    """Common filtering parameters."""

    search: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Search query string",
        examples=["error log", "database"],
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Filter from date (inclusive)",
        examples=["2024-01-15T00:00:00Z"],
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="Filter to date (inclusive)",
        examples=["2024-01-15T23:59:59Z"],
    )
    is_active: Optional[bool] = Field(
        default=None, description="Filter by active status"
    )


class SortParams(BaseSchema):
    """Common sorting parameters."""

    sort_by: str = Field(
        default="created_at",
        description="Field to sort by",
        examples=["created_at", "name", "status"],
    )
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order",
        examples=["asc", "desc"],
    )
