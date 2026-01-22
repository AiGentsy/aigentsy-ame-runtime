"""
GOVERNOR RUNTIME
================

Real-time spend tracking, cap enforcement, and automatic degradation.
Emits ND-JSON events for audit trail and observability.

Features:
- Per-category daily caps (bids, autospawn, assurance, FX)
- Per-module caps with position limits
- Automatic degradation cascade
- ND-JSON event stream for all governor actions
- Soft/hard cap enforcement with warnings

Usage:
    from governors.governor_runtime import guard_spend, get_spend_status

    if not guard_spend("bids", 500.0):
        return {"ok": False, "reason": "cap_hit"}
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict


# Paths
GOV_POLICY_PATH = Path(__file__).parent.parent / "policies" / "risk_governors.json"
NDJSON_LOG_PATH = Path(__file__).parent.parent / "logs" / "run.ndjson"


@dataclass
class GovernorState:
    """Current governor state with daily tracking"""
    day: str = ""
    spent: Dict[str, float] = field(default_factory=lambda: {
        "bids": 0.0,
        "autospawn": 0.0,
        "assurance": 0.0,
        "fx": 0.0,
        "total": 0.0
    })
    module_spent: Dict[str, float] = field(default_factory=dict)
    degradation_level: int = 0
    paused_categories: List[str] = field(default_factory=list)
    last_event_ts: str = ""


# Global state with thread lock
_STATE = GovernorState()
_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load_policy() -> Dict[str, Any]:
    """Load governor policy from JSON"""
    try:
        if GOV_POLICY_PATH.exists():
            return json.loads(GOV_POLICY_PATH.read_text())
    except Exception:
        pass
    # Default policy
    return {
        "caps": {
            "bids_usd_day": 2500,
            "autospawn_usd_day": 1500,
            "assurance_exposure_usd_day": 5000,
            "fx_notional_day": 20000,
            "total_daily_spend_usd": 15000
        },
        "module_caps": {},
        "actions": {
            "on_cap_hit": ["pause", "route_to_LOX", "notify_ops"]
        },
        "degradation_cascade": [
            {"threshold_pct": 80, "action": "disable_premium_channels"},
            {"threshold_pct": 90, "action": "disable_paid_discovery"},
            {"threshold_pct": 95, "action": "route_all_to_LOX"},
            {"threshold_pct": 100, "action": "full_pause"}
        ]
    }


def emit_governor_event(event: str, **kwargs) -> None:
    """Emit ND-JSON event to log file"""
    try:
        NDJSON_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": event,
            "ts": _now_iso(),
            **kwargs
        }
        with open(NDJSON_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Don't fail on logging errors


def _roll_day_if_needed() -> None:
    """Reset daily counters if day changed"""
    global _STATE
    today = _today()
    if _STATE.day != today:
        with _LOCK:
            if _STATE.day != today:
                old_day = _STATE.day
                old_spent = dict(_STATE.spent)
                _STATE = GovernorState(day=today)
                emit_governor_event(
                    "governor_day_roll",
                    old_day=old_day,
                    new_day=today,
                    final_spent=old_spent
                )


def _get_cap_key(kind: str) -> str:
    """Map spend kind to policy cap key"""
    keymap = {
        "bids": "bids_usd_day",
        "autospawn": "autospawn_usd_day",
        "assurance": "assurance_exposure_usd_day",
        "fx": "fx_notional_day",
        "total": "total_daily_spend_usd"
    }
    return keymap.get(kind, f"{kind}_usd_day")


def get_degradation_level() -> Tuple[int, str]:
    """Get current degradation level and action"""
    _roll_day_if_needed()
    policy = _load_policy()
    caps = policy.get("caps", {})
    cascade = policy.get("degradation_cascade", [])

    total_cap = caps.get("total_daily_spend_usd", 15000)
    total_spent = _STATE.spent.get("total", 0)

    if total_cap <= 0:
        return 0, "normal"

    pct_used = (total_spent / total_cap) * 100

    current_level = 0
    current_action = "normal"

    for i, step in enumerate(cascade):
        if pct_used >= step.get("threshold_pct", 100):
            current_level = i + 1
            current_action = step.get("action", "unknown")

    return current_level, current_action


def guard_spend(kind: str, amount_usd: float, *, module: str = None) -> bool:
    """
    Guard a spend operation against caps.

    Args:
        kind: Category (bids, autospawn, assurance, fx)
        amount_usd: Amount in USD
        module: Optional module name for per-module caps

    Returns:
        True if spend allowed, False if cap hit
    """
    _roll_day_if_needed()
    policy = _load_policy()
    caps = policy.get("caps", {})
    actions = policy.get("actions", {})

    cap_key = _get_cap_key(kind)
    cap = caps.get(cap_key, float("inf"))

    with _LOCK:
        current = _STATE.spent.get(kind, 0)
        new_total = current + float(amount_usd)

        # Check category cap
        if new_total > cap:
            for action in actions.get("on_cap_hit", []):
                emit_governor_event(
                    "governor_trip",
                    kind=kind,
                    cap=cap,
                    current=current,
                    attempted=amount_usd,
                    would_be=new_total,
                    action=action
                )
            return False

        # Check total daily cap
        total_cap = caps.get("total_daily_spend_usd", float("inf"))
        total_new = _STATE.spent.get("total", 0) + float(amount_usd)
        if total_new > total_cap:
            for action in actions.get("on_cap_hit", []):
                emit_governor_event(
                    "governor_trip",
                    kind="total",
                    cap=total_cap,
                    current=_STATE.spent.get("total", 0),
                    attempted=amount_usd,
                    would_be=total_new,
                    action=action
                )
            return False

        # Check module cap if specified
        if module:
            module_caps = policy.get("module_caps", {})
            if module in module_caps:
                module_cap = module_caps[module].get("daily_usd", float("inf"))
                module_current = _STATE.module_spent.get(module, 0)
                module_new = module_current + float(amount_usd)
                if module_new > module_cap:
                    emit_governor_event(
                        "governor_trip",
                        kind=f"module:{module}",
                        cap=module_cap,
                        current=module_current,
                        attempted=amount_usd,
                        action="module_cap_hit"
                    )
                    return False
                _STATE.module_spent[module] = module_new

        # Record spend
        _STATE.spent[kind] = new_total
        _STATE.spent["total"] = total_new
        _STATE.last_event_ts = _now_iso()

        # Check for soft cap warnings
        pct_used = (new_total / cap * 100) if cap > 0 else 0
        if pct_used >= 80 and pct_used < 95:
            emit_governor_event(
                "governor_warning",
                kind=kind,
                pct_used=round(pct_used, 1),
                remaining=round(cap - new_total, 2)
            )

        emit_governor_event(
            "governor_spend",
            kind=kind,
            amount=amount_usd,
            new_total=new_total,
            cap=cap,
            pct_used=round(pct_used, 1),
            module=module
        )

        return True


def check_module_cap(module: str, amount_usd: float) -> Tuple[bool, float]:
    """
    Check if module has cap headroom without recording spend.

    Returns:
        (allowed, remaining_headroom)
    """
    _roll_day_if_needed()
    policy = _load_policy()
    module_caps = policy.get("module_caps", {})

    if module not in module_caps:
        return True, float("inf")

    cap = module_caps[module].get("daily_usd", float("inf"))
    current = _STATE.module_spent.get(module, 0)
    remaining = cap - current

    return (amount_usd <= remaining), remaining


def get_spend_status() -> Dict[str, Any]:
    """Get current spend status across all categories"""
    _roll_day_if_needed()
    policy = _load_policy()
    caps = policy.get("caps", {})

    status = {
        "day": _STATE.day,
        "categories": {},
        "modules": {},
        "degradation_level": get_degradation_level()[0],
        "degradation_action": get_degradation_level()[1],
        "paused_categories": list(_STATE.paused_categories),
        "last_event_ts": _STATE.last_event_ts
    }

    for kind in ["bids", "autospawn", "assurance", "fx", "total"]:
        cap_key = _get_cap_key(kind)
        cap = caps.get(cap_key, 0)
        spent = _STATE.spent.get(kind, 0)
        status["categories"][kind] = {
            "spent": round(spent, 2),
            "cap": cap,
            "remaining": round(cap - spent, 2),
            "pct_used": round((spent / cap * 100) if cap > 0 else 0, 1)
        }

    for module, spent in _STATE.module_spent.items():
        module_caps = policy.get("module_caps", {})
        cap = module_caps.get(module, {}).get("daily_usd", 0)
        status["modules"][module] = {
            "spent": round(spent, 2),
            "cap": cap,
            "remaining": round(cap - spent, 2)
        }

    return status


def reset_daily_caps() -> Dict[str, Any]:
    """Force reset daily caps (for testing/manual intervention)"""
    global _STATE
    old_spent = dict(_STATE.spent)
    old_day = _STATE.day

    with _LOCK:
        _STATE = GovernorState(day=_today())

    emit_governor_event(
        "governor_manual_reset",
        old_day=old_day,
        old_spent=old_spent
    )

    return {"ok": True, "reset_at": _now_iso(), "previous_spent": old_spent}


def pause_category(kind: str) -> bool:
    """Pause a spend category"""
    with _LOCK:
        if kind not in _STATE.paused_categories:
            _STATE.paused_categories.append(kind)
            emit_governor_event("governor_pause", kind=kind)
    return True


def resume_category(kind: str) -> bool:
    """Resume a paused category"""
    with _LOCK:
        if kind in _STATE.paused_categories:
            _STATE.paused_categories.remove(kind)
            emit_governor_event("governor_resume", kind=kind)
    return True


def is_category_paused(kind: str) -> bool:
    """Check if category is paused"""
    return kind in _STATE.paused_categories
