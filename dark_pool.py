"""
AiGentsy Dark-Pool Performance Auctions
Anonymous bidding with reputation-based matching
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import hashlib
import random

def _now():
    return datetime.now(timezone.utc).isoformat()

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).days
    except:
        return 9999


# Reputation tiers for matching
REPUTATION_TIERS = {
    "bronze": {
        "min_score": 0,
        "max_score": 49,
        "badge": "🥉",
        "multiplier": 0.8
    },
    "silver": {
        "min_score": 50,
        "max_score": 69,
        "badge": "🥈",
        "multiplier": 1.0
    },
    "gold": {
        "min_score": 70,
        "max_score": 84,
        "badge": "🥇",
        "multiplier": 1.2
    },
    "platinum": {
        "min_score": 85,
        "max_score": 94,
        "badge": "💎",
        "multiplier": 1.4
    },
    "diamond": {
        "min_score": 95,
        "max_score": 100,
        "badge": "💠",
        "multiplier": 1.6
    }
}


def anonymize_agent(agent_username: str, auction_id: str) -> str:
    """
    Create anonymous ID for agent in auction
    """
    # Create deterministic but anonymous hash
    hash_input = f"{agent_username}_{auction_id}_salt"
    agent_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    
    return f"agent_{agent_hash}"


def get_reputation_tier(outcome_score: int) -> Dict[str, Any]:
    """
    Get reputation tier for outcome score
    """
    for tier_name, tier in REPUTATION_TIERS.items():
        if tier["min_score"] <= outcome_score <= tier["max_score"]:
            return {
                "tier": tier_name,
                "badge": tier["badge"],
                "multiplier": tier["multiplier"],
                "score": outcome_score
            }
    
    return {
        "tier": "bronze",
        "badge": "🥉",
        "multiplier": 0.8,
        "score": outcome_score
    }


def create_dark_pool_auction(
    intent: Dict[str, Any],
    min_reputation_tier: str = "silver",
    auction_duration_hours: int = 24,
    reveal_reputation: bool = True
) -> Dict[str, Any]:
    """
    Create a dark pool auction for an intent
    
    Dark pool features:
    - Agent identities hidden
    - Only reputation tier and performance metrics visible
    - Bids are sealed until auction ends
    """
    from uuid import uuid4
    
    auction_id = f"dark_{uuid4().hex[:12]}"
    
    auction = {
        "id": auction_id,
        "intent_id": intent.get("id"),
        "intent_summary": {
            "brief": intent.get("brief", ""),
            "budget": intent.get("budget", 0),
            "delivery_days": intent.get("delivery_days", 7)
        },
        "type": "dark_pool",
        "status": "open",
        "min_reputation_tier": min_reputation_tier,
        "reveal_reputation": reveal_reputation,
        "created_at": _now(),
        "closes_at": (datetime.now(timezone.utc) + timedelta(hours=auction_duration_hours)).isoformat(),
        "bids": [],
        "winner": None,
        "matching_algorithm": "reputation_weighted_price"
    }
    
    return auction


def submit_dark_pool_bid(
    auction: Dict[str, Any],
    agent_user: Dict[str, Any],
    bid_amount: float,
    delivery_hours: int,
    proposal_summary: str = ""
) -> Dict[str, Any]:
    """
    Submit anonymous bid to dark pool auction
    """
    # Check if auction is open
    if auction["status"] != "open":
        return {
            "ok": False,
            "error": "auction_closed",
            "status": auction["status"]
        }
    
    # Check if auction has expired
    if auction["closes_at"] < _now():
        return {
            "ok": False,
            "error": "auction_expired",
            "closes_at": auction["closes_at"]
        }
    
    # Get agent reputation
    outcome_score = int(agent_user.get("outcomeScore", 0))
    reputation = get_reputation_tier(outcome_score)
    
    # Check minimum reputation requirement
    min_tier = auction.get("min_reputation_tier", "silver")
    tier_order = list(REPUTATION_TIERS.keys())
    
    if tier_order.index(reputation["tier"]) < tier_order.index(min_tier):
        return {
            "ok": False,
            "error": "reputation_too_low",
            "agent_tier": reputation["tier"],
            "required_tier": min_tier
        }
    
    # Create anonymous bid
    agent_username = agent_user.get("consent", {}).get("username") or agent_user.get("username")
    anonymous_id = anonymize_agent(agent_username, auction["id"])
    
    # Calculate performance metrics (anonymous but verifiable)
    ledger = agent_user.get("ownership", {}).get("ledger", [])
    
    completed_jobs = len([e for e in ledger if e.get("basis") == "revenue"])
    on_time_deliveries = len([e for e in ledger if e.get("basis") == "sla_bonus"])
    disputes = len([e for e in ledger if e.get("basis") == "bond_slash"])
    
    on_time_rate = (on_time_deliveries / completed_jobs) if completed_jobs > 0 else 0
    dispute_rate = (disputes / completed_jobs) if completed_jobs > 0 else 0
    
    bid = {
        "id": f"bid_{anonymous_id}",
        "anonymous_id": anonymous_id,
        "real_agent": agent_username,  # Hidden from buyer until award
        "bid_amount": bid_amount,
        "delivery_hours": delivery_hours,
        "proposal_summary": proposal_summary,
        "reputation": {
            "tier": reputation["tier"],
            "badge": reputation["badge"],
            "score": outcome_score if auction.get("reveal_reputation") else None
        },
        "performance_metrics": {
            "completed_jobs": completed_jobs,
            "on_time_rate": round(on_time_rate, 2),
            "dispute_rate": round(dispute_rate, 3),
            "avg_rating": 4.5  # Could calculate from feedback
        },
        "submitted_at": _now(),
        "is_sealed": True
    }
    
    auction["bids"].append(bid)
    
    return {
        "ok": True,
        "bid_id": bid["id"],
        "anonymous_id": anonymous_id,
        "message": "Bid submitted to dark pool. Identity will remain anonymous until award."
    }


def calculate_bid_score(
    bid: Dict[str, Any],
    weights: Dict[str, float] = None
) -> float:
    """
    Calculate composite score for bid ranking
    
    Default weights: 40% price, 30% reputation, 20% on-time rate, 10% experience
    """
    if not weights:
        weights = {
            "price": 0.40,
            "reputation": 0.30,
            "on_time": 0.20,
            "experience": 0.10
        }
    
    # Price score (lower is better, normalize to 0-1)
    # Assume max price is 2x the bid amount
    price_score = 1 - (bid["bid_amount"] / (bid["bid_amount"] * 2))
    
    # Reputation score (based on tier multiplier)
    reputation_multiplier = REPUTATION_TIERS[bid["reputation"]["tier"]]["multiplier"]
    reputation_score = reputation_multiplier / 1.6  # Normalize (diamond = 1.6)
    
    # On-time score
    on_time_score = bid["performance_metrics"]["on_time_rate"]
    
    # Experience score (normalize completed jobs, max 100)
    experience_score = min(bid["performance_metrics"]["completed_jobs"] / 100, 1.0)
    
    # Calculate weighted score
    total_score = (
        (price_score * weights["price"]) +
        (reputation_score * weights["reputation"]) +
        (on_time_score * weights["on_time"]) +
        (experience_score * weights["experience"])
    )
    
    return round(total_score, 4)


def close_dark_pool_auction(
    auction: Dict[str, Any],
    matching_algorithm: str = "reputation_weighted_price"
) -> Dict[str, Any]:
    """
    Close auction and determine winner
    
    matching_algorithm options:
    - reputation_weighted_price: Balance of quality and price
    - lowest_price: Cheapest qualified bid
    - highest_reputation: Best reputation regardless of price
    - best_value: Optimize for value score
    """
    if auction["status"] != "open":
        return {
            "ok": False,
            "error": "auction_not_open",
            "status": auction["status"]
        }
    
    bids = auction.get("bids", [])
    
    if not bids:
        auction["status"] = "expired"
        return {
            "ok": False,
            "error": "no_bids_received",
            "auction_id": auction["id"]
        }
    
    # Unseal all bids
    for bid in bids:
        bid["is_sealed"] = False
    
    # Select winner based on algorithm
    if matching_algorithm == "lowest_price":
        winner = min(bids, key=lambda b: b["bid_amount"])
    
    elif matching_algorithm == "highest_reputation":
        winner = max(bids, key=lambda b: b["reputation"]["score"] or 0)
    
    elif matching_algorithm == "best_value":
        # Calculate value score for each bid
        for bid in bids:
            bid["value_score"] = calculate_bid_score(bid)
        
        winner = max(bids, key=lambda b: b.get("value_score", 0))
    
    else:  # reputation_weighted_price (default)
        # Calculate composite score
        for bid in bids:
            bid["composite_score"] = calculate_bid_score(bid)
        
        winner = max(bids, key=lambda b: b.get("composite_score", 0))
    
    # Update auction
    auction["status"] = "closed"
    auction["closed_at"] = _now()
    auction["winner"] = {
        "bid_id": winner["id"],
        "anonymous_id": winner["anonymous_id"],
        "real_agent": winner["real_agent"],  # Revealed to buyer only
        "bid_amount": winner["bid_amount"],
        "delivery_hours": winner["delivery_hours"],
        "reputation": winner["reputation"]
    }
    
    # Rank all bids
    all_bids_ranked = sorted(bids, key=lambda b: b.get("composite_score", 0), reverse=True)
    
    auction["all_bids_ranked"] = [
        {
            "rank": idx + 1,
            "anonymous_id": b["anonymous_id"],
            "bid_amount": b["bid_amount"],
            "reputation_tier": b["reputation"]["tier"],
            "score": b.get("composite_score", 0)
        }
        for idx, b in enumerate(all_bids_ranked)
    ]
    
    return {
        "ok": True,
        "auction_id": auction["id"],
        "winner": auction["winner"],
        "total_bids": len(bids),
        "closed_at": auction["closed_at"]
    }


def reveal_agent_identity(
    auction: Dict[str, Any],
    anonymous_id: str,
    requester: str
) -> Dict[str, Any]:
    """
    Reveal agent identity (only allowed for buyer or after auction close)
    """
    if auction["status"] == "open":
        return {
            "ok": False,
            "error": "auction_still_open",
            "message": "Identities remain anonymous until auction closes"
        }
    
    # Find bid
    bid = next((b for b in auction["bids"] if b["anonymous_id"] == anonymous_id), None)
    
    if not bid:
        return {
            "ok": False,
            "error": "bid_not_found",
            "anonymous_id": anonymous_id
        }
    
    # Check if requester is authorized (buyer or winner)
    winner_id = auction.get("winner", {}).get("anonymous_id")
    
    if anonymous_id == winner_id:
        # Winner identity can be revealed
        return {
            "ok": True,
            "anonymous_id": anonymous_id,
            "real_agent": bid["real_agent"],
            "bid_amount": bid["bid_amount"],
            "reputation": bid["reputation"]
        }
    else:
        # Non-winners remain anonymous
        return {
            "ok": False,
            "error": "identity_protected",
            "message": "Non-winning agents remain anonymous"
        }


def calculate_dark_pool_metrics(
    auctions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate dark pool performance metrics
    """
    total_auctions = len(auctions)
    completed = len([a for a in auctions if a.get("status") == "closed"])
    expired = len([a for a in auctions if a.get("status") == "expired"])
    
    total_bids = sum([len(a.get("bids", [])) for a in auctions])
    avg_bids_per_auction = round(total_bids / total_auctions, 1) if total_auctions > 0 else 0
    
    # Reputation distribution of winners
    reputation_dist = {}
    for auction in auctions:
        winner = auction.get("winner")
        if winner:
            tier = winner.get("reputation", {}).get("tier")
            if tier:
                reputation_dist[tier] = reputation_dist.get(tier, 0) + 1
    
    # Average winning bid
    winning_bids = [a["winner"]["bid_amount"] for a in auctions if a.get("winner")]
    avg_winning_bid = round(sum(winning_bids) / len(winning_bids), 2) if winning_bids else 0
    
    return {
        "total_auctions": total_auctions,
        "completed": completed,
        "expired": expired,
        "total_bids": total_bids,
        "avg_bids_per_auction": avg_bids_per_auction,
        "reputation_distribution": reputation_dist,
        "avg_winning_bid": avg_winning_bid,
        "completion_rate": round(completed / total_auctions, 2) if total_auctions > 0 else 0
    }


