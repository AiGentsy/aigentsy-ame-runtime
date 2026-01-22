"""
SPAWN VS RESALE EV ARBITER
==========================

Explicit, explainable decision engine for spawn vs resale routing.
Compares Expected Values with risk premiums and budget constraints.

All decisions are logged and explainable for audit.

Usage:
    from arbiter.spawn_resale_arbiter import decide

    decision, info = decide(ev_spawn=1500, ev_resale=1200, risk_premium=0.12)
    # decision = "spawn" or "resale"
    # info = {"ev_spawn_adj": 1320, "ev_resale": 1200, ...}
"""

import json
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List
from uuid import uuid4


NDJSON_LOG = Path(__file__).parent.parent / "logs" / "run.ndjson"
DECISION_HISTORY: List[Dict[str, Any]] = []


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


class SpawnResaleArbiter:
    """
    Arbiter for spawn vs resale decisions.

    Decision Factors:
    - Expected Value (EV) of each path
    - Risk premium (discount for spawn uncertainty)
    - Budget constraints
    - Governor caps
    - Historical success rates
    """

    def __init__(self):
        self.default_risk_premium = 0.12  # 12% discount for spawn risk
        self.min_ev_threshold = 50.0      # Min EV to consider
        self.decision_count = 0

    def decide(
        self,
        ev_spawn: float,
        ev_resale: float,
        *,
        risk_premium: float = None,
        budget_ok: bool = True,
        governor_ok: bool = True,
        spawn_success_rate: float = 0.85,
        resale_success_rate: float = 0.95,
        opportunity_id: str = None,
        metadata: dict = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Decide between spawn and resale routing.

        Args:
            ev_spawn: Expected value of spawning new business
            ev_resale: Expected value of reselling via LOX
            risk_premium: Risk discount for spawn (default 0.12)
            budget_ok: Whether budget allows spawn
            governor_ok: Whether governor caps allow spawn
            spawn_success_rate: Historical spawn success rate
            resale_success_rate: Historical resale success rate
            opportunity_id: Optional opportunity identifier
            metadata: Additional context

        Returns:
            (decision, explanation)
            decision: "spawn" or "resale"
            explanation: Dict with full decision reasoning
        """
        decision_id = f"arbiter_{uuid4().hex[:8]}"
        risk_pct = risk_premium if risk_premium is not None else self.default_risk_premium

        # Validate inputs
        if not math.isfinite(ev_spawn):
            ev_spawn = 0.0
        if not math.isfinite(ev_resale):
            ev_resale = 0.0

        # Risk-adjusted spawn EV
        ev_spawn_adj = ev_spawn * (1.0 - risk_pct) * spawn_success_rate

        # Success-adjusted resale EV
        ev_resale_adj = ev_resale * resale_success_rate

        # Build explanation
        explanation = {
            "decision_id": decision_id,
            "opportunity_id": opportunity_id,
            "inputs": {
                "ev_spawn_raw": round(ev_spawn, 2),
                "ev_resale_raw": round(ev_resale, 2),
                "risk_premium": risk_pct,
                "spawn_success_rate": spawn_success_rate,
                "resale_success_rate": resale_success_rate,
                "budget_ok": budget_ok,
                "governor_ok": governor_ok
            },
            "calculations": {
                "ev_spawn_adj": round(ev_spawn_adj, 2),
                "ev_resale_adj": round(ev_resale_adj, 2),
                "spawn_risk_discount": round(ev_spawn * risk_pct, 2),
                "ev_difference": round(ev_spawn_adj - ev_resale_adj, 2)
            },
            "metadata": metadata or {},
            "decided_at": _now_iso()
        }

        # Decision logic
        decision = None
        reason = None

        # Check constraints first
        if not budget_ok:
            decision = "resale"
            reason = "budget_constraint"

        elif not governor_ok:
            decision = "resale"
            reason = "governor_cap"

        elif ev_spawn < self.min_ev_threshold and ev_resale < self.min_ev_threshold:
            decision = "resale"
            reason = "below_min_threshold"

        elif ev_spawn_adj >= ev_resale_adj:
            decision = "spawn"
            reason = "spawn_ev_higher"

        else:
            decision = "resale"
            reason = "resale_ev_higher"

        explanation["decision"] = decision
        explanation["reason"] = reason
        explanation["margin"] = abs(round(ev_spawn_adj - ev_resale_adj, 2))
        explanation["confidence"] = self._calculate_confidence(ev_spawn_adj, ev_resale_adj)

        # Log decision
        self.decision_count += 1
        DECISION_HISTORY.append(explanation)

        _emit(
            "arbiter_decision",
            decision_id=decision_id,
            decision=decision,
            reason=reason,
            ev_spawn_adj=explanation["calculations"]["ev_spawn_adj"],
            ev_resale_adj=explanation["calculations"]["ev_resale_adj"],
            opportunity_id=opportunity_id
        )

        return decision, explanation

    def _calculate_confidence(self, ev_spawn: float, ev_resale: float) -> str:
        """Calculate decision confidence level"""
        if ev_spawn == 0 and ev_resale == 0:
            return "low"

        total = ev_spawn + ev_resale
        if total == 0:
            return "low"

        margin_pct = abs(ev_spawn - ev_resale) / total

        if margin_pct > 0.30:
            return "high"
        elif margin_pct > 0.15:
            return "medium"
        else:
            return "low"

    def get_stats(self) -> Dict[str, Any]:
        """Get arbiter statistics"""
        if not DECISION_HISTORY:
            return {"total_decisions": 0}

        spawn_count = len([d for d in DECISION_HISTORY if d["decision"] == "spawn"])
        resale_count = len([d for d in DECISION_HISTORY if d["decision"] == "resale"])

        return {
            "total_decisions": len(DECISION_HISTORY),
            "spawn_count": spawn_count,
            "resale_count": resale_count,
            "spawn_pct": round(spawn_count / len(DECISION_HISTORY) * 100, 1),
            "reasons": self._count_reasons(),
            "avg_margin": round(
                sum(d.get("margin", 0) for d in DECISION_HISTORY) / len(DECISION_HISTORY), 2
            )
        }

    def _count_reasons(self) -> Dict[str, int]:
        """Count decision reasons"""
        reasons = {}
        for d in DECISION_HISTORY:
            r = d.get("reason", "unknown")
            reasons[r] = reasons.get(r, 0) + 1
        return reasons


# Module-level singleton
_arbiter = SpawnResaleArbiter()


def decide(
    ev_spawn: float,
    ev_resale: float,
    risk_premium: float = 0.12,
    budget_ok: bool = True,
    **kwargs
) -> Tuple[str, Dict[str, Any]]:
    """
    Decide between spawn and resale.

    Returns:
        (decision, explanation)
    """
    return _arbiter.decide(
        ev_spawn,
        ev_resale,
        risk_premium=risk_premium,
        budget_ok=budget_ok,
        **kwargs
    )


def get_decision_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent decision history"""
    return list(reversed(DECISION_HISTORY[-limit:]))


def get_arbiter_stats() -> Dict[str, Any]:
    """Get arbiter statistics"""
    return _arbiter.get_stats()
