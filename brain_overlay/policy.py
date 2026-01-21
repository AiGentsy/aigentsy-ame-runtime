"""
POLICY ENGINE
=============

Policy interfaces for pricing, placement, tranching, and routing.

Each policy:
- State: Context features (segment, OCS, demand, cost curve, etc.)
- Action: Decision (price, spread, PG flag, Kelly fraction, etc.)
- Reward: Profit after risk - penalties (SLA breach, refunds)

Supports:
- Bandit/actor-critic updates
- Off-policy corrections
- Hot-loading from Apex Routes
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from collections import defaultdict
import random
import math


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class Policy:
    """
    Individual policy with state → action mapping.

    Maintains:
    - Current weights/parameters
    - Learning history
    - Performance metrics
    """

    def __init__(self, name: str, default_params: Dict[str, float] = None):
        self.name = name
        self.params = default_params or {}
        self._history: List[Dict[str, Any]] = []
        self._metrics = {
            "total_suggestions": 0,
            "total_reward": 0.0,
            "avg_reward": 0.0,
            "best_reward": 0.0,
            "worst_reward": 0.0
        }
        self._learning_rate = 0.01
        self._exploration_rate = 0.1

    def suggest(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Suggest action given state.

        Args:
            state: Current context features

        Returns:
            Suggested action dict
        """
        self._metrics["total_suggestions"] += 1

        # Epsilon-greedy exploration
        if random.random() < self._exploration_rate:
            return self._explore(state)
        return self._exploit(state)

    def _exploit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Exploit current best policy"""
        # Default implementation - override in subclasses
        return {"action": "default", "params": self.params}

    def _explore(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Explore with random perturbation"""
        perturbed = {}
        for k, v in self.params.items():
            if isinstance(v, (int, float)):
                perturbed[k] = v * (1 + random.uniform(-0.2, 0.2))
            else:
                perturbed[k] = v
        return {"action": "explore", "params": perturbed}

    def learn(self, state: Dict[str, Any], action: Dict[str, Any], reward: float, meta: Dict = None):
        """
        Learn from outcome.

        Args:
            state: State when action was taken
            action: Action that was taken
            reward: Reward received
            meta: Additional metadata
        """
        # Record history
        self._history.append({
            "ts": _now_iso(),
            "state": state,
            "action": action,
            "reward": reward,
            "meta": meta
        })

        # Trim history
        if len(self._history) > 10000:
            self._history = self._history[-10000:]

        # Update metrics
        self._metrics["total_reward"] += reward
        self._metrics["avg_reward"] = self._metrics["total_reward"] / len(self._history)
        self._metrics["best_reward"] = max(self._metrics["best_reward"], reward)
        if self._metrics["worst_reward"] == 0:
            self._metrics["worst_reward"] = reward
        else:
            self._metrics["worst_reward"] = min(self._metrics["worst_reward"], reward)

        # Update params via gradient-free optimization
        self._update_params(state, action, reward)

    def _update_params(self, state: Dict[str, Any], action: Dict[str, Any], reward: float):
        """Update policy parameters based on reward"""
        action_params = action.get("params", {})

        # If reward > avg, move params toward action
        # If reward < avg, move params away from action
        avg = self._metrics["avg_reward"]
        direction = 1 if reward > avg else -1

        for k, v in action_params.items():
            if k in self.params and isinstance(v, (int, float)):
                current = self.params[k]
                delta = (v - current) * self._learning_rate * direction
                self.params[k] = current + delta

    def load_apex(self, apex_params: Dict[str, Any]):
        """Load parameters from apex route"""
        self.params.update(apex_params.get("policy", {}))

    def get_metrics(self) -> Dict[str, Any]:
        """Get policy metrics"""
        return {
            "name": self.name,
            "params": self.params,
            "history_size": len(self._history),
            **self._metrics
        }


