"""
OUTCOME SUBSCRIPTIONS & RETAINERS
=================================

Extends subscription_engine.py with:
- Outcome-as-a-Service retainer packages
- Per-category subscriptions
- Rollover credits with decay
- Priority fulfillment queue
- Corporate retainer accounts

Revenue:
- 2% processing fee on all subscription payments
- Credit expiry recapture (unused credits after 90 days)

Usage:
    from outcome_subscriptions import create_retainer, use_credit, get_subscriber_status
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4
from collections import defaultdict

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Retainer package definitions
RETAINER_PACKAGES = {
    "starter": {
        "name": "Starter",
        "credits_per_month": 10,
        "price_monthly": 99.00,
        "price_annual": 990.00,
        "rollover_max_months": 2,
        "priority_level": 1,
        "categories": ["all"],
        "max_single_outcome": 100,
        "features": ["10 credits/month", "2-month rollover", "Standard priority"]
    },
    "professional": {
        "name": "Professional",
        "credits_per_month": 30,
        "price_monthly": 249.00,
        "price_annual": 2490.00,
        "rollover_max_months": 3,
        "priority_level": 2,
        "categories": ["all"],
        "max_single_outcome": 250,
        "features": ["30 credits/month", "3-month rollover", "Priority queue", "24h SLA"]
    },
    "business": {
        "name": "Business",
        "credits_per_month": 100,
        "price_monthly": 699.00,
        "price_annual": 6990.00,
        "rollover_max_months": 3,
        "priority_level": 3,
        "categories": ["all"],
        "max_single_outcome": 500,
        "features": ["100 credits/month", "3-month rollover", "High priority", "12h SLA", "Dedicated support"]
    },
    "enterprise": {
        "name": "Enterprise",
        "credits_per_month": 500,
        "price_monthly": 2499.00,
        "price_annual": 24990.00,
        "rollover_max_months": 6,
        "priority_level": 4,
        "categories": ["all"],
        "max_single_outcome": 2500,
        "features": ["500 credits/month", "6-month rollover", "Top priority", "4h SLA", "Account manager", "Custom integrations"]
    }
}

# Category-specific subscriptions
CATEGORY_SUBSCRIPTIONS = {
    "code": {"name": "Code & Development", "credit_multiplier": 1.0},
    "design": {"name": "Design & Creative", "credit_multiplier": 1.2},
    "writing": {"name": "Content & Writing", "credit_multiplier": 0.8},
    "data": {"name": "Data & Analytics", "credit_multiplier": 1.5},
    "research": {"name": "Research", "credit_multiplier": 1.0},
}

# Fee structure
PROCESSING_FEE_PCT = 0.02  # 2% on subscription payments
CREDIT_DECAY_DAYS = 90  # Credits expire after 90 days of non-use

# Storage
_RETAINERS: Dict[str, Dict[str, Any]] = {}
_CREDIT_LEDGER: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_USAGE_HISTORY: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_PRIORITY_QUEUE: List[Dict[str, Any]] = []


class OutcomeSubscriptions:
    """
    Manages outcome subscriptions and retainer accounts.
    """

    def __init__(self):
        self.packages = RETAINER_PACKAGES
        self.categories = CATEGORY_SUBSCRIPTIONS
        self.processing_fee = PROCESSING_FEE_PCT
        self.credit_decay_days = CREDIT_DECAY_DAYS

    def create_retainer(
        self,
        subscriber_id: str,
        package: str,
        *,
        billing_cycle: str = "monthly",
        categories: list = None,
        company_name: str = None,
        stripe_customer_id: str = None,
        metadata: dict = None
    ) -> Dict[str, Any]:
        """
        Create a new outcome retainer account.

        Args:
            subscriber_id: Unique subscriber ID
            package: Package name (starter, professional, business, enterprise)
            billing_cycle: monthly or annual
            categories: Specific categories to subscribe to (None = all)
            company_name: Company name for corporate accounts
            stripe_customer_id: Stripe customer ID
            metadata: Additional metadata

        Returns:
            Retainer account details
        """
        if package not in self.packages:
            return {"ok": False, "error": "invalid_package", "valid_packages": list(self.packages.keys())}

        if billing_cycle not in ["monthly", "annual"]:
            return {"ok": False, "error": "invalid_billing_cycle"}

        if subscriber_id in _RETAINERS:
            return {"ok": False, "error": "subscriber_already_exists"}

        pkg = self.packages[package]
        price_key = f"price_{billing_cycle}"
        price = pkg[price_key]

        # Calculate processing fee
        processing_fee = round(price * self.processing_fee, 2)

        retainer_id = f"ret_{subscriber_id}_{uuid4().hex[:6]}"

        retainer = {
            "id": retainer_id,
            "subscriber_id": subscriber_id,
            "package": package,
            "package_name": pkg["name"],
            "billing_cycle": billing_cycle,
            "price": price,
            "processing_fee": processing_fee,
            "credits_per_month": pkg["credits_per_month"],
            "credits_available": pkg["credits_per_month"],  # Start with full allocation
            "credits_used_total": 0,
            "rollover_credits": 0,
            "rollover_max_months": pkg["rollover_max_months"],
            "priority_level": pkg["priority_level"],
            "categories": categories or pkg["categories"],
            "max_single_outcome": pkg["max_single_outcome"],
            "company_name": company_name,
            "stripe_customer_id": stripe_customer_id,
            "metadata": metadata or {},
            "status": "ACTIVE",
            "created_at": _now(),
            "current_period_start": _now(),
            "current_period_end": self._calculate_period_end(billing_cycle),
            "next_renewal": self._calculate_period_end(billing_cycle),
            "events": [{"type": "RETAINER_CREATED", "package": package, "at": _now()}]
        }

        _RETAINERS[subscriber_id] = retainer

        # Add initial credits to ledger
        self._add_credits_to_ledger(subscriber_id, pkg["credits_per_month"], "initial_allocation")

        # Post fee to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="subscription_fee",
                ref=f"retainer:{retainer_id}",
                debit=0,
                credit=processing_fee,
                meta={
                    "subscriber_id": subscriber_id,
                    "package": package,
                    "subscription_amount": price
                }
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "retainer": retainer,
            "processing_fee": processing_fee,
            "message": f"Created {pkg['name']} retainer with {pkg['credits_per_month']} credits"
        }

    def _calculate_period_end(self, billing_cycle: str) -> str:
        """Calculate period end date"""
        if billing_cycle == "annual":
            end = datetime.now(timezone.utc) + timedelta(days=365)
        else:
            end = datetime.now(timezone.utc) + timedelta(days=30)
        return end.isoformat() + "Z"

    def _add_credits_to_ledger(self, subscriber_id: str, amount: int, source: str):
        """Add credits to subscriber's credit ledger"""
        credit_entry = {
            "id": f"cred_{uuid4().hex[:8]}",
            "amount": amount,
            "remaining": amount,
            "source": source,
            "added_at": _now(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=self.credit_decay_days)).isoformat() + "Z"
        }
        _CREDIT_LEDGER[subscriber_id].append(credit_entry)

    def use_credit(
        self,
        subscriber_id: str,
        credits_needed: int,
        *,
        outcome_id: str = None,
        category: str = "general",
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Use credits from retainer account.

        Args:
            subscriber_id: Subscriber ID
            credits_needed: Number of credits to use
            outcome_id: Outcome being fulfilled
            category: Category of outcome
            description: Description

        Returns:
            Credit usage result
        """
        retainer = _RETAINERS.get(subscriber_id)
        if not retainer:
            return {"ok": False, "error": "retainer_not_found"}

        if retainer["status"] != "ACTIVE":
            return {"ok": False, "error": f"retainer_is_{retainer['status'].lower()}"}

        # Check category eligibility
        if "all" not in retainer["categories"] and category not in retainer["categories"]:
            return {"ok": False, "error": "category_not_covered", "allowed_categories": retainer["categories"]}

        # Apply category multiplier
        category_config = self.categories.get(category, {"credit_multiplier": 1.0})
        adjusted_credits = int(credits_needed * category_config.get("credit_multiplier", 1.0))

        # Check single outcome limit
        if adjusted_credits > retainer["max_single_outcome"]:
            return {
                "ok": False,
                "error": "exceeds_single_outcome_limit",
                "requested": adjusted_credits,
                "max": retainer["max_single_outcome"]
            }

        # Consume credits FIFO from ledger (oldest first)
        credits_consumed = 0
        ledger_entries = _CREDIT_LEDGER[subscriber_id]

        # Remove expired credits first
        now = datetime.now(timezone.utc)
        ledger_entries = [
            e for e in ledger_entries
            if datetime.fromisoformat(e["expires_at"].replace("Z", "+00:00")) > now and e["remaining"] > 0
        ]
        _CREDIT_LEDGER[subscriber_id] = ledger_entries

        for entry in ledger_entries:
            if credits_consumed >= adjusted_credits:
                break
            available = entry["remaining"]
            to_consume = min(available, adjusted_credits - credits_consumed)
            entry["remaining"] -= to_consume
            credits_consumed += to_consume

        if credits_consumed < adjusted_credits:
            return {
                "ok": False,
                "error": "insufficient_credits",
                "needed": adjusted_credits,
                "available": sum(e["remaining"] for e in ledger_entries)
            }

        # Update retainer
        retainer["credits_available"] = sum(e["remaining"] for e in ledger_entries)
        retainer["credits_used_total"] += adjusted_credits

        # Record usage
        usage = {
            "id": f"usage_{uuid4().hex[:8]}",
            "subscriber_id": subscriber_id,
            "outcome_id": outcome_id,
            "category": category,
            "credits_requested": credits_needed,
            "credits_charged": adjusted_credits,
            "category_multiplier": category_config.get("credit_multiplier", 1.0),
            "description": description,
            "used_at": _now()
        }

        _USAGE_HISTORY[subscriber_id].append(usage)

        retainer["events"].append({
            "type": "CREDITS_USED",
            "credits": adjusted_credits,
            "outcome_id": outcome_id,
            "at": _now()
        })

        return {
            "ok": True,
            "usage": usage,
            "credits_remaining": retainer["credits_available"],
            "priority_level": retainer["priority_level"]
        }

    def renew_retainer(self, subscriber_id: str) -> Dict[str, Any]:
        """
        Renew retainer and add monthly credits.
        Called by billing webhook on successful payment.
        """
        retainer = _RETAINERS.get(subscriber_id)
        if not retainer:
            return {"ok": False, "error": "retainer_not_found"}

        pkg = self.packages[retainer["package"]]

        # Calculate rollover
        current_credits = retainer["credits_available"]
        max_rollover = pkg["credits_per_month"] * pkg["rollover_max_months"]
        rollover = min(current_credits, max_rollover)

        # Add new credits
        new_credits = pkg["credits_per_month"]
        total_credits = rollover + new_credits

        # Update retainer
        retainer["credits_available"] = total_credits
        retainer["rollover_credits"] = rollover
        retainer["current_period_start"] = _now()
        retainer["current_period_end"] = self._calculate_period_end(retainer["billing_cycle"])
        retainer["next_renewal"] = retainer["current_period_end"]

        # Add to credit ledger
        self._add_credits_to_ledger(subscriber_id, new_credits, "renewal")

        # Calculate processing fee
        processing_fee = round(retainer["price"] * self.processing_fee, 2)

        retainer["events"].append({
            "type": "RETAINER_RENEWED",
            "new_credits": new_credits,
            "rollover": rollover,
            "at": _now()
        })

        # Post fee
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="subscription_renewal_fee",
                ref=f"retainer:{retainer['id']}",
                debit=0,
                credit=processing_fee,
                meta={"subscriber_id": subscriber_id, "renewal": True}
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "subscriber_id": subscriber_id,
            "new_credits": new_credits,
            "rollover": rollover,
            "total_credits": total_credits,
            "processing_fee": processing_fee,
            "next_renewal": retainer["next_renewal"]
        }

    def upgrade_package(
        self,
        subscriber_id: str,
        new_package: str,
        *,
        prorate: bool = True
    ) -> Dict[str, Any]:
        """
        Upgrade subscriber to a higher package.
        """
        retainer = _RETAINERS.get(subscriber_id)
        if not retainer:
            return {"ok": False, "error": "retainer_not_found"}

        if new_package not in self.packages:
            return {"ok": False, "error": "invalid_package"}

        old_pkg = self.packages[retainer["package"]]
        new_pkg = self.packages[new_package]

        if new_pkg["credits_per_month"] <= old_pkg["credits_per_month"]:
            return {"ok": False, "error": "can_only_upgrade_to_higher_package"}

        old_package = retainer["package"]

        # Add bonus credits for upgrade (difference)
        bonus_credits = new_pkg["credits_per_month"] - old_pkg["credits_per_month"]

        retainer["package"] = new_package
        retainer["package_name"] = new_pkg["name"]
        retainer["credits_per_month"] = new_pkg["credits_per_month"]
        retainer["credits_available"] += bonus_credits
        retainer["priority_level"] = new_pkg["priority_level"]
        retainer["max_single_outcome"] = new_pkg["max_single_outcome"]
        retainer["rollover_max_months"] = new_pkg["rollover_max_months"]
        retainer["price"] = new_pkg[f"price_{retainer['billing_cycle']}"]

        self._add_credits_to_ledger(subscriber_id, bonus_credits, "upgrade_bonus")

        retainer["events"].append({
            "type": "PACKAGE_UPGRADED",
            "from": old_package,
            "to": new_package,
            "bonus_credits": bonus_credits,
            "at": _now()
        })

        return {
            "ok": True,
            "subscriber_id": subscriber_id,
            "old_package": old_package,
            "new_package": new_package,
            "bonus_credits": bonus_credits,
            "new_credits_available": retainer["credits_available"],
            "new_priority_level": retainer["priority_level"]
        }

    def get_subscriber_status(self, subscriber_id: str) -> Dict[str, Any]:
        """Get subscriber's current status"""
        retainer = _RETAINERS.get(subscriber_id)
        if not retainer:
            return {"ok": False, "error": "retainer_not_found"}

        return {
            "subscriber_id": subscriber_id,
            "package": retainer["package"],
            "package_name": retainer["package_name"],
            "status": retainer["status"],
            "credits_available": retainer["credits_available"],
            "credits_used_total": retainer["credits_used_total"],
            "rollover_credits": retainer["rollover_credits"],
            "priority_level": retainer["priority_level"],
            "categories": retainer["categories"],
            "next_renewal": retainer["next_renewal"],
            "features": self.packages[retainer["package"]]["features"]
        }

    def add_to_priority_queue(
        self,
        subscriber_id: str,
        outcome_id: str,
        *,
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """Add outcome to priority fulfillment queue"""
        retainer = _RETAINERS.get(subscriber_id)
        if not retainer:
            return {"ok": False, "error": "retainer_not_found"}

        urgency_boost = {"normal": 0, "high": 1, "urgent": 2}.get(urgency, 0)
        priority_score = retainer["priority_level"] + urgency_boost

        queue_entry = {
            "id": f"pq_{uuid4().hex[:8]}",
            "subscriber_id": subscriber_id,
            "outcome_id": outcome_id,
            "priority_level": retainer["priority_level"],
            "urgency": urgency,
            "priority_score": priority_score,
            "added_at": _now()
        }

        # Insert sorted by priority score (higher = first)
        _PRIORITY_QUEUE.append(queue_entry)
        _PRIORITY_QUEUE.sort(key=lambda x: (-x["priority_score"], x["added_at"]))

        position = _PRIORITY_QUEUE.index(queue_entry) + 1

        return {
            "ok": True,
            "queue_entry": queue_entry,
            "queue_position": position,
            "total_in_queue": len(_PRIORITY_QUEUE)
        }

    def get_retainer(self, subscriber_id: str) -> Optional[Dict[str, Any]]:
        """Get full retainer details"""
        return _RETAINERS.get(subscriber_id)

    def get_usage_history(self, subscriber_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get subscriber's usage history"""
        history = _USAGE_HISTORY.get(subscriber_id, [])
        return list(reversed(history[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Get subscription statistics"""
        total_subscribers = len(_RETAINERS)
        active_subscribers = len([r for r in _RETAINERS.values() if r["status"] == "ACTIVE"])
        total_credits_issued = sum(r["credits_per_month"] for r in _RETAINERS.values())
        total_credits_used = sum(r["credits_used_total"] for r in _RETAINERS.values())

        mrr = sum(
            r["price"] / (12 if r["billing_cycle"] == "annual" else 1)
            for r in _RETAINERS.values()
            if r["status"] == "ACTIVE"
        )

        return {
            "total_subscribers": total_subscribers,
            "active_subscribers": active_subscribers,
            "by_package": {
                pkg: len([r for r in _RETAINERS.values() if r["package"] == pkg])
                for pkg in self.packages.keys()
            },
            "total_credits_issued": total_credits_issued,
            "total_credits_used": total_credits_used,
            "credit_utilization_rate": round(total_credits_used / total_credits_issued, 4) if total_credits_issued > 0 else 0,
            "mrr": round(mrr, 2),
            "arr": round(mrr * 12, 2),
            "priority_queue_length": len(_PRIORITY_QUEUE)
        }


# Module-level singleton
_subscriptions = OutcomeSubscriptions()


def create_retainer(subscriber_id: str, package: str, **kwargs) -> Dict[str, Any]:
    """Create outcome retainer account"""
    return _subscriptions.create_retainer(subscriber_id, package, **kwargs)


def use_credit(subscriber_id: str, credits_needed: int, **kwargs) -> Dict[str, Any]:
    """Use credits from retainer"""
    return _subscriptions.use_credit(subscriber_id, credits_needed, **kwargs)


def renew_retainer(subscriber_id: str) -> Dict[str, Any]:
    """Renew retainer (called by billing webhook)"""
    return _subscriptions.renew_retainer(subscriber_id)


def upgrade_package(subscriber_id: str, new_package: str, **kwargs) -> Dict[str, Any]:
    """Upgrade subscriber package"""
    return _subscriptions.upgrade_package(subscriber_id, new_package, **kwargs)


def get_subscriber_status(subscriber_id: str) -> Dict[str, Any]:
    """Get subscriber status"""
    return _subscriptions.get_subscriber_status(subscriber_id)


def add_to_priority_queue(subscriber_id: str, outcome_id: str, **kwargs) -> Dict[str, Any]:
    """Add to priority fulfillment queue"""
    return _subscriptions.add_to_priority_queue(subscriber_id, outcome_id, **kwargs)


def get_retainer(subscriber_id: str) -> Optional[Dict[str, Any]]:
    """Get retainer details"""
    return _subscriptions.get_retainer(subscriber_id)


def get_usage_history(subscriber_id: str, limit: int = 50) -> list:
    """Get usage history"""
    return _subscriptions.get_usage_history(subscriber_id, limit)


def get_subscription_stats() -> Dict[str, Any]:
    """Get subscription statistics"""
    return _subscriptions.get_stats()


def get_subscription_tiers() -> Dict[str, Any]:
    """Get available subscription tiers"""
    return _subscriptions.packages
