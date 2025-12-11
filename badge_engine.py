"""
AiGentsy Passport Badges & Social Proof System
-----------------------------------------------
Tracks achievements, unlocks badges, provides social proof signals.

Features:
- Achievement tracking (First Deal, 10 Deals, 100 UoO, etc.)
- Badge unlocking based on milestones
- Social proof (verification, ratings, portfolio)
- Trust signals (badges, credentials, testimonials)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


# ============================================================
# BADGE DEFINITIONS
# ============================================================

BADGE_CATALOG = {
    # ========== OUTCOME BADGES ==========
    "first_outcome": {
        "id": "first_outcome",
        "name": "First Delivery",
        "description": "Completed your first verified outcome",
        "icon": "🎯",
        "tier": "bronze",
        "criteria": {"verified_outcomes": 1},
        "points": 10
    },
    "ten_outcomes": {
        "id": "ten_outcomes",
        "name": "Reliable Deliverer",
        "description": "Completed 10 verified outcomes",
        "icon": "📦",
        "tier": "silver",
        "criteria": {"verified_outcomes": 10},
        "points": 50
    },
    "fifty_outcomes": {
        "id": "fifty_outcomes",
        "name": "Veteran Agent",
        "description": "Completed 50 verified outcomes",
        "icon": "⭐",
        "tier": "gold",
        "criteria": {"verified_outcomes": 50},
        "points": 250
    },
    "hundred_outcomes": {
        "id": "hundred_outcomes",
        "name": "Elite Producer",
        "description": "Completed 100 verified outcomes",
        "icon": "👑",
        "tier": "platinum",
        "criteria": {"verified_outcomes": 100},
        "points": 1000
    },
    
    # ========== UoO BADGES ==========
    "uoo_10": {
        "id": "uoo_10",
        "name": "Rising Star",
        "description": "Earned 10 UoO points",
        "icon": "🌟",
        "tier": "bronze",
        "criteria": {"total_uoo": 10},
        "points": 20
    },
    "uoo_50": {
        "id": "uoo_50",
        "name": "Skilled Professional",
        "description": "Earned 50 UoO points",
        "icon": "💎",
        "tier": "silver",
        "criteria": {"total_uoo": 50},
        "points": 100
    },
    "uoo_100": {
        "id": "uoo_100",
        "name": "Master Agent",
        "description": "Earned 100 UoO points",
        "icon": "🏆",
        "tier": "gold",
        "criteria": {"total_uoo": 100},
        "points": 500
    },
    
    # ========== REVENUE BADGES ==========
    "first_revenue": {
        "id": "first_revenue",
        "name": "First Earnings",
        "description": "Earned your first dollar",
        "icon": "💵",
        "tier": "bronze",
        "criteria": {"total_revenue": 1},
        "points": 5
    },
    "revenue_1k": {
        "id": "revenue_1k",
        "name": "Thousand Club",
        "description": "Earned $1,000 in revenue",
        "icon": "💰",
        "tier": "silver",
        "criteria": {"total_revenue": 1000},
        "points": 50
    },
    "revenue_10k": {
        "id": "revenue_10k",
        "name": "Five Figure Earner",
        "description": "Earned $10,000 in revenue",
        "icon": "💸",
        "tier": "gold",
        "criteria": {"total_revenue": 10000},
        "points": 250
    },
    "revenue_100k": {
        "id": "revenue_100k",
        "name": "Six Figure Club",
        "description": "Earned $100,000 in revenue",
        "icon": "🎖️",
        "tier": "platinum",
        "criteria": {"total_revenue": 100000},
        "points": 2500
    },
    
    # ========== QUALITY BADGES ==========
    "perfect_score": {
        "id": "perfect_score",
        "name": "Perfect Record",
        "description": "100% verification rate on 10+ outcomes",
        "icon": "✨",
        "tier": "gold",
        "criteria": {"verified_outcomes": 10, "verification_rate": 100},
        "points": 200
    },
    "top_rated": {
        "id": "top_rated",
        "name": "Top Rated",
        "description": "Outcome score of 90+",
        "icon": "🌠",
        "tier": "gold",
        "criteria": {"outcome_score": 90},
        "points": 150
    },
    
    # ========== SPEED BADGES ==========
    "lightning_fast": {
        "id": "lightning_fast",
        "name": "Lightning Fast",
        "description": "Delivered 5 outcomes ahead of schedule",
        "icon": "⚡",
        "tier": "silver",
        "criteria": {"early_deliveries": 5},
        "points": 100
    },
    
    # ========== SOCIAL BADGES ==========
    "early_adopter": {
        "id": "early_adopter",
        "name": "Early Adopter",
        "description": "Joined AiGentsy in the first 100 users",
        "icon": "🚀",
        "tier": "platinum",
        "criteria": {"user_number": 100},
        "points": 500
    },
    "referral_master": {
        "id": "referral_master",
        "name": "Referral Master",
        "description": "Referred 10 active users",
        "icon": "🤝",
        "tier": "gold",
        "criteria": {"active_referrals": 10},
        "points": 300
    },
    
    # ========== SPECIALTY BADGES ==========
    "multi_skilled": {
        "id": "multi_skilled",
        "name": "Multi-Skilled",
        "description": "Delivered outcomes in 3+ different archetypes",
        "icon": "🎭",
        "tier": "silver",
        "criteria": {"archetype_count": 3},
        "points": 75
    },
    "specialist": {
        "id": "specialist",
        "name": "Specialist",
        "description": "50+ outcomes in single archetype",
        "icon": "🎯",
        "tier": "gold",
        "criteria": {"single_archetype_count": 50},
        "points": 200
    }
}


# ============================================================
# BADGE CHECKING & UNLOCKING
# ============================================================

def check_badges(user_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check which badges user has unlocked based on their stats.
    
    Args:
        user_stats: User statistics (outcomes, revenue, UoO, etc.)
        
    Returns:
        dict: Unlocked badges and newly earned badges
    """
    
    unlocked_badges = []
    newly_earned = []
    
    for badge_id, badge_def in BADGE_CATALOG.items():
        criteria = badge_def["criteria"]
        
        # Check if user meets all criteria
        meets_criteria = True
        for criterion, required_value in criteria.items():
            user_value = user_stats.get(criterion, 0)
            
            # Special handling for verification_rate (percentage)
            if criterion == "verification_rate":
                if user_value < required_value:
                    meets_criteria = False
                    break
            # Special handling for user_number (less than or equal to)
            elif criterion == "user_number":
                if user_value > required_value:
                    meets_criteria = False
                    break
            # Default: user must have at least the required value
            else:
                if user_value < required_value:
                    meets_criteria = False
                    break
        
        if meets_criteria:
            badge_data = {
                **badge_def,
                "earned_at": now_iso(),
                "criteria_met": criteria
            }
            unlocked_badges.append(badge_data)
    
    return {
        "ok": True,
        "unlocked_badges": unlocked_badges,
        "total_badges": len(unlocked_badges),
        "total_points": sum(b["points"] for b in unlocked_badges),
        "checked_at": now_iso()
    }


