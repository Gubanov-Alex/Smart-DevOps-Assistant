"""Event middleware for cross-cutting concerns."""

import time

import structlog

from app.events.base import DomainEvent

logger = structlog.get_logger()


async def logging_middleware(event: DomainEvent) -> DomainEvent:
    """
    Middleware for event logging.

    Interview talking point: Cross-cutting concerns with middleware
    """
    logger.info(
        "Event processed",
        event_type=event.event_type,
        event_id=str(event.event_id),
        aggregate_id=str(event.aggregate_id),
        occurred_at=event.occurred_at.isoformat(),
    )
    return event


async def metrics_middleware(event: DomainEvent) -> DomainEvent:
    """Middleware for event metrics collection."""
    start_time = time.time()

    # Add processing timestamp to metadata
    enhanced_metadata = {
        **event.metadata,
        "processing_started_at": time.time(),
        "middleware_applied": ["logging", "metrics"],
    }

    # Create new event with enhanced metadata (immutable pattern)
    from dataclasses import replace

    enhanced_event = replace(event, metadata=enhanced_metadata)

    processing_time = (time.time() - start_time) * 1000
    logger.debug(
        "Event middleware processing completed",
        event_type=event.event_type,
        processing_time_ms=processing_time,
    )

    return enhanced_event


async def audit_middleware(event: DomainEvent) -> DomainEvent:
    """Middleware for event auditing."""
    audit_data = {
        "event_id": str(event.event_id),
        "event_type": event.event_type,
        "aggregate_id": str(event.aggregate_id),
        "timestamp": event.occurred_at.isoformat(),
        "version": event.version,
    }

    # TODO: Store in audit log
    # await audit_service.log_event(audit_data)

    logger.debug("Event audited", **audit_data)
    return event
