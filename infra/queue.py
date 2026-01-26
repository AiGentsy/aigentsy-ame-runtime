"""
EVENT BUS: Async Event Processing

Features:
- Publish/subscribe pattern
- Typed event channels
- Async handlers
- Backpressure management
- Idempotency support
"""

import asyncio
import logging
import time
import hashlib
from typing import Dict, List, Callable, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types"""
    OPPORTUNITY_DISCOVERED = "opportunity.discovered"
    OPPORTUNITY_ENRICHED = "opportunity.enriched"
    OPPORTUNITY_ROUTED = "opportunity.routed"
    OPPORTUNITY_EXECUTED = "opportunity.executed"
    OPPORTUNITY_WON = "opportunity.won"
    OPPORTUNITY_LOST = "opportunity.lost"

    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"

    SYSTEM_ERROR = "system.error"
    SYSTEM_ALERT = "system.alert"


@dataclass
class Event:
    """Event structure"""
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: Optional[str] = None
    source: str = "system"

    def __post_init__(self):
        if not self.event_id:
            # Generate idempotency key
            key = f"{self.type}:{self.timestamp.isoformat()}:{hash(str(self.payload))}"
            self.event_id = hashlib.sha256(key.encode()).hexdigest()[:16]


class EventBus:
    """
    Async event bus for decoupled communication.

    Features:
    - Topic-based pub/sub
    - Async handlers with timeout
    - Backpressure via queue size limits
    - Idempotency tracking
    """

    MAX_QUEUE_SIZE = 10000
    HANDLER_TIMEOUT = 30.0
    IDEMPOTENCY_WINDOW = 3600  # 1 hour

    def __init__(self, max_queue_size: Optional[int] = None):
        self.max_queue_size = max_queue_size or self.MAX_QUEUE_SIZE

        # Subscribers: topic -> list of handlers
        self.subscribers: Dict[str, List[Callable]] = {}

        # Event queue for async processing
        self.queue: deque = deque(maxlen=self.max_queue_size)

        # Idempotency tracking
        self.processed_events: Set[str] = set()
        self.last_cleanup = time.time()

        # Stats
        self.stats = {
            'published': 0,
            'delivered': 0,
            'dropped_backpressure': 0,
            'dropped_duplicate': 0,
            'handler_errors': 0,
        }

        # Processing task
        self._processing = False
        self._task: Optional[asyncio.Task] = None

    def subscribe(self, topic: str, handler: Callable):
        """Subscribe handler to topic"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)
        logger.debug(f"[event_bus] Subscribed to {topic}")

    def unsubscribe(self, topic: str, handler: Callable):
        """Unsubscribe handler from topic"""
        if topic in self.subscribers:
            try:
                self.subscribers[topic].remove(handler)
            except ValueError:
                pass

    async def publish(self, event: Event) -> bool:
        """
        Publish event to bus.

        Returns True if event was queued, False if dropped.
        """
        self.stats['published'] += 1

        # Check idempotency
        if event.event_id in self.processed_events:
            self.stats['dropped_duplicate'] += 1
            return False

        # Check backpressure
        if len(self.queue) >= self.max_queue_size:
            self.stats['dropped_backpressure'] += 1
            logger.warning(f"[event_bus] Backpressure: dropped {event.type}")
            return False

        # Queue event
        self.queue.append(event)

        # Start processing if not running
        if not self._processing:
            self._task = asyncio.create_task(self._process_queue())

        return True

    async def publish_sync(self, event: Event):
        """Publish and wait for all handlers to complete"""
        if event.event_id in self.processed_events:
            return

        await self._deliver(event)
        self.processed_events.add(event.event_id)

    async def _process_queue(self):
        """Process events from queue"""
        self._processing = True

        try:
            while self.queue:
                event = self.queue.popleft()
                await self._deliver(event)
                self.processed_events.add(event.event_id)

                # Cleanup old idempotency keys periodically
                if time.time() - self.last_cleanup > 60:
                    self._cleanup_idempotency()

        finally:
            self._processing = False

    async def _deliver(self, event: Event):
        """Deliver event to all matching handlers"""
        # Get handlers for exact topic and wildcards
        handlers = []
        handlers.extend(self.subscribers.get(event.type, []))
        handlers.extend(self.subscribers.get('*', []))  # Wildcard

        # Also match topic prefixes (e.g., "opportunity.*" matches "opportunity.discovered")
        for topic, topic_handlers in self.subscribers.items():
            if topic.endswith('.*'):
                prefix = topic[:-2]
                if event.type.startswith(prefix):
                    handlers.extend(topic_handlers)

        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await asyncio.wait_for(result, timeout=self.HANDLER_TIMEOUT)
                self.stats['delivered'] += 1
            except asyncio.TimeoutError:
                logger.error(f"[event_bus] Handler timeout for {event.type}")
                self.stats['handler_errors'] += 1
            except Exception as e:
                logger.error(f"[event_bus] Handler error for {event.type}: {e}")
                self.stats['handler_errors'] += 1

    def _cleanup_idempotency(self):
        """Clean up old idempotency keys"""
        # Simple approach: clear all if too large
        if len(self.processed_events) > 100000:
            self.processed_events.clear()
        self.last_cleanup = time.time()

    def emit(self, event_type: str, payload: Dict[str, Any], source: str = "system"):
        """Convenience method to create and publish event"""
        event = Event(type=event_type, payload=payload, source=source)
        asyncio.create_task(self.publish(event))

    def get_stats(self) -> Dict:
        """Get bus stats"""
        return {
            **self.stats,
            'queue_size': len(self.queue),
            'topics': len(self.subscribers),
            'idempotency_keys': len(self.processed_events),
        }


# Singleton
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get or create event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
