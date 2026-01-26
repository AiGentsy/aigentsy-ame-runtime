"""
AUDIT LOG: Opportunity Lifecycle Tracking

Features:
- Full lifecycle events
- Searchable history
- Retention policies
- Export capabilities
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    # Discovery
    DISCOVERED = "discovered"
    DEDUPLICATED = "deduplicated"

    # Enrichment
    ENRICHED = "enriched"
    SCORED = "scored"

    # Routing
    ROUTED = "routed"
    FAST_PATH = "fast_path"

    # Execution
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_RETRIED = "execution_retried"

    # Outcome
    WON = "won"
    LOST = "lost"
    EXPIRED = "expired"

    # Risk
    BLOCKED = "blocked"
    FLAGGED = "flagged"

    # Manual
    MANUAL_REVIEW = "manual_review"
    MANUAL_OVERRIDE = "manual_override"


@dataclass
class AuditEvent:
    """Single audit event"""
    event_type: str
    opportunity_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any] = field(default_factory=dict)
    actor: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


class AuditLog:
    """
    Track opportunity lifecycle events.

    Provides:
    - Event logging
    - History queries
    - Statistics
    - Export
    """

    MAX_EVENTS = 100000  # Max events to keep in memory
    MAX_PER_OPPORTUNITY = 100  # Max events per opportunity

    def __init__(self, max_events: Optional[int] = None):
        self.max_events = max_events or self.MAX_EVENTS

        # All events (circular buffer)
        self._events: deque = deque(maxlen=self.max_events)

        # Events by opportunity ID
        self._by_opportunity: Dict[str, List[AuditEvent]] = {}

        # Event counts
        self._counts: Dict[str, int] = {}

        # Stats
        self.stats = {
            'events_logged': 0,
            'opportunities_tracked': 0,
        }

    def log(
        self,
        event_type: AuditEventType,
        opportunity_id: str,
        data: Optional[Dict] = None,
        actor: str = "system",
        metadata: Optional[Dict] = None,
    ) -> AuditEvent:
        """
        Log audit event.

        Args:
            event_type: Type of event
            opportunity_id: ID of related opportunity
            data: Event-specific data
            actor: Who/what triggered the event
            metadata: Additional metadata

        Returns:
            The created AuditEvent
        """
        event = AuditEvent(
            event_type=event_type.value if isinstance(event_type, AuditEventType) else event_type,
            opportunity_id=opportunity_id,
            data=data or {},
            actor=actor,
            metadata=metadata or {},
        )

        # Add to global events
        self._events.append(event)

        # Add to opportunity-specific events
        if opportunity_id not in self._by_opportunity:
            self._by_opportunity[opportunity_id] = []
            self.stats['opportunities_tracked'] += 1

        opp_events = self._by_opportunity[opportunity_id]
        if len(opp_events) < self.MAX_PER_OPPORTUNITY:
            opp_events.append(event)

        # Update counts
        self._counts[event.event_type] = self._counts.get(event.event_type, 0) + 1

        self.stats['events_logged'] += 1

        logger.debug(f"[audit] {event.event_type} for {opportunity_id}")

        return event

    def get_opportunity_history(self, opportunity_id: str) -> List[Dict]:
        """Get all events for an opportunity"""
        events = self._by_opportunity.get(opportunity_id, [])
        return [e.to_dict() for e in events]

    def get_recent_events(self, limit: int = 100, event_type: Optional[str] = None) -> List[Dict]:
        """Get recent events, optionally filtered by type"""
        events = list(self._events)[-limit:]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return [e.to_dict() for e in reversed(events)]

    def get_opportunity_state(self, opportunity_id: str) -> Optional[str]:
        """Get current state based on most recent event"""
        events = self._by_opportunity.get(opportunity_id, [])
        if not events:
            return None

        return events[-1].event_type

    def get_opportunities_by_state(self, state: str, limit: int = 100) -> List[str]:
        """Get opportunity IDs by current state"""
        matching = []
        for opp_id, events in self._by_opportunity.items():
            if events and events[-1].event_type == state:
                matching.append(opp_id)
                if len(matching) >= limit:
                    break
        return matching

    def get_funnel_stats(self) -> Dict:
        """Get funnel conversion stats"""
        # Count opportunities at each stage
        stages = {
            'discovered': 0,
            'enriched': 0,
            'routed': 0,
            'execution_started': 0,
            'execution_completed': 0,
            'won': 0,
            'blocked': 0,
        }

        for opp_id, events in self._by_opportunity.items():
            for event in events:
                if event.event_type in stages:
                    stages[event.event_type] += 1

        # Calculate conversion rates
        conversions = {}
        prev = None
        for stage, count in stages.items():
            if prev is not None and stages[prev] > 0:
                conversions[f"{prev}_to_{stage}"] = count / stages[prev]
            prev = stage

        return {
            'stages': stages,
            'conversions': conversions,
        }

    def search(
        self,
        opportunity_id: Optional[str] = None,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Search events with filters"""
        results = []

        for event in self._events:
            # Apply filters
            if opportunity_id and event.opportunity_id != opportunity_id:
                continue
            if event_type and event.event_type != event_type:
                continue
            if actor and event.actor != actor:
                continue
            if since and event.timestamp < since:
                continue
            if until and event.timestamp > until:
                continue

            results.append(event.to_dict())
            if len(results) >= limit:
                break

        return results

    def export_json(self, opportunity_id: Optional[str] = None) -> str:
        """Export events as JSON"""
        if opportunity_id:
            events = self.get_opportunity_history(opportunity_id)
        else:
            events = [e.to_dict() for e in self._events]

        return json.dumps(events, indent=2)

    def get_stats(self) -> Dict:
        """Get audit log stats"""
        return {
            **self.stats,
            'event_counts': self._counts.copy(),
            'events_in_memory': len(self._events),
            'funnel': self.get_funnel_stats(),
        }

    def clear(self):
        """Clear all events (for testing)"""
        self._events.clear()
        self._by_opportunity.clear()
        self._counts.clear()
        self.stats = {'events_logged': 0, 'opportunities_tracked': 0}


# Singleton
_audit_log: Optional[AuditLog] = None


def get_audit_log() -> AuditLog:
    """Get or create audit log instance"""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log
