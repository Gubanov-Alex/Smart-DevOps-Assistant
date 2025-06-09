"""Event bus implementation for domain events."""

import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List, Type

import structlog

from app.events.base import DomainEvent

logger = structlog.get_logger()


class EventBus:
    """
    In-memory event bus with async support.

    Interview talking point: Event-driven architecture implementation
    """

    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[Callable[[DomainEvent], Any]]] = defaultdict(
            list
        )
        self._middleware: List[Callable[[DomainEvent], DomainEvent]] = []
        self._dead_letter_queue: List[DomainEvent] = []

    def subscribe(
        self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], Any]
    ) -> None:
        """Subscribe handler to an event type."""
        self._handlers[event_type].append(handler)
        logger.info(
            "Handler subscribed",
            event_type=event_type.__name__,
            handler=handler.__name__,
        )

    def add_middleware(self, middleware: Callable[[DomainEvent], DomainEvent]) -> None:
        """Add middleware for event processing."""
        self._middleware.append(middleware)

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish event to all registered handlers.

        Interview talking point: Async event processing with error handling
        """
        try:
            # Apply middleware
            processed_event = event
            for middleware in self._middleware:
                processed_event = await self._apply_middleware(middleware, processed_event)

            # Get handlers for this event type
            handlers = self._handlers.get(type(processed_event), [])

            if not handlers:
                logger.debug("No handlers found", event_type=type(processed_event).__name__)
                return

            # Execute handlers concurrently
            tasks = []
            for handler in handlers:
                task = asyncio.create_task(self._execute_handler(handler, processed_event))
                tasks.append(task)

            # Wait for all handlers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "Handler failed",
                        handler=handlers[i].__name__,
                        error=str(result),
                        event_type=type(processed_event).__name__,
                    )

            logger.info(
                "Event published",
                event_type=type(processed_event).__name__,
                handlers_count=len(handlers),
                event_id=str(processed_event.event_id),
            )

        except Exception as e:
            logger.error(
                "Event publishing failed",
                event_type=type(event).__name__,
                error=str(e),
            )
            self._dead_letter_queue.append(event)

    async def _apply_middleware(self, middleware: Callable, event: DomainEvent) -> DomainEvent:
        """Apply middleware to event."""
        try:
            if asyncio.iscoroutinefunction(middleware):
                return await middleware(event)
            else:
                return middleware(event)
        except Exception as e:
            logger.error(
                "Middleware failed",
                middleware=middleware.__name__,
                error=str(e),
            )
            return event  # Return the original event if middleware fails

    async def _execute_handler(self, handler: Callable, event: DomainEvent) -> None:
        """Execute event handler with error handling."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(
                "Event handler failed",
                handler=handler.__name__,
                error=str(e),
                event_id=str(event.event_id),
            )
            raise  # Re-raise to be caught by gather()

    def get_dead_letter_events(self) -> List[DomainEvent]:
        """Get events that failed to process."""
        return self._dead_letter_queue.copy()

    def clear_dead_letter_queue(self) -> None:
        """Clear dead letter queue."""
        self._dead_letter_queue.clear()
