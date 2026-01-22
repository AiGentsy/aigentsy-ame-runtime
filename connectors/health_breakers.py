"""
HEALTH BREAKERS
===============

Circuit breaker system with exponential backoff for platform connectors.
Turns warnings into auto-circuit-breakers with configurable cooloff.

Features:
- Per-connector circuit breakers
- Exponential backoff on failures
- Health color tracking (green/yellow/red)
- Automatic recovery attempts
- ND-JSON event emission

Usage:
    from connectors.health_breakers import breaker, get_health_status

    if not breaker("twitter_dm", healthy=health_check_passed):
        return {"ok": True, "skipped": "platform_cooloff"}
"""

import time
import threading
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class HealthColor(Enum):
    GREEN = "green"    # Healthy, full operation
    YELLOW = "yellow"  # Degraded, proceed with caution
    RED = "red"        # Unhealthy, circuit open


@dataclass
class BreakerState:
    """State for a single circuit breaker"""
    key: str
    color: HealthColor = HealthColor.GREEN
    consecutive_failures: int = 0
    last_failure_ts: float = 0.0
    cooloff_until: float = 0.0
    cooloff_seconds: float = 600.0  # Base cooloff (10 min)
    backoff_multiplier: float = 1.0
    total_trips: int = 0
    total_recoveries: int = 0
    last_success_ts: float = 0.0


# Global state with lock
_BREAKERS: Dict[str, BreakerState] = {}
_LOCK = threading.Lock()

# Config
DEFAULT_COOLOFF = 600       # 10 minutes base
MAX_COOLOFF = 7200          # 2 hours max
BACKOFF_FACTOR = 2.0        # Double on each failure
FAILURE_THRESHOLD = 3       # Failures before trip
YELLOW_THRESHOLD = 1        # Failures before yellow
RECOVERY_SUCCESSES = 3      # Successes to recover to green

NDJSON_LOG = Path(__file__).parent.parent / "logs" / "run.ndjson"