def get_user_badges(username: str) -> Dict[str, Any]:
    """
    Get all badges for a user from their stats.
    
    Calculates stats from user record and checks badge eligibility.
    """
    from log_to_jsonbin import get_user
    from outcome_oracle import get_agent_poo_stats
    from analytics_engine import get_uol_summary
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "user_not_found"}
    
    # ============================================
    # GATHER USER STATS
    # ============================================
    
    # Outcome stats
    poo_stats = get_agent_poo_stats(username)
    verified_outcomes = poo_stats.get("stats", {}).get("verified", 0)
    total_submitted = poo_stats.get("stats", {}).get("total_submitted", 0)
    verification_rate = poo_stats.get("stats", {}).get("verification_rate", 0)
    
    # UoO stats
    uol_summary = get_uol_summary(username)
    total_uoo = uol_summary.get("total_uoo", 0)
    
    # Revenue stats
    revenue_tracking = user.get("revenue_tracking", {})
    total_revenue = revenue_tracking.get("total_revenue_usd", 0)
    
    # Outcome score
    outcome_score = int(user.get("outcomeScore", 0))
    
    # User number (for early adopter)
    user_number = user.get("user_number", 9999)
    
    # Archetype diversity
    uoo_by_archetype = uol_summary.get("by_archetype", {})
    archetype_count = len(uoo_by_archetype)
    
    single_archetype_max = max(
        (data.get("count", 0) for data in uoo_by_archetype.values()),
        default=0
    )
    
    # Referrals (if tracked)
    active_referrals = len(user.get("referrals", []))
    
    # Early deliveries (if tracked)
    early_deliveries = user.get("early_deliveries", 0)
    
    # ============================================
    # BUILD STATS OBJECT
    # ============================================
    
    user_stats = {
        "verified_outcomes": verified_outcomes,
        "total_uoo": total_uoo,
        "total_revenue": total_revenue,
        "verification_rate": verification_rate,
        "outcome_score": outcome_score,
        "user_number": user_number,
        "archetype_count": archetype_count,
        "single_archetype_count": single_archetype_max,
        "active_referrals": active_referrals,
        "early_deliveries": early_deliveries
    }
    
    # ============================================
    # CHECK BADGES
    # ============================================
    
    badge_result = check_badges(user_stats)
    
    return {
        "ok": True,
        "username": username,
        "badges": badge_result["unlocked_badges"],
        "badge_count": badge_result["total_badges"],
        "total_points": badge_result["total_points"],
        "stats": user_stats,
        "generated_at": now_iso()
    }


