"""
R3 Allocator - Risk/Return/Runway Capital Allocation
=====================================================

Tier 3 Capital Allocation Module

Features:
- Kelly criterion sizing
- Runway protection (<30 days = conservative)
- Risk-adjusted returns
- Dynamic capital allocation

Impact: Sustainable aggressive growth without burning runway
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import math
import logging

logger = logging.getLogger("r3_allocator")


class RiskLevel(Enum):
    """Risk level classifications"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ULTRA_AGGRESSIVE = "ultra_aggressive"


@dataclass
class Allocation:
    """Single allocation decision"""
    opp_id: str
    amount: float
    max_amount: float
    kelly_fraction: float
    risk_adjusted_ev: float
    risk_level: RiskLevel
    reasoning: List[str]


@dataclass
class AllocationResult:
    """Result of allocation calculation"""
    allocations: List[Allocation]
    total_allocated: float
    budget_remaining: float
    risk_profile: RiskLevel
    runway_days: int
    reasoning: List[str]


# Risk level thresholds
RUNWAY_THRESHOLDS = {
    RiskLevel.ULTRA_AGGRESSIVE: 90,   # >90 days runway
    RiskLevel.AGGRESSIVE: 60,         # >60 days runway
    RiskLevel.MODERATE: 30,           # >30 days runway
    RiskLevel.CONSERVATIVE: 0,        # <30 days runway
}

# Kelly fraction limits by risk level
KELLY_LIMITS = {
    RiskLevel.ULTRA_AGGRESSIVE: 0.5,  # Up to 50% Kelly
    RiskLevel.AGGRESSIVE: 0.25,       # Up to 25% Kelly
    RiskLevel.MODERATE: 0.15,         # Up to 15% Kelly
    RiskLevel.CONSERVATIVE: 0.05,     # Up to 5% Kelly
}

# Per-opportunity caps by risk level
PER_OPP_CAPS = {
    RiskLevel.ULTRA_AGGRESSIVE: 0.2,  # 20% of budget per opp
    RiskLevel.AGGRESSIVE: 0.1,        # 10% of budget per opp
    RiskLevel.MODERATE: 0.05,         # 5% of budget per opp
    RiskLevel.CONSERVATIVE: 0.02,     # 2% of budget per opp
}


