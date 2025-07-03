"""Complete tests for Event Bus to improve coverage."""

import asyncio
from datetime import datetime

import pytest

from app.events.base import DomainEvent
from app.events.event_bus import EventBus, EventSubscription
from app.events.log_events import AnomalyDetected, LogEntryCreated
from app.events.middleware import AuditMiddleware, LoggingMiddleware, MetricsMiddleware


class TestEvent(DomainEvent):
    """Test event for testing purposes."""

    def __init__(self, test_data: str):
        super().__init__(event_type="test.event", data={"test_data": test_data})


class TestEventBus:
    """Comprehensive tests for EventBus."""

    def test_event_bus_initialization(self):
        """Test EventBus initialization."""
        bus = EventBus()
        assert isinstance(bus.subscriptions, dict)
        assert isinstance(bus.middleware, list)
        assert len(bus.subscriptions) == 0
        assert len(bus.middleware) == 0

    def test_event_bus_with_middleware(self):
        """Test EventBus initialization with middleware."""
        middleware = [AuditMiddleware(), LoggingMiddleware()]
        bus = EventBus(middleware=middleware)

        assert len(bus.middleware) == 2
        assert isinstance(bus.middleware[0], AuditMiddleware)
        assert isinstance(bus.middleware[1], LoggingMiddleware)

    def test_subscribe_handler(self):
        """Test subscribing event handlers."""
        bus = EventBus()

        async def test_handler(event: TestEvent):
            pass

        subscription = bus.subscribe("test.event", test_handler)

        assert isinstance(subscription, EventSubscription)
        assert subscription.event_type == "test.event"
        assert subscription.handler == test_handler
        assert "test.event" in bus.subscriptions
        assert subscription in bus.subscriptions["test.event"]

    def test_subscribe_multiple_handlers_same_event(self):
        """Test subscribing multiple handlers to the same event."""
        bus = EventBus()

        async def handler1(event: TestEvent):
            pass

        async def handler2(event: TestEvent):
            pass

        sub1 = bus.subscribe("test.event", handler1)
        sub2 = bus.subscribe("test.event", handler2)

        assert len(bus.subscriptions["test.event"]) == 2
        assert sub1 in bus.subscriptions["test.event"]
        assert sub2 in bus.subscriptions["test.event"]

    def test_subscribe_handlers_different_events(self):
        """Test subscribing handlers to different events."""
        bus = EventBus()

        async def handler1(event: TestEvent):
            pass

        async def handler2(event: TestEvent):
            pass

        bus.subscribe("test.event1", handler1)
        bus.subscribe("test.event2", handler2)

        assert len(bus.subscriptions) == 2
        assert "test.event1" in bus.subscriptions
        assert "test.event2" in bus.subscriptions

    def test_unsubscribe_handler(self):
        """Test unsubscribing event handlers."""
        bus = EventBus()

        async def test_handler(event: TestEvent):
            pass

        subscription = bus.subscribe("test.event", test_handler)
        assert "test.event" in bus.subscriptions

        bus.unsubscribe(subscription)
        assert len(bus.subscriptions.get("test.event", [])) == 0

    def test_unsubscribe_one_of_multiple_handlers(self):
        """Test unsubscribing one handler when multiple exist."""
        bus = EventBus()

        async def handler1(event: TestEvent):
            pass

        async def handler2(event: TestEvent):
            pass

        sub1 = bus.subscribe("test.event", handler1)
        sub2 = bus.subscribe("test.event", handler2)

        bus.unsubscribe(sub1)

        assert len(bus.subscriptions["test.event"]) == 1
        assert sub2 in bus.subscriptions["test.event"]
        assert sub1 not in bus.subscriptions["test.event"]

    def test_unsubscribe_nonexistent_subscription(self):
        """Test unsubscribing a subscription that doesn't exist."""
        bus = EventBus()

        async def test_handler(event: TestEvent):
            pass

        fake_subscription = EventSubscription("fake.event", test_handler, "fake_id")

        # Should not raise an error
        bus.unsubscribe(fake_subscription)

    @pytest.mark.asyncio
    async def test_publish_event_no_handlers(self):
        """Test publishing event with no handlers."""
        bus = EventBus()
        event = TestEvent("test_data")

        # Should not raise an error
        await bus.publish(event)

    @pytest.mark.asyncio
    async def test_publish_event_with_handlers(self):
        """Test publishing event with handlers."""
        bus = EventBus()
        handler_called = False
        received_event = None

        async def test_handler(event: TestEvent):
            nonlocal handler_called, received_event
            handler_called = True
            received_event = event

        bus.subscribe("test.event", test_handler)
        event = TestEvent("test_data")

        await bus.publish(event)

        assert handler_called
        assert received_event == event

    @pytest.mark.asyncio
    async def test_publish_event_multiple_handlers(self):
        """Test publishing event to multiple handlers."""
        bus = EventBus()
        handler1_called = False
        handler2_called = False

        async def handler1(event: TestEvent):
            nonlocal handler1_called
            handler1_called = True

        async def handler2(event: TestEvent):
            nonlocal handler2_called
            handler2_called = True

        bus.subscribe("test.event", handler1)
        bus.subscribe("test.event", handler2)

        event = TestEvent("test_data")
        await bus.publish(event)

        assert handler1_called
        assert handler2_called

    @pytest.mark.asyncio
    async def test_publish_with_middleware(self):
        """Test publishing with middleware."""
        middleware_called = []

        class TestMiddleware:
            async def process_event(self, event: DomainEvent, next_middleware):
                middleware_called.append("before")
                await next_middleware(event)
                middleware_called.append("after")

        bus = EventBus(middleware=[TestMiddleware()])

        handler_called = False

        async def test_handler(event: TestEvent):
            nonlocal handler_called
            handler_called = True

        bus.subscribe("test.event", test_handler)
        event = TestEvent("test_data")

        await bus.publish(event)

        assert handler_called
        assert middleware_called == ["before", "after"]

    @pytest.mark.asyncio
    async def test_publish_with_multiple_middleware(self):
        """Test publishing with multiple middleware."""
        execution_order = []

        class Middleware1:
            async def process_event(self, event: DomainEvent, next_middleware):
                execution_order.append("middleware1_before")
                await next_middleware(event)
                execution_order.append("middleware1_after")

        class Middleware2:
            async def process_event(self, event: DomainEvent, next_middleware):
                execution_order.append("middleware2_before")
                await next_middleware(event)
                execution_order.append("middleware2_after")

        bus = EventBus(middleware=[Middleware1(), Middleware2()])

        async def test_handler(event: TestEvent):
            execution_order.append("handler")

        bus.subscribe("test.event", test_handler)
        event = TestEvent("test_data")

        await bus.publish(event)

        expected_order = [
            "middleware1_before",
            "middleware2_before",
            "handler",
            "middleware2_after",
            "middleware1_after",
        ]
        assert execution_order == expected_order

    @pytest.mark.asyncio
    async def test_handler_exception_handling(self):
        """Test handling exceptions in event handlers."""
        bus = EventBus()

        async def failing_handler(event: TestEvent):
            raise ValueError("Handler failed")

        async def working_handler(event: TestEvent):
            working_handler.called = True

        working_handler.called = False

        bus.subscribe("test.event", failing_handler)
        bus.subscribe("test.event", working_handler)

        event = TestEvent("test_data")

        # Should not raise, but should log the error
        await bus.publish(event)

        # Working handler should still be called
        assert working_handler.called

    @pytest.mark.asyncio
    async def test_middleware_exception_handling(self):
        """Test handling exceptions in middleware."""

        class FailingMiddleware:
            async def process_event(self, event: DomainEvent, next_middleware):
                raise RuntimeError("Middleware failed")

        bus = EventBus(middleware=[FailingMiddleware()])

        handler_called = False

        async def test_handler(event: TestEvent):
            nonlocal handler_called
            handler_called = True

        bus.subscribe("test.event", test_handler)
        event = TestEvent("test_data")

        # Should handle middleware exception gracefully
        await bus.publish(event)

        # Handler should not be called due to middleware failure
        assert not handler_called

    @pytest.mark.asyncio
    async def test_concurrent_event_publishing(self):
        """Test concurrent event publishing."""
        bus = EventBus()
        results = []

        async def test_handler(event: TestEvent):
            await asyncio.sleep(0.01)  # Simulate async work
            results.append(event.data["test_data"])

        bus.subscribe("test.event", test_handler)

        events = [TestEvent(f"data_{i}") for i in range(5)]

        # Publish all events concurrently
        await asyncio.gather(*[bus.publish(event) for event in events])

        assert len(results) == 5
        assert all(f"data_{i}" in results for i in range(5))

    def test_subscription_id_uniqueness(self):
        """Test that subscription IDs are unique."""
        bus = EventBus()

        async def handler1(event: TestEvent):
            pass

        async def handler2(event: TestEvent):
            pass

        sub1 = bus.subscribe("test.event", handler1)
        sub2 = bus.subscribe("test.event", handler2)

        assert sub1.subscription_id != sub2.subscription_id

    def test_get_subscriptions(self):
        """Test getting subscriptions for event type."""
        bus = EventBus()

        async def test_handler(event: TestEvent):
            pass

        # No subscriptions initially
        subs = bus.get_subscriptions("test.event")
        assert len(subs) == 0

        # Add subscription
        bus.subscribe("test.event", test_handler)
        subs = bus.get_subscriptions("test.event")
        assert len(subs) == 1

    def test_clear_subscriptions(self):
        """Test clearing all subscriptions."""
        bus = EventBus()

        async def handler1(event: TestEvent):
            pass

        async def handler2(event: TestEvent):
            pass

        bus.subscribe("test.event1", handler1)
        bus.subscribe("test.event2", handler2)

        assert len(bus.subscriptions) == 2

        bus.clear_subscriptions()

        assert len(bus.subscriptions) == 0

    def test_add_middleware_after_initialization(self):
        """Test adding middleware after bus initialization."""
        bus = EventBus()

        middleware = AuditMiddleware()
        bus.add_middleware(middleware)

        assert middleware in bus.middleware

    def test_remove_middleware(self):
        """Test removing middleware."""
        middleware = AuditMiddleware()
        bus = EventBus(middleware=[middleware])

        assert middleware in bus.middleware

        bus.remove_middleware(middleware)

        assert middleware not in bus.middleware

    @pytest.mark.asyncio
    async def test_event_bus_shutdown(self):
        """Test event bus shutdown."""
        bus = EventBus()

        async def test_handler(event: TestEvent):
            pass

        bus.subscribe("test.event", test_handler)

        # Should cleanup resources
        await bus.shutdown()

        # Subscriptions should be cleared
        assert len(bus.subscriptions) == 0

    @pytest.mark.asyncio
    async def test_real_domain_events(self):
        """Test with real domain events."""
        bus = EventBus()

        received_events = []

        async def log_handler(event: LogEntryCreated):
            received_events.append(event)

        async def anomaly_handler(event: AnomalyDetected):
            received_events.append(event)

        bus.subscribe("log.entry_created", log_handler)
        bus.subscribe("anomaly.detected", anomaly_handler)

        # Create real events
        log_event = LogEntryCreated(
            log_id="123",
            message="Test log",
            level="INFO",
            timestamp=datetime.now(),
            source="test",
        )

        anomaly_event = AnomalyDetected(
            log_id="456", anomaly_score=0.8, threshold=0.5, detected_at=datetime.now()
        )

        await bus.publish(log_event)
        await bus.publish(anomaly_event)

        assert len(received_events) == 2
        assert any(isinstance(e, LogEntryCreated) for e in received_events)
        assert any(isinstance(e, AnomalyDetected) for e in received_events)


