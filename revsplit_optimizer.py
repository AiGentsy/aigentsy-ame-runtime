"""
ADAPTIVE REVSPLIT OPTIMIZER
============================

Thompson-sampling experiments on revenue split curves.
Finds Pareto-optimal splits per vertical/partner/seasonality.

How it works:
1. Define 3-5 split policies per segment
2. Run small experiments with Thompson sampling
3. Reward = (Platform_profit - Risk_cost + LTV_delta)
4. Graduate winners, kill losers
5. Guardrails: never below compliance/tax minimums

Usage:
    from revsplit_optimizer import get_optimal_split, record_split_outcome

    # Get recommended split for a transaction
    split = get_optimal_split(segment="freelance", amount=500)

    # After transaction completes, record outcome
    record_split_outcome(split_id, accepted=True, ltv_delta=50)
"""

import random
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class ThompsonBandit:
    """
    Thompson sampling bandit for split optimization.

    Each arm represents a split policy.
    Beta distributions track success/failure.
    """

    def __init__(self, arms: List[str]):
        self.arms = arms
        # Beta distribution params: (alpha, beta) = (successes+1, failures+1)
        self.params: Dict[str, Dict[str, float]] = {
            arm: {"alpha": 1.0, "beta": 1.0} for arm in arms
        }
        self.pulls: Dict[str, int] = {arm: 0 for arm in arms}
        self.rewards: Dict[str, float] = {arm: 0.0 for arm in arms}

    def sample(self) -> str:
        """Sample from each arm's distribution and return best"""
        samples = {}
        for arm in self.arms:
            p = self.params[arm]
            # Sample from Beta distribution
            samples[arm] = random.betavariate(p["alpha"], p["beta"])
        return max(samples, key=samples.get)

    def update(self, arm: str, reward: float):
        """Update arm's distribution with observed reward"""
        if arm not in self.arms:
            return

        self.pulls[arm] += 1
        self.rewards[arm] += reward

        # Update Beta params (reward as success probability)
        # Normalize reward to [0, 1]
        normalized = max(0, min(1, (reward + 1) / 2))  # Assuming reward in [-1, 1]

        self.params[arm]["alpha"] += normalized
        self.params[arm]["beta"] += 1 - normalized

    def get_stats(self) -> Dict[str, Any]:
        """Get arm statistics"""
        stats = {}
        for arm in self.arms:
            p = self.params[arm]
            pulls = self.pulls[arm]
            mean = p["alpha"] / (p["alpha"] + p["beta"])
            stats[arm] = {
                "mean": round(mean, 4),
                "pulls": pulls,
                "total_reward": round(self.rewards[arm], 2),
                "avg_reward": round(self.rewards[arm] / pulls, 4) if pulls > 0 else 0
            }
        return stats


