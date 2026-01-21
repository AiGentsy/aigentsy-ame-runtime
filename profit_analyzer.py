"""
ROOT-CAUSE PROFIT ANALYZER
==========================

Traces every dollar of profit/loss to its source.
Enables surgical optimization of the revenue flywheel.

Analysis dimensions:
- By connector
- By category
- By provider (OCS tier)
- By time-of-day
- By split policy
- By insurance attachment

Revenue:
- No direct fee (value is optimization insights)
- Indirect: better margins from optimization

Usage:
    from profit_analyzer import trace_outcome, get_profit_attribution, get_optimization_suggestions
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import statistics

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Analysis dimensions
DIMENSIONS = [
    "connector",
    "category",
    "provider_tier",
    "time_of_day",
    "day_of_week",
    "split_policy",
    "insurance_attached",
    "subscriber_tier"
]

# Benchmark targets
BENCHMARKS = {
    "gross_margin": 0.25,  # 25% target
    "completion_rate": 0.95,  # 95% target
    "dispute_rate": 0.02,  # 2% max
    "sla_hit_rate": 0.90,  # 90% target
}

# Storage
_OUTCOME_TRACES: List[Dict[str, Any]] = []
_AGGREGATES: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
    "count": 0,
    "revenue": 0.0,
    "cost": 0.0,
    "profit": 0.0,
    "disputes": 0,
    "completions": 0,
    "sla_hits": 0
})


class ProfitAnalyzer:
    """
    Root-cause profit analysis and attribution engine.
    """

    def __init__(self):
        self.dimensions = DIMENSIONS
        self.benchmarks = BENCHMARKS

    def trace_outcome(
        self,
        outcome_id: str,
        *,
        revenue: float,
        cost: float,
        connector: str = "unknown",
        category: str = "general",
        provider_id: str = None,
        provider_ocs: int = 50,
        split_policy: str = "standard",
        insurance_attached: bool = False,
        subscriber_tier: str = None,
        completed: bool = True,
        sla_met: bool = True,
        disputed: bool = False,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """
        Trace profit/loss for a single outcome.

        Args:
            outcome_id: Unique outcome ID
            revenue: Total revenue
            cost: Total cost (provider payout, fees, etc.)
            connector: Connector used
            category: Outcome category
            provider_id: Provider ID
            provider_ocs: Provider's OCS score
            split_policy: Revenue split policy used
            insurance_attached: Whether OIO was attached
            subscriber_tier: Subscriber tier (if applicable)
            completed: Whether outcome was completed
            sla_met: Whether SLA was met
            disputed: Whether there was a dispute
            metadata: Additional context

        Returns:
            Trace details with attribution
        """
        profit = revenue - cost
        margin = profit / revenue if revenue > 0 else 0

        # Determine provider tier
        if provider_ocs >= 80:
            provider_tier = "premium"
        elif provider_ocs >= 60:
            provider_tier = "standard"
        elif provider_ocs >= 40:
            provider_tier = "developing"
        else:
            provider_tier = "new"

        # Determine time dimensions
        now = datetime.now(timezone.utc)
        hour = now.hour
        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"

        day_of_week = now.strftime("%A").lower()

        trace = {
            "id": f"trace_{outcome_id}",
            "outcome_id": outcome_id,
            "timestamp": _now(),
            "financials": {
                "revenue": revenue,
                "cost": cost,
                "profit": profit,
                "margin": round(margin, 4)
            },
            "dimensions": {
                "connector": connector,
                "category": category,
                "provider_tier": provider_tier,
                "time_of_day": time_of_day,
                "day_of_week": day_of_week,
                "split_policy": split_policy,
                "insurance_attached": "yes" if insurance_attached else "no",
                "subscriber_tier": subscriber_tier or "none"
            },
            "outcomes": {
                "completed": completed,
                "sla_met": sla_met,
                "disputed": disputed
            },
            "metadata": {
                "provider_id": provider_id,
                "provider_ocs": provider_ocs,
                **(metadata or {})
            }
        }

        _OUTCOME_TRACES.append(trace)

        # Update aggregates for each dimension
        for dim, value in trace["dimensions"].items():
            key = f"{dim}:{value}"
            agg = _AGGREGATES[key]
            agg["count"] += 1
            agg["revenue"] += revenue
            agg["cost"] += cost
            agg["profit"] += profit
            if completed:
                agg["completions"] += 1
            if sla_met:
                agg["sla_hits"] += 1
            if disputed:
                agg["disputes"] += 1

        return {
            "ok": True,
            "trace": trace,
            "margin_vs_benchmark": round(margin - self.benchmarks["gross_margin"], 4)
        }

    def get_profit_attribution(
        self,
        dimension: str,
        *,
        start_date: str = None,
        end_date: str = None,
        min_count: int = 5
    ) -> Dict[str, Any]:
        """
        Get profit attribution by dimension.

        Args:
            dimension: Dimension to analyze (connector, category, etc.)
            start_date: Filter start date
            end_date: Filter end date
            min_count: Minimum outcomes for inclusion

        Returns:
            Profit attribution breakdown
        """
        if dimension not in self.dimensions:
            return {"ok": False, "error": "invalid_dimension", "valid": self.dimensions}

        # Filter aggregates by dimension
        results = []
        for key, agg in _AGGREGATES.items():
            if not key.startswith(f"{dimension}:"):
                continue
            if agg["count"] < min_count:
                continue

            value = key.split(":", 1)[1]
            margin = agg["profit"] / agg["revenue"] if agg["revenue"] > 0 else 0
            completion_rate = agg["completions"] / agg["count"] if agg["count"] > 0 else 0
            dispute_rate = agg["disputes"] / agg["count"] if agg["count"] > 0 else 0
            sla_rate = agg["sla_hits"] / agg["count"] if agg["count"] > 0 else 0

            results.append({
                "value": value,
                "count": agg["count"],
                "revenue": round(agg["revenue"], 2),
                "cost": round(agg["cost"], 2),
                "profit": round(agg["profit"], 2),
                "margin": round(margin, 4),
                "completion_rate": round(completion_rate, 4),
                "dispute_rate": round(dispute_rate, 4),
                "sla_rate": round(sla_rate, 4),
                "margin_vs_benchmark": round(margin - self.benchmarks["gross_margin"], 4),
                "status": "above_benchmark" if margin > self.benchmarks["gross_margin"] else "below_benchmark"
            })

        # Sort by profit (highest first)
        results.sort(key=lambda x: x["profit"], reverse=True)

        total_profit = sum(r["profit"] for r in results)

        # Add profit share
        for r in results:
            r["profit_share"] = round(r["profit"] / total_profit, 4) if total_profit > 0 else 0

        return {
            "ok": True,
            "dimension": dimension,
            "total_profit": round(total_profit, 2),
            "segments": results,
            "benchmark": self.benchmarks["gross_margin"]
        }

    def get_optimization_suggestions(self) -> Dict[str, Any]:
        """
        Get optimization suggestions based on analysis.

        Returns:
            Actionable optimization suggestions
        """
        suggestions = []

        # Analyze each dimension for opportunities
        for dim in self.dimensions:
            attribution = self.get_profit_attribution(dim, min_count=3)
            if not attribution.get("ok"):
                continue

            segments = attribution.get("segments", [])
            if not segments:
                continue

            # Find best and worst performers
            best = max(segments, key=lambda x: x["margin"])
            worst = min(segments, key=lambda x: x["margin"])

            margin_spread = best["margin"] - worst["margin"]

            if margin_spread > 0.10:  # 10%+ spread
                suggestions.append({
                    "dimension": dim,
                    "type": "margin_optimization",
                    "priority": "high" if margin_spread > 0.20 else "medium",
                    "insight": f"{dim.replace('_', ' ').title()}: '{best['value']}' has {best['margin']*100:.1f}% margin vs '{worst['value']}' at {worst['margin']*100:.1f}%",
                    "action": f"Route more volume to '{best['value']}' or improve '{worst['value']}' operations",
                    "potential_impact": round(worst["revenue"] * margin_spread, 2)
                })

            # Check for below-benchmark segments
            below_benchmark = [s for s in segments if s["margin"] < self.benchmarks["gross_margin"]]
            if below_benchmark:
                total_below = sum(s["revenue"] for s in below_benchmark)
                suggestions.append({
                    "dimension": dim,
                    "type": "benchmark_gap",
                    "priority": "high" if total_below > 10000 else "medium",
                    "insight": f"{len(below_benchmark)} {dim} segments below {self.benchmarks['gross_margin']*100:.0f}% margin benchmark",
                    "action": f"Review pricing or costs for: {', '.join(s['value'] for s in below_benchmark[:3])}",
                    "potential_impact": round(total_below * 0.05, 2)  # 5% improvement potential
                })

            # Check dispute rates
            high_dispute = [s for s in segments if s["dispute_rate"] > self.benchmarks["dispute_rate"]]
            if high_dispute:
                suggestions.append({
                    "dimension": dim,
                    "type": "dispute_reduction",
                    "priority": "high",
                    "insight": f"{len(high_dispute)} {dim} segments have dispute rate > {self.benchmarks['dispute_rate']*100:.0f}%",
                    "action": f"Improve quality or SLAs for: {', '.join(s['value'] for s in high_dispute[:3])}",
                    "potential_impact": round(sum(s["revenue"] * s["dispute_rate"] for s in high_dispute), 2)
                })

        # Sort by potential impact
        suggestions.sort(key=lambda x: x.get("potential_impact", 0), reverse=True)

        return {
            "ok": True,
            "suggestions": suggestions[:10],  # Top 10
            "total_potential_impact": round(sum(s.get("potential_impact", 0) for s in suggestions[:10]), 2),
            "benchmarks": self.benchmarks
        }

    def get_trend_analysis(
        self,
        dimension: str,
        value: str,
        *,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get trend analysis for a specific dimension value.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        filtered = [
            t for t in _OUTCOME_TRACES
            if t["dimensions"].get(dimension) == value and t["timestamp"] >= cutoff
        ]

        if not filtered:
            return {"ok": False, "error": "no_data"}

        # Group by day
        by_day = defaultdict(lambda: {"revenue": 0, "cost": 0, "count": 0})
        for trace in filtered:
            day = trace["timestamp"][:10]
            by_day[day]["revenue"] += trace["financials"]["revenue"]
            by_day[day]["cost"] += trace["financials"]["cost"]
            by_day[day]["count"] += 1

        daily_margins = []
        for day, data in sorted(by_day.items()):
            margin = (data["revenue"] - data["cost"]) / data["revenue"] if data["revenue"] > 0 else 0
            daily_margins.append({
                "date": day,
                "revenue": round(data["revenue"], 2),
                "margin": round(margin, 4),
                "count": data["count"]
            })

        # Calculate trend
        margins = [d["margin"] for d in daily_margins]
        trend = "stable"
        if len(margins) >= 7:
            first_half = statistics.mean(margins[:len(margins)//2])
            second_half = statistics.mean(margins[len(margins)//2:])
            if second_half > first_half + 0.02:
                trend = "improving"
            elif second_half < first_half - 0.02:
                trend = "declining"

        return {
            "ok": True,
            "dimension": dimension,
            "value": value,
            "days": days,
            "data_points": len(filtered),
            "daily_data": daily_margins,
            "trend": trend,
            "avg_margin": round(statistics.mean(margins), 4) if margins else 0,
            "margin_volatility": round(statistics.stdev(margins), 4) if len(margins) > 1 else 0
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get overall profit analysis summary"""
        if not _OUTCOME_TRACES:
            return {"ok": False, "error": "no_data"}

        total_revenue = sum(t["financials"]["revenue"] for t in _OUTCOME_TRACES)
        total_cost = sum(t["financials"]["cost"] for t in _OUTCOME_TRACES)
        total_profit = total_revenue - total_cost
        total_margin = total_profit / total_revenue if total_revenue > 0 else 0

        completed = sum(1 for t in _OUTCOME_TRACES if t["outcomes"]["completed"])
        disputes = sum(1 for t in _OUTCOME_TRACES if t["outcomes"]["disputed"])
        sla_hits = sum(1 for t in _OUTCOME_TRACES if t["outcomes"]["sla_met"])

        return {
            "total_outcomes": len(_OUTCOME_TRACES),
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "gross_margin": round(total_margin, 4),
            "margin_vs_benchmark": round(total_margin - self.benchmarks["gross_margin"], 4),
            "completion_rate": round(completed / len(_OUTCOME_TRACES), 4),
            "dispute_rate": round(disputes / len(_OUTCOME_TRACES), 4),
            "sla_hit_rate": round(sla_hits / len(_OUTCOME_TRACES), 4),
            "dimensions_tracked": len(self.dimensions),
            "benchmarks": self.benchmarks
        }


# Module-level singleton
_analyzer = ProfitAnalyzer()


def trace_outcome(outcome_id: str, **kwargs) -> Dict[str, Any]:
    """Trace profit/loss for outcome"""
    return _analyzer.trace_outcome(outcome_id, **kwargs)


def get_profit_attribution(dimension: str, **kwargs) -> Dict[str, Any]:
    """Get profit attribution by dimension"""
    return _analyzer.get_profit_attribution(dimension, **kwargs)


def get_optimization_suggestions() -> Dict[str, Any]:
    """Get optimization suggestions"""
    return _analyzer.get_optimization_suggestions()


def get_trend_analysis(dimension: str, value: str, **kwargs) -> Dict[str, Any]:
    """Get trend analysis"""
    return _analyzer.get_trend_analysis(dimension, value, **kwargs)


def get_profit_summary() -> Dict[str, Any]:
    """Get profit summary"""
    return _analyzer.get_summary()
