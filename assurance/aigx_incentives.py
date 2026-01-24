"""
AIGx Incentives - Hot-streak Bonuses + Failure Rebates
=======================================================

Tier 4 Quality & Trust Module

Features:
- Hot-streak bonuses (7-day alpha)
- Failure rebates (SLO met, outcome missed)
- No custody, AIGx credits only
- Aligned incentives for performance

Impact: Aligned incentives, higher quality delivery
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("aigx_incentives")


@dataclass
class IncentiveResult:
    """Incentive calculation result"""
    opp_id: str
    hot_streak_bonus: float
    failure_rebate: float
    streak_days: int
    slo_met: bool
    outcome_met: bool
    reasoning: List[str]


# Incentive configuration
HOT_STREAK_CONFIG = {
    "min_days": 3,              # Min streak for bonus
    "bonus_per_day": 5.0,       # AIGx per streak day
    "max_bonus": 50.0,          # Max bonus cap
    "alpha_threshold": 0.7,     # Win rate threshold
}

FAILURE_REBATE_CONFIG = {
    "rebate_pct": 0.1,          # 10% rebate on SLO-met failures
    "max_rebate": 25.0,         # Max rebate cap
    "slo_required": True,       # Must meet SLO for rebate
}


class AIGxIncentives:
    """
    AIGx-based incentive system for aligned agent behavior

    No custody - only AIGx credit tracking
    P2P assurance model
    """

    def __init__(self):
        self._streak_tracker: Dict[str, int] = {}  # agent_id -> streak_days
        self._outcome_history: List[Dict] = []
        self._total_bonuses_issued: float = 0
        self._total_rebates_issued: float = 0

    def incentives_for(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate incentives for an execution result

        Args:
            result: Execution result with ok, agent_id, value, slo_status

        Returns:
            Dict with hot_streak_bonus, failure_rebate, etc.
        """
        agent_id = result.get("agent_id", "default")
        opp_id = result.get("opp_id", result.get("id", ""))
        success = result.get("ok", False)
        value = float(result.get("value", 0) or result.get("revenue", 0) or 0)
        slo_met = result.get("slo_met", True)

        # Track outcome
        self._outcome_history.append({
            "agent_id": agent_id,
            "success": success,
            "value": value,
            "slo_met": slo_met,
            "ts": datetime.now(timezone.utc).isoformat()
        })

        reasoning = []
        hot_streak_bonus = 0.0
        failure_rebate = 0.0

        # Calculate hot-streak bonus
        if success:
            # Update streak
            self._streak_tracker[agent_id] = self._streak_tracker.get(agent_id, 0) + 1
            streak_days = self._streak_tracker[agent_id]

            if streak_days >= HOT_STREAK_CONFIG["min_days"]:
                bonus = min(
                    streak_days * HOT_STREAK_CONFIG["bonus_per_day"],
                    HOT_STREAK_CONFIG["max_bonus"]
                )
                hot_streak_bonus = bonus
                reasoning.append(f"streak={streak_days}d, bonus={bonus:.0f}")
        else:
            # Reset streak on failure
            old_streak = self._streak_tracker.get(agent_id, 0)
            self._streak_tracker[agent_id] = 0

            # Check for failure rebate
            if slo_met and FAILURE_REBATE_CONFIG["slo_required"]:
                rebate = min(
                    value * FAILURE_REBATE_CONFIG["rebate_pct"],
                    FAILURE_REBATE_CONFIG["max_rebate"]
                )
                failure_rebate = rebate
                reasoning.append(f"slo_met=True, rebate={rebate:.0f}")

            if old_streak > 0:
                reasoning.append(f"streak_reset (was {old_streak}d)")

        # Track totals
        self._total_bonuses_issued += hot_streak_bonus
        self._total_rebates_issued += failure_rebate

        streak_days = self._streak_tracker.get(agent_id, 0)

        result_obj = IncentiveResult(
            opp_id=opp_id,
            hot_streak_bonus=hot_streak_bonus,
            failure_rebate=failure_rebate,
            streak_days=streak_days,
            slo_met=slo_met,
            outcome_met=success,
            reasoning=reasoning
        )

        logger.info(f"Incentives calculated: bonus={hot_streak_bonus:.0f}, rebate={failure_rebate:.0f}")

        return {
            "opp_id": result_obj.opp_id,
            "hot_streak_bonus": result_obj.hot_streak_bonus,
            "failure_rebate": result_obj.failure_rebate,
            "streak_days": result_obj.streak_days,
            "slo_met": result_obj.slo_met,
            "outcome_met": result_obj.outcome_met,
            "reasoning": result_obj.reasoning,
            "aigx_total": hot_streak_bonus + failure_rebate
        }

    def get_agent_streak(self, agent_id: str) -> int:
        """Get current streak for agent"""
        return self._streak_tracker.get(agent_id, 0)

    def get_stats(self) -> Dict[str, Any]:
        """Get incentive statistics"""
        return {
            "total_bonuses_issued": self._total_bonuses_issued,
            "total_rebates_issued": self._total_rebates_issued,
            "active_streaks": {k: v for k, v in self._streak_tracker.items() if v > 0},
            "outcome_count": len(self._outcome_history),
            "config": {
                "hot_streak": HOT_STREAK_CONFIG,
                "failure_rebate": FAILURE_REBATE_CONFIG
            }
        }


# Singleton
_aigx_incentives: Optional[AIGxIncentives] = None

def get_aigx_incentives() -> AIGxIncentives:
    global _aigx_incentives
    if _aigx_incentives is None:
        _aigx_incentives = AIGxIncentives()
    return _aigx_incentives

def calculate_incentives(result: Dict[str, Any]) -> Dict[str, Any]:
    return get_aigx_incentives().incentives_for(result)
