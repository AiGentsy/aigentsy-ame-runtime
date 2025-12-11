# subscription_engine.py
"""
AiGentsy Subscription Engine - Feature #7

Recurring revenue through outcome subscriptions:
- Monthly outcome packages (Bronze/Silver/Gold/Platinum)
- Per-outcome subscriptions
- Credit allocation and rollover
- Subscriber priority queue
- Savings calculations

Integrates with:
- intent_exchange_UPGRADED.py (subscription-funded intents)
- outcome_oracle.py (subscription outcome tracking)
- analytics_engine.py (MRR, churn analysis)
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
import json

# Subscription tier definitions
SUBSCRIPTION_TIERS = {
    "bronze": {
        "name": "Bronze",
        "outcomes_per_month": 5,
        "price_monthly": 499,  # $4.99
        "price_annual": 4990,  # $49.90 (2 months free)
        "one_time_equivalent": 625,  # 5 outcomes @ $125 avg
        "rollover_cap_percent": 0.5,  # Max 50% rollover
        "priority_level": 1,
        "features": [
            "5 outcomes per month",
            "20% savings vs one-time",
            "Rollover up to 2.5 credits",
            "Priority queue Level 1",
            "Cancel anytime"
        ]
    },
    "silver": {
        "name": "Silver",
        "outcomes_per_month": 15,
        "price_monthly": 1299,  # $12.99
        "price_annual": 12990,  # $129.90 (2 months free)
        "one_time_equivalent": 1875,  # 15 outcomes @ $125 avg
        "rollover_cap_percent": 0.5,
        "priority_level": 2,
        "features": [
            "15 outcomes per month",
            "31% savings vs one-time",
            "Rollover up to 7.5 credits",
            "Priority queue Level 2",
            "Cancel anytime"
        ]
    },
    "gold": {
        "name": "Gold",
        "outcomes_per_month": 30,
        "price_monthly": 2399,  # $23.99
        "price_annual": 23990,  # $239.90 (2 months free)
        "one_time_equivalent": 3750,  # 30 outcomes @ $125 avg
        "rollover_cap_percent": 0.5,
        "priority_level": 3,
        "features": [
            "30 outcomes per month",
            "36% savings vs one-time",
            "Rollover up to 15 credits",
            "Priority queue Level 3",
            "Cancel anytime"
        ]
    },
    "platinum": {
        "name": "Platinum",
        "outcomes_per_month": 999,  # Effectively unlimited
        "price_monthly": 4999,  # $49.99
        "price_annual": 49990,  # $499.90 (2 months free)
        "one_time_equivalent": 12500,  # 100 outcomes @ $125 avg
        "rollover_cap_percent": 0.5,
        "priority_level": 4,
        "features": [
            "Unlimited outcomes",
            "60% savings vs one-time",
            "Rollover up to 499 credits",
            "Priority queue Level 4 (highest)",
            "Cancel anytime",
            "Dedicated support"
        ]
    }
}

# In-memory subscription storage (use JSONBin in production)
SUBSCRIPTIONS_DB = {}
SUBSCRIPTION_USAGE_DB = {}


def create_subscription(
    username: str,
    tier: str,
    billing_cycle: str = "monthly",
    stripe_subscription_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new outcome subscription.
    
    Args:
        username: User's username
        tier: Subscription tier (bronze/silver/gold/platinum)
        billing_cycle: monthly or annual
        stripe_subscription_id: Stripe subscription ID
    
    Returns:
        Subscription object with credits and status
    """
    if tier not in SUBSCRIPTION_TIERS:
        raise ValueError(f"Invalid tier: {tier}")
    
    if billing_cycle not in ["monthly", "annual"]:
        raise ValueError(f"Invalid billing cycle: {billing_cycle}")
    
    tier_config = SUBSCRIPTION_TIERS[tier]
    
    subscription_id = f"sub_{username}_{tier}_{int(datetime.now(timezone.utc).timestamp())}"
    
    # Calculate billing amount
    price_key = f"price_{billing_cycle}"
    billing_amount = tier_config[price_key]
    
    # Create subscription
    subscription = {
        "subscription_id": subscription_id,
        "username": username,
        "tier": tier,
        "tier_name": tier_config["name"],
        "billing_cycle": billing_cycle,
        "billing_amount": billing_amount,
        "outcomes_per_month": tier_config["outcomes_per_month"],
        "credits_remaining": tier_config["outcomes_per_month"],  # Start with full allocation
        "credits_used_this_month": 0,
        "rollover_cap": int(tier_config["outcomes_per_month"] * tier_config["rollover_cap_percent"]),
        "priority_level": tier_config["priority_level"],
        "status": "active",
        "stripe_subscription_id": stripe_subscription_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "current_period_start": datetime.now(timezone.utc).isoformat(),
        "current_period_end": _calculate_period_end(billing_cycle),
        "next_billing_date": _calculate_period_end(billing_cycle),
        "total_credits_allocated": tier_config["outcomes_per_month"],
        "total_credits_used": 0,
        "months_subscribed": 0,
        "canceled_at": None,
        "ends_at": None
    }
    
    SUBSCRIPTIONS_DB[subscription_id] = subscription
    
    return subscription


