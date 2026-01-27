"""
EVENT BUS: System-Wide Event Routing with Backpressure
═══════════════════════════════════════════════════════════════════════════════

Manages asynchronous events across all systems with flow control.

Features:
- Pub/sub event routing
- Backpressure when queues fill
- Event persistence for replay
- Metrics per event type

Updated: Jan 2026
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """System event types"""
    # Discovery events
    OPPORTUNITY_DISCOVERED = "opportunity.discovered"
    OPPORTUNITY_ENRICHED = "opportunity.enriched"
    OPPORTUNITY_ROUTED = "opportunity.routed"

    # Contract events
    SOW_GENERATED = "sow.generated"
    CONTRACT_CREATED = "contract.created"
    CONTRACT_SIGNED = "contract.signed"

    # Execution events
    PLAN_CREATED = "plan.created"
    STEP_STARTED = "step.started"
    STEP_COMPLETED = "step.completed"
    STEP_FAILED = "step.failed"

    # Milestone events
    MILESTONE_FUNDED = "milestone.funded"
    MILESTONE_COMPLETED = "milestone.completed"
    MILESTONE_RELEASED = "milestone.released"

    # QA events
    QA_GATE_PASSED = "qa.gate.passed"
    QA_GATE_FAILED = "qa.gate.failed"

    # Workforce events
    TASK_DISPATCHED = "task.dispatched"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # Proof events
    PROOF_CREATED = "proof.created"
    PROOF_VERIFIED = "proof.verified"

    # Growth events
    UPSELL_IDENTIFIED = "growth.upsell.identified"
    REFERRAL_RECEIVED = "growth.referral.received"

    # System events
    SYSTEM_HEALTH_CHECK = "system.health"
    BUDGET_THRESHOLD = "budget.threshold"
    SLO_BREACH = "slo.breach"


@dataclass
class Event:
    """An event in the system"""
    id: str
    type: EventType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "system"
    processed: bool = False
    retries: int = 0


@dataclass
class Subscription:
    """A subscription to events"""
    id: str
    event_types: List[EventType]
    handler: Callable[[Event], Awaitable[None]]
    active: bool = True
    events_received: int = 0
    events_processed: int = 0
    errors: int = 0


class EventBus:
    """
    Central event bus with backpressure.

    Features:
    - Async pub/sub
    - Queue-based with configurable limits
    - Backpressure when queues fill
    - Dead letter queue for failed events
    """

    def __init__(self, max_queue_size: int = 10000, max_dlq_size: int = 1000):
        self.max_queue_size = max_queue_size
        self.max_dlq_size = max_dlq_size

        self.queue: deque = deque(maxlen=max_queue_size)
        self.dlq: deque = deque(maxlen=max_dlq_size)  # Dead letter queue
        self.subscriptions: Dict[str, Subscription] = {}
        self.event_counter = 0

        self.stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'events_dropped': 0,
            'backpressure_events': 0,
            'dlq_size': 0,
        }

        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the event processor"""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")

    async def stop(self):
        """Stop the event processor"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("Event bus stopped")

    def subscribe(
        self,
        subscription_id: str,
        event_types: List[EventType],
        handler: Callable[[Event], Awaitable[None]],
    ) -> Subscription:
        """
        Subscribe to event types.

        Args:
            subscription_id: Unique subscription ID
            event_types: List of event types to subscribe to
            handler: Async function to handle events

        Returns:
            Subscription object
        """
        sub = Subscription(
            id=subscription_id,
            event_types=event_types,
            handler=handler,
        )
        self.subscriptions[subscription_id] = sub
        logger.info(f"Subscription {subscription_id} created for {len(event_types)} event types")
        return sub

    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from events"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id].active = False
            del self.subscriptions[subscription_id]

    async def publish(self, event_type: EventType, data: Dict[str, Any], source: str = "system") -> Optional[Event]:
        """
        Publish an event.

        Args:
            event_type: Type of event
            data: Event data
            source: Source system

        Returns:
            Event if queued, None if dropped due to backpressure
        """
        # Check backpressure
        if len(self.queue) >= self.max_queue_size:
            self.stats['backpressure_events'] += 1
            self.stats['events_dropped'] += 1
            logger.warning(f"Event dropped due to backpressure: {event_type.value}")
            return None

        self.event_counter += 1
        event = Event(
            id=f"evt_{self.event_counter}",
            type=event_type,
            data=data,
            source=source,
        )

        self.queue.append(event)
        self.stats['events_published'] += 1

        logger.debug(f"Event published: {event_type.value}")

        return event

    async def _process_events(self):
        """Background event processor"""
        while self._running:
            try:
                if not self.queue:
                    await asyncio.sleep(0.01)
                    continue

                event = self.queue.popleft()
                await self._dispatch_event(event)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event processor error: {e}")
                await asyncio.sleep(0.1)

    async def _dispatch_event(self, event: Event):
        """Dispatch event to subscribers"""
        dispatched = False

        for sub in self.subscriptions.values():
            if not sub.active:
                continue

            if event.type in sub.event_types:
                sub.events_received += 1
                try:
                    await sub.handler(event)
                    sub.events_processed += 1
                    dispatched = True
                except Exception as e:
                    sub.errors += 1
                    logger.warning(f"Subscriber {sub.id} error: {e}")
                    event.retries += 1

                    if event.retries >= 3:
                        self._move_to_dlq(event)

        if dispatched:
            event.processed = True
            self.stats['events_processed'] += 1
        elif event.retries >= 3:
            self.stats['events_failed'] += 1

    def _move_to_dlq(self, event: Event):
        """Move failed event to dead letter queue"""
        self.dlq.append(event)
        self.stats['dlq_size'] = len(self.dlq)
        logger.warning(f"Event moved to DLQ: {event.id}")

    def get_queue_depth(self) -> int:
        """Get current queue depth"""
        return len(self.queue)

    def get_backpressure_status(self) -> Dict[str, Any]:
        """Get backpressure status"""
        queue_pct = len(self.queue) / self.max_queue_size * 100 if self.max_queue_size > 0 else 0

        return {
            'queue_depth': len(self.queue),
            'queue_capacity': self.max_queue_size,
            'queue_utilization_pct': round(queue_pct, 1),
            'backpressure_active': queue_pct > 80,
            'dlq_depth': len(self.dlq),
            'events_dropped': self.stats['events_dropped'],
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus stats"""
        return {
            **self.stats,
            'queue_depth': len(self.queue),
            'subscriptions': len(self.subscriptions),
            'running': self._running,
            'backpressure': self.get_backpressure_status(),
        }

    def get_subscription_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get per-subscription stats"""
        return {
            sub_id: {
                'event_types': [et.value for et in sub.event_types],
                'active': sub.active,
                'events_received': sub.events_received,
                'events_processed': sub.events_processed,
                'errors': sub.errors,
            }
            for sub_id, sub in self.subscriptions.items()
        }


# Global instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create event bus singleton"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def publish_event(event_type: EventType, data: Dict[str, Any], source: str = "system") -> Optional[Event]:
    """Convenience function to publish event"""
    return await get_event_bus().publish(event_type, data, source)


def subscribe(subscription_id: str, event_types: List[EventType], handler: Callable) -> Subscription:
    """Convenience function to subscribe"""
    return get_event_bus().subscribe(subscription_id, event_types, handler)
