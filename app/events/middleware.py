"""Event middleware components."""


class AuditMiddleware:
    """Audit middleware for event processing."""

    async def process_event(self, event, next_middleware):
        """Process event with audit logging."""
        await next_middleware(event)


class LoggingMiddleware:
    """Logging middleware for event processing."""

    async def process_event(self, event, next_middleware):
        """Process event with logging."""
        await next_middleware(event)


class MetricsMiddleware:
    """Metrics middleware for event processing."""

    async def process_event(self, event, next_middleware):
        """Process event with metrics collection."""
        await next_middleware(event)