def _calculate_period_end(billing_cycle: str) -> str:
    """Calculate end of current billing period."""
    now = datetime.now(timezone.utc)
    
    if billing_cycle == "monthly":
        # Add 30 days
        period_end = now + timedelta(days=30)
    else:  # annual
        # Add 365 days
        period_end = now + timedelta(days=365)
    
    return period_end.isoformat()


def process_monthly_allocation(subscription_id: str) -> Dict[str, Any]:
    """
    Process monthly credit allocation with rollover.
    Called automatically at billing cycle renewal.
    
    Args:
        subscription_id: Subscription ID
    
    Returns:
        Updated subscription with new credits
    """
    if subscription_id not in SUBSCRIPTIONS_DB:
        raise ValueError(f"Subscription not found: {subscription_id}")
    
    subscription = SUBSCRIPTIONS_DB[subscription_id]
    
    if subscription["status"] != "active":
        return subscription
    
    tier = subscription["tier"]
    tier_config = SUBSCRIPTION_TIERS[tier]
    
    # Calculate rollover credits
    unused_credits = subscription["credits_remaining"]
    rollover_cap = subscription["rollover_cap"]
    rollover_credits = min(unused_credits, rollover_cap)
    
    # Allocate new credits + rollover
    new_monthly_allocation = tier_config["outcomes_per_month"]
    total_credits = new_monthly_allocation + rollover_credits
    
    # Update subscription
    subscription["credits_remaining"] = total_credits
    subscription["credits_used_this_month"] = 0
    subscription["current_period_start"] = datetime.now(timezone.utc).isoformat()
    subscription["current_period_end"] = _calculate_period_end(subscription["billing_cycle"])
    subscription["next_billing_date"] = _calculate_period_end(subscription["billing_cycle"])
    subscription["total_credits_allocated"] += new_monthly_allocation
    subscription["months_subscribed"] += 1
    
    SUBSCRIPTIONS_DB[subscription_id] = subscription
    
    return {
        "subscription_id": subscription_id,
        "new_credits": new_monthly_allocation,
        "rollover_credits": rollover_credits,
        "total_credits": total_credits,
        "message": f"Monthly allocation processed: {new_monthly_allocation} new + {rollover_credits} rollover = {total_credits} total credits"
    }


def use_subscription_credit(
    username: str,
    intent_id: str,
    credits_to_use: int = 1
) -> Dict[str, Any]:
    """
    Use subscription credit(s) for an intent.
    
    Args:
        username: User's username
        intent_id: Intent ID being funded
        credits_to_use: Number of credits to use (default 1)
    
    Returns:
        Usage record and updated subscription
    """
    # Find active subscription
    subscription = get_active_subscription(username)
    
    if not subscription:
        raise ValueError(f"No active subscription for user: {username}")
    
    # Check credit balance
    if subscription["credits_remaining"] < credits_to_use:
        raise ValueError(
            f"Insufficient credits. Remaining: {subscription['credits_remaining']}, "
            f"Required: {credits_to_use}"
        )
    
    # Deduct credits
    subscription["credits_remaining"] -= credits_to_use
    subscription["credits_used_this_month"] += credits_to_use
    subscription["total_credits_used"] += credits_to_use
    
    SUBSCRIPTIONS_DB[subscription["subscription_id"]] = subscription
    
    # Record usage
    usage_id = f"usage_{username}_{intent_id}_{int(datetime.now(timezone.utc).timestamp())}"
    usage_record = {
        "usage_id": usage_id,
        "subscription_id": subscription["subscription_id"],
        "username": username,
        "intent_id": intent_id,
        "credits_used": credits_to_use,
        "credits_remaining_after": subscription["credits_remaining"],
        "used_at": datetime.now(timezone.utc).isoformat()
    }
    
    SUBSCRIPTION_USAGE_DB[usage_id] = usage_record
    
    return {
        "success": True,
        "usage_id": usage_id,
        "credits_used": credits_to_use,
        "credits_remaining": subscription["credits_remaining"],
        "subscription_tier": subscription["tier_name"],
        "message": f"Used {credits_to_use} credit(s). {subscription['credits_remaining']} remaining."
    }