def _now() -> float:
    return time.time()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _emit(event: str, **kwargs):
    """Emit ND-JSON event"""
    try:
        NDJSON_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {"event": event, "ts": _now_iso(), **kwargs}
        with open(NDJSON_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _get_breaker(key: str) -> BreakerState:
    """Get or create breaker state"""
    if key not in _BREAKERS:
        _BREAKERS[key] = BreakerState(key=key)
    return _BREAKERS[key]


def breaker(
    key: str,
    healthy: bool,
    *,
    cooloff: float = DEFAULT_COOLOFF,
    max_cooloff: float = MAX_COOLOFF
) -> bool:
    """
    Circuit breaker check with exponential backoff.

    Args:
        key: Unique identifier for this breaker (e.g., "twitter_dm")
        healthy: Result of health check (True = healthy, False = unhealthy)
        cooloff: Base cooloff time in seconds
        max_cooloff: Maximum cooloff time

    Returns:
        True if operation should proceed, False if circuit is open
    """
    now = _now()

    with _LOCK:
        state = _get_breaker(key)

        # Check if still in cooloff
        if now < state.cooloff_until:
            # Still cooling off, reject
            return False

        if healthy:
            # Success - recovery path
            state.consecutive_failures = max(0, state.consecutive_failures - 1)
            state.last_success_ts = now
            state.backoff_multiplier = max(1.0, state.backoff_multiplier / 2)

            if state.color == HealthColor.RED and state.consecutive_failures == 0:
                state.color = HealthColor.YELLOW
                state.total_recoveries += 1
                _emit("breaker_recovering", key=key, color="yellow")

            elif state.color == HealthColor.YELLOW and state.consecutive_failures == 0:
                state.color = HealthColor.GREEN
                _emit("breaker_recovered", key=key, color="green")

            return True

        else:
            # Failure - trip path
            state.consecutive_failures += 1
            state.last_failure_ts = now

            # Update color
            if state.consecutive_failures >= FAILURE_THRESHOLD:
                if state.color != HealthColor.RED:
                    state.color = HealthColor.RED
                    state.total_trips += 1
                    _emit("breaker_tripped", key=key, failures=state.consecutive_failures)

                # Calculate exponential backoff cooloff
                actual_cooloff = min(
                    cooloff * state.backoff_multiplier,
                    max_cooloff
                )
                state.cooloff_until = now + actual_cooloff
                state.backoff_multiplier = min(state.backoff_multiplier * BACKOFF_FACTOR, 8.0)

                _emit(
                    "breaker_cooloff",
                    key=key,
                    cooloff_seconds=actual_cooloff,
                    until=datetime.fromtimestamp(state.cooloff_until, timezone.utc).isoformat()
                )

                return False

            elif state.consecutive_failures >= YELLOW_THRESHOLD:
                if state.color == HealthColor.GREEN:
                    state.color = HealthColor.YELLOW
                    _emit("breaker_degraded", key=key, failures=state.consecutive_failures)

            return True


def reset_breaker(key: str) -> Dict[str, Any]:
    """Manually reset a breaker"""
    with _LOCK:
        if key in _BREAKERS:
            old_state = _BREAKERS[key]
            _BREAKERS[key] = BreakerState(key=key)
            _emit("breaker_manual_reset", key=key)
            return {"ok": True, "previous_color": old_state.color.value}
        return {"ok": False, "error": "breaker_not_found"}


def get_health_status(key: str = None) -> Dict[str, Any]:
    """
    Get health status for one or all breakers.

    Args:
        key: Optional specific breaker key

    Returns:
        Health status dict
    """
    now = _now()

    if key:
        with _LOCK:
            state = _get_breaker(key)
            return {
                "key": key,
                "color": state.color.value,
                "consecutive_failures": state.consecutive_failures,
                "in_cooloff": now < state.cooloff_until,
                "cooloff_remaining_seconds": max(0, state.cooloff_until - now),
                "total_trips": state.total_trips,
                "total_recoveries": state.total_recoveries,
                "backoff_multiplier": state.backoff_multiplier
            }

    # All breakers
    with _LOCK:
        return {
            "breakers": {
                k: {
                    "color": v.color.value,
                    "failures": v.consecutive_failures,
                    "in_cooloff": now < v.cooloff_until,
                    "total_trips": v.total_trips
                }
                for k, v in _BREAKERS.items()
            },
            "summary": {
                "total": len(_BREAKERS),
                "green": len([b for b in _BREAKERS.values() if b.color == HealthColor.GREEN]),
                "yellow": len([b for b in _BREAKERS.values() if b.color == HealthColor.YELLOW]),
                "red": len([b for b in _BREAKERS.values() if b.color == HealthColor.RED])
            }
        }


def is_healthy(key: str) -> bool:
    """Quick check if a breaker is healthy (green)"""
    with _LOCK:
        state = _get_breaker(key)
        return state.color == HealthColor.GREEN and _now() >= state.cooloff_until


def get_all_red_breakers() -> list:
    """Get list of all red (tripped) breakers"""
    with _LOCK:
        return [k for k, v in _BREAKERS.items() if v.color == HealthColor.RED]


# Pre-configured breaker wrappers for common platforms
def twitter_breaker(healthy: bool) -> bool:
    return breaker("twitter", healthy, cooloff=1800, max_cooloff=7200)

def reddit_breaker(healthy: bool) -> bool:
    return breaker("reddit", healthy, cooloff=900, max_cooloff=3600)

def linkedin_breaker(healthy: bool) -> bool:
    return breaker("linkedin", healthy, cooloff=1800, max_cooloff=7200)

def instagram_breaker(healthy: bool) -> bool:
    return breaker("instagram", healthy, cooloff=1200, max_cooloff=5400)

def email_breaker(healthy: bool) -> bool:
    return breaker("email", healthy, cooloff=300, max_cooloff=1800)

def stripe_breaker(healthy: bool) -> bool:
    return breaker("stripe", healthy, cooloff=60, max_cooloff=600)