class PricingPolicy(Policy):
    """Pricing & Spread Policy (OAA/IFX)"""

    def __init__(self):
        super().__init__("pricing.oaa", {
            "price_slope": 0.20,      # Price sensitivity to demand
            "pg_attach_logit": 1.5,   # PG attachment probability
            "kelly_cap": 0.35,        # Max Kelly fraction
            "min_margin": 0.28,       # Floor margin
            "surge_sensitivity": 0.5  # Surge pricing sensitivity
        })

    def _exploit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal price given state"""
        base_price = state.get("base_price", 100)
        ocs = state.get("ocs", 50)
        demand = state.get("demand_score", 0.5)
        variance = state.get("historical_variance", 0.1)
        cost = state.get("cost", base_price * 0.3)

        # Price calculation
        demand_adj = 1 + (demand - 0.5) * self.params["price_slope"]
        ocs_adj = 1 - (ocs - 50) / 200  # OCS discount/premium

        price = base_price * demand_adj * ocs_adj

        # Ensure margin floor
        min_price = cost * (1 + self.params["min_margin"])
        price = max(price, min_price)

        # PG attachment decision
        pg_logit = self.params["pg_attach_logit"]
        pg_prob = 1 / (1 + math.exp(-pg_logit * (ocs / 100 - 0.5)))
        attach_pg = random.random() < pg_prob

        # Calculate spread
        spread = variance * self.params["surge_sensitivity"]

        # Kelly fraction
        kelly = min(self.params["kelly_cap"], (price - cost) / price * 0.5)

        return {
            "action": "price",
            "params": self.params,
            "price": round(price, 2),
            "spread": round(spread, 4),
            "pg_attach": attach_pg,
            "kelly_fraction": round(kelly, 3)
        }


class PlacementPolicy(Policy):
    """Placement Market Policy"""

    def __init__(self):
        super().__init__("placement.market", {
            "bid_elasticity": 0.15,     # Bid-to-rank sensitivity
            "quality_weight": 0.6,      # Quality vs bid weight
            "fraud_penalty": 5.0,       # Fraud penalty multiplier
            "min_quality_score": 0.3    # Minimum quality threshold
        })

    def _exploit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal bid/rank"""
        base_rank = state.get("organic_rank", 10)
        quality = state.get("quality_score", 0.5)
        bid = state.get("bid", 0)
        category_avg_bid = state.get("category_avg_bid", 1.0)

        # Quality gate
        if quality < self.params["min_quality_score"]:
            return {
                "action": "reject",
                "reason": "quality_below_threshold",
                "params": self.params
            }

        # Rank calculation
        bid_lift = (bid / category_avg_bid) * self.params["bid_elasticity"] if category_avg_bid > 0 else 0
        quality_score = quality * self.params["quality_weight"]

        final_rank = base_rank * (1 - bid_lift - quality_score)

        return {
            "action": "rank",
            "params": self.params,
            "organic_rank": base_rank,
            "final_rank": max(1, round(final_rank)),
            "bid_lift": round(bid_lift, 3),
            "quality_contribution": round(quality_score, 3)
        }