def get_active_subscription(username: str) -> Optional[Dict[str, Any]]:
    """Get user's active subscription (if any)."""
    for sub in SUBSCRIPTIONS_DB.values():
        if sub["username"] == username and sub["status"] == "active":
            return sub
    return None


def get_subscription_status(username: str) -> Dict[str, Any]:
    """
    Get comprehensive subscription status for user.
    
    Returns:
        Status including credits, tier, billing info
    """
    subscription = get_active_subscription(username)
    
    if not subscription:
        return {
            "has_subscription": False,
            "message": "No active subscription"
        }
    
    # Calculate days until renewal
    period_end = datetime.fromisoformat(subscription["current_period_end"])
    now = datetime.now(timezone.utc)
    days_until_renewal = (period_end - now).days
    
    # Calculate usage percentage
    monthly_allocation = SUBSCRIPTION_TIERS[subscription["tier"]]["outcomes_per_month"]
    usage_percent = (subscription["credits_used_this_month"] / monthly_allocation) * 100
    
    return {
        "has_subscription": True,
        "subscription_id": subscription["subscription_id"],
        "tier": subscription["tier"],
        "tier_name": subscription["tier_name"],
        "status": subscription["status"],
        "billing_cycle": subscription["billing_cycle"],
        "billing_amount": subscription["billing_amount"],
        "credits_remaining": subscription["credits_remaining"],
        "credits_used_this_month": subscription["credits_used_this_month"],
        "monthly_allocation": monthly_allocation,
        "usage_percent": round(usage_percent, 1),
        "rollover_cap": subscription["rollover_cap"],
        "priority_level": subscription["priority_level"],
        "days_until_renewal": days_until_renewal,
        "next_billing_date": subscription["next_billing_date"],
        "months_subscribed": subscription["months_subscribed"],
        "total_credits_used": subscription["total_credits_used"]
    }


def calculate_subscription_savings(tier: str, billing_cycle: str = "monthly") -> Dict[str, Any]:
    """
    Calculate savings for a subscription tier vs one-time purchases.
    
    Args:
        tier: Subscription tier
        billing_cycle: monthly or annual
    
    Returns:
        Savings breakdown
    """
    if tier not in SUBSCRIPTION_TIERS:
        raise ValueError(f"Invalid tier: {tier}")
    
    tier_config = SUBSCRIPTION_TIERS[tier]
    
    # Get pricing
    price_key = f"price_{billing_cycle}"
    subscription_price = tier_config[price_key]
    one_time_equivalent = tier_config["one_time_equivalent"]
    
    # Calculate for billing cycle
    if billing_cycle == "annual":
        subscription_price_effective = subscription_price  # Already annual
        one_time_equivalent_effective = one_time_equivalent * 12  # 12 months
    else:
        subscription_price_effective = subscription_price
        one_time_equivalent_effective = one_time_equivalent
    
    # Calculate savings
    savings_amount = one_time_equivalent_effective - subscription_price_effective
    savings_percent = (savings_amount / one_time_equivalent_effective) * 100
    
    # Per-outcome cost
    outcomes_per_period = tier_config["outcomes_per_month"]
    if billing_cycle == "annual":
        outcomes_per_period *= 12
    
    cost_per_outcome = subscription_price_effective / outcomes_per_period if outcomes_per_period > 0 else 0
    one_time_cost_per_outcome = one_time_equivalent_effective / outcomes_per_period if outcomes_per_period > 0 else 0
    
    return {
        "tier": tier,
        "tier_name": tier_config["name"],
        "billing_cycle": billing_cycle,
        "subscription_price": subscription_price_effective,
        "one_time_equivalent": one_time_equivalent_effective,
        "savings_amount": savings_amount,
        "savings_percent": round(savings_percent, 2),
        "cost_per_outcome": round(cost_per_outcome, 2),
        "one_time_cost_per_outcome": round(one_time_cost_per_outcome, 2),
        "outcomes_included": outcomes_per_period,
        "message": f"Save ${savings_amount/100:.2f} ({savings_percent:.1f}%) with {tier_config['name']} subscription"
    }


