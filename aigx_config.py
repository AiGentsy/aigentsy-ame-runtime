# aigx_config.py
"""
AiGentsy AIGx Configuration
Complete configuration for AIGx earning, tier progression, and early adopter benefits.
"""

AIGX_CONFIG = {
    # ============================================================
    # LEGAL & EQUITY STRUCTURE
    # ============================================================
    "legal_structure": "Profit Participation Rights",
    "company_valuation": 100_000_000,  # $100M fixed, increases over time
    "equity_pool_percent": 20.0,  # 20% of company TOTAL
    "supply_model": "dynamic",  # Grows as needed, never runs out
    "conversion_events": [
        "IPO", 
        "Acquisition > $500M", 
        "Qualified Financing > $100M"
    ],
    "payout_method": "Cash = (user_AIGx / total_AIGx) * 20% * exit_value",
    "transferable": False,
    "vesting": "immediate",
    
    # ============================================================
    # EARNING METHODS
    # ============================================================
    "earning_methods": {
        "transaction_revenue": True,   # 1-5 AIGx per $100 based on tier
        "platform_activity": True,     # 10 AIGx/day, 100/week, 500/month
        "milestones": True,            # 1k-100k AIGx for achievements
        "referrals": True,             # 500-2k AIGx per referral
        "subscription_payment": False  # ❌ NO payment → AIGx (SEC safe)
    },
    
    # ============================================================
    # PRICING (NO SUBSCRIPTION MODEL)
    # ============================================================
    "pricing": {
        "monthly_fee": 0,              # NO subscription
        "transaction_rate": 0.025,     # 2.5% per transaction
        "transaction_fixed": 0.30      # 30¢ per transaction
    },
    
    # ============================================================
    # TIER PROGRESSION (Revenue-Based Unlocks)
    # ============================================================
    "tier_progression": {
        "free": {
            "unlock_at": 0,              # Available immediately
            "aigx_multiplier": 1.0,      # 1x AIGx earning
            "transaction_rate": 0.025,   # 2.5%
            "features": [
                "Basic dashboard",
                "AME auto-pitches",
                "Intent Exchange access",
                "Up to $1k monthly revenue"
            ]
        },
        "pro": {
            "unlock_at": 10_000,         # $10k lifetime revenue
            "aigx_multiplier": 2.0,      # 2x AIGx earning
            "transaction_rate": 0.020,   # 2.0% (discounted)
            "features": [
                "Advanced analytics",
                "OCL (working capital)",
                "Priority support",
                "Unlimited revenue"
            ]
        },
        "ultra": {
            "unlock_at": 100_000,        # $100k lifetime revenue
            "aigx_multiplier": 5.0,      # 5x AIGx earning
            "transaction_rate": 0.015,   # 1.5% (best rate)
            "features": [
                "Dedicated account manager",
                "Custom integrations",
                "White-label options",
                "Enterprise SLA"
            ]
        }
    },
    
    # ============================================================
    # EARLY ADOPTER TIERS (One-Time Bonuses)
    # ============================================================
    "early_adopter": {
        "founding_100": {
            "user_range": (1, 100),      # Users 1-100
            "multiplier": 3.0,           # 3x permanent multiplier
            "bonus": 10_000,             # 10k AIGx signup bonus
            "badge": "Founder",
            "perks": [
                "Lifetime 3x AIGx multiplier",
                "Founding member badge",
                "Priority feature requests",
                "Annual founder summit invite"
            ]
        },
        "early_1000": {
            "user_range": (101, 1000),   # Users 101-1,000
            "multiplier": 2.0,           # 2x permanent multiplier
            "bonus": 5_000,              # 5k AIGx signup bonus
            "badge": "Early Adopter",
            "perks": [
                "Lifetime 2x AIGx multiplier",
                "Early adopter badge",
                "Beta feature access"
            ]
        },
        "pioneer_10000": {
            "user_range": (1001, 10_000),  # Users 1,001-10,000
            "multiplier": 1.5,             # 1.5x permanent multiplier
            "bonus": 1_000,                # 1k AIGx signup bonus
            "badge": "Pioneer",
            "perks": [
                "Lifetime 1.5x AIGx multiplier",
                "Pioneer badge"
            ]
        }
    },
    
    # ============================================================
    # MILESTONE REWARDS (Achievement-Based)
    # ============================================================
    "milestones": {
        "first_sale": {
            "aigx_reward": 1_000,
            "description": "Complete your first transaction"
        },
        "revenue_1k": {
            "aigx_reward": 2_000,
            "description": "Reach $1,000 in revenue"
        },
        "revenue_10k": {
            "aigx_reward": 10_000,
            "description": "Reach $10,000 in revenue (Pro tier unlocked)"
        },
        "revenue_50k": {
            "aigx_reward": 25_000,
            "description": "Reach $50,000 in revenue"
        },
        "revenue_100k": {
            "aigx_reward": 50_000,
            "description": "Reach $100,000 in revenue (Ultra tier unlocked)"
        },
        "revenue_500k": {
            "aigx_reward": 100_000,
            "description": "Reach $500,000 in revenue"
        },
        "first_referral": {
            "aigx_reward": 500,
            "description": "Refer your first user"
        },
        "referral_5": {
            "aigx_reward": 2_000,
            "description": "Refer 5 active users"
        },
        "referral_10": {
            "aigx_reward": 5_000,
            "description": "Refer 10 active users"
        }
    },
    
    # ============================================================
    # ACTIVITY REWARDS (Daily/Weekly/Monthly)
    # ============================================================
    "activity_rewards": {
        "daily_active": {
            "aigx_reward": 10,
            "description": "Log in and engage daily"
        },
        "weekly_streak": {
            "aigx_reward": 100,
            "description": "Maintain 7-day active streak"
        },
        "monthly_power_user": {
            "aigx_reward": 500,
            "description": "30 days of consistent activity"
        }
    },
    
    # ============================================================
    # AIGX EARNING RATES (Transaction-Based)
    # ============================================================
    "transaction_earning_rates": {
        "free_tier": {
            "aigx_per_100_usd": 1.0,    # 1 AIGx per $100 revenue
            "description": "Base earning rate"
        },
        "pro_tier": {
            "aigx_per_100_usd": 2.0,    # 2 AIGx per $100 revenue
            "description": "2x earning rate"
        },
        "ultra_tier": {
            "aigx_per_100_usd": 5.0,    # 5 AIGx per $100 revenue
            "description": "5x earning rate"
        }
    }
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def determine_early_adopter_tier(user_number: int) -> dict:
    """
    Determine early adopter tier based on user number.
    
    Args:
        user_number: Sequential user number (1, 2, 3, etc.)
        
    Returns:
        dict: {
            "tier": str,           # "founding_100", "early_1000", "pioneer_10000", or None
            "multiplier": float,   # Permanent AIGx multiplier
            "bonus": int,          # One-time signup bonus
            "badge": str,          # Display badge
            "perks": list          # List of perks
        }
    """
    for tier_key, tier_data in AIGX_CONFIG["early_adopter"].items():
        min_user, max_user = tier_data["user_range"]
        if min_user <= user_number <= max_user:
            return {
                "tier": tier_key,
                "multiplier": tier_data["multiplier"],
                "bonus": tier_data["bonus"],
                "badge": tier_data["badge"],
                "perks": tier_data["perks"]
            }
    
    # Standard tier (no early adopter benefits)
    return {
        "tier": None,
        "multiplier": 1.0,
        "bonus": 0,
        "badge": None,
        "perks": []
    }


def calculate_user_tier(lifetime_revenue: float) -> str:
    """
    Calculate user tier based on lifetime revenue.
    
    Args:
        lifetime_revenue: Total revenue generated by user
        
    Returns:
        str: "free", "pro", or "ultra"
    """
    tiers = AIGX_CONFIG["tier_progression"]
    
    if lifetime_revenue >= tiers["ultra"]["unlock_at"]:
        return "ultra"
    elif lifetime_revenue >= tiers["pro"]["unlock_at"]:
        return "pro"
    else:
        return "free"


def calculate_aigx_from_transaction(
    amount_usd: float,
    user_tier: str,
    early_adopter_multiplier: float = 1.0
) -> float:
    """
    Calculate AIGx earned from a transaction.
    
    Args:
        amount_usd: Transaction amount in USD
        user_tier: "free", "pro", or "ultra"
        early_adopter_multiplier: Early adopter permanent multiplier (1.0, 1.5, 2.0, or 3.0)
        
    Returns:
        float: AIGx earned from transaction
    """
    # Get tier multiplier
    tier_data = AIGX_CONFIG["tier_progression"].get(user_tier, {})
    tier_multiplier = tier_data.get("aigx_multiplier", 1.0)
    
    # Base earning: 1 AIGx per $100
    base_aigx = amount_usd / 100.0
    
    # Apply multipliers
    total_aigx = base_aigx * tier_multiplier * early_adopter_multiplier
    
    return round(total_aigx, 2)


def get_platform_fee(amount_usd: float, user_tier: str = "free") -> dict:
    """
    Calculate platform fee for a transaction.
    
    Args:
        amount_usd: Transaction amount in USD
        user_tier: "free", "pro", or "ultra"
        
    Returns:
        dict: {
            "percentage_fee": float,
            "fixed_fee": float,
            "total_fee": float,
            "net_to_user": float
        }
    """
    tier_data = AIGX_CONFIG["tier_progression"].get(user_tier, {})
    rate = tier_data.get("transaction_rate", AIGX_CONFIG["pricing"]["transaction_rate"])
    fixed = AIGX_CONFIG["pricing"]["transaction_fixed"]
    
    percentage_fee = amount_usd * rate
    total_fee = percentage_fee + fixed
    net_to_user = amount_usd - total_fee
    
    return {
        "percentage_fee": round(percentage_fee, 2),
        "fixed_fee": fixed,
        "total_fee": round(total_fee, 2),
        "net_to_user": round(net_to_user, 2),
        "rate_applied": rate
    }


def check_milestone_reward(lifetime_revenue: float, previous_revenue: float = 0) -> dict:
    """
    Check if user crossed a milestone threshold with this revenue.
    
    Args:
        lifetime_revenue: New total lifetime revenue
        previous_revenue: Previous lifetime revenue
        
    Returns:
        dict: {
            "milestone_hit": bool,
            "milestone_key": str or None,
            "aigx_reward": int,
            "description": str
        }
    """
    milestones = AIGX_CONFIG["milestones"]
    
    # Define revenue milestones in order
    revenue_milestones = [
        ("revenue_1k", 1_000),
        ("revenue_10k", 10_000),
        ("revenue_50k", 50_000),
        ("revenue_100k", 100_000),
        ("revenue_500k", 500_000)
    ]
    
    for milestone_key, threshold in revenue_milestones:
        if previous_revenue < threshold <= lifetime_revenue:
            milestone_data = milestones[milestone_key]
            return {
                "milestone_hit": True,
                "milestone_key": milestone_key,
                "aigx_reward": milestone_data["aigx_reward"],
                "description": milestone_data["description"]
            }
    
    return {
        "milestone_hit": False,
        "milestone_key": None,
        "aigx_reward": 0,
        "description": ""
    }


def calculate_equity_value(user_aigx: float, total_aigx: float) -> dict:
    """
    Calculate user's equity value based on AIGx holdings.
    
    Args:
        user_aigx: User's total AIGx balance
        total_aigx: Total AIGx in circulation
        
    Returns:
        dict: {
            "equity_percent": float,
            "equity_value_usd": float,
            "company_valuation": float
        }
    """
    if total_aigx == 0:
        return {
            "equity_percent": 0.0,
            "equity_value_usd": 0.0,
            "company_valuation": AIGX_CONFIG["company_valuation"]
        }
    
    # User's share of the 20% equity pool
    user_share_of_pool = user_aigx / total_aigx
    equity_percent = user_share_of_pool * AIGX_CONFIG["equity_pool_percent"]
    
    # Dollar value at current valuation
    equity_value_usd = (equity_percent / 100) * AIGX_CONFIG["company_valuation"]
    
    return {
        "equity_percent": round(equity_percent, 4),
        "equity_value_usd": round(equity_value_usd, 2),
        "company_valuation": AIGX_CONFIG["company_valuation"]
    }
