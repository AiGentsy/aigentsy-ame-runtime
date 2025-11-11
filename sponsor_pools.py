"""
AiGentsy Sponsor/Co-Op Outcome Pools
External capital subsidizes specific outcomes with verified ROI tracking
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4

def _now():
    return datetime.now(timezone.utc).isoformat()


# Pool types
POOL_TYPES = {
    "outcome_specific": {
        "name": "Outcome-Specific Pool",
        "description": "Subsidize specific job types/outcomes",
        "examples": ["website_migrations", "seo_audits", "design_refreshes"]
    },
    "category_wide": {
        "name": "Category-Wide Pool",
        "description": "Subsidize entire category of work",
        "examples": ["all_marketing", "all_development", "all_consulting"]
    },
    "agent_sponsored": {
        "name": "Agent-Sponsored Pool",
        "description": "Sponsor specific high-performing agents",
        "examples": ["top_10_agents", "rising_stars", "specialists"]
    },
    "geographic": {
        "name": "Geographic Pool",
        "description": "Target specific regions/markets",
        "examples": ["seattle_area", "eu_market", "emerging_markets"]
    }
}

# Discount application methods
DISCOUNT_METHODS = {
    "percentage": "Apply X% discount to job price",
    "fixed_amount": "Apply $X discount to job price",
    "credit_allocation": "Allocate X credits to buyer account"
}


def create_sponsor_pool(
    sponsor_name: str,
    pool_type: str,
    target_outcomes: List[str],
    total_budget: float,
    discount_percentage: float = None,
    discount_fixed: float = None,
    duration_days: int = 90,
    max_per_job: float = None,
    criteria: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create a sponsor pool
    
    Parameters:
    - sponsor_name: Company/brand sponsoring
    - pool_type: Type of pool
    - target_outcomes: List of outcome types to subsidize
    - total_budget: Total pool funding
    - discount_percentage: % discount (e.g., 0.20 for 20% off)
    - discount_fixed: Fixed $ discount per job
    - duration_days: How long pool is active
    - max_per_job: Maximum discount per individual job
    - criteria: Additional filtering (e.g., min_agent_score, specific_skills)
    """
    if pool_type not in POOL_TYPES:
        return {
            "ok": False,
            "error": "invalid_pool_type",
            "valid_types": list(POOL_TYPES.keys())
        }
    
    if total_budget <= 0:
        return {
            "ok": False,
            "error": "budget_must_be_positive",
            "provided": total_budget
        }
    
    # Must specify either percentage or fixed discount
    if not discount_percentage and not discount_fixed:
        return {
            "ok": False,
            "error": "must_specify_discount_percentage_or_fixed"
        }
    
    pool_id = f"pool_{uuid4().hex[:12]}"
    
    pool = {
        "id": pool_id,
        "sponsor": sponsor_name,
        "pool_type": pool_type,
        "target_outcomes": target_outcomes,
        "status": "active",
        "created_at": _now(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat(),
        "duration_days": duration_days,
        
        # Budget tracking
        "total_budget": total_budget,
        "remaining_budget": total_budget,
        "total_spent": 0.0,
        
        # Discount structure
        "discount_percentage": discount_percentage,
        "discount_fixed": discount_fixed,
        "max_per_job": max_per_job,
        
        # Targeting criteria
        "criteria": criteria or {},
        
        # Performance tracking
        "jobs_subsidized": 0,
        "total_job_value": 0.0,
        "conversions": 0,
        "conversion_rate": 0.0,
        "avg_discount": 0.0,
        "roi_multiplier": 0.0,
        
        # Usage history
        "applications": []
    }
    
    return {
        "ok": True,
        "pool": pool
    }


def check_pool_eligibility(
    pool: Dict[str, Any],
    job: Dict[str, Any],
    agent: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Check if a job/agent is eligible for pool discount
    """
    # Check pool status
    if pool["status"] != "active":
        return {
            "eligible": False,
            "reason": "pool_not_active",
            "pool_status": pool["status"]
        }
    
    # Check if pool expired
    if pool["expires_at"] < _now():
        return {
            "eligible": False,
            "reason": "pool_expired",
            "expired_at": pool["expires_at"]
        }
    
    # Check if budget remaining
    if pool["remaining_budget"] <= 0:
        return {
            "eligible": False,
            "reason": "pool_depleted",
            "remaining": pool["remaining_budget"]
        }
    
    # Check outcome type match
    job_type = job.get("type") or job.get("category")
    target_outcomes = pool["target_outcomes"]
    
    if target_outcomes and job_type not in target_outcomes:
        return {
            "eligible": False,
            "reason": "outcome_type_mismatch",
            "job_type": job_type,
            "target_outcomes": target_outcomes
        }
    
    # Check criteria if specified
    criteria = pool.get("criteria", {})
    
    if criteria and agent:
        # Min agent score
        min_score = criteria.get("min_agent_score")
        if min_score:
            agent_score = int(agent.get("outcomeScore", 0))
            if agent_score < min_score:
                return {
                    "eligible": False,
                    "reason": "agent_score_too_low",
                    "required": min_score,
                    "actual": agent_score
                }
        
        # Required skills
        required_skills = criteria.get("required_skills", [])
        if required_skills:
            agent_skills = set(agent.get("profile", {}).get("skills", []))
            missing_skills = set(required_skills) - agent_skills
            
            if missing_skills:
                return {
                    "eligible": False,
                    "reason": "missing_required_skills",
                    "missing": list(missing_skills)
                }
    
    return {
        "eligible": True,
        "pool_id": pool["id"],
        "sponsor": pool["sponsor"]
    }


def calculate_discount(
    pool: Dict[str, Any],
    job_value: float
) -> Dict[str, Any]:
    """
    Calculate discount amount from pool
    """
    discount_pct = pool.get("discount_percentage")
    discount_fixed = pool.get("discount_fixed")
    max_per_job = pool.get("max_per_job")
    remaining_budget = pool["remaining_budget"]
    
    # Calculate base discount
    if discount_pct:
        discount_amount = job_value * discount_pct
    elif discount_fixed:
        discount_amount = discount_fixed
    else:
        return {"ok": False, "error": "no_discount_configured"}
    
    # Apply max per job limit
    if max_per_job:
        discount_amount = min(discount_amount, max_per_job)
    
    # Cap at remaining budget
    discount_amount = min(discount_amount, remaining_budget)
    
    # Calculate final price
    discounted_price = max(0, job_value - discount_amount)
    
    return {
        "ok": True,
        "original_price": round(job_value, 2),
        "discount_amount": round(discount_amount, 2),
        "discounted_price": round(discounted_price, 2),
        "discount_percentage": round((discount_amount / job_value * 100), 1) if job_value > 0 else 0,
        "sponsor": pool["sponsor"],
        "pool_id": pool["id"]
    }


def apply_pool_discount(
    pool: Dict[str, Any],
    job: Dict[str, Any],
    agent: Dict[str, Any],
    buyer: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply pool discount to a job
    """
    # Check eligibility
    eligibility = check_pool_eligibility(pool, job, agent)
    
    if not eligibility["eligible"]:
        return {
            "ok": False,
            **eligibility
        }
    
    job_value = float(job.get("budget", 0))
    
    # Calculate discount
    discount_calc = calculate_discount(pool, job_value)
    
    if not discount_calc["ok"]:
        return discount_calc
    
    discount_amount = discount_calc["discount_amount"]
    discounted_price = discount_calc["discounted_price"]
    
    # Update pool budget
    pool["remaining_budget"] -= discount_amount
    pool["total_spent"] += discount_amount
    pool["jobs_subsidized"] += 1
    pool["total_job_value"] += job_value
    
    # Update average discount
    pool["avg_discount"] = round(pool["total_spent"] / pool["jobs_subsidized"], 2)
    
    # Record application
    application = {
        "job_id": job.get("id"),
        "agent": agent.get("username"),
        "buyer": buyer.get("username"),
        "original_price": job_value,
        "discount_amount": discount_amount,
        "discounted_price": discounted_price,
        "applied_at": _now()
    }
    
    pool.setdefault("applications", []).append(application)
    
    # Update job with discount
    job["sponsor_discount"] = {
        "pool_id": pool["id"],
        "sponsor": pool["sponsor"],
        "discount_amount": discount_amount,
        "original_price": job_value,
        "discounted_price": discounted_price
    }
    
    # Add ledger entry for agent (credit from sponsor)
    agent.setdefault("ownership", {}).setdefault("ledger", []).append({
        "ts": _now(),
        "amount": discount_amount,
        "currency": "USD",
        "basis": "sponsor_subsidy",
        "pool_id": pool["id"],
        "sponsor": pool["sponsor"],
        "job_id": job.get("id")
    })
    
    # Check if pool should be marked as depleted
    if pool["remaining_budget"] <= 0:
        pool["status"] = "depleted"
        pool["depleted_at"] = _now()
    
    return {
        "ok": True,
        "discount_applied": True,
        "pool_id": pool["id"],
        "sponsor": pool["sponsor"],
        **discount_calc
    }


def track_conversion(
    pool: Dict[str, Any],
    job_id: str,
    converted: bool
) -> Dict[str, Any]:
    """
    Track if a subsidized job converted to completion
    """
    # Find application
    application = next(
        (a for a in pool.get("applications", []) if a.get("job_id") == job_id),
        None
    )
    
    if not application:
        return {
            "ok": False,
            "error": "job_not_found_in_pool",
            "job_id": job_id
        }
    
    # Update application
    application["converted"] = converted
    application["conversion_tracked_at"] = _now()
    
    # Update pool conversion metrics
    if converted:
        pool["conversions"] += 1
    
    # Recalculate conversion rate
    total_tracked = len([a for a in pool["applications"] if "converted" in a])
    if total_tracked > 0:
        pool["conversion_rate"] = round(pool["conversions"] / total_tracked, 2)
    
    # Calculate ROI multiplier (revenue generated / budget spent)
    # Simplified: assume converted jobs = job value earned
    if pool["total_spent"] > 0:
        revenue_generated = sum([
            a["original_price"] for a in pool["applications"]
            if a.get("converted")
        ])
        pool["roi_multiplier"] = round(revenue_generated / pool["total_spent"], 2)
    
    return {
        "ok": True,
        "job_id": job_id,
        "converted": converted,
        "pool_conversions": pool["conversions"],
        "conversion_rate": pool["conversion_rate"],
        "roi_multiplier": pool["roi_multiplier"]
    }


def generate_sponsor_report(
    pool: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate sponsor ROI report
    """
    total_budget = pool["total_budget"]
    spent = pool["total_spent"]
    remaining = pool["remaining_budget"]
    
    budget_utilization = (spent / total_budget) if total_budget > 0 else 0
    
    # Calculate impact metrics
    jobs_subsidized = pool["jobs_subsidized"]
    conversions = pool["conversions"]
    conversion_rate = pool["conversion_rate"]
    roi_multiplier = pool["roi_multiplier"]
    
    # Cost per conversion
    cost_per_conversion = (spent / conversions) if conversions > 0 else 0
    
    # Revenue impact
    total_job_value = pool["total_job_value"]
    
    # Top agents who benefited
    agent_impacts = {}
    for app in pool.get("applications", []):
        agent = app.get("agent")
        agent_impacts[agent] = agent_impacts.get(agent, 0) + 1
    
    top_agents = sorted(agent_impacts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    report = {
        "pool_id": pool["id"],
        "sponsor": pool["sponsor"],
        "pool_type": pool["pool_type"],
        "status": pool["status"],
        "created_at": pool["created_at"],
        "expires_at": pool.get("expires_at"),
        
        "budget": {
            "total": round(total_budget, 2),
            "spent": round(spent, 2),
            "remaining": round(remaining, 2),
            "utilization_percentage": round(budget_utilization * 100, 1)
        },
        
        "impact": {
            "jobs_subsidized": jobs_subsidized,
            "total_job_value": round(total_job_value, 2),
            "avg_discount_per_job": round(pool["avg_discount"], 2),
            "conversions": conversions,
            "conversion_rate": round(conversion_rate * 100, 1),
            "cost_per_conversion": round(cost_per_conversion, 2),
            "roi_multiplier": f"{roi_multiplier}x"
        },
        
        "top_agents": [
            {"agent": agent, "jobs_subsidized": count}
            for agent, count in top_agents
        ],
        
        "generated_at": _now()
    }
    
    return report


def refill_pool(
    pool: Dict[str, Any],
    additional_budget: float,
    extend_days: int = 0
) -> Dict[str, Any]:
    """
    Refill a sponsor pool with additional budget
    """
    if additional_budget <= 0:
        return {
            "ok": False,
            "error": "additional_budget_must_be_positive"
        }
    
    old_total = pool["total_budget"]
    old_remaining = pool["remaining_budget"]
    
    # Add budget
    pool["total_budget"] += additional_budget
    pool["remaining_budget"] += additional_budget
    
    # Reactivate if depleted
    if pool["status"] == "depleted":
        pool["status"] = "active"
    
    # Extend expiration if requested
    if extend_days > 0:
        from datetime import datetime
        expires = datetime.fromisoformat(pool["expires_at"].replace("Z", "+00:00"))
        new_expires = expires + timedelta(days=extend_days)
        pool["expires_at"] = new_expires.isoformat()
    
    # Record refill
    pool.setdefault("refills", []).append({
        "amount": additional_budget,
        "extend_days": extend_days,
        "refilled_at": _now()
    })
    
    return {
        "ok": True,
        "pool_id": pool["id"],
        "refilled": True,
        "previous_budget": round(old_total, 2),
        "new_budget": round(pool["total_budget"], 2),
        "previous_remaining": round(old_remaining, 2),
        "new_remaining": round(pool["remaining_budget"], 2),
        "status": pool["status"]
    }


def find_matching_pools(
    job: Dict[str, Any],
    agent: Dict[str, Any],
    all_pools: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Find all sponsor pools that match a job/agent
    """
    matching_pools = []
    
    for pool in all_pools:
        eligibility = check_pool_eligibility(pool, job, agent)
        
        if eligibility["eligible"]:
            discount_calc = calculate_discount(pool, float(job.get("budget", 0)))
            
            matching_pools.append({
                "pool_id": pool["id"],
                "sponsor": pool["sponsor"],
                "discount_amount": discount_calc["discount_amount"],
                "discount_percentage": discount_calc["discount_percentage"],
                "remaining_budget": pool["remaining_budget"]
            })
    
    # Sort by discount amount (highest first)
    matching_pools.sort(key=lambda p: p["discount_amount"], reverse=True)
    
    return {
        "ok": True,
        "matching_pools": matching_pools,
        "count": len(matching_pools),
        "best_match": matching_pools[0] if matching_pools else None
    }


def get_pool_leaderboard(
    pools: List[Dict[str, Any]],
    sort_by: str = "roi"
) -> Dict[str, Any]:
    """
    Get leaderboard of sponsor pools
    
    sort_by: roi | conversions | jobs_subsidized | budget_spent
    """
    active_pools = [p for p in pools if p.get("status") == "active"]
    
    if sort_by == "roi":
        sorted_pools = sorted(active_pools, key=lambda p: p.get("roi_multiplier", 0), reverse=True)
    elif sort_by == "conversions":
        sorted_pools = sorted(active_pools, key=lambda p: p.get("conversions", 0), reverse=True)
    elif sort_by == "jobs_subsidized":
        sorted_pools = sorted(active_pools, key=lambda p: p.get("jobs_subsidized", 0), reverse=True)
    elif sort_by == "budget_spent":
        sorted_pools = sorted(active_pools, key=lambda p: p.get("total_spent", 0), reverse=True)
    else:
        sorted_pools = active_pools
    
    leaderboard = [
        {
            "rank": idx + 1,
            "pool_id": p["id"],
            "sponsor": p["sponsor"],
            "roi_multiplier": p.get("roi_multiplier", 0),
            "conversions": p.get("conversions", 0),
            "jobs_subsidized": p.get("jobs_subsidized", 0),
            "budget_spent": round(p.get("total_spent", 0), 2)
        }
        for idx, p in enumerate(sorted_pools[:10])
    ]
    
    return {
        "ok": True,
        "leaderboard": leaderboard,
        "sort_by": sort_by
    }