def check_subscriber_priority(username: str) -> Dict[str, Any]:
    """
    Check if user has subscriber priority in queue.
    
    Returns:
        Priority status and level
    """
    subscription = get_active_subscription(username)
    
    if not subscription:
        return {
            "has_priority": False,
            "priority_level": 0,
            "message": "No active subscription - standard queue"
        }
    
    return {
        "has_priority": True,
        "priority_level": subscription["priority_level"],
        "tier": subscription["tier_name"],
        "message": f"Priority Level {subscription['priority_level']} - {subscription['tier_name']} subscriber"
    }


def cancel_subscription(subscription_id: str, immediate: bool = False) -> Dict[str, Any]:
    """
    Cancel a subscription.
    
    Args:
        subscription_id: Subscription ID
        immediate: If True, cancel immediately. If False, cancel at period end.
    
    Returns:
        Cancellation confirmation
    """
    if subscription_id not in SUBSCRIPTIONS_DB:
        raise ValueError(f"Subscription not found: {subscription_id}")
    
    subscription = SUBSCRIPTIONS_DB[subscription_id]
    
    if subscription["status"] == "canceled":
        return {
            "success": False,
            "message": "Subscription already canceled"
        }
    
    canceled_at = datetime.now(timezone.utc).isoformat()
    
    if immediate:
        # Cancel immediately
        subscription["status"] = "canceled"
        subscription["canceled_at"] = canceled_at
        subscription["ends_at"] = canceled_at
        subscription["credits_remaining"] = 0  # Forfeit remaining credits
        
        message = "Subscription canceled immediately. Credits forfeited."
    else:
        # Cancel at period end (keep credits until then)
        subscription["status"] = "canceling"
        subscription["canceled_at"] = canceled_at
        subscription["ends_at"] = subscription["current_period_end"]
        
        message = f"Subscription will cancel on {subscription['ends_at']}. Credits remain until then."
    
    SUBSCRIPTIONS_DB[subscription_id] = subscription
    
    return {
        "success": True,
        "subscription_id": subscription_id,
        "status": subscription["status"],
        "canceled_at": canceled_at,
        "ends_at": subscription["ends_at"],
        "credits_remaining": subscription["credits_remaining"],
        "message": message
    }


def get_all_subscription_tiers() -> Dict[str, Any]:
    """Get all available subscription tiers with pricing."""
    tiers = {}
    
    for tier_key, tier_config in SUBSCRIPTION_TIERS.items():
        # Calculate savings
        monthly_savings = calculate_subscription_savings(tier_key, "monthly")
        annual_savings = calculate_subscription_savings(tier_key, "annual")
        
        tiers[tier_key] = {
            "name": tier_config["name"],
            "outcomes_per_month": tier_config["outcomes_per_month"],
            "pricing": {
                "monthly": {
                    "price": tier_config["price_monthly"],
                    "display": f"${tier_config['price_monthly']/100:.2f}/mo",
                    "savings_percent": monthly_savings["savings_percent"]
                },
                "annual": {
                    "price": tier_config["price_annual"],
                    "display": f"${tier_config['price_annual']/100:.2f}/yr",
                    "monthly_equivalent": f"${tier_config['price_annual']/100/12:.2f}/mo",
                    "savings_percent": annual_savings["savings_percent"],
                    "discount": "2 months free"
                }
            },
            "features": tier_config["features"],
            "priority_level": tier_config["priority_level"],
            "rollover_cap": int(tier_config["outcomes_per_month"] * tier_config["rollover_cap_percent"])
        }
    
    return tiers


