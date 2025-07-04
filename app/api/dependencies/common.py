"""Common API dependencies for request processing."""

import uuid
from typing import Optional

from fastapi import Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.schemas.common.base import FilterParams, PaginationParams, SortParams


async def get_database() -> AsyncSession:
    """Get database session dependency.

    Yields:
        Database session for request processing
    """
    async for session in get_db_session():
        yield session


def get_request_id(
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-ID")
) -> str:
    """Get or generate request ID for tracking.

    Args:
        x_request_id: Optional request ID from header

    Returns:
        Request ID for tracking
    """
    if x_request_id:
        try:
            # Validate UUID format
            uuid.UUID(x_request_id)
            return x_request_id
        except ValueError:
            # If invalid UUID, generate new one
            pass

    return str(uuid.uuid4())


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    """Get pagination parameters from query params.

    Args:
        page: Page number (1-based)
        page_size: Number of items per page

    Returns:
        Pagination parameters
    """
    return PaginationParams(page=page, page_size=page_size)


def get_filter_params(
    search: Optional[str] = Query(
        None, max_length=200, description="Search query string"
    ),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
) -> FilterParams:
    """Get filtering parameters from query params.

    Args:
        search: Search query string
        date_from: Start date filter
        date_to: End date filter
        is_active: Active status filter

    Returns:
        Filter parameters

    Raises:
        HTTPException: If date format is invalid
    """
    try:
        return FilterParams(
            search=search,
            date_from=date_from,
            date_to=date_to,
            is_active=is_active,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid filter parameters: {e}")


def get_sort_params(
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query(
        "desc", pattern="^(asc|desc)$", description="Sort order (asc or desc)"
    ),
) -> SortParams:
    """Get sorting parameters from query params.

    Args:
        sort_by: Field to sort by
        sort_order: Sort direction

    Returns:
        Sort parameters
    """
    return SortParams(sort_by=sort_by, sort_order=sort_order)


def validate_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")
) -> Optional[str]:
    """Validate API key if provided.

    Args:
        x_api_key: Optional API key from header

    Returns:
        Validated API key or None

    Raises:
        HTTPException: If API key is invalid
    """
    if x_api_key:
        # TODO: Implement actual API key validation
        # For now, just return the key if provided
        if len(x_api_key) < 10:
            raise HTTPException(status_code=401, detail="Invalid API key format")

    return x_api_key


def get_user_agent(
    user_agent: Optional[str] = Header(default=None, alias="User-Agent")
) -> Optional[str]:
    """Get user agent from request headers.

    Args:
        user_agent: User agent string

    Returns:
        User agent string or None
    """
    return user_agent


def validate_content_type(
    content_type: Optional[str] = Header(default=None, alias="Content-Type")
) -> Optional[str]:
    """Validate content type for POST/PUT requests.

    Args:
        content_type: Content type header

    Returns:
        Validated content type

    Raises:
        HTTPException: If content type is unsupported
    """
    if content_type:
        supported_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]

        # Extract main content type (ignore charset, boundary, etc.)
        main_type = content_type.split(";")[0].strip().lower()

        if main_type not in supported_types:
            raise HTTPException(
                status_code=415, detail=f"Unsupported content type: {main_type}"
            )

    return content_type


class RateLimitDependency:
    """Rate limiting dependency (placeholder for future implementation)."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute

    async def __call__(self, request_id: str = get_request_id) -> bool:
        """Check rate limit for request.

        Args:
            request_id: Request ID for tracking

        Returns:
            True if request is allowed

        Raises:
            HTTPException: If rate limit exceeded
        """
        # TODO: Implement actual rate limiting with Redis
        # For now, always allow requests
        return True


# Common dependency instances
standard_rate_limit = RateLimitDependency(requests_per_minute=60)
strict_rate_limit = RateLimitDependency(requests_per_minute=10)