class RevSplitOptimizer:
    """
    Adaptive revenue split optimizer using Thompson sampling.

    Segments:
    - freelance: Freelancer marketplace transactions
    - enterprise: B2B enterprise deals
    - creator: Creator economy transactions
    - retail: Consumer retail transactions
    - default: Fallback segment

    Split policies (platform %):
    - aggressive: 8% platform (more user-friendly)
    - standard: 6% platform (current default)
    - premium: 4% platform (high-value/loyalty)
    - growth: 10% platform (high margin)
    """

    # Split policies: name -> {platform_pct, user_pct, pool_pct, partner_pct}
    SPLIT_POLICIES = {
        "premium": {"platform": 0.04, "user": 0.75, "pool": 0.08, "partner": 0.03},
        "standard": {"platform": 0.06, "user": 0.70, "pool": 0.10, "partner": 0.05},
        "aggressive": {"platform": 0.08, "user": 0.68, "pool": 0.10, "partner": 0.05},
        "growth": {"platform": 0.10, "user": 0.65, "pool": 0.12, "partner": 0.05},
    }

    # Compliance floors (never go below these)
    COMPLIANCE_FLOORS = {
        "platform_min": 0.02,  # 2% minimum platform take
        "pool_min": 0.05,      # 5% minimum pool contribution
    }

    def __init__(self):
        self._segments = ["freelance", "enterprise", "creator", "retail", "default"]
        self._policies = list(self.SPLIT_POLICIES.keys())

        # One bandit per segment
        self._bandits: Dict[str, ThompsonBandit] = {
            segment: ThompsonBandit(self._policies)
            for segment in self._segments
        }

        # Track recent splits for analysis
        self._split_history: List[Dict[str, Any]] = []
        self._max_history = 10000

    def get_optimal_split(
        self,
        amount: float,
        *,
        segment: str = "default",
        entity_id: str = None,
        force_policy: str = None
    ) -> Dict[str, Any]:
        """
        Get optimal revenue split for a transaction.

        Args:
            amount: Transaction amount
            segment: Business segment
            entity_id: Optional entity for personalization
            force_policy: Force a specific policy (for A/B testing)

        Returns:
            Split recommendation with amounts
        """
        # Validate segment
        if segment not in self._segments:
            segment = "default"

        # Select policy
        if force_policy and force_policy in self._policies:
            policy_name = force_policy
        else:
            policy_name = self._bandits[segment].sample()

        policy = self.SPLIT_POLICIES[policy_name]

        # Calculate amounts
        platform_amt = round(amount * policy["platform"], 2)
        user_amt = round(amount * policy["user"], 2)
        pool_amt = round(amount * policy["pool"], 2)
        partner_amt = round(amount * policy["partner"], 2)

        # Apply compliance floors
        min_platform = round(amount * self.COMPLIANCE_FLOORS["platform_min"], 2)
        min_pool = round(amount * self.COMPLIANCE_FLOORS["pool_min"], 2)

        if platform_amt < min_platform:
            diff = min_platform - platform_amt
            platform_amt = min_platform
            user_amt -= diff  # Take from user share

        if pool_amt < min_pool:
            diff = min_pool - pool_amt
            pool_amt = min_pool
            user_amt -= diff

        # Generate split ID for tracking
        split_id = f"split_{segment}_{policy_name}_{int(datetime.now().timestamp())}"

        split = {
            "split_id": split_id,
            "amount": amount,
            "segment": segment,
            "policy": policy_name,
            "splits": {
                "platform": platform_amt,
                "user": user_amt,
                "pool": pool_amt,
                "partner": partner_amt
            },
            "percentages": {
                "platform": policy["platform"],
                "user": policy["user"],
                "pool": policy["pool"],
                "partner": policy["partner"]
            },
            "compliance_adjusted": platform_amt > amount * policy["platform"],
            "created_at": _now_iso()
        }

        # Record for history
        self._split_history.append(split)
        if len(self._split_history) > self._max_history:
            self._split_history = self._split_history[-self._max_history:]

        return split

    def record_outcome(
        self,
        split_id: str,
        *,
        accepted: bool = True,
        completed: bool = True,
        ltv_delta: float = 0.0,
        risk_cost: float = 0.0
    ) -> Dict[str, Any]:
        """
        Record outcome for a split to update bandit.

        Args:
            split_id: Split ID from get_optimal_split
            accepted: Whether transaction was accepted
            completed: Whether transaction completed successfully
            ltv_delta: Change in customer lifetime value
            risk_cost: Any risk/dispute costs incurred

        Returns:
            Update result
        """
        # Find split in history
        split = None
        for s in reversed(self._split_history):
            if s.get("split_id") == split_id:
                split = s
                break

        if not split:
            return {"ok": False, "error": "split_not_found"}

        segment = split["segment"]
        policy = split["policy"]
        amount = split["amount"]
        platform_take = split["splits"]["platform"]

        # Calculate reward
        # Reward = normalized(platform_profit - risk_cost + ltv_delta)
        if accepted and completed:
            base_reward = platform_take - risk_cost + (ltv_delta * 0.1)  # LTV weighted 10%
            reward = base_reward / (amount * 0.1)  # Normalize by expected platform take
            reward = max(-1, min(1, reward))  # Clamp to [-1, 1]
        elif accepted and not completed:
            reward = -0.5  # Partial failure
        else:
            reward = -1.0  # Rejection

        # Update bandit
        self._bandits[segment].update(policy, reward)

        return {
            "ok": True,
            "split_id": split_id,
            "segment": segment,
            "policy": policy,
            "reward": round(reward, 4),
            "bandit_updated": True
        }

    def get_segment_stats(self, segment: str = None) -> Dict[str, Any]:
        """Get optimization stats for segment(s)"""
        if segment and segment in self._bandits:
            return {
                segment: self._bandits[segment].get_stats()
            }

        return {
            seg: bandit.get_stats()
            for seg, bandit in self._bandits.items()
        }

    def get_recommended_policies(self) -> Dict[str, str]:
        """Get current recommended policy per segment"""
        recommendations = {}
        for segment, bandit in self._bandits.items():
            stats = bandit.get_stats()
            # Recommend policy with highest mean
            best = max(stats.items(), key=lambda x: x[1]["mean"])
            recommendations[segment] = {
                "policy": best[0],
                "confidence": best[1]["mean"],
                "pulls": best[1]["pulls"]
            }
        return recommendations

    def get_stats(self) -> Dict[str, Any]:
        """Get overall optimizer statistics"""
        total_splits = len(self._split_history)
        by_segment = defaultdict(int)
        by_policy = defaultdict(int)

        for split in self._split_history:
            by_segment[split["segment"]] += 1
            by_policy[split["policy"]] += 1

        return {
            "total_splits": total_splits,
            "by_segment": dict(by_segment),
            "by_policy": dict(by_policy),
            "recommendations": self.get_recommended_policies(),
            "policies_available": list(self.SPLIT_POLICIES.keys())
        }


# Module-level singleton
_optimizer = RevSplitOptimizer()


def get_optimal_split(amount: float, **kwargs) -> Dict[str, Any]:
    """Get optimal revenue split"""
    return _optimizer.get_optimal_split(amount, **kwargs)


def record_split_outcome(split_id: str, **kwargs) -> Dict[str, Any]:
    """Record outcome for split learning"""
    return _optimizer.record_outcome(split_id, **kwargs)


def get_split_stats(segment: str = None) -> Dict[str, Any]:
    """Get split optimization stats"""
    return _optimizer.get_segment_stats(segment)


def get_split_recommendations() -> Dict[str, str]:
    """Get recommended policies per segment"""
    return _optimizer.get_recommended_policies()


def get_optimizer_stats() -> Dict[str, Any]:
    """Get overall optimizer statistics"""
    return _optimizer.get_stats()