class TestEventSubscription:
    """Tests for EventSubscription."""

    def test_subscription_creation(self):
        """Test EventSubscription creation."""

        async def test_handler(event: TestEvent):
            pass

        subscription = EventSubscription("test.event", test_handler)

        assert subscription.event_type == "test.event"
        assert subscription.handler == test_handler
        assert subscription.subscription_id is not None
        assert isinstance(subscription.subscription_id, str)

    def test_subscription_equality(self):
        """Test EventSubscription equality."""

        async def test_handler(event: TestEvent):
            pass

        sub1 = EventSubscription("test.event", test_handler, "id1")
        sub2 = EventSubscription("test.event", test_handler, "id1")
        sub3 = EventSubscription("test.event", test_handler, "id2")

        assert sub1 == sub2
        assert sub1 != sub3

    def test_subscription_hash(self):
        """Test EventSubscription hashing."""

        async def test_handler(event: TestEvent):
            pass

        sub1 = EventSubscription("test.event", test_handler, "id1")
        sub2 = EventSubscription("test.event", test_handler, "id1")

        # Should be able to use in sets/dicts
        subscription_set = {sub1, sub2}
        assert len(subscription_set) == 1  # Should be deduplicated

    def test_subscription_string_representation(self):
        """Test EventSubscription string representation."""

        async def test_handler(event: TestEvent):
            pass

        subscription = EventSubscription("test.event", test_handler, "test_id")
        str_repr = str(subscription)

        assert "test.event" in str_repr
        assert "test_id" in str_repr


class TestEventBusIntegration:
    """Integration tests for EventBus with middleware."""

    @pytest.mark.asyncio
    async def test_full_middleware_stack(self):
        """Test EventBus with full middleware stack."""
        audit_middleware = AuditMiddleware()
        logging_middleware = LoggingMiddleware()
        metrics_middleware = MetricsMiddleware()

        bus = EventBus(
            middleware=[audit_middleware, logging_middleware, metrics_middleware]
        )

        events_processed = []

        async def test_handler(event: TestEvent):
            events_processed.append(event)

        bus.subscribe("test.event", test_handler)

        event = TestEvent("integration_test")
        await bus.publish(event)

        assert len(events_processed) == 1
        assert events_processed[0] == event

    @pytest.mark.asyncio
    async def test_high_volume_event_processing(self):
        """Test EventBus performance with high volume of events."""
        bus = EventBus()

        processed_count = 0

        async def counting_handler(event: TestEvent):
            nonlocal processed_count
            processed_count += 1

        bus.subscribe("test.event", counting_handler)

        # Generate many events
        events = [TestEvent(f"event_{i}") for i in range(100)]

        # Process all events
        await asyncio.gather(*[bus.publish(event) for event in events])

        assert processed_count == 100
