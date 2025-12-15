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
from typing import Dict, Optional, Any, List

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
    
    # Get APEX ULTRA data from user record (set during mint)
    apex_ultra_data = user.get("apexUltra", {})
    systems_operational = apex_ultra_data.get("systemsActivated", 43)  # Defaults to 43

    apex_status = {
        "activated": apex_ultra_data.get("activated", True),
        "systems_operational": systems_operational,  # ← NOW READS FROM USER!
        "total_systems": 43,
        "success_rate": round((systems_operational/43) * 100, 1),
        "template": apex_ultra_data.get("template", user.get("template", "whitelabel_general"))
    }
    
    # ============================================================
    # OPPORTUNITIES (Template-generated revenue opportunities)
    # ============================================================
    
    opportunities = user.get("opportunities", [])
    
    # Enrich opportunities with additional context
    enriched_opportunities = []
    for opp in opportunities:
        enriched_opp = {
            **opp,
            "days_since_created": _days_since(opp.get("created_at")),
            "urgency": _calculate_urgency(opp)
        }
        enriched_opportunities.append(enriched_opp)
    
    # Sort by estimated value (highest first)
    enriched_opportunities.sort(key=lambda x: x.get("estimated_value", 0), reverse=True)
    
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
    # UNIVERSAL OUTCOME LEDGER (UoL) WIDGET
    # ============================================================
    
    from analytics_engine import get_uol_summary
    
    uol_data = get_uol_summary(username)
    
    uol_widget = {
        "total_outcomes": uol_data.get("total_outcomes", 0),
        "total_uoo": uol_data.get("total_uoo", 0),
        "average_uoo": uol_data.get("average_uoo", 0),
        "percentile": uol_data.get("percentile", 0),
        "by_archetype": uol_data.get("by_archetype", {})
    }
    
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
        "opportunities": enriched_opportunities,
        "recent_activity": recent_activity,
        "uol": uol_widget,  # NEW: UoL widget data
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


def _days_since(timestamp_str: Optional[str]) -> int:
    """Calculate days since a timestamp"""
    if not timestamp_str:
        return 0
    
    try:
        created = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - created
        return delta.days
    except:
        return 0