def get_user_subscription_history(username: str) -> Dict[str, Any]:
    """Get complete subscription history for user."""
    user_subscriptions = [
        sub for sub in SUBSCRIPTIONS_DB.values()
        if sub["username"] == username
    ]
    
    # Sort by creation date
    user_subscriptions.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Get usage records
    user_usage = [
        usage for usage in SUBSCRIPTION_USAGE_DB.values()
        if usage["username"] == username
    ]
    
    # Calculate totals
    total_credits_used = sum(usage["credits_used"] for usage in user_usage)
    total_months_subscribed = sum(sub["months_subscribed"] for sub in user_subscriptions)
    total_spent = sum(
        sub["billing_amount"] * sub["months_subscribed"]
        for sub in user_subscriptions
    )
    
    return {
        "username": username,
        "subscriptions": user_subscriptions,
        "usage_history": user_usage,
        "summary": {
            "total_subscriptions": len(user_subscriptions),
            "total_credits_used": total_credits_used,
            "total_months_subscribed": total_months_subscribed,
            "total_spent": total_spent,
            "average_monthly_spend": total_spent / total_months_subscribed if total_months_subscribed > 0 else 0
        }
    }


def calculate_mrr() -> Dict[str, Any]:
    """
    Calculate Monthly Recurring Revenue (MRR) across all subscriptions.
    
    Returns:
        MRR breakdown by tier and billing cycle
    """
    active_subscriptions = [
        sub for sub in SUBSCRIPTIONS_DB.values()
        if sub["status"] == "active"
    ]
    
    mrr_by_tier = {}
    total_mrr = 0
    
    for tier in SUBSCRIPTION_TIERS.keys():
        tier_subs = [sub for sub in active_subscriptions if sub["tier"] == tier]
        
        tier_mrr = 0
        for sub in tier_subs:
            if sub["billing_cycle"] == "monthly":
                tier_mrr += sub["billing_amount"]
            else:  # annual
                tier_mrr += sub["billing_amount"] / 12  # Normalize to monthly
        
        mrr_by_tier[tier] = {
            "subscriber_count": len(tier_subs),
            "mrr": tier_mrr,
            "display": f"${tier_mrr/100:.2f}/mo"
        }
        
        total_mrr += tier_mrr
    
    return {
        "total_mrr": total_mrr,
        "total_mrr_display": f"${total_mrr/100:.2f}/mo",
        "annual_run_rate": total_mrr * 12,
        "annual_run_rate_display": f"${(total_mrr * 12)/100:.2f}/yr",
        "total_subscribers": len(active_subscriptions),
        "by_tier": mrr_by_tier,
        "calculated_at": datetime.now(timezone.utc).isoformat()
    }


def handle_rollover(subscription_id: str) -> Dict[str, Any]:
    """
    Handle credit rollover at end of billing period.
    Called automatically by process_monthly_allocation.
    
    Args:
        subscription_id: Subscription ID
    
    Returns:
        Rollover details
    """
    if subscription_id not in SUBSCRIPTIONS_DB:
        raise ValueError(f"Subscription not found: {subscription_id}")
    
    subscription = SUBSCRIPTIONS_DB[subscription_id]
    
    unused_credits = subscription["credits_remaining"]
    rollover_cap = subscription["rollover_cap"]
    
    # Calculate rollover
    if unused_credits <= rollover_cap:
        rollover_credits = unused_credits
        forfeited_credits = 0
    else:
        rollover_credits = rollover_cap
        forfeited_credits = unused_credits - rollover_cap
    
    return {
        "subscription_id": subscription_id,
        "unused_credits": unused_credits,
        "rollover_cap": rollover_cap,
        "rollover_credits": rollover_credits,
        "forfeited_credits": forfeited_credits,
        "message": f"Rolling over {rollover_credits} credits. {forfeited_credits} forfeited (over cap)."
    }


# Example usage
if __name__ == "__main__":
    # Create subscription
    sub = create_subscription("wade999", "gold", "monthly")
    print(f"Created subscription: {sub['subscription_id']}")
    print(f"Credits: {sub['credits_remaining']}")
    
    # Use credits
    usage = use_subscription_credit("wade999", "intent_123", 1)
    print(f"\nUsed credit: {usage['message']}")
    
    # Check status
    status = get_subscription_status("wade999")
    print(f"\nStatus: {status['tier_name']}")
    print(f"Credits remaining: {status['credits_remaining']}")
    print(f"Days until renewal: {status['days_until_renewal']}")
    
    # Calculate savings
    savings = calculate_subscription_savings("gold", "annual")
    print(f"\nSavings: {savings['message']}")
    
    # Get all tiers
    tiers = get_all_subscription_tiers()
    print(f"\nAvailable tiers: {', '.join(tiers.keys())}")
    
    # Calculate MRR
    mrr = calculate_mrr()
    print(f"\nMRR: {mrr['total_mrr_display']}")
    print(f"ARR: {mrr['annual_run_rate_display']}")
