# booster_engine.py
"""
AiGentsy Booster Engine - Feature #10

Individual earnings multipliers and viral growth mechanics.
Standalone system complementary to MetaHive collective rewards.

Features:
- Referral boosters (invite friends, earn multipliers)
- Streak boosters (daily/weekly/monthly activity)
- Milestone boosters (early adopter, achievement-based)
- Time-limited boosters (weekend, happy hour, flash events)
- Power-up boosters (purchasable temporary multipliers)

Complementary to MetaHive:
- Boosters multiply individual earnings
- MetaHive shares collective revenue pool
- Can stack: Boosted earnings → MetaHive contribution → Shared rewards
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
import json

# Booster type definitions
BOOSTER_TYPES = {
    # Referral Boosters
    "referral_1": {
        "name": "First Referral",
        "category": "referral",
        "multiplier": 1.10,  # +10%
        "duration_days": 30,
        "trigger": "friend_signup",
        "stackable": True,
        "max_stack": 10,  # Max 10 referrals = 100% boost
        "description": "+10% AIGx earnings for 30 days per active referral",
        "icon": "👥"
    },
    "referral_milestone_1": {
        "name": "Referral Champion",
        "category": "referral_milestone",
        "multiplier": 1.50,  # +50% bonus
        "trigger": "5_active_referrals",
        "stackable": False,
        "description": "Permanent +50% boost at 5 active referrals",
        "icon": "🏆"
    },
    
    # Streak Boosters
    "streak_7": {
        "name": "Week Warrior",
        "category": "streak",
        "multiplier": 1.05,  # +5%
        "duration_days": 7,
        "trigger": "7_day_login_streak",
        "stackable": True,
        "description": "+5% boost for maintaining 7-day streak",
        "icon": "🔥"
    },
    "streak_30": {
        "name": "Month Master",
        "category": "streak",
        "multiplier": 1.15,  # +15%
        "duration_days": 30,
        "trigger": "30_day_active_streak",
        "stackable": True,
        "description": "+15% boost for 30-day active streak",
        "icon": "🔥🔥"
    },
    "streak_90": {
        "name": "Quarter Champion",
        "category": "streak",
        "multiplier": 1.25,  # +25%
        "duration_days": None,  # Permanent until broken
        "trigger": "90_day_active_streak",
        "stackable": True,
        "description": "+25% permanent boost (until streak broken)",
        "icon": "🔥🔥🔥"
    },
    
    # Milestone Boosters
    "early_adopter": {
        "name": "Early Adopter",
        "category": "milestone",
        "multiplier": 2.0,  # 2x earnings
        "duration_days": None,  # Permanent
        "trigger": "first_100_users",
        "stackable": False,
        "description": "2x AIGx forever - first 100 users",
        "icon": "🌟",
        "badge": "EARLY_ADOPTER"
    },
    "high_earner": {
        "name": "High Roller",
        "category": "milestone",
        "multiplier": 1.20,  # +20%
        "duration_days": None,  # Permanent
        "trigger": "earned_10k",
        "stackable": False,
        "description": "Permanent +20% after earning $10k",
        "icon": "💎"
    },
    "prolific_creator": {
        "name": "Prolific Creator",
        "category": "milestone",
        "multiplier": 1.15,  # +15%
        "duration_days": None,  # Permanent
        "trigger": "completed_50_outcomes",
        "stackable": False,
        "description": "Permanent +15% after 50 outcomes",
        "icon": "⭐"
    },
    
    # Time-Limited Boosters
    "weekend_bonus": {
        "name": "Weekend Warrior",
        "category": "time_limited",
        "multiplier": 1.25,  # +25%
        "trigger": "automatic_weekend",
        "stackable": True,
        "active_days": [5, 6],  # Saturday, Sunday
        "description": "+25% earnings on weekends",
        "icon": "🎉"
    },
    "happy_hour": {
        "name": "Happy Hour",
        "category": "time_limited",
        "multiplier": 1.50,  # +50%
        "trigger": "automatic_happy_hour",
        "stackable": True,
        "active_hours": [17, 18, 19],  # 5-7pm EST
        "description": "+50% earnings 5-7pm EST daily",
        "icon": "⏰"
    },
    
    # Power-Up Boosters (Purchasable)
    "power_up_24h": {
        "name": "24hr Power-Up",
        "category": "power_up",
        "multiplier": 2.0,  # 2x
        "duration_hours": 24,
        "cost_usd": 9.99,
        "purchasable": True,
        "stackable": False,
        "description": "2x earnings for 24 hours",
        "icon": "⚡"
    },
    "power_up_7d": {
        "name": "Week Booster",
        "category": "power_up",
        "multiplier": 3.0,  # 3x
        "duration_days": 7,
        "cost_usd": 19.99,
        "purchasable": True,
        "stackable": False,
        "description": "3x earnings for 7 days",
        "icon": "⚡⚡"
    },
    "power_up_30d": {
        "name": "Month Multiplier",
        "category": "power_up",
        "multiplier": 5.0,  # 5x
        "duration_days": 30,
        "cost_usd": 49.99,
        "purchasable": True,
        "stackable": False,
        "description": "5x earnings for 30 days",
        "icon": "⚡⚡⚡"
    },
    "mega_boost": {
        "name": "Mega Boost",
        "category": "power_up",
        "multiplier": 10.0,  # 10x
        "single_use": True,
        "cost_usd": 99.00,
        "purchasable": True,
        "stackable": False,
        "description": "10x earnings on next outcome only",
        "icon": "💥"
    }
}

# In-memory booster storage (use JSONBin in production)
USER_BOOSTERS_DB = {}
REFERRAL_DB = {}
STREAK_DB = {}
BOOSTER_PURCHASES_DB = {}


def activate_booster(
    username: str,
    booster_type: str,
    source: str = "automatic",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Activate a booster for a user.
    
    Args:
        username: User's username
        booster_type: Type of booster to activate
        source: How booster was triggered (automatic/referral/purchase)
        metadata: Additional booster metadata
    
    Returns:
        Activated booster record
    """
    if booster_type not in BOOSTER_TYPES:
        raise ValueError(f"Invalid booster type: {booster_type}")
    
    booster_config = BOOSTER_TYPES[booster_type]
    
    # Check if user can stack this booster
    if not booster_config.get("stackable", False):
        # Check if already active
        existing = _get_active_booster(username, booster_type)
        if existing:
            return {
                "success": False,
                "error": "Booster already active (not stackable)",
                "existing_booster": existing
            }
    
    # Calculate expiration
    expires_at = _calculate_expiration(booster_config)
    
    booster_id = f"booster_{username}_{booster_type}_{int(datetime.now(timezone.utc).timestamp())}"
    
    booster = {
        "booster_id": booster_id,
        "username": username,
        "booster_type": booster_type,
        "name": booster_config["name"],
        "category": booster_config["category"],
        "multiplier": booster_config["multiplier"],
        "icon": booster_config["icon"],
        "description": booster_config["description"],
        "source": source,
        "metadata": metadata or {},
        "status": "active",
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
        "single_use": booster_config.get("single_use", False),
        "used": False
    }
    
    # Store booster
    if username not in USER_BOOSTERS_DB:
        USER_BOOSTERS_DB[username] = []
    
    USER_BOOSTERS_DB[username].append(booster)
    
    return {
        "success": True,
        "booster": booster,
        "message": f"Activated {booster_config['name']}: {booster_config['multiplier']}x multiplier"
    }