class TranchingPolicy(Policy):
    """DealGraph Risk Policy"""

    def __init__(self):
        super().__init__("dealgraph.tranche", {
            "senior_threshold": 0.85,    # OCS threshold for senior
            "mezz_threshold": 0.60,      # OCS threshold for mezz
            "coverage_floor": 0.70,      # Min coverage ratio
            "sharpe_target": 1.5,        # Target Sharpe ratio
            "expected_loss_cap": 0.15    # Max expected loss
        })

    def _exploit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine tranche allocation"""
        ocs = state.get("ocs", 50)
        variance = state.get("variance", 0.1)
        principal = state.get("principal", 1000)
        historical_default_rate = state.get("default_rate", 0.02)

        # Tranche assignment based on OCS
        if ocs >= self.params["senior_threshold"] * 100:
            tranche = "senior"
            expected_loss = historical_default_rate * 0.5
            premium_mult = 0.8
        elif ocs >= self.params["mezz_threshold"] * 100:
            tranche = "mezzanine"
            expected_loss = historical_default_rate * 1.0
            premium_mult = 1.0
        else:
            tranche = "junior"
            expected_loss = historical_default_rate * 2.0
            premium_mult = 1.5

        # Cap expected loss
        expected_loss = min(expected_loss, self.params["expected_loss_cap"])

        # Calculate premium
        base_premium = expected_loss * 2 + variance * 0.5
        premium = round(principal * base_premium * premium_mult, 2)

        return {
            "action": "allocate",
            "params": self.params,
            "tranche": tranche,
            "expected_loss": round(expected_loss, 4),
            "premium": premium,
            "coverage_ratio": round(1 - expected_loss, 4)
        }


class ConnectorPolicy(Policy):
    """Connector Selection Policy (UCB)"""

    def __init__(self):
        super().__init__("connector.ucb", {
            "api_preference": 0.8,       # Prefer API over alternatives
            "webhook_preference": 0.6,   # Prefer webhook over headless
            "ban_risk_weight": 2.0,      # Weight for ban risk cost
            "latency_weight": 0.01,      # Weight for latency cost
            "retry_boost": 1.2           # Boost for retry capability
        })
        self._connector_stats: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"successes": 0, "trials": 0, "avg_latency": 0}
        )

    def _exploit(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Select optimal connector"""
        available = state.get("connectors", ["api", "webhook", "headless"])
        pdl = state.get("pdl_id", "unknown")
        rate_limit_window = state.get("rate_limit_remaining", 100)
        tos_risk = state.get("tos_risk_score", 0.1)

        scores = {}
        for conn in available:
            stats = self._connector_stats[f"{pdl}:{conn}"]

            # UCB calculation
            if stats["trials"] == 0:
                ucb = float("inf")  # Explore untried
            else:
                success_rate = stats["successes"] / stats["trials"]
                exploration_bonus = math.sqrt(2 * math.log(sum(s["trials"] for s in self._connector_stats.values()) + 1) / stats["trials"])
                ucb = success_rate + exploration_bonus

            # Preference adjustment
            if conn == "api":
                ucb *= self.params["api_preference"]
            elif conn == "webhook":
                ucb *= self.params["webhook_preference"]

            # Risk adjustment
            if conn == "headless":
                ucb -= tos_risk * self.params["ban_risk_weight"]

            # Latency adjustment
            ucb -= stats["avg_latency"] * self.params["latency_weight"]

            # Rate limit check
            if rate_limit_window < 10 and conn == "api":
                ucb *= 0.5  # Penalize API when rate limited

            scores[conn] = ucb

        # Select best
        best = max(scores, key=scores.get)

        return {
            "action": "select",
            "params": self.params,
            "connector": best,
            "scores": {k: round(v, 3) for k, v in scores.items()},
            "retry_envelope": best != "headless"
        }

    def record_connector_outcome(self, pdl: str, connector: str, success: bool, latency_ms: float):
        """Record connector outcome for UCB updates"""
        key = f"{pdl}:{connector}"
        stats = self._connector_stats[key]
        stats["trials"] += 1
        if success:
            stats["successes"] += 1
        # Exponential moving average for latency
        stats["avg_latency"] = stats["avg_latency"] * 0.9 + latency_ms * 0.1


class PolicyEngine:
    """
    Policy engine that manages all policies.

    Provides consistent interface for:
    - Getting policy suggestions
    - Recording learning
    - Loading apex routes
    """

    def __init__(self):
        self._policies: Dict[str, Policy] = {
            "pricing.oaa": PricingPolicy(),
            "placement.market": PlacementPolicy(),
            "dealgraph.tranche": TranchingPolicy(),
            "connector.ucb": ConnectorPolicy()
        }

    def get(self, policy_name: str, scope: Dict[str, Any] = None) -> Policy:
        """Get policy by name"""
        if policy_name not in self._policies:
            # Create generic policy
            self._policies[policy_name] = Policy(policy_name)
        return self._policies[policy_name]

    def suggest(self, policy_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get suggestion from policy"""
        policy = self.get(policy_name)
        return policy.suggest(state)

    def learn(self, policy_name: str, state: Dict, action: Dict, reward: float, meta: Dict = None):
        """Record learning for policy"""
        policy = self.get(policy_name)
        policy.learn(state, action, reward, meta)

    def load_apex_routes(self, routes: List[Dict[str, Any]]):
        """Load apex routes into policies"""
        for route in routes:
            policy_name = route.get("route_id", "").replace("_", ".")
            if policy_name in self._policies:
                self._policies[policy_name].load_apex(route)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get metrics for all policies"""
        return {name: policy.get_metrics() for name, policy in self._policies.items()}


# Module-level singleton
_policy_engine = PolicyEngine()


def get_policy(policy_name: str, scope: Dict = None) -> Policy:
    """Get policy from default engine"""
    return _policy_engine.get(policy_name, scope)


def suggest(policy_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Get suggestion from default engine"""
    return _policy_engine.suggest(policy_name, state)


def learn(policy_name: str, state: Dict, action: Dict, reward: float, **kwargs):
    """Record learning in default engine"""
    return _policy_engine.learn(policy_name, state, action, reward, **kwargs)