def get_agent_dark_pool_history(
    agent_username: str,
    auctions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Get agent's dark pool bidding history
    """
    agent_bids = []
    wins = 0
    total_bid = 0
    
    for auction in auctions:
        for bid in auction.get("bids", []):
            if bid.get("real_agent") == agent_username:
                is_winner = (auction.get("winner", {}).get("real_agent") == agent_username)
                
                agent_bids.append({
                    "auction_id": auction["id"],
                    "bid_amount": bid["bid_amount"],
                    "anonymous_id": bid["anonymous_id"],
                    "status": auction["status"],
                    "is_winner": is_winner,
                    "submitted_at": bid["submitted_at"]
                })
                
                total_bid += 1
                if is_winner:
                    wins += 1
    
    win_rate = round(wins / total_bid, 2) if total_bid > 0 else 0
    
    return {
        "agent": agent_username,
        "total_bids": total_bid,
        "wins": wins,
        "win_rate": win_rate,
        "bids": agent_bids
    }


# ============================================================
# UoO-BASED DARK POOL ACCESS CONTROL
# ============================================================

# Access tiers based on UoO score
DARK_POOL_ACCESS_TIERS = {
    "bronze": {
        "min_uoo": 0,
        "max_uoo": 49,
        "access_level": "none",
        "description": "No dark pool access",
        "min_deal_value": None,
        "max_deal_value": None
    },
    "silver": {
        "min_uoo": 50,
        "max_uoo": 99,
        "access_level": "basic",
        "description": "Access to standard dark pool deals",
        "min_deal_value": 1000,
        "max_deal_value": 5000
    },
    "gold": {
        "min_uoo": 100,
        "max_uoo": 199,
        "access_level": "premium",
        "description": "Access to premium dark pool deals",
        "min_deal_value": 5000,
        "max_deal_value": 20000
    },
    "platinum": {
        "min_uoo": 200,
        "max_uoo": 499,
        "access_level": "elite",
        "description": "Access to elite dark pool deals",
        "min_deal_value": 20000,
        "max_deal_value": 100000
    },
    "diamond": {
        "min_uoo": 500,
        "max_uoo": 999999,
        "access_level": "unlimited",
        "description": "Unlimited dark pool access",
        "min_deal_value": 0,
        "max_deal_value": None
    }
}


def check_dark_pool_access(username: str) -> Dict[str, Any]:
    """
    Check user's dark pool access level based on UoO score.
    
    Access tiers:
    - Bronze (0-49 UoO): No access
    - Silver (50-99 UoO): Standard deals ($1k-$5k)
    - Gold (100-199 UoO): Premium deals ($5k-$20k)
    - Platinum (200-499 UoO): Elite deals ($20k-$100k)
    - Diamond (500+ UoO): Unlimited access
    """
    from analytics_engine import get_uol_summary
    
    uol = get_uol_summary(username)
    if not uol.get("ok"):
        return {"ok": False, "error": "user_not_found"}
    
    total_uoo = uol.get("total_uoo", 0)
    
    # Determine access tier
    current_tier = None
    for tier_name, tier_config in DARK_POOL_ACCESS_TIERS.items():
        if tier_config["min_uoo"] <= total_uoo <= tier_config["max_uoo"]:
            current_tier = tier_name
            break
    
    if not current_tier:
        current_tier = "bronze"
    
    tier_config = DARK_POOL_ACCESS_TIERS[current_tier]
    
    # Calculate progress to next tier
    tier_order = ["bronze", "silver", "gold", "platinum", "diamond"]
    current_idx = tier_order.index(current_tier)
    
    next_tier = None
    uoo_needed = None
    if current_idx < len(tier_order) - 1:
        next_tier = tier_order[current_idx + 1]
        next_tier_config = DARK_POOL_ACCESS_TIERS[next_tier]
        uoo_needed = next_tier_config["min_uoo"] - total_uoo
    
    return {
        "ok": True,
        "username": username,
        "total_uoo": total_uoo,
        "current_tier": current_tier,
        "access_level": tier_config["access_level"],
        "description": tier_config["description"],
        "can_access_dark_pool": tier_config["access_level"] != "none",
        "deal_value_range": {
            "min": tier_config["min_deal_value"],
            "max": tier_config["max_deal_value"]
        },
        "next_tier": next_tier,
        "uoo_needed_for_next_tier": uoo_needed,
        "progress_to_next": {
            "current": total_uoo,
            "required": DARK_POOL_ACCESS_TIERS[next_tier]["min_uoo"] if next_tier else None,
            "percentage": round((total_uoo / DARK_POOL_ACCESS_TIERS[next_tier]["min_uoo"] * 100), 1) if next_tier else 100
        } if next_tier else None
    }


def qualify_for_dark_pool_intent(
    username: str,
    intent_value: float
) -> Dict[str, Any]:
    """
    Check if user qualifies to bid on specific dark pool intent.
    
    Args:
        username: Agent username
        intent_value: Deal value of the intent
    """
    access_check = check_dark_pool_access(username)
    
    if not access_check.get("ok"):
        return access_check
    
    if not access_check["can_access_dark_pool"]:
        return {
            "ok": False,
            "qualified": False,
            "reason": "no_dark_pool_access",
            "current_tier": access_check["current_tier"],
            "uoo_needed": access_check.get("uoo_needed_for_next_tier"),
            "message": f"Need {access_check.get('uoo_needed_for_next_tier')} more UoO to unlock dark pool access"
        }
    
    # Check if intent value is within user's range
    deal_range = access_check["deal_value_range"]
    
    if deal_range["min"] is not None and intent_value < deal_range["min"]:
        return {
            "ok": False,
            "qualified": False,
            "reason": "deal_value_too_low",
            "intent_value": intent_value,
            "your_min": deal_range["min"],
            "message": f"Your tier only allows deals ≥${deal_range['min']}"
        }
    
    if deal_range["max"] is not None and intent_value > deal_range["max"]:
        return {
            "ok": False,
            "qualified": False,
            "reason": "deal_value_too_high",
            "intent_value": intent_value,
            "your_max": deal_range["max"],
            "message": f"Upgrade to {access_check.get('next_tier', 'platinum')} tier for deals >${deal_range['max']}"
        }
    
    return {
        "ok": True,
        "qualified": True,
        "access_level": access_check["access_level"],
        "current_tier": access_check["current_tier"],
        "intent_value": intent_value,
        "message": f"Qualified for ${intent_value} dark pool deal"
    }


def create_premium_dark_pool_auction(
    intent: Dict[str, Any],
    min_uoo_required: float = 200,
    min_reputation_tier: str = "gold",
    auction_duration_hours: int = 48
) -> Dict[str, Any]:
    """
    Create premium dark pool auction with UoO requirements.
    
    Args:
        intent: Intent to auction
        min_uoo_required: Minimum UoO score to participate
        min_reputation_tier: Minimum reputation tier
        auction_duration_hours: Auction duration
    """
    from uuid import uuid4
    
    auction_id = f"darkpremium_{uuid4().hex[:12]}"
    intent_value = intent.get("budget", 0)
    
    # Determine access tier based on value
    access_tier = "gold"
    for tier_name, tier_config in DARK_POOL_ACCESS_TIERS.items():
        min_val = tier_config["min_deal_value"]
        max_val = tier_config["max_deal_value"]
        
        if min_val is None:
            continue
        
        if max_val is None:
            if intent_value >= min_val:
                access_tier = tier_name
                break
        else:
            if min_val <= intent_value <= max_val:
                access_tier = tier_name
                break
    
    auction = {
        "id": auction_id,
        "intent_id": intent.get("id"),
        "intent_summary": {
            "brief": intent.get("brief", ""),
            "budget": intent_value,
            "delivery_days": intent.get("delivery_days", 7)
        },
        "type": "premium_dark_pool",
        "status": "open",
        "access_requirements": {
            "min_uoo_required": min_uoo_required,
            "min_reputation_tier": min_reputation_tier,
            "access_tier": access_tier
        },
        "created_at": _now(),
        "closes_at": (datetime.now(timezone.utc) + timedelta(hours=auction_duration_hours)).isoformat(),
        "bids": [],
        "qualified_agents": 0,
        "rejected_agents": [],
        "winner": None,
        "matching_algorithm": "reputation_weighted_price"
    }
    
    return auction


def submit_premium_dark_pool_bid(
    auction: Dict[str, Any],
    agent_user: Dict[str, Any],
    bid_amount: float,
    delivery_hours: int,
    proposal_summary: str = ""
) -> Dict[str, Any]:
    """
    Submit bid to premium dark pool with qualification checks.
    """
    agent_username = agent_user.get("consent", {}).get("username") or agent_user.get("username")
    
    # Check basic auction status
    if auction["status"] != "open":
        return {"ok": False, "error": "auction_closed"}
    
    if auction["closes_at"] < _now():
        return {"ok": False, "error": "auction_expired"}
    
    # Check UoO qualification
    intent_value = auction["intent_summary"]["budget"]
    qualification = qualify_for_dark_pool_intent(agent_username, intent_value)
    
    if not qualification.get("qualified"):
        auction["rejected_agents"].append({
            "agent": agent_username,
            "reason": qualification.get("reason"),
            "rejected_at": _now()
        })
        return {
            "ok": False,
            "error": "not_qualified",
            "qualification": qualification
        }
    
    # Check reputation requirement
    outcome_score = int(agent_user.get("outcomeScore", 0))
    reputation = get_reputation_tier(outcome_score)
    
    min_tier = auction["access_requirements"]["min_reputation_tier"]
    tier_order = list(REPUTATION_TIERS.keys())
    
    if tier_order.index(reputation["tier"]) < tier_order.index(min_tier):
        auction["rejected_agents"].append({
            "agent": agent_username,
            "reason": "reputation_too_low",
            "rejected_at": _now()
        })
        return {
            "ok": False,
            "error": "reputation_too_low",
            "agent_tier": reputation["tier"],
            "required_tier": min_tier
        }
    
    # Submit bid (use regular dark pool bid logic)
    bid_result = submit_dark_pool_bid(auction, agent_user, bid_amount, delivery_hours, proposal_summary)
    
    if bid_result.get("ok"):
        auction["qualified_agents"] += 1
        bid_result["qualification"] = qualification
    
    return bid_result


def get_dark_pool_leaderboard(
    auctions: List[Dict[str, Any]],
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get dark pool leaderboard of top performers.
    """
    agent_stats = {}
    
    for auction in auctions:
        if auction.get("status") != "closed":
            continue
        
        winner = auction.get("winner")
        if not winner:
            continue
        
        agent = winner.get("real_agent")
        if not agent:
            continue
        
        if agent not in agent_stats:
            agent_stats[agent] = {
                "agent": agent,
                "wins": 0,
                "total_value": 0,
                "avg_bid": 0,
                "reputation_tier": winner.get("reputation", {}).get("tier")
            }
        
        agent_stats[agent]["wins"] += 1
        agent_stats[agent]["total_value"] += winner.get("bid_amount", 0)
    
    # Calculate averages
    for agent, stats in agent_stats.items():
        stats["avg_bid"] = round(stats["total_value"] / stats["wins"], 2) if stats["wins"] > 0 else 0
    
    # Sort by total value won
    leaderboard = sorted(agent_stats.values(), key=lambda x: x["total_value"], reverse=True)[:limit]
    
    return {
        "ok": True,
        "leaderboard": leaderboard,
        "total_agents": len(agent_stats)
    }


def unlock_dark_pool_milestone(username: str) -> Dict[str, Any]:
    """
    Check if user has unlocked dark pool access and award badge.
    """
    access_check = check_dark_pool_access(username)
    
    if not access_check.get("ok"):
        return access_check
    
    if access_check["can_access_dark_pool"]:
        return {
            "ok": True,
            "milestone": "dark_pool_unlocked",
            "tier": access_check["current_tier"],
            "message": f"🎉 Dark Pool Unlocked! You now have {access_check['access_level']} access.",
            "badge_earned": "🔐 Dark Pool Access"
        }
    
    return {
        "ok": False,
        "milestone": "not_reached",
        "uoo_needed": access_check.get("uoo_needed_for_next_tier"),
        "message": f"Earn {access_check.get('uoo_needed_for_next_tier')} more UoO to unlock dark pool access"
    }