def get_badge_progress(username: str) -> Dict[str, Any]:
    """
    Show progress toward earning badges (not yet unlocked).
    """
    from log_to_jsonbin import get_user
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "user_not_found"}
    
    # Get current badges
    current_badges_result = get_user_badges(username)
    if not current_badges_result.get("ok"):
        return current_badges_result
    
    unlocked_badge_ids = {b["id"] for b in current_badges_result["badges"]}
    user_stats = current_badges_result["stats"]
    
    # Check progress on locked badges
    locked_badges = []
    
    for badge_id, badge_def in BADGE_CATALOG.items():
        if badge_id in unlocked_badge_ids:
            continue  # Already unlocked
        
        criteria = badge_def["criteria"]
        progress = {}
        
        for criterion, required_value in criteria.items():
            current_value = user_stats.get(criterion, 0)
            progress[criterion] = {
                "current": current_value,
                "required": required_value,
                "percentage": min(100, round((current_value / required_value * 100), 1)) if required_value > 0 else 0,
                "remaining": max(0, required_value - current_value)
            }
        
        # Calculate overall progress (average of all criteria)
        avg_progress = sum(p["percentage"] for p in progress.values()) / len(progress) if progress else 0
        
        locked_badges.append({
            **badge_def,
            "progress": progress,
            "overall_progress": round(avg_progress, 1)
        })
    
    # Sort by progress (closest to unlocking first)
    locked_badges.sort(key=lambda b: b["overall_progress"], reverse=True)
    
    return {
        "ok": True,
        "username": username,
        "locked_badges": locked_badges,
        "unlocked_count": len(unlocked_badge_ids),
        "total_badges": len(BADGE_CATALOG),
        "completion_percentage": round((len(unlocked_badge_ids) / len(BADGE_CATALOG) * 100), 1)
    }


# ============================================================
# SOCIAL PROOF
# ============================================================

def get_social_proof(username: str) -> Dict[str, Any]:
    """
    Get social proof signals for a user.
    
    Includes:
    - Badges
    - Verification status
    - Rating/outcome score
    - Portfolio highlights
    - Trust signals
    """
    from log_to_jsonbin import get_user
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "user_not_found"}
    
    # Get badges
    badges_result = get_user_badges(username)
    badges = badges_result.get("badges", [])
    
    # Verification status
    is_verified = user.get("verified", False)
    verification_level = "unverified"
    if is_verified:
        verification_level = "verified"
    if user.get("outcome_score", 0) >= 85:
        verification_level = "elite"
    
    # Rating
    outcome_score = int(user.get("outcomeScore", 50))
    rating_stars = round(outcome_score / 20, 1)  # Convert 0-100 to 0-5 stars
    
    # Portfolio highlights (top 3 outcomes by UoO)
    from outcome_oracle import list_poos
    poos_result = list_poos(agent=username, status="VERIFIED")
    poos = poos_result.get("poos", [])
    
    # Sort by UoO score
    poos_sorted = sorted(poos, key=lambda p: p.get("uoo", {}).get("uoo_score", 0), reverse=True)
    portfolio_highlights = [
        {
            "title": p.get("title"),
            "uoo_score": p.get("uoo", {}).get("uoo_score"),
            "archetype": p.get("uoo", {}).get("archetype_name"),
            "verified_at": p.get("verified_at")
        }
        for p in poos_sorted[:3]
    ]
    
    # Trust signals
    trust_signals = []
    
    if outcome_score >= 85:
        trust_signals.append({
            "signal": "elite_performer",
            "label": "Elite Performer",
            "icon": "⭐",
            "description": "Top 15% outcome score"
        })
    
    if is_verified:
        trust_signals.append({
            "signal": "verified_account",
            "label": "Verified Account",
            "icon": "✓",
            "description": "Identity verified"
        })
    
    if len(badges) >= 5:
        trust_signals.append({
            "signal": "achievement_unlocked",
            "label": f"{len(badges)} Badges Earned",
            "icon": "🏅",
            "description": "Proven track record"
        })
    
    verification_rate = badges_result.get("stats", {}).get("verification_rate", 0)
    if verification_rate >= 95:
        trust_signals.append({
            "signal": "high_approval",
            "label": f"{verification_rate}% Approval Rate",
            "icon": "👍",
            "description": "Consistently delivers quality"
        })
    
    return {
        "ok": True,
        "username": username,
        "verification_level": verification_level,
        "rating": {
            "outcome_score": outcome_score,
            "stars": rating_stars,
            "formatted": f"{rating_stars}/5.0"
        },
        "badges": {
            "earned": badges,
            "count": len(badges),
            "top_tier": max((b["tier"] for b in badges), default="none") if badges else "none"
        },
        "portfolio_highlights": portfolio_highlights,
        "trust_signals": trust_signals,
        "generated_at": now_iso()
    }


# ============================================================
# BADGE CATALOG HELPERS
# ============================================================

def list_all_badges() -> Dict[str, Any]:
    """Get complete badge catalog"""
    return {
        "ok": True,
        "badges": list(BADGE_CATALOG.values()),
        "total_badges": len(BADGE_CATALOG),
        "tiers": ["bronze", "silver", "gold", "platinum"]
    }


def get_badge_info(badge_id: str) -> Dict[str, Any]:
    """Get details for a specific badge"""
    badge = BADGE_CATALOG.get(badge_id)
    if not badge:
        return {"ok": False, "error": "badge_not_found"}
    
    return {
        "ok": True,
        "badge": badge
    }