def _calculate_expiration(booster_config: Dict[str, Any]) -> Optional[str]:
    """Calculate when booster expires."""
    now = datetime.now(timezone.utc)
    
    if booster_config.get("duration_hours"):
        expires = now + timedelta(hours=booster_config["duration_hours"])
        return expires.isoformat()
    elif booster_config.get("duration_days"):
        expires = now + timedelta(days=booster_config["duration_days"])
        return expires.isoformat()
    else:
        return None  # Permanent or special rules


def _get_active_booster(username: str, booster_type: str) -> Optional[Dict[str, Any]]:
    """Check if user has an active booster of this type."""
    if username not in USER_BOOSTERS_DB:
        return None
    
    for booster in USER_BOOSTERS_DB[username]:
        if (booster["booster_type"] == booster_type and 
            booster["status"] == "active" and
            not _is_expired(booster)):
            return booster
    
    return None


def _is_expired(booster: Dict[str, Any]) -> bool:
    """Check if booster is expired."""
    if not booster.get("expires_at"):
        return False  # Permanent boosters don't expire
    
    expires = datetime.fromisoformat(booster["expires_at"])
    return datetime.now(timezone.utc) > expires


def get_active_boosters(username: str) -> Dict[str, Any]:
    """
    Get all active boosters for a user.
    
    Args:
        username: User's username
    
    Returns:
        List of active boosters with total multiplier
    """
    if username not in USER_BOOSTERS_DB:
        return {
            "username": username,
            "active_boosters": [],
            "total_multiplier": 1.0,
            "boost_percent": 0
        }
    
    active_boosters = []
    total_multiplier = 1.0
    
    for booster in USER_BOOSTERS_DB[username]:
        # Skip expired or used boosters
        if booster["status"] != "active":
            continue
        
        if _is_expired(booster):
            booster["status"] = "expired"
            continue
        
        if booster.get("single_use") and booster.get("used"):
            continue
        
        # Check time-limited boosters
        if not _is_time_limited_active(booster):
            continue
        
        active_boosters.append(booster)
        
        # Calculate multiplier stacking
        booster_config = BOOSTER_TYPES[booster["booster_type"]]
        if booster_config.get("stackable", False):
            # Additive stacking: (1.1 - 1) + (1.1 - 1) = 0.2 → 1.2x
            total_multiplier += (booster["multiplier"] - 1.0)
        else:
            # Multiplicative for non-stackable
            total_multiplier *= booster["multiplier"]
    
    boost_percent = (total_multiplier - 1.0) * 100
    
    return {
        "username": username,
        "active_boosters": active_boosters,
        "booster_count": len(active_boosters),
        "total_multiplier": round(total_multiplier, 2),
        "boost_percent": round(boost_percent, 1)
    }