class R3Allocator:
    """
    Risk/Return/Runway-based Capital Allocator

    Uses:
    - Kelly Criterion for optimal bet sizing
    - Runway protection to prevent death spiral
    - Portfolio diversification
    - Risk-adjusted expected values
    """

    def __init__(self):
        self._allocation_history: List[AllocationResult] = []
        self._current_runway_days = 60  # Default assumption
        self._monthly_burn_rate = 5000  # Default burn rate

    def set_runway(self, runway_days: int, monthly_burn_rate: float = None):
        """Update runway information"""
        self._current_runway_days = runway_days
        if monthly_burn_rate:
            self._monthly_burn_rate = monthly_burn_rate

    def allocate(self, opportunities: List[Dict[str, Any]],
                 budget: float,
                 caps: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Allocate budget across opportunities using Kelly Criterion

        Args:
            opportunities: List of opportunity dicts with ev, probability, risk
            budget: Total available budget
            caps: Optional caps dict with per_opp, total keys

        Returns:
            Dict with allocations and metadata
        """
        caps = caps or {}
        per_opp_cap = caps.get("per_opp", budget * 0.1)
        total_cap = caps.get("total", budget)

        # Determine risk level based on runway
        risk_level = self._determine_risk_level()

        # Get Kelly limit for this risk level
        kelly_limit = KELLY_LIMITS[risk_level]
        per_opp_limit = min(per_opp_cap, budget * PER_OPP_CAPS[risk_level])

        # Calculate allocations
        allocations = []
        total_allocated = 0

        for opp in opportunities:
            if total_allocated >= total_cap:
                break

            opp_id = opp.get("id", opp.get("opp_id", str(hash(str(opp)))))
            ev = float(opp.get("ev", 0) or opp.get("value", 0) or 0)
            prob = float(opp.get("probability", 0.5) or opp.get("win_probability", 0.5))
            risk = float(opp.get("risk", 0.3) or opp.get("risk_score", 0.3))

            # Calculate Kelly fraction
            kelly = self._kelly_criterion(ev, prob, risk)

            # Apply risk-level limit
            kelly = min(kelly, kelly_limit)

            # Calculate allocation amount
            amount = min(
                budget * kelly,
                per_opp_limit,
                total_cap - total_allocated
            )

            if amount <= 0:
                continue

            # Risk-adjusted EV
            risk_adj_ev = ev * prob * (1 - risk)

            reasoning = [
                f"ev=${ev:.0f}",
                f"prob={prob:.0%}",
                f"risk={risk:.0%}",
                f"kelly={kelly:.2%}",
                f"risk_level={risk_level.value}"
            ]

            allocation = Allocation(
                opp_id=opp_id,
                amount=round(amount, 2),
                max_amount=per_opp_limit,
                kelly_fraction=kelly,
                risk_adjusted_ev=risk_adj_ev,
                risk_level=risk_level,
                reasoning=reasoning
            )

            allocations.append(allocation)
            total_allocated += amount

        # Build result
        result = AllocationResult(
            allocations=allocations,
            total_allocated=round(total_allocated, 2),
            budget_remaining=round(budget - total_allocated, 2),
            risk_profile=risk_level,
            runway_days=self._current_runway_days,
            reasoning=[
                f"runway={self._current_runway_days}d",
                f"risk_profile={risk_level.value}",
                f"kelly_limit={kelly_limit:.0%}",
                f"allocated={total_allocated:.0f}/{budget:.0f}"
            ]
        )

        self._allocation_history.append(result)

        logger.info(f"Allocated ${total_allocated:.0f} across {len(allocations)} opportunities")

        return {
            "allocations": [
                {
                    "opp_id": a.opp_id,
                    "amount": a.amount,
                    "kelly_fraction": a.kelly_fraction,
                    "risk_adjusted_ev": a.risk_adjusted_ev
                }
                for a in allocations
            ],
            "total_allocated": result.total_allocated,
            "budget_remaining": result.budget_remaining,
            "risk_profile": result.risk_profile.value,
            "runway_days": result.runway_days,
            "reasoning": result.reasoning
        }

    def _determine_risk_level(self) -> RiskLevel:
        """Determine appropriate risk level based on runway"""
        runway = self._current_runway_days

        if runway >= RUNWAY_THRESHOLDS[RiskLevel.ULTRA_AGGRESSIVE]:
            return RiskLevel.ULTRA_AGGRESSIVE
        elif runway >= RUNWAY_THRESHOLDS[RiskLevel.AGGRESSIVE]:
            return RiskLevel.AGGRESSIVE
        elif runway >= RUNWAY_THRESHOLDS[RiskLevel.MODERATE]:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.CONSERVATIVE

    def _kelly_criterion(self, ev: float, prob: float, risk: float) -> float:
        """
        Calculate Kelly Criterion fraction

        f* = (bp - q) / b

        where:
        - b = net odds received on the wager
        - p = probability of winning
        - q = probability of losing = 1 - p
        """
        if prob <= 0 or prob >= 1:
            return 0

        # Adjust probability for risk
        adj_prob = prob * (1 - risk * 0.5)

        # Calculate odds
        if ev <= 0:
            return 0

        # Assume we risk 1 unit to win ev/risk_amount units
        b = ev / max(0.01, 100)  # Normalize to reasonable odds

        # Kelly formula
        q = 1 - adj_prob
        kelly = (b * adj_prob - q) / max(0.01, b)

        # Ensure non-negative and reasonable
        kelly = max(0, min(1, kelly))

        # Apply fractional Kelly (half Kelly is common)
        return kelly * 0.5

    def get_runway_recommendation(self, budget: float) -> Dict[str, Any]:
        """Get recommendation based on current runway"""
        risk_level = self._determine_risk_level()

        recommendations = {
            RiskLevel.CONSERVATIVE: {
                "action": "preserve_capital",
                "max_spend_pct": 10,
                "focus": "high_probability_opps_only"
            },
            RiskLevel.MODERATE: {
                "action": "balanced_growth",
                "max_spend_pct": 30,
                "focus": "diversified_portfolio"
            },
            RiskLevel.AGGRESSIVE: {
                "action": "growth_focused",
                "max_spend_pct": 50,
                "focus": "high_ev_opps"
            },
            RiskLevel.ULTRA_AGGRESSIVE: {
                "action": "maximum_growth",
                "max_spend_pct": 70,
                "focus": "all_positive_ev_opps"
            }
        }

        rec = recommendations[risk_level]
        rec["runway_days"] = self._current_runway_days
        rec["risk_level"] = risk_level.value
        rec["max_spend_amount"] = budget * (rec["max_spend_pct"] / 100)

        return rec

    def get_stats(self) -> Dict[str, Any]:
        """Get allocator statistics"""
        return {
            "current_runway_days": self._current_runway_days,
            "monthly_burn_rate": self._monthly_burn_rate,
            "risk_level": self._determine_risk_level().value,
            "allocation_history_count": len(self._allocation_history),
            "total_allocated_lifetime": sum(
                a.total_allocated for a in self._allocation_history
            )
        }


# Singleton instance
_r3_allocator: Optional[R3Allocator] = None


def get_r3_allocator() -> R3Allocator:
    """Get or create the R3 Allocator singleton"""
    global _r3_allocator
    if _r3_allocator is None:
        _r3_allocator = R3Allocator()
    return _r3_allocator


def allocate_capital(opportunities: List[Dict[str, Any]],
                     budget: float,
                     caps: Dict[str, float] = None) -> Dict[str, Any]:
    """Convenience function to allocate capital"""
    return get_r3_allocator().allocate(opportunities, budget, caps)