def _calculate_urgency(opportunity: Dict) -> str:
    """Calculate urgency level for an opportunity"""
    days_old = _days_since(opportunity.get("created_at"))
    confidence = opportunity.get("confidence", 0)
    estimated_value = opportunity.get("estimated_value", 0)
    
    # High urgency: high value + high confidence + fresh
    if estimated_value > 5000 and confidence > 0.7 and days_old < 3:
        return "high"
    
    # Medium urgency: decent value or getting old
    if estimated_value > 1000 or days_old > 7:
        return "medium"
    
    # Low urgency: everything else
    return "low"


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
    
    # ============================================================
    # UNIVERSAL OUTCOME LEDGER (UoL) ENDPOINTS
    # ============================================================
    
    @app.get("/uol/summary")
    async def uol_summary_get(username: str):
        """
        Get UoL summary for user.
        
        Returns total outcomes, UoO score, percentile, and breakdowns
        by archetype, difficulty, and value band.
        """
        from analytics_engine import get_uol_summary
        return get_uol_summary(username)
    
    @app.get("/uol/by_sku")
    async def uol_by_sku_get(username: str):
        """
        Get UoO breakdown by SKU (archetype).
        
        Useful for showing which types of work the user excels at.
        """
        from analytics_engine import get_uol_summary
        
        summary = get_uol_summary(username)
        
        if not summary.get("ok"):
            return summary
        
        by_archetype = summary.get("by_archetype", {})
        
        # Format for frontend
        sku_breakdown = []
        for archetype, data in by_archetype.items():
            sku_breakdown.append({
                "sku": archetype,
                "sku_name": data.get("name", archetype.title()),
                "count": data.get("count", 0),
                "total_uoo": data.get("total_uoo", 0),
                "avg_uoo": data.get("avg_uoo", 0)
            })
        
        # Sort by total_uoo descending
        sku_breakdown.sort(key=lambda x: x["total_uoo"], reverse=True)
        
        return {
            "ok": True,
            "username": username,
            "total_outcomes": summary.get("total_outcomes", 0),
            "total_uoo": summary.get("total_uoo", 0),
            "by_sku": sku_breakdown
        }
    
    @app.get("/uol/by_date")
    async def uol_by_date_get(username: str, days: int = 30):
        """
        Get UoO over time (daily aggregates).
        
        Useful for charts showing outcome velocity.
        Args:
            days: Number of days to look back (default 30)
        """
        from analytics_engine import get_uol_by_date
        return get_uol_by_date(username, days)
    
    @app.get("/uol/export")
    async def uol_export_get(username: str, format: str = "csv"):
        """
        Export all PoO receipts with UoO metadata.
        
        Args:
            format: "csv" or "json" (default csv)
        """
        from analytics_engine import export_uol_receipts
        from fastapi.responses import PlainTextResponse
        
        if format == "json":
            receipts = export_uol_receipts(username, format="json")
            return {"ok": True, "receipts": receipts, "count": len(receipts)}
        else:
            csv_content = export_uol_receipts(username, format="csv")
            return PlainTextResponse(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=uol_export_{username}.csv"
                }
            )
    
    # ============================================================
    # VALUE ROUTER - REVENUE ENDPOINTS
    # ============================================================
    
    @app.get("/revenue/yield_statement")
    async def revenue_yield_statement_get(username: str, period_days: int = 30):
        """
        Get unified yield statement showing all revenue sources.
        
        Returns revenue breakdown by source (Shopify, Affiliate, Services, SaaS, etc.)
        with percentages and totals.
        
        Args:
            period_days: Number of days to look back (default 30)
        """
        from analytics_engine import get_yield_statement
        return get_yield_statement(username, period_days)
    
    @app.get("/revenue/by_rail")
    async def revenue_by_rail_get(username: str):
        """
        Get revenue breakdown by "rail" (source category).
        
        Rails include: Services, SaaS, Affiliate, CPM, Shopify, Bundles, Chains, Other
        """
        from analytics_engine import get_revenue_by_rail
        return get_revenue_by_rail(username)
    
    @app.get("/revenue/breakdown")
    async def revenue_breakdown_get(username: str, period_days: int = 30):
        """
        Get detailed revenue breakdown with trend analysis.
        
        Includes:
        - Current period revenue
        - Previous period comparison
        - Growth rate
        - Trend status (growing/declining/stable)
        
        Args:
            period_days: Number of days for current period (default 30)
        """
        from analytics_engine import get_revenue_breakdown
        return get_revenue_breakdown(username, period_days)
    
    @app.get("/pricing/explain")
    async def pricing_explain_get(
        base_price: float,
        agent: str,
        intent_id: str = None,
        service_type: str = "general",
        buyer: str = None
    ):
        """
        Get pricing explanation for "Why this price?" modal.
        
        Returns:
        - Market analysis (similar deals, price range)
        - Agent's historical average
        - Price adjustments breakdown
        - Win probability
        - Confidence score
        
        Args:
            base_price: Recommended price to explain
            agent: Agent username
            intent_id: Optional intent ID
            service_type: Type of service
            buyer: Optional buyer username
        """
        from pricing_oracle import explain_price
        
        context = {
            "service_type": service_type,
            "buyer": buyer
        }
        
        return await explain_price(base_price, agent, intent_id, context)
    
    # ============================================================
    # DELIVERY MODE - DIY/DWY/DFY ENDPOINTS
    # ============================================================
    
    @app.get("/pricing/modes")
    async def pricing_modes_get(base_price: float, modes: str = "DIY,DWY,DFY"):
        """
        Get pricing breakdown for all delivery modes.
        
        Returns pricing for DIY (Do-It-Yourself), DWY (Done-With-You),
        and DFY (Done-For-You) delivery modes.
        
        Args:
            base_price: Base DFY (full service) price
            modes: Comma-separated list of modes (default: all)
            
        Example:
            GET /pricing/modes?base_price=11500
            
        Returns:
            {
              "by_mode": {
                "DIY": {"price": 4200, "savings_pct": 64, ...},
                "DWY": {"price": 6800, "savings_pct": 41, ...},
                "DFY": {"price": 11500, "savings_pct": 0, ...}
              }
            }
        """
        from pricing_oracle import calculate_mode_pricing
        
        mode_list = [m.strip().upper() for m in modes.split(",")]
        return calculate_mode_pricing(base_price, mode_list)
    
    @app.get("/pricing/mode/calculate")
    async def pricing_mode_calculate_get(base_price: float, mode: str):
        """
        Calculate price for a specific delivery mode.
        
        Args:
            base_price: Base DFY price
            mode: Delivery mode (DIY/DWY/DFY)
            
        Returns:
            Calculated price for the specified mode
        """
        from pricing_oracle import calculate_mode_price
        
        mode_price = calculate_mode_price(base_price, mode)
        
        return {
            "ok": True,
            "base_price": base_price,
            "mode": mode.upper(),
            "mode_price": mode_price
        }
    
    @app.get("/pricing/mode/recommend")
    async def pricing_mode_recommend_get(
        buyer_budget: float,
        buyer_experience: str = "beginner",
        buyer_time: str = "limited"
    ):
        """
        Recommend optimal delivery mode based on buyer context.
        
        Args:
            buyer_budget: Buyer's maximum budget
            buyer_experience: Experience level (beginner/intermediate/advanced)
            buyer_time: Time availability (limited/moderate/abundant)
            
        Returns:
            Recommended mode with reasoning
        """
        from pricing_oracle import recommend_mode
        
        return recommend_mode(buyer_budget, buyer_experience, buyer_time)
    
    # ============================================================
    # PASSPORT BADGES & SOCIAL PROOF ENDPOINTS
    # ============================================================
    
    @app.get("/badges/user/{username}")
    async def badges_user_get(username: str):
        """
        Get all earned badges for a user.
        
        Returns badges, badge count, total points, and user stats.
        
        Example:
            GET /badges/user/wade
            
        Returns:
            {
              "badges": [...],
              "badge_count": 8,
              "total_points": 1235,
              "stats": {...}
            }
        """
        from badge_engine import get_user_badges
        return get_user_badges(username)
    
    @app.get("/badges/progress/{username}")
    async def badges_progress_get(username: str):
        """
        Get progress toward earning locked badges.
        
        Shows which badges user hasn't earned yet and how close they are.
        
        Example:
            GET /badges/progress/wade
            
        Returns:
            {
              "locked_badges": [
                {
                  "name": "Elite Producer",
                  "progress": {"verified_outcomes": {"current": 75, "required": 100}},
                  "overall_progress": 75.0
                }
              ]
            }
        """
        from badge_engine import get_badge_progress
        return get_badge_progress(username)
    
    @app.get("/badges/catalog")
    async def badges_catalog_get():
        """
        Get complete badge catalog.
        
        Returns all available badges with criteria and rewards.
        
        Example:
            GET /badges/catalog
            
        Returns:
            {
              "badges": [...],
              "total_badges": 17,
              "tiers": ["bronze", "silver", "gold", "platinum"]
            }
        """
        from badge_engine import list_all_badges
        return list_all_badges()
    
    @app.get("/badges/info/{badge_id}")
    async def badge_info_get(badge_id: str):
        """
        Get details for a specific badge.
        
        Args:
            badge_id: Badge identifier (e.g., "first_outcome", "uoo_100")
            
        Returns:
            Badge definition with criteria and rewards
        """
        from badge_engine import get_badge_info
        return get_badge_info(badge_id)
    
    @app.get("/social_proof/{username}")
    async def social_proof_get(username: str):
        """
        Get social proof signals for a user.
        
        Includes:
        - Badges earned
        - Verification status
        - Rating/outcome score
        - Portfolio highlights
        - Trust signals
        
        Used to display trust indicators on profiles and proposals.
        
        Example:
            GET /social_proof/wade
            
        Returns:
            {
              "verification_level": "elite",
              "rating": {"stars": 4.3, "outcome_score": 86},
              "badges": {"count": 8, "top_tier": "gold"},
              "portfolio_highlights": [...],
              "trust_signals": [...]
            }
        """
        from badge_engine import get_social_proof
        return get_social_proof(username)
    
    # ============================================================
    # OCL P2P LENDING ENDPOINTS
    # ============================================================
    
    @app.get("/ocl/credit_score/{username}")
    async def ocl_credit_score_get(username: str):
        """
        Get UoO-based credit score for user.
        
        Credit score: 300-850 (FICO-like scale)
        Based on: UoO (40%), verification rate (30%), revenue (20%), account age (10%)
        
        Returns:
            {
              "credit_score": 720,
              "tier": "good",
              "max_loan_amount": 25000,
              "components": {...}
            }
        """
        from ocl_p2p_lending import calculate_credit_score
        return calculate_credit_score(username)
    
    @app.post("/ocl/loan_offer/create")
    async def ocl_loan_offer_create_post(
        lender_username: str,
        amount: float,
        interest_rate: float,
        duration_days: int,
        min_credit_score: int = 600
    ):
        """
        Create loan offer (lender stakes capital).
        
        Args:
            lender_username: Username of lender
            amount: Amount to lend
            interest_rate: Annual interest rate (e.g., 12.0 for 12%)
            duration_days: Loan duration
            min_credit_score: Minimum credit score required
        """
        from ocl_p2p_lending import create_loan_offer
        return create_loan_offer(lender_username, amount, interest_rate, duration_days, min_credit_score)
    
    @app.post("/ocl/loan_request/create")
    async def ocl_loan_request_create_post(
        borrower_username: str,
        amount: float,
        purpose: str,
        duration_days: int = 30
    ):
        """
        Create loan request (borrower seeks capital).
        
        Auto-matches with available loan offers.
        
        Args:
            borrower_username: Username of borrower
            amount: Amount needed
            purpose: Loan purpose
            duration_days: Desired duration
        """
        from ocl_p2p_lending import create_loan_request
        return create_loan_request(borrower_username, amount, purpose, duration_days)
    
    @app.post("/ocl/loan/accept")
    async def ocl_loan_accept_post(request_id: str, offer_id: str):
        """
        Accept loan offer (complete the loan).
        
        Transfers funds and creates active loan.
        """
        from ocl_p2p_lending import accept_loan_offer
        return accept_loan_offer(request_id, offer_id)
    
    @app.post("/ocl/loan/payment")
    async def ocl_loan_payment_post(loan_id: str, payment_amount: float):
        """
        Make payment toward loan.
        """
        from ocl_p2p_lending import make_loan_payment
        return make_loan_payment(loan_id, payment_amount)
    
    @app.post("/ocl/loan/auto_repay")
    async def ocl_loan_auto_repay_post(
        username: str,
        earnings_amount: float,
        repayment_percentage: float = 0.5
    ):
        """
        Auto-repay loans from earnings.
        
        Default: 50% of earnings go to loan repayment.
        """
        from ocl_p2p_lending import auto_repay_from_earnings
        return auto_repay_from_earnings(username, earnings_amount, repayment_percentage)
    
    @app.get("/ocl/loans/active/{username}")
    async def ocl_loans_active_get(username: str, role: str = "borrower"):
        """
        Get active loans for user.
        
        Args:
            username: User to query
            role: "borrower" or "lender"
        """
        from ocl_p2p_lending import get_active_loans
        return get_active_loans(username, role)
    
    @app.get("/ocl/loans/history/{username}")
    async def ocl_loans_history_get(username: str):
        """
        Get complete loan history for user.
        
        Returns loans as both borrower and lender.
        """
        from ocl_p2p_lending import get_loan_history
        return get_loan_history(username)
    
    @app.get("/ocl/offers/available")
    async def ocl_offers_available_get(min_amount: float = 0, max_interest: float = 100):
        """
        List all available loan offers in marketplace.
        
        Args:
            min_amount: Minimum loan amount
            max_interest: Maximum interest rate
        """
        from ocl_p2p_lending import list_available_offers
        return list_available_offers(min_amount, max_interest)
    
    # ============================================================
    # DARK POOL - PREMIUM INTENTS ENDPOINTS
    # ============================================================
    
    @app.get("/dark_pool/access/{username}")
    async def dark_pool_access_get(username: str):
        """
        Check user's dark pool access level based on UoO score.
        
        Returns:
            {
              "current_tier": "gold",
              "access_level": "premium",
              "can_access_dark_pool": true,
              "deal_value_range": {"min": 5000, "max": 20000},
              "next_tier": "platinum",
              "uoo_needed_for_next_tier": 80
            }
        """
        from dark_pool import check_dark_pool_access
        return check_dark_pool_access(username)
    
    @app.get("/dark_pool/qualify")
    async def dark_pool_qualify_get(username: str, intent_value: float):
        """
        Check if user qualifies for specific dark pool intent.
        
        Args:
            username: Agent username
            intent_value: Deal value of intent
            
        Returns qualification status and requirements.
        """
        from dark_pool import qualify_for_dark_pool_intent
        return qualify_for_dark_pool_intent(username, intent_value)
    
    @app.post("/dark_pool/auction/create")
    async def dark_pool_auction_create_post(
        intent: Dict[str, Any],
        min_uoo_required: float = 200,
        min_reputation_tier: str = "gold",
        auction_duration_hours: int = 48
    ):
        """
        Create premium dark pool auction.
        
        Args:
            intent: Intent to auction
            min_uoo_required: Minimum UoO to participate (default: 200)
            min_reputation_tier: Minimum reputation tier (default: gold)
            auction_duration_hours: Duration in hours (default: 48)
        """
        from dark_pool import create_premium_dark_pool_auction
        return create_premium_dark_pool_auction(
            intent,
            min_uoo_required,
            min_reputation_tier,
            auction_duration_hours
        )
    
    @app.post("/dark_pool/bid/submit")
    async def dark_pool_bid_submit_post(
        auction: Dict[str, Any],
        agent_user: Dict[str, Any],
        bid_amount: float,
        delivery_hours: int,
        proposal_summary: str = ""
    ):
        """
        Submit bid to premium dark pool auction.
        
        Includes automatic qualification checks.
        """
        from dark_pool import submit_premium_dark_pool_bid
        return submit_premium_dark_pool_bid(
            auction,
            agent_user,
            bid_amount,
            delivery_hours,
            proposal_summary
        )
    
    @app.get("/dark_pool/leaderboard")
    async def dark_pool_leaderboard_get(limit: int = 10):
        """
        Get dark pool leaderboard of top performers.
        
        Args:
            limit: Number of top performers to return (default: 10)
        """
        # This would need access to all auctions - implementation depends on storage
        return {
            "ok": True,
            "leaderboard": [],
            "message": "Leaderboard requires auction storage implementation"
        }
    
    @app.get("/dark_pool/unlock/{username}")
    async def dark_pool_unlock_get(username: str):
        """
        Check if user has unlocked dark pool access.
        
        Returns milestone status and badge if earned.
        """
        from dark_pool import unlock_dark_pool_milestone
        return unlock_dark_pool_milestone(username)
    
    # ========================================
    # FEATURE #7: OUTCOME SUBSCRIPTIONS
    # ========================================
    
    @app.post("/subscriptions/create")
    async def subscription_create_post(
        username: str,
        tier: str,
        billing_cycle: str = "monthly",
        stripe_subscription_id: Optional[str] = None
    ):
        """
        Create a new outcome subscription.
        
        Args:
            username: User's username
            tier: bronze/silver/gold/platinum
            billing_cycle: monthly or annual
            stripe_subscription_id: Stripe subscription ID (optional)
        
        Returns:
            Subscription object with credits allocated
        """
        from subscription_engine import create_subscription
        return create_subscription(username, tier, billing_cycle, stripe_subscription_id)
    
    @app.get("/subscriptions/status/{username}")
    async def subscription_status_get(username: str):
        """
        Get user's subscription status.
        
        Returns:
            Current subscription, credits, billing info
        """
        from subscription_engine import get_subscription_status
        return get_subscription_status(username)
    
    @app.post("/subscriptions/use_credit")
    async def subscription_use_credit_post(
        username: str,
        intent_id: str,
        credits_to_use: int = 1
    ):
        """
        Use subscription credit(s) for an intent.
        
        Args:
            username: User's username
            intent_id: Intent ID being funded
            credits_to_use: Number of credits (default 1)
        
        Returns:
            Usage record and updated credit balance
        """
        from subscription_engine import use_subscription_credit
        return use_subscription_credit(username, intent_id, credits_to_use)
    
    @app.post("/subscriptions/cancel")
    async def subscription_cancel_post(
        subscription_id: str,
        immediate: bool = False
    ):
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Subscription ID
            immediate: Cancel now (true) or at period end (false)
        
        Returns:
            Cancellation confirmation
        """
        from subscription_engine import cancel_subscription
        return cancel_subscription(subscription_id, immediate)
    
    @app.get("/subscriptions/tiers")
    async def subscription_tiers_get():
        """
        Get all available subscription tiers.
        
        Returns:
            Tier pricing, features, and benefits
        """
        from subscription_engine import get_all_subscription_tiers
        return get_all_subscription_tiers()
    
    @app.get("/subscriptions/savings")
    async def subscription_savings_get(
        tier: str,
        billing_cycle: str = "monthly"
    ):
        """
        Calculate savings for a subscription tier.
        
        Args:
            tier: bronze/silver/gold/platinum
            billing_cycle: monthly or annual
        
        Returns:
            Savings vs one-time purchase pricing
        """
        from subscription_engine import calculate_subscription_savings
        return calculate_subscription_savings(tier, billing_cycle)
    
    @app.get("/subscriptions/priority/{username}")
    async def subscription_priority_get(username: str):
        """
        Check subscriber priority queue status.
        
        Returns:
            Priority level and tier info
        """
        from subscription_engine import check_subscriber_priority
        return check_subscriber_priority(username)
    
    @app.get("/subscriptions/history/{username}")
    async def subscription_history_get(username: str):
        """
        Get user's complete subscription history.
        
        Returns:
            All subscriptions, usage, and totals
        """
        from subscription_engine import get_user_subscription_history
        return get_user_subscription_history(username)
    
    @app.get("/subscriptions/mrr")
    async def subscription_mrr_get():
        """
        Calculate Monthly Recurring Revenue.
        
        Admin endpoint for business metrics.
        
        Returns:
            MRR, ARR, subscriber counts by tier
        """
        from subscription_engine import calculate_mrr
        return calculate_mrr()
    
    # ========================================
    # FEATURE #8: WARRANTIES & GUARANTEES
    # ========================================
    
    @app.post("/warranties/create")
    async def warranty_create_post(
        agent_username: str,
        warranty_type: str,
        outcome_price: float,
        custom_terms: Optional[Dict[str, Any]] = None
    ):
        """
        Create a warranty offer for an outcome.
        
        Args:
            agent_username: Agent offering warranty
            warranty_type: money_back_100, unlimited_revisions, etc
            outcome_price: Price of outcome being warranted
            custom_terms: Optional custom terms
        
        Returns:
            Warranty with bond requirement
        """
        from warranty_engine import create_warranty
        return create_warranty(agent_username, warranty_type, outcome_price, custom_terms)
    
    @app.post("/warranties/stake_bond")
    async def warranty_stake_bond_post(
        warranty_id: str,
        agent_username: str,
        amount: float,
        payment_method: str = "stripe"
    ):
        """
        Stake warranty bond to activate warranty.
        
        Args:
            warranty_id: Warranty ID
            agent_username: Agent staking bond
            amount: Bond amount
            payment_method: Payment method
        
        Returns:
            Bond staking confirmation
        """
        from warranty_engine import stake_warranty_bond
        return stake_warranty_bond(warranty_id, agent_username, amount, payment_method)
    
    @app.post("/warranties/claim")
    async def warranty_claim_post(
        buyer_username: str,
        outcome_id: str,
        warranty_id: str,
        claim_reason: str,
        evidence: Optional[str] = None,
        desired_resolution: str = "refund"
    ):
        """
        File a warranty claim.
        
        Args:
            buyer_username: Buyer filing claim
            outcome_id: Outcome ID
            warranty_id: Warranty ID
            claim_reason: Reason for claim
            evidence: Supporting evidence
            desired_resolution: refund or revision
        
        Returns:
            Claim record
        """
        from warranty_engine import file_warranty_claim
        return file_warranty_claim(
            buyer_username,
            outcome_id,
            warranty_id,
            claim_reason,
            evidence,
            desired_resolution
        )
    
    @app.post("/warranties/claim/process")
    async def warranty_claim_process_post(
        claim_id: str,
        approved: bool,
        reviewer: str = "aigentsy_admin",
        review_notes: Optional[str] = None
    ):
        """
        Process (approve/deny) a warranty claim.
        
        Admin endpoint.
        
        Args:
            claim_id: Claim ID
            approved: True to approve, False to deny
            reviewer: Reviewer username
            review_notes: Review notes
        
        Returns:
            Claim processing result with refund/bond info
        """
        from warranty_engine import process_warranty_claim
        return process_warranty_claim(claim_id, approved, reviewer, review_notes)
    
    @app.post("/warranties/revision/request")
    async def warranty_revision_request_post(
        buyer_username: str,
        outcome_id: str,
        warranty_id: str,
        revision_feedback: str,
        revision_details: Optional[Dict[str, Any]] = None
    ):
        """
        Request a revision under warranty.
        
        Args:
            buyer_username: Buyer requesting
            outcome_id: Outcome ID
            warranty_id: Warranty ID
            revision_feedback: Feedback for revision
            revision_details: Detailed requirements
        
        Returns:
            Revision request with SLA deadline
        """
        from warranty_engine import request_revision
        return request_revision(
            buyer_username,
            outcome_id,
            warranty_id,
            revision_feedback,
            revision_details
        )
    
    @app.post("/warranties/revision/deliver")
    async def warranty_revision_deliver_post(
        agent_username: str,
        revision_id: str,
        revised_outcome: Dict[str, Any],
        revision_notes: Optional[str] = None
    ):
        """
        Agent delivers a revision.
        
        Args:
            agent_username: Agent delivering
            revision_id: Revision request ID
            revised_outcome: Revised outcome data
            revision_notes: Notes about revision
        
        Returns:
            Delivery confirmation with SLA status
        """
        from warranty_engine import deliver_revision
        return deliver_revision(agent_username, revision_id, revised_outcome, revision_notes)
    
    @app.get("/warranties/terms/{warranty_id}")
    async def warranty_terms_get(warranty_id: str):
        """
        Get warranty terms and details.
        
        Returns:
            Complete warranty information
        """
        from warranty_engine import get_warranty_terms
        return get_warranty_terms(warranty_id)
    
    @app.get("/warranties/agent/{username}")
    async def warranty_agent_get(username: str):
        """
        Get all warranties offered by an agent.
        
        Returns:
            Agent's warranties, bonds, claims
        """
        from warranty_engine import get_agent_warranties
        return get_agent_warranties(username)
    
    @app.get("/warranties/types")
    async def warranty_types_get():
        """
        Get all available warranty types.
        
        Returns:
            Warranty types with terms and bond requirements
        """
        from warranty_engine import get_all_warranty_types
        return get_all_warranty_types()
    
    @app.get("/warranties/calculate_bond")
    async def warranty_calculate_bond_get(
        warranty_type: str,
        outcome_price: float
    ):
        """
        Calculate bond requirement for warranty.
        
        Args:
            warranty_type: Type of warranty
            outcome_price: Outcome price
        
        Returns:
            Bond calculation details
        """
        from warranty_engine import calculate_bond_requirement
        return calculate_bond_requirement(warranty_type, outcome_price)
    
    @app.get("/warranties/buyer_claims/{username}")
    async def warranty_buyer_claims_get(username: str):
        """
        Get all claims filed by a buyer.
        
        Returns:
            Buyer's claim history and refunds
        """
        from warranty_engine import get_buyer_claims
        return get_buyer_claims(username)
    
    # ========================================
    # FEATURE #9: EXPRESS SLOs
    # ========================================
    
    @app.get("/slo/tiers")
    async def slo_tiers_get():
        """
        Get all available SLO tiers.
        
        Returns:
            All SLO tiers with pricing and delivery times
        """
        from slo_engine import get_all_slo_tiers
        return get_all_slo_tiers()
    
    @app.get("/slo/pricing")
    async def slo_pricing_get(
        base_price: float,
        tier: str
    ):
        """
        Calculate SLO pricing breakdown.
        
        Args:
            base_price: Base outcome price
            tier: SLO tier (express/premium/standard/economy)
        
        Returns:
            Detailed pricing breakdown
        """
        from slo_engine import calculate_slo_pricing_detailed
        return calculate_slo_pricing_detailed(base_price, tier)
    
    @app.get("/slo/compare")
    async def slo_compare_get(base_price: float):
        """
        Compare all SLO tiers for a base price.
        
        Args:
            base_price: Base outcome price
        
        Returns:
            Comparison table of all tiers
        """
        from slo_engine import compare_slo_tiers
        return compare_slo_tiers(base_price)
    
    @app.get("/slo/status/{contract_id}")
    async def slo_status_get(contract_id: str):
        """
        Get SLO contract status.
        
        Returns:
            Contract status with timeline and metrics
        """
        from slo_engine import get_slo_contract_status
        return get_slo_contract_status(contract_id)
    
    @app.get("/slo/agent_dashboard/{username}")
    async def slo_agent_dashboard_get(username: str):
        """
        Get agent's SLO performance dashboard.
        
        Returns:
            Performance metrics and active contracts
        """
        from slo_engine import get_agent_slo_dashboard
        return get_agent_slo_dashboard(username)
    
    @app.get("/slo/buyer_dashboard/{username}")
    async def slo_buyer_dashboard_get(username: str):
        """
        Get buyer's SLO contracts dashboard.
        
        Returns:
            Active contracts and protection status
        """
        from slo_engine import get_buyer_slo_dashboard
        return get_buyer_slo_dashboard(username)
    
    @app.get("/slo/recommend")
    async def slo_recommend_get(
        urgency: str = "medium",
        budget_flexible: bool = True,
        quality_priority: bool = True
    ):
        """
        Get SLO tier recommendation.
        
        Args:
            urgency: low/medium/high/critical
            budget_flexible: Can pay premium
            quality_priority: Prioritize quality over speed
        
        Returns:
            Recommended tier with reasoning
        """
        from slo_engine import recommend_slo_tier
        return recommend_slo_tier(urgency, budget_flexible, quality_priority)
    
    # ========================================
    # FEATURE #10: BOOSTERS
    # ========================================
    
    @app.post("/boosters/activate")
    async def booster_activate_post(
        username: str,
        booster_type: str,
        source: str = "automatic",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Activate a booster for a user.
        
        Args:
            username: User's username
            booster_type: Type of booster
            source: How triggered (automatic/referral/purchase)
            metadata: Additional metadata
        
        Returns:
            Activated booster
        """
        from booster_engine import activate_booster
        return activate_booster(username, booster_type, source, metadata)
    
    @app.get("/boosters/active/{username}")
    async def booster_active_get(username: str):
        """
        Get all active boosters for a user.
        
        Returns:
            Active boosters with total multiplier
        """
        from booster_engine import get_active_boosters
        return get_active_boosters(username)
    
    @app.get("/boosters/earnings")
    async def booster_earnings_get(
        base_amount: float,
        username: str,
        outcome_id: Optional[str] = None
    ):
        """
        Calculate boosted earnings.
        
        Args:
            base_amount: Base earnings
            username: User's username
            outcome_id: Outcome ID (for single-use boosters)
        
        Returns:
            Boosted earnings breakdown
        """
        from booster_engine import calculate_boosted_earnings
        return calculate_boosted_earnings(base_amount, username, outcome_id)
    
    @app.post("/boosters/referral/track")
    async def booster_referral_track_post(
        referrer_username: str,
        referee_username: str,
        referral_code: Optional[str] = None
    ):
        """
        Track a referral.
        
        Args:
            referrer_username: User who referred
            referee_username: User who signed up
            referral_code: Referral code used
        
        Returns:
            Referral tracking confirmation
        """
        from booster_engine import track_referral
        return track_referral(referrer_username, referee_username, referral_code)
    
    @app.post("/boosters/referral/milestone")
    async def booster_referral_milestone_post(
        referrer_username: str,
        milestone: str,
        referee_username: str
    ):
        """
        Award referral milestone bonus.
        
        Args:
            referrer_username: Referrer
            milestone: first_outcome/subscription
            referee_username: Referee who hit milestone
        
        Returns:
            Bonus award confirmation
        """
        from booster_engine import award_referral_milestone_bonus
        return award_referral_milestone_bonus(referrer_username, milestone, referee_username)
    
    @app.post("/boosters/streak/check")
    async def booster_streak_check_post(
        username: str,
        last_active: str
    ):
        """
        Check and update activity streak.
        
        Args:
            username: User's username
            last_active: ISO timestamp of last activity
        
        Returns:
            Streak status and booster awards
        """
        from booster_engine import check_streak
        return check_streak(username, last_active)
    
    @app.post("/boosters/purchase")
    async def booster_purchase_post(
        username: str,
        power_up_type: str,
        payment_method: str = "stripe"
    ):
        """
        Purchase a power-up booster.
        
        Args:
            username: User purchasing
            power_up_type: Type of power-up
            payment_method: Payment method
        
        Returns:
            Purchase confirmation
        """
        from booster_engine import purchase_power_up
        return purchase_power_up(username, power_up_type, payment_method)
    
    @app.get("/boosters/available")
    async def booster_available_get(username: Optional[str] = None):
        """
        Get all available boosters.
        
        Returns:
            Categorized list of boosters
        """
        from booster_engine import get_available_boosters
        return get_available_boosters(username or "guest")
    
    @app.get("/boosters/leaderboard")
    async def booster_leaderboard_get(limit: int = 10):
        """
        Get booster leaderboard.
        
        Args:
            limit: Number of top users
        
        Returns:
            Top boosted users
        """
        from booster_engine import get_booster_leaderboard
        return get_booster_leaderboard(limit)
    
    # ========================================
    # FEATURE #11: PAY-WITH-PERFORMANCE (PWP)
    # ========================================
    
    @app.post("/pwp/create")
    async def pwp_create_post(
        buyer_username: str,
        agent_username: str,
        outcome_id: str,
        outcome_price: float,
        pwp_plan: str,
        outcome_type: str = "marketing_campaign",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create PWP contract.
        
        Args:
            buyer_username: Buyer deferring payment
            agent_username: Agent receiving upfront
            outcome_id: Outcome ID
            outcome_price: Outcome price
            pwp_plan: PWP plan type
            outcome_type: Outcome type
            metadata: Additional metadata
        
        Returns:
            PWP contract
        """
        from pwp_engine import create_pwp_contract
        return create_pwp_contract(
            buyer_username, agent_username, outcome_id,
            outcome_price, pwp_plan, outcome_type, metadata
        )
    
    @app.post("/pwp/payment")
    async def pwp_payment_post(
        contract_id: str,
        revenue_amount: float,
        payment_source: str = "stripe",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record revenue payment.
        
        Args:
            contract_id: PWP contract ID
            revenue_amount: Buyer's revenue
            payment_source: Payment source
            metadata: Payment metadata
        
        Returns:
            Payment record
        """
        from pwp_engine import record_revenue_payment
        return record_revenue_payment(contract_id, revenue_amount, payment_source, metadata)
    
    @app.get("/pwp/status/{contract_id}")
    async def pwp_status_get(contract_id: str):
        """
        Get PWP contract status.
        
        Returns:
            Contract status
        """
        from pwp_engine import get_pwp_contract_status
        return get_pwp_contract_status(contract_id)
    
    @app.get("/pwp/check_expiry/{contract_id}")
    async def pwp_check_expiry_get(contract_id: str):
        """
        Check contract expiry.
        
        Returns:
            Expiry status
        """
        from pwp_engine import check_pwp_contract_expiry
        return check_pwp_contract_expiry(contract_id)
    
    @app.get("/pwp/pricing")
    async def pwp_pricing_get(
        outcome_price: float,
        pwp_plan: str,
        outcome_type: str = "marketing_campaign"
    ):
        """
        Calculate PWP pricing.
        
        Args:
            outcome_price: Outcome price
            pwp_plan: PWP plan
            outcome_type: Outcome type
        
        Returns:
            Pricing breakdown
        """
        from pwp_engine import calculate_pwp_pricing
        return calculate_pwp_pricing(outcome_price, pwp_plan, outcome_type)
    
    @app.get("/pwp/buyer_dashboard/{username}")
    async def pwp_buyer_dashboard_get(username: str):
        """
        Get buyer's PWP dashboard.
        
        Returns:
            Buyer's contracts
        """
        from pwp_engine import get_buyer_pwp_dashboard
        return get_buyer_pwp_dashboard(username)
    
    @app.get("/pwp/capital_pool")
    async def pwp_capital_pool_get():
        """
        Get capital pool status.
        
        Returns:
            Pool metrics
        """
        from pwp_engine import get_capital_pool_status
        return get_capital_pool_status()
    
    @app.get("/pwp/plans")
    async def pwp_plans_get():
        """
        Get all PWP plans.
        
        Returns:
            All available plans
        """
        from pwp_engine import get_all_pwp_plans
        return get_all_pwp_plans()
    
    # ========================================
    # FEATURE #12: TEMPLATE FRANCHISE RIGHTS
    # ========================================
    
    @app.post("/franchise/template/create")
    async def franchise_template_create_post(
        creator_username: str,
        template_name: str,
        category: str,
        description: str,
        base_price: float,
        available_licenses: List[str] = ["basic", "professional"],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Create franchisable template.
        
        Args:
            creator_username: Template creator
            template_name: Template name
            category: Template category
            description: Description
            base_price: Base outcome price
            available_licenses: License types offered
            metadata: Template files/instructions
        
        Returns:
            Created template
        """
        from franchise_engine import create_template
        return create_template(
            creator_username, template_name, category,
            description, base_price, available_licenses, metadata
        )
    
    @app.post("/franchise/license/purchase")
    async def franchise_license_purchase_post(
        franchisee_username: str,
        template_id: str,
        license_type: str,
        territory: Optional[str] = None,
        niche: Optional[str] = None
    ):
        """
        Purchase template license.
        
        Args:
            franchisee_username: Franchisee
            template_id: Template to license
            license_type: License type
            territory: Geographic territory
            niche: Industry niche
        
        Returns:
            License agreement
        """
        from franchise_engine import purchase_license
        return purchase_license(franchisee_username, template_id, license_type, territory, niche)
    
    @app.post("/franchise/outcome/record")
    async def franchise_outcome_record_post(
        license_id: str,
        outcome_id: str,
        revenue_amount: float,
        buyer_username: str
    ):
        """
        Record franchise outcome.
        
        Args:
            license_id: Franchisee's license
            outcome_id: Outcome delivered
            revenue_amount: Revenue from outcome
            buyer_username: Buyer
        
        Returns:
            Revenue split
        """
        from franchise_engine import record_franchise_outcome
        return record_franchise_outcome(license_id, outcome_id, revenue_amount, buyer_username)
    
    @app.get("/franchise/marketplace")
    async def franchise_marketplace_get(
        category: Optional[str] = None,
        sort_by: str = "popular"
    ):
        """
        Get template marketplace.
        
        Args:
            category: Filter by category
            sort_by: popular/revenue/recent/rating
        
        Returns:
            Marketplace listings
        """
        from franchise_engine import get_template_marketplace
        return get_template_marketplace(category, sort_by)
    
    @app.get("/franchise/franchisee_dashboard/{username}")
    async def franchise_franchisee_dashboard_get(username: str):
        """
        Get franchisee dashboard.
        
        Returns:
            Franchisee's licenses and performance
        """
        from franchise_engine import get_franchisee_dashboard
        return get_franchisee_dashboard(username)
    
    @app.get("/franchise/creator_dashboard/{username}")
    async def franchise_creator_dashboard_get(username: str):
        """
        Get creator dashboard.
        
        Returns:
            Creator's templates and earnings
        """
        from franchise_engine import get_creator_dashboard
        return get_creator_dashboard(username)
    
    @app.get("/franchise/template/performance/{template_id}")
    async def franchise_template_performance_get(template_id: str):
        """
        Get template performance.
        
        Returns:
            Performance metrics
        """
        from franchise_engine import get_template_performance
        return get_template_performance(template_id)
    
    @app.get("/franchise/license_types")
    async def franchise_license_types_get():
        """
        Get all license types.
        
        Returns:
            All available license types
        """
        from franchise_engine import get_all_license_types
        return get_all_license_types()
