"""
BRAIN EVENTS
============

Shared Outcomes Bus - emit normalized, model-ready records to the brain.

Events to publish (append-only):
- coi.executed: inputs, PDL used, connector, cost, price, proof hashes, SLA
- pricing.quoted: quote tree, PG premium, spreads, FX
- ifx.order_placed|filled: side, size, Kelly fraction, slippage
- dealgraph.tranche_bound: senior/mezz/junior, expected loss, premium
- ocs.updated: delta, cause → proofs/sla/dispute
- placement.auction: bids, position, CTR, CPC/CPS
- bundle.attach: which runbooks co-sold
- passport.verified: downstream usage
- connector.health: latency, fail rate, rate-limit incidents
"""

from typing import Dict, Any, List, Callable, Optional
from datetime import datetime, timezone
from collections import defaultdict
import asyncio
import json
import hashlib

# Try to import MetaHive for network-wide distribution
try:
    from metahive_brain import contribute_to_hive
    METAHIVE_AVAILABLE = True
except ImportError:
    METAHIVE_AVAILABLE = False
    async def contribute_to_hive(*args, **kwargs): return {"ok": False}

# Try to import event bus for SSE streaming
try:
    from event_bus import publish as sse_publish
    SSE_AVAILABLE = True
except ImportError:
    SSE_AVAILABLE = False
    def sse_publish(*args, **kwargs): pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _hash_payload(payload: dict) -> str:
    """Generate deterministic hash of payload"""
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


