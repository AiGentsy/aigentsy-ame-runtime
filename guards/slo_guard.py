"""
SLO GUARD
=========

Service Level Objective enforcement for white-label and autospawn operations.
Auto-cooldown on SLO breaches.

Features:
- Min CSAT enforcement
- Max late delivery rate
- Min margin per SKU/partner
- Jurisdiction-specific compliance rails
- Auto-cooldown on breaches

Usage:
    from guards.slo_guard import allow_launch

    ok, reason = allow_launch(metrics)
    if not ok:
        return {"ok": False, "skipped": f"slo_guard:{reason}"}
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List


SLO_POLICY_PATH = Path(__file__).parent.parent / "policies" / "slo_guard.json"
NDJSON_LOG = Path(__file__).parent.parent / "logs" / "run.ndjson"

# Cooldown state: {sku_id: cooldown_until_timestamp}
_COOLDOWNS: Dict[str, float] = {}


def _now() -> float:
    return time.time()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_policy() -> Dict[str, Any]:
    """Load SLO policy from JSON"""
    try:
        if SLO_POLICY_PATH.exists():
            return json.loads(SLO_POLICY_PATH.read_text())
    except Exception:
        pass
    # Default policy
    return {
        "sku_min_margin_pct": 0.22,
        "sku_min_csat": 4.4,
        "sku_max_late_7d": 0.08,
        "sku_max_dispute_rate": 0.03,
        "sku_min_completion_rate": 0.92,
        "cooldown_hours_on_breach": 24,
        "partner_tiers": {},
        "jurisdictions": {
            "default": {"min_creator_payout_pct": 0.50, "max_platform_take_pct": 0.30}
        }
    }


def _emit(event: str, **kwargs):
    """Emit ND-JSON event"""
    try:
        NDJSON_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {"event": event, "ts": _now_iso(), **kwargs}
        with open(NDJSON_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _is_in_cooldown(sku_id: str) -> Tuple[bool, float]:
    """Check if SKU is in cooldown"""
    cooldown_until = _COOLDOWNS.get(sku_id, 0)
    now = _now()
    if now < cooldown_until:
        return True, cooldown_until - now
    return False, 0


def _set_cooldown(sku_id: str, hours: float):
    """Set cooldown for SKU"""
    _COOLDOWNS[sku_id] = _now() + (hours * 3600)


def allow_launch(
    metrics: Dict[str, Any],
    *,
    sku_id: str = None,
    partner_tier: str = "silver",
    jurisdiction: str = "default"
) -> Tuple[bool, str]:
    """
    Check if SKU/autospawn launch is allowed based on SLO metrics.

    Args:
        metrics: Dict with margin_pct, csat, late_rate_7d, dispute_rate, completion_rate
        sku_id: SKU identifier (for cooldown tracking)
        partner_tier: Partner tier (platinum, gold, silver, bronze)
        jurisdiction: Jurisdiction code for compliance rails

    Returns:
        (allowed, reason)
    """
    policy = _load_policy()

    # Check cooldown first
    if sku_id:
        in_cooldown, remaining = _is_in_cooldown(sku_id)
        if in_cooldown:
            return False, f"in_cooldown:{int(remaining)}s"

    # Get tier-specific thresholds
    tier_config = policy.get("partner_tiers", {}).get(partner_tier, {})

    min_margin = tier_config.get("min_margin_pct", policy.get("sku_min_margin_pct", 0.22))
    min_csat = tier_config.get("min_csat", policy.get("sku_min_csat", 4.4))
    max_late = tier_config.get("max_late_7d", policy.get("sku_max_late_7d", 0.08))
    cooldown_hours = tier_config.get("cooldown_hours", policy.get("cooldown_hours_on_breach", 24))

    max_dispute = policy.get("sku_max_dispute_rate", 0.03)
    min_completion = policy.get("sku_min_completion_rate", 0.92)

    # Check each metric
    breach = None

    margin = metrics.get("margin_pct", 1.0)
    if margin < min_margin:
        breach = f"low_margin:{margin:.2f}<{min_margin:.2f}"

    csat = metrics.get("csat", 5.0)
    if csat < min_csat:
        breach = f"low_csat:{csat:.1f}<{min_csat:.1f}"

    late_rate = metrics.get("late_rate_7d", 0)
    if late_rate > max_late:
        breach = f"high_late:{late_rate:.2f}>{max_late:.2f}"

    dispute_rate = metrics.get("dispute_rate", 0)
    if dispute_rate > max_dispute:
        breach = f"high_dispute:{dispute_rate:.2f}>{max_dispute:.2f}"

    completion_rate = metrics.get("completion_rate", 1.0)
    if completion_rate < min_completion:
        breach = f"low_completion:{completion_rate:.2f}<{min_completion:.2f}"

    if breach:
        if sku_id:
            _set_cooldown(sku_id, cooldown_hours)
        _emit("slo_breach", sku_id=sku_id, breach=breach, cooldown_hours=cooldown_hours)
        return False, breach

    return True, ""


def check_sku_health(
    sku_id: str,
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Check SKU health against SLO thresholds.

    Returns detailed health report.
    """
    policy = _load_policy()

    checks = {
        "margin_pct": {
            "value": metrics.get("margin_pct", 0),
            "threshold": policy.get("sku_min_margin_pct", 0.22),
            "type": "min",
            "passed": metrics.get("margin_pct", 0) >= policy.get("sku_min_margin_pct", 0.22)
        },
        "csat": {
            "value": metrics.get("csat", 0),
            "threshold": policy.get("sku_min_csat", 4.4),
            "type": "min",
            "passed": metrics.get("csat", 0) >= policy.get("sku_min_csat", 4.4)
        },
        "late_rate_7d": {
            "value": metrics.get("late_rate_7d", 0),
            "threshold": policy.get("sku_max_late_7d", 0.08),
            "type": "max",
            "passed": metrics.get("late_rate_7d", 0) <= policy.get("sku_max_late_7d", 0.08)
        },
        "dispute_rate": {
            "value": metrics.get("dispute_rate", 0),
            "threshold": policy.get("sku_max_dispute_rate", 0.03),
            "type": "max",
            "passed": metrics.get("dispute_rate", 0) <= policy.get("sku_max_dispute_rate", 0.03)
        },
        "completion_rate": {
            "value": metrics.get("completion_rate", 0),
            "threshold": policy.get("sku_min_completion_rate", 0.92),
            "type": "min",
            "passed": metrics.get("completion_rate", 0) >= policy.get("sku_min_completion_rate", 0.92)
        }
    }

    in_cooldown, remaining = _is_in_cooldown(sku_id)
    all_passed = all(c["passed"] for c in checks.values())

    return {
        "sku_id": sku_id,
        "healthy": all_passed and not in_cooldown,
        "in_cooldown": in_cooldown,
        "cooldown_remaining_seconds": remaining,
        "checks": checks,
        "passing_count": len([c for c in checks.values() if c["passed"]]),
        "total_checks": len(checks)
    }


