"""
SUBSCRIPTIONS
=============

Subscription tiers with SLAs, API quotas, and burst credits.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from .fee_schedule import get_fee
from .ledger import post_entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class Subscriptions:
    """
    Subscription tier management.

    Tiers:
    - starter: $49/mo, 50k API calls, standard SLA
    - pro: $199/mo, 200k API calls, priority SLA
    - scale: $799/mo, 2M API calls, priority+ SLA
    - enterprise: Custom pricing
    """

    TIERS = {
        "free": {
            "price_monthly": 0,
            "api_calls_monthly": 1000,
            "sla": "best_effort",
            "burst_credits_included": 0,
            "features": ["basic_discovery", "manual_fulfillment"]
        },
        "starter": {
            "price_monthly": 49,
            "api_calls_monthly": 50000,
            "sla": "standard",
            "burst_credits_included": 10,
            "features": ["discovery", "auto_fulfillment", "basic_analytics"]
        },
        "pro": {
            "price_monthly": 199,
            "api_calls_monthly": 200000,
            "sla": "priority",
            "burst_credits_included": 50,
            "features": ["discovery", "auto_fulfillment", "advanced_analytics", "ame_auto", "metabridge"]
        },
        "scale": {
            "price_monthly": 799,
            "api_calls_monthly": 2000000,
            "sla": "priority_plus",
            "burst_credits_included": 200,
            "features": ["all", "dedicated_support", "custom_connectors", "white_label_lite"]
        },
        "enterprise": {
            "price_monthly": None,  # Custom
            "api_calls_monthly": None,  # Unlimited
            "sla": "enterprise",
            "burst_credits_included": 1000,
            "features": ["all", "dedicated_infra", "sla_guarantees", "full_white_label"]
        }
    }

    SLA_RESPONSE_TIMES = {
        "best_effort": {"p50_ms": 5000, "p95_ms": 15000, "p99_ms": 30000},
        "standard": {"p50_ms": 2000, "p95_ms": 5000, "p99_ms": 10000},
        "priority": {"p50_ms": 1000, "p95_ms": 2000, "p99_ms": 5000},
        "priority_plus": {"p50_ms": 500, "p95_ms": 1000, "p99_ms": 2000},
        "enterprise": {"p50_ms": 200, "p95_ms": 500, "p99_ms": 1000}
    }

    def __init__(self):
        self._subscriptions: Dict[str, Dict[str, Any]] = {}
        self._usage: Dict[str, Dict[str, int]] = {}  # user -> {period: count}
        self._burst_balances: Dict[str, int] = {}    # user -> burst credits

    def get_tier(self, tier_name: str) -> Dict[str, Any]:
        """Get tier details"""
        if tier_name not in self.TIERS:
            return {"ok": False, "error": f"unknown_tier:{tier_name}"}

        tier = self.TIERS[tier_name]
        sla = self.SLA_RESPONSE_TIMES.get(tier["sla"], {})

        return {
            "ok": True,
            "tier": tier_name,
            **tier,
            "sla_targets": sla
        }

    def subscribe(
        self,
        user: str,
        tier: str,
        billing_period: str = "monthly"
    ) -> Dict[str, Any]:
        """
        Subscribe user to a tier.

        Args:
            user: Username
            tier: Tier name
            billing_period: monthly or annual (20% discount)
        """
        if tier not in self.TIERS:
            return {"ok": False, "error": f"unknown_tier:{tier}"}

        tier_info = self.TIERS[tier]
        monthly_price = tier_info["price_monthly"]

        if monthly_price is None:
            return {"ok": False, "error": "enterprise_requires_custom_quote"}

        # Calculate price
        if billing_period == "annual":
            price = round(monthly_price * 12 * 0.80, 2)  # 20% discount
            period_days = 365
        else:
            price = monthly_price
            period_days = 30

        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=period_days)

        subscription = {
            "id": f"sub_{uuid4().hex[:10]}",
            "user": user,
            "tier": tier,
            "price": price,
            "billing_period": billing_period,
            "created_at": now.isoformat() + "Z",
            "expires_at": expires.isoformat() + "Z",
            "status": "active"
        }

        self._subscriptions[user] = subscription

        # Initialize burst credits
        self._burst_balances[user] = tier_info["burst_credits_included"]

        # Reset usage
        period_key = now.strftime("%Y-%m")
        self._usage[user] = {period_key: 0}

        # Record in ledger
        post_entry(
            "subscription",
            f"entity:{user}",
            debit=price,
            credit=0,
            meta={"tier": tier, "billing_period": billing_period}
        )

        post_entry(
            "subscription_revenue",
            "entity:aigentsy_platform",
            debit=0,
            credit=price,
            meta={"user": user, "tier": tier}
        )

        return {
            "ok": True,
            "subscription": subscription,
            "burst_credits": self._burst_balances[user]
        }

    def get_subscription(self, user: str) -> Dict[str, Any]:
        """Get user's subscription"""
        sub = self._subscriptions.get(user)
        if not sub:
            return {"ok": True, "tier": "free", "subscription": None}

        # Check if expired
        expires = datetime.fromisoformat(sub["expires_at"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            sub["status"] = "expired"

        return {
            "ok": True,
            "tier": sub["tier"] if sub["status"] == "active" else "free",
            "subscription": sub,
            "burst_credits": self._burst_balances.get(user, 0)
        }

    def check_quota(
        self,
        user: str,
        calls_needed: int = 1
    ) -> Dict[str, Any]:
        """
        Check if user has API quota available.

        Returns:
            ok: True if quota available
            can_burst: True if can use burst credits
            overage_cost: Cost if using overage
        """
        sub_info = self.get_subscription(user)
        tier_name = sub_info.get("tier", "free")
        tier = self.TIERS.get(tier_name, self.TIERS["free"])

        # Get current period usage
        period_key = datetime.now(timezone.utc).strftime("%Y-%m")
        user_usage = self._usage.get(user, {})
        current_usage = user_usage.get(period_key, 0)

        monthly_limit = tier["api_calls_monthly"] or float("inf")
        remaining = max(0, monthly_limit - current_usage)

        if remaining >= calls_needed:
            return {
                "ok": True,
                "remaining": remaining,
                "within_quota": True
            }

        # Check burst credits
        burst_available = self._burst_balances.get(user, 0)
        if burst_available >= calls_needed:
            return {
                "ok": True,
                "remaining": 0,
                "within_quota": False,
                "can_burst": True,
                "burst_available": burst_available
            }

        # Calculate overage cost
        overage_rate = get_fee("api_overage_per_k", 1.50)
        overage_cost = round((calls_needed - remaining) / 1000 * overage_rate, 4)

        return {
            "ok": False,
            "remaining": remaining,
            "within_quota": False,
            "can_burst": False,
            "overage_calls": calls_needed - remaining,
            "overage_cost": overage_cost,
            "upgrade_suggested": tier_name in ["free", "starter"]
        }

    def record_usage(self, user: str, calls: int = 1) -> Dict[str, Any]:
        """Record API usage"""
        period_key = datetime.now(timezone.utc).strftime("%Y-%m")

        if user not in self._usage:
            self._usage[user] = {}

        self._usage[user][period_key] = self._usage[user].get(period_key, 0) + calls

        return {
            "ok": True,
            "period": period_key,
            "total_calls": self._usage[user][period_key]
        }

    def use_burst_credit(self, user: str, credits: int = 1) -> Dict[str, Any]:
        """Use burst credits"""
        available = self._burst_balances.get(user, 0)
        if available < credits:
            return {"ok": False, "error": "insufficient_burst_credits", "available": available}

        self._burst_balances[user] -= credits

        return {
            "ok": True,
            "used": credits,
            "remaining": self._burst_balances[user]
        }

    def purchase_burst_credits(self, user: str, quantity: int) -> Dict[str, Any]:
        """Purchase additional burst credits"""
        price_per_credit = get_fee("burst_credit_price", 0.10)
        total_price = round(quantity * price_per_credit, 2)

        self._burst_balances[user] = self._burst_balances.get(user, 0) + quantity

        post_entry(
            "burst_purchase",
            f"entity:{user}",
            debit=total_price,
            credit=0,
            meta={"quantity": quantity, "price_per": price_per_credit}
        )

        return {
            "ok": True,
            "quantity": quantity,
            "price": total_price,
            "new_balance": self._burst_balances[user]
        }


# Module-level singleton
_default_subscriptions = Subscriptions()


def get_tier(tier_name: str) -> Dict[str, Any]:
    """Get tier details"""
    return _default_subscriptions.get_tier(tier_name)


def check_quota(user: str, calls_needed: int = 1) -> Dict[str, Any]:
    """Check user quota"""
    return _default_subscriptions.check_quota(user, calls_needed)


def subscribe(user: str, tier: str, **kwargs) -> Dict[str, Any]:
    """Subscribe user"""
    return _default_subscriptions.subscribe(user, tier, **kwargs)


def record_usage(user: str, calls: int = 1) -> Dict[str, Any]:
    """Record API usage"""
    return _default_subscriptions.record_usage(user, calls)


def get_subscription_stats() -> Dict[str, Any]:
    """Get subscription statistics"""
    subs = _default_subscriptions._subscriptions
    active = len([s for s in subs.values() if s.get("status") == "active"])
    mrr = sum(
        s.get("price", 0) / (12 if s.get("billing_period") == "annual" else 1)
        for s in subs.values()
        if s.get("status") == "active"
    )
    return {
        "ok": True,
        "total_subscribers": len(subs),
        "active_subscriptions": active,
        "mrr": round(mrr, 2),
        "arr": round(mrr * 12, 2)
    }