class BrainEvents:
    """
    Event emitter for brain integration.

    Emits events to:
    1. Local handlers (for feature store updates)
    2. MetaHive (for network-wide learning)
    3. SSE bus (for real-time dashboards)
    """

    # Event schemas for validation
    EVENT_SCHEMAS = {
        "coi.executed": {
            "required": ["actor_id", "outcome_type", "success"],
            "optional": ["sku_id", "pdl_id", "connector_id", "cost", "price", "margin",
                        "proof_hashes", "sla_met", "latency_ms", "proofs"]
        },
        "pricing.quoted": {
            "required": ["sku_id", "base_price", "quoted_price"],
            "optional": ["segment", "spread", "fx_rate", "surge_multiplier",
                        "pg_attached", "pg_premium", "ocs"]
        },
        "ifx.order_placed": {
            "required": ["actor_id", "side", "size", "price"],
            "optional": ["sku_id", "kelly_fraction", "order_id"]
        },
        "ifx.order_filled": {
            "required": ["actor_id", "order_id", "fill_price", "fill_size"],
            "optional": ["slippage", "kelly_fraction"]
        },
        "dealgraph.tranche_bound": {
            "required": ["tranche_id", "tranche_type", "principal"],
            "optional": ["expected_loss", "premium", "coverage_ratio", "ocs_floor"]
        },
        "ocs.updated": {
            "required": ["actor_id", "ocs", "delta"],
            "optional": ["cause", "proofs_added", "sla_hits", "disputes"]
        },
        "placement.auction": {
            "required": ["placement_id", "winning_bid"],
            "optional": ["bids", "position", "ctr", "cpc", "cps", "category"]
        },
        "bundle.attach": {
            "required": ["coi_id", "bundle_skus"],
            "optional": ["total_value", "attach_rate"]
        },
        "passport.verified": {
            "required": ["entity_id", "passport_hash"],
            "optional": ["ocs", "downstream_usage", "verifier"]
        },
        "connector.health": {
            "required": ["connector_id"],
            "optional": ["latency_p50", "latency_p95", "latency_p99",
                        "fail_rate", "rate_limit_hits", "tos_risk_score"]
        }
    }

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = defaultdict(list)
        self._history: List[Dict[str, Any]] = []
        self._history_limit = 10000

    def on(self, event_type: str, handler: Callable):
        """Register event handler"""
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: Callable):
        """Unregister event handler"""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def emit(self, event_type: str, payload: dict) -> dict:
        """
        Emit an event to all channels.

        Args:
            event_type: Event type (e.g., "coi.executed")
            payload: Event payload

        Returns:
            Emit result with event_id
        """
        # Validate against schema
        schema = self.EVENT_SCHEMAS.get(event_type, {})
        required = schema.get("required", [])
        missing = [f for f in required if f not in payload]
        if missing:
            return {"ok": False, "error": f"missing_fields:{missing}"}

        # Create event envelope
        event = {
            "event_id": f"evt_{_hash_payload(payload)}_{_now_iso()[:19].replace(':', '')}",
            "type": event_type,
            "ts": _now_iso(),
            "payload": payload
        }

        # Store in history
        self._history.append(event)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit:]

        # Call local handlers
        for handler in self._handlers.get(event_type, []):
            try:
                handler(payload)
            except Exception as e:
                pass  # Don't fail on handler errors

        # Emit to SSE for dashboards
        if SSE_AVAILABLE:
            try:
                sse_publish(f"brain.{event_type}", event)
            except Exception:
                pass

        # Contribute to MetaHive for network learning
        if METAHIVE_AVAILABLE:
            self._contribute_to_hive(event_type, payload)

        return {"ok": True, "event_id": event["event_id"]}

    def _contribute_to_hive(self, event_type: str, payload: dict):
        """Contribute event to MetaHive for network-wide learning"""
        try:
            # Map event types to pattern types
            pattern_map = {
                "coi.executed": "fulfillment_workflow",
                "pricing.quoted": "pricing_insight",
                "ifx.order_filled": "market_maker_spread",
                "dealgraph.tranche_bound": "tranche_allocation",
                "placement.auction": "monetization_strategy",
                "connector.health": "ai_routing"
            }

            pattern_type = pattern_map.get(event_type)
            if not pattern_type:
                return

            # Calculate quality/ROAS from payload
            roas = 1.0
            quality = 0.5
            revenue = 0

            if event_type == "coi.executed":
                margin = payload.get("margin", 0)
                cost = payload.get("cost", 1)
                roas = 1 + (margin / cost) if cost > 0 else 1
                quality = 0.9 if payload.get("sla_met") else 0.5
                revenue = payload.get("price", 0)

            elif event_type == "pricing.quoted":
                base = payload.get("base_price", 1)
                quoted = payload.get("quoted_price", base)
                roas = quoted / base if base > 0 else 1
                quality = 0.7 if payload.get("pg_attached") else 0.5

            elif event_type == "ifx.order_filled":
                slippage = payload.get("slippage", 0)
                quality = max(0.3, 1 - slippage * 10)
                revenue = payload.get("fill_size", 0) * payload.get("fill_price", 0)

            # Async contribute
            asyncio.create_task(contribute_to_hive(
                username=payload.get("actor_id", "brain"),
                pattern_type=pattern_type,
                context={"event_type": event_type, **{k: v for k, v in payload.items() if k not in ["actor_id"]}},
                action={"type": event_type},
                outcome={"roas": roas, "quality_score": quality, "revenue": revenue},
                anonymize=True
            ))
        except Exception:
            pass

    def get_history(self, event_type: str = None, limit: int = 100) -> List[dict]:
        """Get event history"""
        events = self._history
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        return list(reversed(events[-limit:]))

    def get_stats(self) -> dict:
        """Get event statistics"""
        by_type = defaultdict(int)
        for e in self._history:
            by_type[e["type"]] += 1

        return {
            "total_events": len(self._history),
            "by_type": dict(by_type),
            "handlers_registered": {k: len(v) for k, v in self._handlers.items()}
        }


# Module-level singleton
_brain_events = BrainEvents()


def emit_event(event_type: str, payload: dict) -> dict:
    """Emit event using default instance"""
    return _brain_events.emit(event_type, payload)


def on_event(event_type: str, handler: Callable):
    """Register handler on default instance"""
    _brain_events.on(event_type, handler)


def get_event_history(event_type: str = None, limit: int = 100) -> List[dict]:
    """Get event history from default instance"""
    return _brain_events.get_history(event_type, limit)