def check_partner_compliance(
    partner_id: str,
    partner_tier: str,
    jurisdiction: str,
    *,
    creator_payout_pct: float,
    platform_take_pct: float
) -> Tuple[bool, str]:
    """
    Check if partner revenue split complies with jurisdiction rules.

    Args:
        partner_id: Partner identifier
        partner_tier: Partner tier
        jurisdiction: Jurisdiction code (US, EU, UK, etc.)
        creator_payout_pct: Percentage going to creator
        platform_take_pct: Percentage taken by platform

    Returns:
        (compliant, reason)
    """
    policy = _load_policy()
    jurisdictions = policy.get("jurisdictions", {})

    j_rules = jurisdictions.get(jurisdiction, jurisdictions.get("default", {}))

    min_creator = j_rules.get("min_creator_payout_pct", 0.50)
    max_platform = j_rules.get("max_platform_take_pct", 0.30)

    if creator_payout_pct < min_creator:
        _emit(
            "compliance_breach",
            partner_id=partner_id,
            jurisdiction=jurisdiction,
            issue="creator_payout_too_low",
            actual=creator_payout_pct,
            minimum=min_creator
        )
        return False, f"creator_payout:{creator_payout_pct:.2f}<{min_creator:.2f}"

    if platform_take_pct > max_platform:
        _emit(
            "compliance_breach",
            partner_id=partner_id,
            jurisdiction=jurisdiction,
            issue="platform_take_too_high",
            actual=platform_take_pct,
            maximum=max_platform
        )
        return False, f"platform_take:{platform_take_pct:.2f}>{max_platform:.2f}"

    return True, ""


def clear_cooldown(sku_id: str) -> Dict[str, Any]:
    """Manually clear cooldown for a SKU"""
    if sku_id in _COOLDOWNS:
        del _COOLDOWNS[sku_id]
        _emit("cooldown_cleared", sku_id=sku_id)
        return {"ok": True, "sku_id": sku_id}
    return {"ok": False, "error": "no_cooldown_found"}


def get_guard_status() -> Dict[str, Any]:
    """Get current guard status"""
    policy = _load_policy()
    now = _now()

    active_cooldowns = {
        k: v - now for k, v in _COOLDOWNS.items() if v > now
    }

    return {
        "policy_version": policy.get("version", "unknown"),
        "active_cooldowns": len(active_cooldowns),
        "cooldowns": {k: round(v, 0) for k, v in active_cooldowns.items()},
        "thresholds": {
            "min_margin": policy.get("sku_min_margin_pct"),
            "min_csat": policy.get("sku_min_csat"),
            "max_late": policy.get("sku_max_late_7d"),
            "max_dispute": policy.get("sku_max_dispute_rate"),
            "min_completion": policy.get("sku_min_completion_rate")
        },
        "partner_tiers": list(policy.get("partner_tiers", {}).keys()),
        "jurisdictions": list(policy.get("jurisdictions", {}).keys())
    }
