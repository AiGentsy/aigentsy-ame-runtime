# dashboard_api.py
"""
AiGentsy Dashboard API

Provides comprehensive dashboard data for users:
- AIGx balance and equity value
- Tier progression and unlock status
- Activity streaks and rewards
- Referral statistics
- Revenue breakdown
- APEX ULTRA system status
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from aigx_config import (
    AIGX_CONFIG,
    calculate_user_tier,
    calculate_equity_value,
    get_platform_fee
)
from log_to_jsonbin import get_user, list_users


def get_dashboard_data(username: str) -> Dict:
    """
    Get complete dashboard data for a user.
    
    Args:
        username: User's username
        
    Returns:
        dict: Complete dashboard data including AIGx, equity, tier, activity, etc.
    """
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "User not found"}
    
    # ============================================================
    # BASIC USER INFO
    # ============================================================
    
    basic_info = {
        "username": username,
        "user_number": user.get("userNumber"),
        "created": user.get("created"),
        "company_type": user.get("companyType")
    }
    
    # ============================================================
    # AIGX & EQUITY
    # ============================================================
    
    ownership = user.get("ownership", {})
    user_aigx = ownership.get("aigx", 0)
    
    # Calculate total AIGx in circulation
    all_users = list_users()
    total_aigx = sum(u.get("ownership", {}).get("aigx", 0) for u in all_users)
    
    # Calculate equity value
    equity_data = calculate_equity_value(user_aigx, total_aigx)
    
    aigx_equity = {
        "aigx_balance": user_aigx,
        "equity_percent": equity_data["equity_percent"],
        "equity_value_usd": equity_data["equity_value_usd"],
        "company_valuation": equity_data["company_valuation"],
        "total_aigx_in_circulation": total_aigx
    }
    
    # ============================================================
    # TIER PROGRESSION
    # ============================================================
    
    lifetime_revenue = user.get("lifetimeRevenue", 0.0)
    current_tier = user.get("currentTier", "free")
    calculated_tier = calculate_user_tier(lifetime_revenue)
    
    # Get tier details
    tier_config = AIGX_CONFIG["tier_progression"]
    current_tier_data = tier_config[current_tier]
    
    # Calculate next tier
    if current_tier == "free":
        next_tier = "pro"
        next_tier_threshold = tier_config["pro"]["unlock_at"]
        progress_to_next = lifetime_revenue / next_tier_threshold if next_tier_threshold > 0 else 0
        revenue_needed = max(0, next_tier_threshold - lifetime_revenue)
    elif current_tier == "pro":
        next_tier = "ultra"
        next_tier_threshold = tier_config["ultra"]["unlock_at"]
        progress_to_next = lifetime_revenue / next_tier_threshold if next_tier_threshold > 0 else 0
        revenue_needed = max(0, next_tier_threshold - lifetime_revenue)
    else:  # ultra
        next_tier = None
        next_tier_threshold = None
        progress_to_next = 1.0
        revenue_needed = 0
    
    tier_progression = {
        "current_tier": current_tier,
        "tier_multiplier": current_tier_data["aigx_multiplier"],
        "transaction_rate": current_tier_data["transaction_rate"],
        "features": current_tier_data["features"],
        "next_tier": next_tier,
        "next_tier_threshold": next_tier_threshold,
        "progress_to_next": round(progress_to_next * 100, 2),  # Percentage
        "revenue_needed": revenue_needed,
        "lifetime_revenue": lifetime_revenue
    }
    
    # ============================================================
    # EARLY ADOPTER STATUS
    # ============================================================
    
    early_adopter = {
        "tier": user.get("earlyAdopterTier"),
        "badge": user.get("earlyAdopterBadge"),
        "multiplier": user.get("aigxMultiplier", 1.0),
        "permanent": True  # Early adopter multiplier never expires
    }
    
    # ============================================================
    # EARNING RATE
    # ============================================================
    
    earning_rate = user.get("aigxEarningRate", {})
    total_multiplier = (
        current_tier_data["aigx_multiplier"] * 
        early_adopter["multiplier"]
    )
    
    earning_rates = {
        "tier_multiplier": current_tier_data["aigx_multiplier"],
        "early_adopter_multiplier": early_adopter["multiplier"],
        "total_multiplier": total_multiplier,
        "example": {
            "transaction_amount": 1000,
            "base_aigx": 10,  # $1000 / $100
            "aigx_earned": 10 * total_multiplier
        }
    }
    
    # ============================================================
    # ACTIVITY & STREAKS
    # ============================================================
    
    activity_tracking = user.get("activityTracking", {})
    
    activity_streaks = {
        "current_streak": activity_tracking.get("currentStreak", 0),
        "longest_streak": activity_tracking.get("longestStreak", 0),
        "total_active_days": activity_tracking.get("totalActiveDays", 0),
        "last_active": activity_tracking.get("lastActive"),
        "rewards": {
            "daily_claimed_today": _is_today(activity_tracking.get("lastDailyReward")),
            "weekly_eligible": activity_tracking.get("currentStreak", 0) >= 7,
            "monthly_eligible": activity_tracking.get("currentStreak", 0) >= 30
        }
    }
    
    # ============================================================
    # REFERRALS
    # ============================================================
    
    referral_tracking = user.get("referralTracking", {})
    
    referrals = {
        "total_referrals": referral_tracking.get("totalReferrals", 0),
        "active_referrals": referral_tracking.get("activeReferrals", 0),
        "milestones_achieved": referral_tracking.get("milestonesAchieved", []),
        "next_milestone": _get_next_referral_milestone(referral_tracking.get("totalReferrals", 0))
    }
    
    # ============================================================
    # REVENUE BREAKDOWN
    # ============================================================
    
    # Calculate revenue by source from ownership ledger
    ledger = ownership.get("ledger", [])
    revenue_by_source = {
        "transactions": 0,
        "daily_rewards": 0,
        "weekly_rewards": 0,
        "monthly_rewards": 0,
        "milestones": 0,
        "referrals": 0,
        "signup_bonus": 0,
        "apex_ultra": 0
    }
    
    for entry in ledger:
        basis = entry.get("basis", "")
        amount = entry.get("amount", 0)
        
        if "transaction" in basis:
            revenue_by_source["transactions"] += amount
        elif "daily" in basis:
            revenue_by_source["daily_rewards"] += amount
        elif "weekly" in basis:
            revenue_by_source["weekly_rewards"] += amount
        elif "monthly" in basis:
            revenue_by_source["monthly_rewards"] += amount
        elif "milestone" in basis:
            revenue_by_source["milestones"] += amount
        elif "referral" in basis:
            revenue_by_source["referrals"] += amount
        elif "signup_bonus" in basis:
            revenue_by_source["signup_bonus"] += amount
        elif "apex_ultra" in basis or "amg" in basis:
            revenue_by_source["apex_ultra"] += amount
    
    revenue_stats = {
        "lifetime_revenue_usd": lifetime_revenue,
        "aigx_by_source": revenue_by_source,
        "total_ledger_entries": len(ledger)
    }
    
    # ============================================================
    # APEX ULTRA STATUS
    # ============================================================
    
    apex_status = {
        "activated": True,  # All users get APEX on mint
        "systems_operational": 37,  # From your spec
        "total_systems": 43,
        "success_rate": round((37/43) * 100, 1),
        "template": user.get("template", "whitelabel_general")
    }
    
    # ============================================================
    # RECENT ACTIVITY (Last 10 ledger entries)
    # ============================================================
    
    recent_activity = []
    for entry in ledger[-10:]:
        recent_activity.append({
            "timestamp": entry.get("ts"),
            "amount": entry.get("amount", 0),
            "currency": entry.get("currency", "AIGx"),
            "basis": entry.get("basis", ""),
            "description": _format_basis_description(entry.get("basis", ""))
        })
    
    recent_activity.reverse()  # Most recent first
    
    # ============================================================
    # RETURN COMPLETE DASHBOARD DATA
    # ============================================================
    
    return {
        "ok": True,
        "user": basic_info,
        "aigx_equity": aigx_equity,
        "tier_progression": tier_progression,
        "early_adopter": early_adopter,
        "earning_rates": earning_rates,
        "activity_streaks": activity_streaks,
        "referrals": referrals,
        "revenue_stats": revenue_stats,
        "apex_ultra": apex_status,
        "recent_activity": recent_activity,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_leaderboard(metric: str = "aigx", limit: int = 100) -> Dict:
    """
    Get leaderboard for various metrics.
    
    Args:
        metric: What to rank by ("aigx", "revenue", "streak", "referrals")
        limit: Max number of users to return
        
    Returns:
        dict: Leaderboard data
    """
    
    all_users = list_users()
    
    # Sort based on metric
    if metric == "aigx":
        sorted_users = sorted(
            all_users, 
            key=lambda u: u.get("ownership", {}).get("aigx", 0),
            reverse=True
        )
    elif metric == "revenue":
        sorted_users = sorted(
            all_users,
            key=lambda u: u.get("lifetimeRevenue", 0),
            reverse=True
        )
    elif metric == "streak":
        sorted_users = sorted(
            all_users,
            key=lambda u: u.get("activityTracking", {}).get("currentStreak", 0),
            reverse=True
        )
    elif metric == "referrals":
        sorted_users = sorted(
            all_users,
            key=lambda u: u.get("referralTracking", {}).get("totalReferrals", 0),
            reverse=True
        )
    else:
        return {"ok": False, "error": f"Unknown metric: {metric}"}
    
    # Build leaderboard
    leaderboard = []
    for rank, user in enumerate(sorted_users[:limit], start=1):
        entry = {
            "rank": rank,
            "username": user.get("username"),
            "user_number": user.get("userNumber"),
            "early_adopter_badge": user.get("earlyAdopterBadge")
        }
        
        if metric == "aigx":
            entry["aigx"] = user.get("ownership", {}).get("aigx", 0)
        elif metric == "revenue":
            entry["revenue"] = user.get("lifetimeRevenue", 0)
        elif metric == "streak":
            entry["streak"] = user.get("activityTracking", {}).get("currentStreak", 0)
        elif metric == "referrals":
            entry["referrals"] = user.get("referralTracking", {}).get("totalReferrals", 0)
        
        leaderboard.append(entry)
    
    return {
        "ok": True,
        "metric": metric,
        "total_users": len(all_users),
        "showing": len(leaderboard),
        "leaderboard": leaderboard,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def get_platform_stats() -> Dict:
    """
    Get platform-wide statistics.
    
    Returns:
        dict: Platform statistics
    """
    
    all_users = list_users()
    total_users = len(all_users)
    
    # Calculate totals
    total_aigx = sum(u.get("ownership", {}).get("aigx", 0) for u in all_users)
    total_revenue = sum(u.get("lifetimeRevenue", 0) for u in all_users)
    
    # Tier distribution
    tier_counts = {"free": 0, "pro": 0, "ultra": 0}
    for user in all_users:
        tier = user.get("currentTier", "free")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    # Early adopter distribution
    early_adopter_counts = {
        "Founder": 0,
        "Early Adopter": 0,
        "Pioneer": 0,
        "Standard": 0
    }
    for user in all_users:
        badge = user.get("earlyAdopterBadge") or "Standard"
        early_adopter_counts[badge] = early_adopter_counts.get(badge, 0) + 1
    
    # Active users (last 7 days)
    now = datetime.now(timezone.utc)
    active_7d = sum(
        1 for u in all_users 
        if u.get("activityTracking", {}).get("lastActive") and
        (now - datetime.fromisoformat(u["activityTracking"]["lastActive"].replace("Z", "+00:00"))).days <= 7
    )
    
    return {
        "ok": True,
        "platform": {
            "total_users": total_users,
            "total_aigx_distributed": total_aigx,
            "total_revenue_generated": total_revenue,
            "company_valuation": AIGX_CONFIG["company_valuation"],
            "equity_pool_percent": AIGX_CONFIG["equity_pool_percent"]
        },
        "distribution": {
            "tiers": tier_counts,
            "early_adopters": early_adopter_counts
        },
        "activity": {
            "active_last_7_days": active_7d,
            "active_percentage": round((active_7d / total_users * 100) if total_users > 0 else 0, 2)
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _is_today(date_str: Optional[str]) -> bool:
    """Check if a date string is today."""
    if not date_str:
        return False
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return date_str == today


def _get_next_referral_milestone(total_referrals: int) -> Optional[Dict]:
    """Get next referral milestone info."""
    milestones = [
        ("first_referral", 1, 500),
        ("referral_5", 5, 2000),
        ("referral_10", 10, 5000)
    ]
    
    for key, threshold, reward in milestones:
        if total_referrals < threshold:
            return {
                "milestone": key,
                "threshold": threshold,
                "reward": reward,
                "referrals_needed": threshold - total_referrals
            }
    
    return None  # All milestones achieved


def _format_basis_description(basis: str) -> str:
    """Format basis string into readable description."""
    descriptions = {
        "apex_ultra_activation": "APEX ULTRA Activation",
        "amg_revenue_brain_activation": "AMG Revenue Brain",
        "early_adopter_signup_bonus": "Early Adopter Bonus",
        "transaction_revenue": "Transaction Revenue",
        "milestone_first_sale": "First Sale Milestone",
        "milestone_reward": "Revenue Milestone",
        "daily_activity_reward": "Daily Login",
        "weekly_streak_reward": "Weekly Streak",
        "monthly_power_user_reward": "Monthly Power User",
        "referral_milestone": "Referral Milestone",
        "tier_upgrade": "Tier Upgrade"
    }
    return descriptions.get(basis, basis.replace("_", " ").title())


# ============================================================
# FASTAPI ENDPOINT HELPERS
# ============================================================

def create_dashboard_endpoints(app):
    """
    Add dashboard endpoints to FastAPI app.
    
    Usage:
        from dashboard_api import create_dashboard_endpoints
        create_dashboard_endpoints(app)
    """
    
    @app.get("/dashboard/{username}")
    async def dashboard_get(username: str):
        """Get complete dashboard data for user"""
        return get_dashboard_data(username)
    
    @app.get("/leaderboard")
    async def leaderboard_get(metric: str = "aigx", limit: int = 100):
        """Get leaderboard"""
        return get_leaderboard(metric, limit)
    
    @app.get("/platform/stats")
    async def platform_stats_get():
        """Get platform-wide statistics"""
        return get_platform_stats()
