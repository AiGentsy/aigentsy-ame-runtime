# aigx_engine.py
"""
AiGentsy AIGx Activity Rewards Engine

Handles:
- Daily activity rewards
- Weekly streak rewards
- Monthly power user rewards
- Referral rewards
- Activity tracking and streak management
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

from aigx_config import AIGX_CONFIG
from log_to_jsonbin import get_user, list_users
from log_to_jsonbin_merged import log_agent_update, append_intent_ledger

# ============================================================
# ACTIVITY TRACKING
# ============================================================

def record_activity(username: str, activity_type: str = "login") -> Dict:
    """
    Record user activity and check for rewards.
    
    Args:
        username: User's username
        activity_type: Type of activity ("login", "transaction", "engagement", etc.)
        
    Returns:
        dict: {
            "ok": bool,
            "rewards_earned": list,
            "total_aigx": float,
            "streaks": dict
        }
    """
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "User not found"}
    
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    
    # Initialize activity tracking if needed
    if "activityTracking" not in user:
        user["activityTracking"] = {
            "lastActive": None,
            "lastDailyReward": None,
            "lastWeeklyReward": None,
            "lastMonthlyReward": None,
            "activeDays": [],
            "currentStreak": 0,
            "longestStreak": 0,
            "totalActiveDays": 0
        }
    
    tracking = user["activityTracking"]
    rewards_earned = []
    total_aigx = 0.0
    
    # ============================================================
    # CHECK DAILY REWARD
    # ============================================================
    
    last_daily = tracking.get("lastDailyReward")
    if last_daily != today_str:
        # Award daily reward
        daily_reward = AIGX_CONFIG["activity_rewards"]["daily_active"]["aigx_reward"]
        
        _award_aigx(
            user=user,
            amount=daily_reward,
            basis="daily_activity_reward",
            metadata={"date": today_str, "activity_type": activity_type}
        )
        
        tracking["lastDailyReward"] = today_str
        rewards_earned.append({
            "type": "daily_active",
            "amount": daily_reward,
            "description": "Daily activity reward"
        })
        total_aigx += daily_reward
    
    # ============================================================
    # UPDATE ACTIVITY STREAK
    # ============================================================
    
    active_days = tracking.get("activeDays", [])
    
    # Add today if not already tracked
    if today_str not in active_days:
        active_days.append(today_str)
        tracking["totalActiveDays"] = len(active_days)
    
    # Calculate current streak
    streak = _calculate_streak(active_days)
    tracking["currentStreak"] = streak
    tracking["longestStreak"] = max(tracking.get("longestStreak", 0), streak)
    
    # ============================================================
    # CHECK WEEKLY STREAK REWARD
    # ============================================================
    
    if streak >= 7:
        last_weekly = tracking.get("lastWeeklyReward")
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        
        if last_weekly != week_start:
            weekly_reward = AIGX_CONFIG["activity_rewards"]["weekly_streak"]["aigx_reward"]
            
            _award_aigx(
                user=user,
                amount=weekly_reward,
                basis="weekly_streak_reward",
                metadata={"week_start": week_start, "streak_days": streak}
            )
            
            tracking["lastWeeklyReward"] = week_start
            rewards_earned.append({
                "type": "weekly_streak",
                "amount": weekly_reward,
                "description": f"{streak}-day streak maintained"
            })
            total_aigx += weekly_reward
    
    # ============================================================
    # CHECK MONTHLY POWER USER REWARD
    # ============================================================
    
    if streak >= 30:
        last_monthly = tracking.get("lastMonthlyReward")
        month_str = now.strftime("%Y-%m")
        
        if last_monthly != month_str:
            monthly_reward = AIGX_CONFIG["activity_rewards"]["monthly_power_user"]["aigx_reward"]
            
            _award_aigx(
                user=user,
                amount=monthly_reward,
                basis="monthly_power_user_reward",
                metadata={"month": month_str, "streak_days": streak}
            )
            
            tracking["lastMonthlyReward"] = month_str
            rewards_earned.append({
                "type": "monthly_power_user",
                "amount": monthly_reward,
                "description": f"{streak}-day power user streak"
            })
            total_aigx += monthly_reward
    
    # ============================================================
    # UPDATE USER RECORD
    # ============================================================
    
    tracking["lastActive"] = now.isoformat()
    tracking["activeDays"] = active_days[-365:]  # Keep last year only
    user["activityTracking"] = tracking
    
    log_agent_update(user)
    
    return {
        "ok": True,
        "rewards_earned": rewards_earned,
        "total_aigx": total_aigx,
        "streaks": {
            "current": tracking["currentStreak"],
            "longest": tracking["longestStreak"],
            "total_active_days": tracking["totalActiveDays"]
        }
    }


def _calculate_streak(active_days: List[str]) -> int:
    """
    Calculate current consecutive day streak.
    
    Args:
        active_days: List of date strings in YYYY-MM-DD format
        
    Returns:
        int: Number of consecutive days
    """
    if not active_days:
        return 0
    
    # Sort dates
    sorted_dates = sorted([datetime.strptime(d, "%Y-%m-%d") for d in active_days])
    
    # Start from most recent date
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    streak = 0
    
    # Check backwards from today
    check_date = today
    for date in reversed(sorted_dates):
        date_normalized = date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if date_normalized == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif date_normalized < check_date:
            # Gap found, streak broken
            break
    
    return streak


# ============================================================
# REFERRAL REWARDS
# ============================================================

def record_referral(referrer_username: str, referred_username: str) -> Dict:
    """
    Record a referral and check for milestone rewards.
    
    Args:
        referrer_username: User who made the referral
        referred_username: User who was referred
        
    Returns:
        dict: {
            "ok": bool,
            "rewards_earned": list,
            "total_aigx": float,
            "total_referrals": int
        }
    """
    
    referrer = get_user(referrer_username)
    if not referrer:
        return {"ok": False, "error": "Referrer not found"}
    
    referred = get_user(referred_username)
    if not referred:
        return {"ok": False, "error": "Referred user not found"}
    
    # Initialize referral tracking
    if "referralTracking" not in referrer:
        referrer["referralTracking"] = {
            "totalReferrals": 0,
            "activeReferrals": 0,
            "referredUsers": [],
            "milestonesAchieved": []
        }
    
    tracking = referrer["referralTracking"]
    
    # Check if already referred
    if referred_username in tracking.get("referredUsers", []):
        return {
            "ok": False,
            "error": "User already referred",
            "total_referrals": tracking["totalReferrals"]
        }
    
    # Record referral
    tracking["referredUsers"].append(referred_username)
    tracking["totalReferrals"] = len(tracking["referredUsers"])
    
    # Count active referrals (users with lifetime revenue > 0)
    active_count = 0
    for ref_user in tracking["referredUsers"]:
        ref_data = get_user(ref_user)
        if ref_data and ref_data.get("lifetimeRevenue", 0) > 0:
            active_count += 1
    
    tracking["activeReferrals"] = active_count
    
    # ============================================================
    # CHECK REFERRAL MILESTONES
    # ============================================================
    
    rewards_earned = []
    total_aigx = 0.0
    
    milestones = [
        ("first_referral", 1),
        ("referral_5", 5),
        ("referral_10", 10)
    ]
    
    achieved = tracking.get("milestonesAchieved", [])
    
    for milestone_key, threshold in milestones:
        if tracking["totalReferrals"] >= threshold and milestone_key not in achieved:
            milestone_data = AIGX_CONFIG["milestones"][milestone_key]
            reward = milestone_data["aigx_reward"]
            
            _award_aigx(
                user=referrer,
                amount=reward,
                basis="referral_milestone",
                metadata={
                    "milestone": milestone_key,
                    "total_referrals": tracking["totalReferrals"],
                    "active_referrals": tracking["activeReferrals"]
                }
            )
            
            achieved.append(milestone_key)
            rewards_earned.append({
                "type": milestone_key,
                "amount": reward,
                "description": milestone_data["description"]
            })
            total_aigx += reward
    
    tracking["milestonesAchieved"] = achieved
    referrer["referralTracking"] = tracking
    
    # ============================================================
    # UPDATE USER RECORD
    # ============================================================
    
    log_agent_update(referrer)
    
    return {
        "ok": True,
        "rewards_earned": rewards_earned,
        "total_aigx": total_aigx,
        "total_referrals": tracking["totalReferrals"],
        "active_referrals": tracking["activeReferrals"]
    }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _award_aigx(user: Dict, amount: float, basis: str, metadata: Dict = None) -> None:
    """
    Award AIGx to user and log to ledger.
    
    Args:
        user: User dict (will be modified in place)
        amount: AIGx amount to award
        basis: Reason for award
        metadata: Additional metadata
    """
    now = datetime.now(timezone.utc).isoformat()
    
    # Update ownership
    user.setdefault("ownership", {"aigx": 0, "equity": 0, "ledger": []})
    user["ownership"]["aigx"] = user["ownership"].get("aigx", 0) + amount
    
    # Log to ledger
    ledger_entry = {
        "ts": now,
        "amount": amount,
        "currency": "AIGx",
        "basis": basis
    }
    
    if metadata:
        ledger_entry.update(metadata)
    
    user["ownership"]["ledger"].append(ledger_entry)


def get_activity_summary(username: str) -> Dict:
    """
    Get user's activity summary and pending rewards.
    
    Args:
        username: User's username
        
    Returns:
        dict: Activity stats and reward eligibility
    """
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "User not found"}
    
    tracking = user.get("activityTracking", {})
    referrals = user.get("referralTracking", {})
    
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    
    return {
        "ok": True,
        "activity": {
            "last_active": tracking.get("lastActive"),
            "current_streak": tracking.get("currentStreak", 0),
            "longest_streak": tracking.get("longestStreak", 0),
            "total_active_days": tracking.get("totalActiveDays", 0)
        },
        "rewards": {
            "daily_claimed_today": tracking.get("lastDailyReward") == today_str,
            "weekly_eligible": tracking.get("currentStreak", 0) >= 7,
            "monthly_eligible": tracking.get("currentStreak", 0) >= 30
        },
        "referrals": {
            "total": referrals.get("totalReferrals", 0),
            "active": referrals.get("activeReferrals", 0),
            "milestones_achieved": referrals.get("milestonesAchieved", [])
        }
    }


def check_and_award_pending_rewards(username: str) -> Dict:
    """
    Check for any pending rewards and award them.
    Useful for batch processing or cron jobs.
    
    Args:
        username: User's username
        
    Returns:
        dict: Rewards awarded
    """
    return record_activity(username, activity_type="check")


# ============================================================
# BULK OPERATIONS (for cron jobs)
# ============================================================

def process_all_active_users() -> Dict:
    """
    Process activity rewards for all users who were active today.
    This should be run as a daily cron job.
    
    Returns:
        dict: Processing summary
    """
    from log_to_jsonbin import list_users
    
    all_users = list_users()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    processed = 0
    rewarded = 0
    total_aigx_distributed = 0.0
    
    for user in all_users:
        tracking = user.get("activityTracking", {})
        active_days = tracking.get("activeDays", [])
        
        # Check if user was active today
        if today in active_days:
            result = record_activity(user["username"], activity_type="daily_check")
            processed += 1
            
            if result.get("ok") and result.get("total_aigx", 0) > 0:
                rewarded += 1
                total_aigx_distributed += result["total_aigx"]
    
    return {
        "ok": True,
        "processed": processed,
        "rewarded": rewarded,
        "total_aigx_distributed": total_aigx_distributed,
        "date": today
    }


# ============================================================
# API ENDPOINTS HELPERS
# ============================================================

async def credit_aigx(username: str, amount: int, metadata: dict) -> bool:
    """
    Credit AIGx to user's account
    
    Args:
        username: User's username
        amount: Amount of AIGx to credit
        metadata: Context about why AIGx was credited
        
    Returns:
        True if successful, False otherwise
    """
    from log_to_jsonbin import get_user, update_user
    
    try:
        # Get user
        user = get_user(username)
        if not user:
            print(f"User {username} not found")
            return False
        
        # Get current AIGx balance
        current_aigx = user.get("yield", {}).get("aigxEarned", 0)
        new_aigx = current_aigx + amount
        
        # Update balance
        if "yield" not in user:
            user["yield"] = {}
        
        user["yield"]["aigxEarned"] = new_aigx
        
        # Log the transaction
        if "aigx_transactions" not in user:
            user["aigx_transactions"] = []
        
        user["aigx_transactions"].append({
            "amount": amount,
            "balance_after": new_aigx,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        })
        
        # Save
        success = update_user(username, user)
        
        if success:
            print(f"✅ Credited {amount} AIGx to {username} (new balance: {new_aigx})")
        
        return success
        
    except Exception as e:
        print(f"Error crediting AIGx: {e}")
        return False
        
def create_activity_endpoints(app):
    """
    Helper to add activity reward endpoints to FastAPI app.
    Call this from main.py after app initialization.
    
    Usage:
        from aigx_engine import create_activity_endpoints
        create_activity_endpoints(app)
    """
    
    @app.post("/activity/record")
    async def activity_record(username: str, activity_type: str = "login"):
        """Record user activity and check for rewards"""
        return record_activity(username, activity_type)
    
    @app.get("/activity/summary/{username}")
    async def activity_summary(username: str):
        """Get activity summary for user"""
        return get_activity_summary(username)
    
    @app.post("/referral/record")
    async def referral_record(referrer: str, referred: str):
        """Record a referral"""
        return record_referral(referrer, referred)
    
    @app.post("/activity/process_all")
    async def activity_process_all():
        """Process all active users (admin only)"""
        return process_all_active_users()
