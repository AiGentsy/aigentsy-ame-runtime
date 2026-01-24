"""
Policy Shapley - Attribute Revenue to Policies/Engines
=======================================================

Tier 5 Accountability Module

Features:
- Shapley value calculation for each policy/engine
- Fair attribution of revenue delta
- Identify which rules make money

Impact: Know what's working, cut what's not
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from collections import defaultdict
from itertools import combinations
import logging

logger = logging.getLogger("policy_shapley")


@dataclass
class ShapleyValue:
    """Shapley value result for an engine"""
    engine: str
    shapley_value: float  # Contribution to revenue delta
    marginal_contributions: List[float]
    sample_size: int
    confidence: float


class PolicyShapley:
    """
    Calculates Shapley values for policy/engine contribution

    Uses:
    - Coalition game theory
    - Marginal contribution analysis
    - Fair value attribution
    """

    def __init__(self):
        self._outcomes: List[Dict] = []
        self._shapley_cache: Dict[str, ShapleyValue] = {}

    def record_outcome(self, engines_used: List[str], revenue: float,
                       baseline_revenue: float = 0):
        """Record outcome for Shapley calculation"""
        self._outcomes.append({
            "engines": set(engines_used),
            "revenue": revenue,
            "baseline": baseline_revenue,
            "delta": revenue - baseline_revenue,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    async def value(self, outcomes: List[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        Calculate Shapley values for each engine

        Args:
            outcomes: Optional list of outcomes to analyze

        Returns:
            Dict of engine -> Shapley value (0-1, contribution to delta)
        """
        # Use provided outcomes or internal
        if outcomes:
            for o in outcomes:
                self.record_outcome(
                    engines_used=o.get("engines_used", []),
                    revenue=o.get("revenue", 0),
                    baseline_revenue=o.get("baseline", 0)
                )

        # Get all unique engines
        all_engines = set()
        for o in self._outcomes:
            all_engines.update(o["engines"])

        if not all_engines:
            return {}

        # Calculate Shapley values
        shapley_values = {}
        total_delta = sum(o["delta"] for o in self._outcomes)

        for engine in all_engines:
            shapley = self._calculate_shapley(engine, all_engines)
            shapley_values[engine] = shapley

            self._shapley_cache[engine] = ShapleyValue(
                engine=engine,
                shapley_value=shapley,
                marginal_contributions=[],
                sample_size=len(self._outcomes),
                confidence=min(0.95, len(self._outcomes) / 50)
            )

        # Normalize to sum to 1
        total = sum(abs(v) for v in shapley_values.values())
        if total > 0:
            shapley_values = {k: v / total for k, v in shapley_values.items()}

        logger.info(f"Shapley values calculated for {len(shapley_values)} engines")
        return shapley_values

    def _calculate_shapley(self, engine: str, all_engines: set) -> float:
        """Calculate Shapley value for a single engine"""
        other_engines = all_engines - {engine}
        n = len(all_engines)

        if n == 0:
            return 0

        shapley_value = 0

        # For each subset size
        for k in range(len(other_engines) + 1):
            # For each subset of size k
            for subset in combinations(other_engines, k):
                subset_set = set(subset)

                # Value with engine
                v_with = self._coalition_value(subset_set | {engine})
                # Value without engine
                v_without = self._coalition_value(subset_set)

                # Marginal contribution
                marginal = v_with - v_without

                # Shapley weight
                import math
                weight = (math.factorial(k) * math.factorial(n - k - 1)) / math.factorial(n)

                shapley_value += weight * marginal

        return shapley_value

    def _coalition_value(self, engines: set) -> float:
        """Get average delta for outcomes using this coalition of engines"""
        if not engines:
            return 0

        matching_outcomes = [
            o for o in self._outcomes
            if engines.issubset(o["engines"])
        ]

        if not matching_outcomes:
            return 0

        return sum(o["delta"] for o in matching_outcomes) / len(matching_outcomes)

    def get_top_engines(self, n: int = 3) -> List[Tuple[str, float]]:
        """Get top N engines by Shapley value"""
        sorted_engines = sorted(
            self._shapley_cache.items(),
            key=lambda x: x[1].shapley_value,
            reverse=True
        )
        return [(e, sv.shapley_value) for e, sv in sorted_engines[:n]]

    def get_stats(self) -> Dict[str, Any]:
        """Get Shapley statistics"""
        return {
            "outcomes_recorded": len(self._outcomes),
            "engines_analyzed": len(self._shapley_cache),
            "shapley_values": {
                e: round(sv.shapley_value, 4)
                for e, sv in self._shapley_cache.items()
            }
        }


# Singleton
_policy_shapley: Optional[PolicyShapley] = None

def get_policy_shapley() -> PolicyShapley:
    global _policy_shapley
    if _policy_shapley is None:
        _policy_shapley = PolicyShapley()
    return _policy_shapley

async def calculate_shapley(outcomes: List[Dict] = None) -> Dict[str, float]:
    return await get_policy_shapley().value(outcomes)