def _is_time_limited_active(booster: Dict[str, Any]) -> bool:
    """Check if time-limited booster is currently active."""
    booster_config = BOOSTER_TYPES.get(booster["booster_type"])
    
    if not booster_config:
        return True
    
    # Check weekend boosters
    if booster_config.get("active_days"):
        current_day = datetime.now(timezone.utc).weekday()
        if current_day not in booster_config["active_days"]:
            return False
    
    # Check happy hour boosters
    if booster_config.get("active_hours"):
        current_hour = datetime.now(timezone.utc).hour
        if current_hour not in booster_config["active_hours"]:
            return False
    
    return True


def calculate_boosted_earnings(
    base_amount: float,
    username: str,
    outcome_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate earnings with all active boosters applied.
    
    Args:
        base_amount: Base earnings amount
        username: User's username
        outcome_id: Outcome ID (for single-use boosters)
    
    Returns:
        Boosted earnings breakdown
    """
    boosters_data = get_active_boosters(username)
    total_multiplier = boosters_data["total_multiplier"]
    
    boosted_amount = base_amount * total_multiplier
    boost_added = boosted_amount - base_amount
    
    # Mark single-use boosters as used
    for booster in boosters_data["active_boosters"]:
        if booster.get("single_use") and outcome_id:
            booster["used"] = True
            booster["used_at"] = datetime.now(timezone.utc).isoformat()
            booster["used_on_outcome"] = outcome_id
    
    return {
        "base_amount": round(base_amount, 2),
        "total_multiplier": total_multiplier,
        "boosted_amount": round(boosted_amount, 2),
        "boost_added": round(boost_added, 2),
        "active_boosters": boosters_data["active_boosters"],
        "breakdown": {
            "original": f"${base_amount:.2f}",
            "multiplier": f"{total_multiplier}x",
            "bonus": f"+${boost_added:.2f}",
            "total": f"${boosted_amount:.2f}"
        }
    }


def track_referral(
    referrer_username: str,
    referee_username: str,
    referral_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Track a referral and activate referral booster.
    
    Args:
        referrer_username: User who referred
        referee_username: User who signed up
        referral_code: Referral code used
    
    Returns:
        Referral tracking confirmation
    """
    referral_id = f"ref_{referrer_username}_{referee_username}_{int(datetime.now(timezone.utc).timestamp())}"
    
    referral = {
        "referral_id": referral_id,
        "referrer": referrer_username,
        "referee": referee_username,
        "referral_code": referral_code,
        "status": "signed_up",
        "referred_at": datetime.now(timezone.utc).isoformat(),
        "first_outcome_completed": False,
        "subscribed": False,
        "bonuses_awarded": []
    }
    
    REFERRAL_DB[referral_id] = referral
    
    # Activate referral booster for referrer
    activate_booster(
        referrer_username,
        "referral_1",
        source="referral",
        metadata={"referee": referee_username, "referral_id": referral_id}
    )
    
    # Check if referrer qualifies for milestone booster
    _check_referral_milestones(referrer_username)
    
    return {
        "success": True,
        "referral_id": referral_id,
        "message": f"{referrer_username} earned +10% booster for 30 days!",
        "referee": referee_username
    }


def _check_referral_milestones(username: str) -> None:
    """Check if user has hit referral milestones."""
    # Count active referrals
    active_referrals = [
        ref for ref in REFERRAL_DB.values()
        if ref["referrer"] == username and ref["status"] in ["signed_up", "active"]
    ]
    
    if len(active_referrals) >= 5:
        # Award milestone booster
        activate_booster(
            username,
            "referral_milestone_1",
            source="milestone",
            metadata={"active_referrals": len(active_referrals)}
        )


def award_referral_milestone_bonus(
    referrer_username: str,
    milestone: str,
    referee_username: str
) -> Dict[str, Any]:
    """
    Award bonus when referee hits milestone.
    
    Args:
        referrer_username: Referrer to award
        milestone: Milestone type (first_outcome/subscription)
        referee_username: Referee who hit milestone
    
    Returns:
        Bonus award confirmation
    """
    # Find referral
    referral = None
    for ref in REFERRAL_DB.values():
        if ref["referrer"] == referrer_username and ref["referee"] == referee_username:
            referral = ref
            break
    
    if not referral:
        return {"success": False, "error": "Referral not found"}
    
    # Award based on milestone
    bonus_amount = 0
    if milestone == "first_outcome" and not referral["first_outcome_completed"]:
        bonus_amount = 50.00  # $50 bonus
        referral["first_outcome_completed"] = True
        referral["first_outcome_at"] = datetime.now(timezone.utc).isoformat()
    elif milestone == "subscription" and not referral["subscribed"]:
        bonus_amount = 100.00  # $100 bonus
        referral["subscribed"] = True
        referral["subscribed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Also grant 5% kickback booster
        activate_booster(
            referrer_username,
            "referral_kickback",
            source="referral_subscription",
            metadata={"referee": referee_username}
        )
    
    if bonus_amount > 0:
        referral["bonuses_awarded"].append({
            "milestone": milestone,
            "amount": bonus_amount,
            "awarded_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": True,
            "bonus_amount": bonus_amount,
            "milestone": milestone,
            "message": f"Awarded ${bonus_amount} for {milestone}!"
        }
    
    return {"success": False, "error": "Milestone already awarded or invalid"}


def check_streak(username: str, last_active: str) -> Dict[str, Any]:
    """
    Check and update user's activity streak.
    
    Args:
        username: User's username
        last_active: ISO timestamp of last activity
    
    Returns:
        Streak status and booster awards
    """
    if username not in STREAK_DB:
        STREAK_DB[username] = {
            "current_streak": 1,
            "longest_streak": 1,
            "last_active": last_active,
            "streak_start": last_active
        }
        return {"current_streak": 1, "booster_awarded": False}
    
    streak_data = STREAK_DB[username]
    last_active_dt = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
    previous_active_dt = datetime.fromisoformat(streak_data["last_active"].replace("Z", "+00:00"))
    
    hours_since = (last_active_dt - previous_active_dt).total_seconds() / 3600
    
    if hours_since <= 24:
        # Continue streak
        streak_data["current_streak"] += 1
        streak_data["last_active"] = last_active
    elif hours_since <= 48:
        # Same day, don't increment
        streak_data["last_active"] = last_active
    else:
        # Streak broken
        streak_data["current_streak"] = 1
        streak_data["streak_start"] = last_active
        streak_data["last_active"] = last_active
    
    # Update longest streak
    if streak_data["current_streak"] > streak_data["longest_streak"]:
        streak_data["longest_streak"] = streak_data["current_streak"]
    
    # Award streak boosters
    booster_awarded = False
    current = streak_data["current_streak"]
    
    if current == 7:
        activate_booster(username, "streak_7", source="streak")
        booster_awarded = True
    elif current == 30:
        activate_booster(username, "streak_30", source="streak")
        booster_awarded = True
    elif current == 90:
        activate_booster(username, "streak_90", source="streak")
        booster_awarded = True
    
    return {
        "current_streak": current,
        "longest_streak": streak_data["longest_streak"],
        "booster_awarded": booster_awarded,
        "hours_since_last": round(hours_since, 1)
    }


def purchase_power_up(
    username: str,
    power_up_type: str,
    payment_method: str = "stripe"
) -> Dict[str, Any]:
    """
    Purchase a power-up booster.
    
    Args:
        username: User purchasing
        power_up_type: Type of power-up
        payment_method: Payment method
    
    Returns:
        Purchase confirmation and activated booster
    """
    if power_up_type not in BOOSTER_TYPES:
        raise ValueError(f"Invalid power-up type: {power_up_type}")
    
    booster_config = BOOSTER_TYPES[power_up_type]
    
    if not booster_config.get("purchasable"):
        raise ValueError(f"Booster {power_up_type} is not purchasable")
    
    cost = booster_config["cost_usd"]
    
    # Record purchase
    purchase_id = f"purchase_{username}_{power_up_type}_{int(datetime.now(timezone.utc).timestamp())}"
    
    purchase = {
        "purchase_id": purchase_id,
        "username": username,
        "power_up_type": power_up_type,
        "cost_usd": cost,
        "payment_method": payment_method,
        "purchased_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed"
    }
    
    BOOSTER_PURCHASES_DB[purchase_id] = purchase
    
    # Activate booster
    result = activate_booster(username, power_up_type, source="purchase")
    
    return {
        "success": True,
        "purchase_id": purchase_id,
        "cost": cost,
        "booster": result.get("booster"),
        "message": f"Purchased {booster_config['name']} for ${cost}!"
    }


def get_available_boosters(username: str) -> Dict[str, Any]:
    """
    Get all boosters available to user.
    
    Returns:
        Categorized list of available boosters
    """
    categorized = {
        "referral": [],
        "streak": [],
        "milestone": [],
        "time_limited": [],
        "power_up": []
    }
    
    for booster_type, config in BOOSTER_TYPES.items():
        category = config["category"]
        
        booster_info = {
            "type": booster_type,
            "name": config["name"],
            "icon": config["icon"],
            "description": config["description"],
            "multiplier": config["multiplier"],
            "boost_percent": (config["multiplier"] - 1.0) * 100,
            "stackable": config.get("stackable", False)
        }
        
        # Add category-specific info
        if category == "power_up":
            booster_info["cost_usd"] = config.get("cost_usd", 0)
            booster_info["duration"] = _format_duration(config)
        
        categorized[category].append(booster_info)
    
    return {
        "categories": categorized,
        "total_boosters": len(BOOSTER_TYPES)
    }


def _format_duration(config: Dict[str, Any]) -> str:
    """Format booster duration for display."""
    if config.get("single_use"):
        return "Single use"
    elif config.get("duration_hours"):
        return f"{config['duration_hours']} hours"
    elif config.get("duration_days"):
        return f"{config['duration_days']} days"
    else:
        return "Permanent"


def get_booster_leaderboard(limit: int = 10) -> Dict[str, Any]:
    """
    Get leaderboard of users with highest total multipliers.
    
    Args:
        limit: Number of top users to return
    
    Returns:
        Leaderboard with top boosted users
    """
    leaderboard = []
    
    for username in USER_BOOSTERS_DB.keys():
        boosters_data = get_active_boosters(username)
        
        leaderboard.append({
            "username": username,
            "total_multiplier": boosters_data["total_multiplier"],
            "boost_percent": boosters_data["boost_percent"],
            "active_booster_count": boosters_data["booster_count"]
        })
    
    # Sort by multiplier
    leaderboard.sort(key=lambda x: x["total_multiplier"], reverse=True)
    
    return {
        "leaderboard": leaderboard[:limit],
        "total_users": len(leaderboard)
    }


# Example usage
if __name__ == "__main__":
    # Activate boosters
    result = activate_booster("wade999", "early_adopter", "milestone")
    print(f"Activated: {result['booster']['name']}")
    
    # Track referral
    ref = track_referral("wade999", "alice123")
    print(f"\nReferral tracked: {ref['message']}")
    
    # Calculate boosted earnings
    earnings = calculate_boosted_earnings(1000.0, "wade999")
    print(f"\nBase: ${earnings['base_amount']}")
    print(f"Multiplier: {earnings['total_multiplier']}x")
    print(f"Boosted: ${earnings['boosted_amount']}")
    
    # Check active boosters
    active = get_active_boosters("wade999")
    print(f"\nActive boosters: {active['booster_count']}")
    print(f"Total boost: +{active['boost_percent']}%")
