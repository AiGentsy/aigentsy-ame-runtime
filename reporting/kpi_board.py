"""
KPI Board - Real-time Business Intelligence
============================================

Tier 5 Accountability Module

Features:
- Cash-per-token tracking
- Payback days calculation
- CAC:LTV ratio
- Engine attribution
- Policy Shapley exposure

Impact: Measure everything, make data-driven decisions
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger("kpi_board")


@dataclass
class KPISnapshot:
    """Point-in-time KPI snapshot"""
    timestamp: datetime
    cash_per_token: float
    payback_days_median: int
    cac_ltv_ratio: float
    win_rate: float
    refund_rate: float
    assured_share: float
    total_revenue: float
    total_spend: float


class KPIBoard:
    """
    Real-time KPI tracking and exposure

    Tracks:
    - Cash efficiency (cash per token)
    - Payback velocity
    - Unit economics (CAC:LTV)
    - Quality metrics (win rate, refund rate)
    - AIGx assurance share
    """

    def __init__(self):
        self._events: List[Dict] = []
        self._snapshots: List[KPISnapshot] = []

        # Aggregated metrics
        self._total_revenue: float = 0.0
        self._total_spend: float = 0.0
        self._total_tokens_used: int = 0
        self._total_outcomes: int = 0
        self._wins: int = 0
        self._refunds: int = 0
        self._assured_count: int = 0

        # Per-engine tracking
        self._engine_revenue: Dict[str, float] = defaultdict(float)
        self._engine_outcomes: Dict[str, int] = defaultdict(int)

        # Payback tracking
        self._payback_days: List[int] = []

    def emit(self, event: Dict[str, Any]):
        """
        Emit KPI event

        Event should contain:
        - ts: timestamp
        - opp_id: opportunity ID
        - revenue: revenue amount (if applicable)
        - spend: spend amount (if applicable)
        - tokens: tokens used (if applicable)
        - engine: engine used
        - success: outcome success
        - assured: AIGx assured
        - refunded: was refunded
        """
        self._events.append(event)

        # Update aggregates
        revenue = event.get("revenue", 0)
        spend = event.get("spend", 0)
        tokens = event.get("tokens", 0)
        success = event.get("success", False)
        assured = event.get("assured", False)
        refunded = event.get("refunded", False)
        engine = event.get("engine", "unknown")

        self._total_revenue += revenue
        self._total_spend += spend
        self._total_tokens_used += tokens
        self._total_outcomes += 1

        if success:
            self._wins += 1
        if refunded:
            self._refunds += 1
        if assured:
            self._assured_count += 1

        # Engine tracking
        self._engine_revenue[engine] += revenue
        self._engine_outcomes[engine] += 1

        # Payback days
        if event.get("payback_days"):
            self._payback_days.append(event["payback_days"])

    def get_kpis(self) -> Dict[str, Any]:
        """Get current KPIs"""
        # Cash per token
        cash_per_token = self._total_revenue / max(1, self._total_tokens_used)

        # Payback median
        payback_median = 0
        if self._payback_days:
            sorted_days = sorted(self._payback_days)
            mid = len(sorted_days) // 2
            payback_median = sorted_days[mid]

        # CAC:LTV ratio (simplified)
        cac_ltv_ratio = self._total_spend / max(1, self._total_revenue) if self._total_revenue > 0 else 0

        # Win rate
        win_rate = self._wins / max(1, self._total_outcomes)

        # Refund rate
        refund_rate = self._refunds / max(1, self._total_outcomes)

        # Assured share
        assured_share = self._assured_count / max(1, self._total_outcomes)

        # Engine attribution (top 5)
        engine_attribution = sorted(
            self._engine_revenue.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "cash_per_token": round(cash_per_token, 4),
            "payback_days_median": payback_median,
            "cac_ltv_ratio": round(cac_ltv_ratio, 4),
            "win_rate": round(win_rate, 4),
            "refund_rate": round(refund_rate, 4),
            "assured_share": round(assured_share, 4),
            "total_revenue": round(self._total_revenue, 2),
            "total_spend": round(self._total_spend, 2),
            "total_outcomes": self._total_outcomes,
            "engine_attribution": dict(engine_attribution),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_engine_kpis(self, engine: str) -> Dict[str, Any]:
        """Get KPIs for specific engine"""
        revenue = self._engine_revenue.get(engine, 0)
        outcomes = self._engine_outcomes.get(engine, 0)

        engine_events = [e for e in self._events if e.get("engine") == engine]
        wins = sum(1 for e in engine_events if e.get("success"))

        return {
            "engine": engine,
            "revenue": revenue,
            "outcomes": outcomes,
            "win_rate": wins / max(1, outcomes),
            "avg_revenue": revenue / max(1, outcomes)
        }

    def snapshot(self) -> KPISnapshot:
        """Take KPI snapshot"""
        kpis = self.get_kpis()

        snapshot = KPISnapshot(
            timestamp=datetime.now(timezone.utc),
            cash_per_token=kpis["cash_per_token"],
            payback_days_median=kpis["payback_days_median"],
            cac_ltv_ratio=kpis["cac_ltv_ratio"],
            win_rate=kpis["win_rate"],
            refund_rate=kpis["refund_rate"],
            assured_share=kpis["assured_share"],
            total_revenue=kpis["total_revenue"],
            total_spend=kpis["total_spend"]
        )

        self._snapshots.append(snapshot)
        return snapshot

    def get_trend(self, metric: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get trend for a metric over time"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        relevant_snapshots = [
            s for s in self._snapshots
            if s.timestamp >= cutoff
        ]

        return [
            {"ts": s.timestamp.isoformat(), "value": getattr(s, metric, 0)}
            for s in relevant_snapshots
        ]

    def reset(self):
        """Reset all metrics"""
        self._events.clear()
        self._total_revenue = 0.0
        self._total_spend = 0.0
        self._total_tokens_used = 0
        self._total_outcomes = 0
        self._wins = 0
        self._refunds = 0
        self._assured_count = 0
        self._engine_revenue.clear()
        self._engine_outcomes.clear()
        self._payback_days.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get board statistics"""
        return {
            "total_events": len(self._events),
            "snapshots": len(self._snapshots),
            "engines_tracked": len(self._engine_revenue),
            "kpis": self.get_kpis()
        }


# Singleton
_kpi_board: Optional[KPIBoard] = None

def get_kpi_board() -> KPIBoard:
    global _kpi_board
    if _kpi_board is None:
        _kpi_board = KPIBoard()
    return _kpi_board

def emit_kpi(event: Dict[str, Any]):
    get_kpi_board().emit(event)

def get_kpis() -> Dict[str, Any]:
    return get_kpi_board().get_kpis()
