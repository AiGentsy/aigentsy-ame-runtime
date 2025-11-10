"""
AiGentsy R³ Keep-Me-Growing Autopilot
Auto-budget allocation with ROI prediction and tiered optimization
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import random

def _now():
    return datetime.now(timezone.utc).isoformat()

def _days_ago(ts_iso: str) -> int:
    try:
        then = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - then).days
    except:
        return 9999


# Autopilot tiers
AUTOPILOT_TIERS = {
    "conservative": {
        "name": "Conservative Growth",
        "min_budget": 100,
        "risk_tolerance": 0.3,
        "diversification": 0.8,
        "rebalance_frequency_days": 30,
        "target_roi": 1.5,
        "description": "Steady, low-risk growth"
    },
    "balanced": {
        "name": "Balanced Growth",
        "min_budget": 250,
        "risk_tolerance": 0.5,
        "diversification": 0.6,
        "rebalance_frequency_days": 14,
        "target_roi": 2.0,
        "description": "Mix of safety and growth"
    },
    "aggressive": {
        "name": "Aggressive Growth",
        "min_budget": 500,
        "risk_tolerance": 0.7,
        "diversification": 0.4,
        "rebalance_frequency_days": 7,
        "target_roi": 3.0,
        "description": "High-risk, high-reward"
    },
    "experimental": {
        "name": "Experimental",
        "min_budget": 1000,
        "risk_tolerance": 0.9,
        "diversification": 0.2,
        "rebalance_frequency_days": 3,
        "target_roi": 5.0,
        "description": "Maximum optimization, highest risk"
    }
}

# Marketing channels with baseline performance
CHANNELS = {
    "google_ads": {
        "name": "Google Ads",
        "baseline_roi": 1.8,
        "variance": 0.4,
        "min_spend": 50
    },
    "facebook_ads": {
        "name": "Facebook Ads",
        "baseline_roi": 1.6,
        "variance": 0.5,
        "min_spend": 30
    },
    "linkedin_ads": {
        "name": "LinkedIn Ads",
        "baseline_roi": 2.2,
        "variance": 0.3,
        "min_spend": 100
    },
    "content_marketing": {
        "name": "Content Marketing",
        "baseline_roi": 2.5,
        "variance": 0.6,
        "min_spend": 20
    },
    "seo": {
        "name": "SEO",
        "baseline_roi": 3.0,
        "variance": 0.8,
        "min_spend": 50
    },
    "email_campaigns": {
        "name": "Email Campaigns",
        "baseline_roi": 2.0,
        "variance": 0.3,
        "min_spend": 10
    },
    "referral_program": {
        "name": "Referral Program",
        "baseline_roi": 3.5,
        "variance": 1.0,
        "min_spend": 25
    }
}


def create_autopilot_strategy(
    user: Dict[str, Any],
    tier: str = "balanced",
    monthly_budget: float = 500.0
) -> Dict[str, Any]:
    """
    Create an autopilot budget strategy for an agent
    """
    if tier not in AUTOPILOT_TIERS:
        return {
            "ok": False,
            "error": "invalid_tier",
            "valid_tiers": list(AUTOPILOT_TIERS.keys())
        }
    
    tier_config = AUTOPILOT_TIERS[tier]
    
    # Check minimum budget
    if monthly_budget < tier_config["min_budget"]:
        return {
            "ok": False,
            "error": "budget_too_low",
            "min_budget": tier_config["min_budget"],
            "provided": monthly_budget
        }
    
    strategy_id = f"ap_{user.get('username')}_{tier}"
    
    strategy = {
        "id": strategy_id,
        "user": user.get("username"),
        "tier": tier,
        "tier_config": tier_config,
        "monthly_budget": monthly_budget,
        "status": "active",
        "created_at": _now(),
        "last_rebalance": _now(),
        "next_rebalance": (datetime.now(timezone.utc) + timedelta(days=tier_config["rebalance_frequency_days"])).isoformat(),
        "performance": {
            "total_spent": 0.0,
            "total_revenue": 0.0,
            "actual_roi": 0.0,
            "target_roi": tier_config["target_roi"]
        }
    }
    
    # Initial allocation
    allocation = calculate_budget_allocation(
        monthly_budget,
        tier_config,
        historical_performance={}
    )
    
    strategy["current_allocation"] = allocation
    
    return {
        "ok": True,
        "strategy": strategy
    }


def calculate_budget_allocation(
    budget: float,
    tier_config: Dict[str, Any],
    historical_performance: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Calculate optimal budget allocation across channels
    """
    risk_tolerance = tier_config["risk_tolerance"]
    diversification = tier_config["diversification"]
    
    # Score each channel
    channel_scores = {}
    
    for channel_id, channel in CHANNELS.items():
        # Base score from baseline ROI
        base_score = channel["baseline_roi"]
        
        # Adjust for historical performance
        if historical_performance and channel_id in historical_performance:
            actual_roi = historical_performance[channel_id].get("roi", base_score)
            # Weighted average: 70% historical, 30% baseline
            score = (actual_roi * 0.7) + (base_score * 0.3)
        else:
            score = base_score
        
        # Adjust for risk tolerance
        variance = channel["variance"]
        risk_penalty = variance * (1 - risk_tolerance)
        score = score - risk_penalty
        
        channel_scores[channel_id] = max(0, score)
    
    # Sort channels by score
    sorted_channels = sorted(channel_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Calculate allocation based on diversification
    allocation = {}
    remaining_budget = budget
    
    if diversification >= 0.8:
        # High diversification - spread evenly
        num_channels = min(len(CHANNELS), 5)
        per_channel = budget / num_channels
        
        for channel_id, _ in sorted_channels[:num_channels]:
            min_spend = CHANNELS[channel_id]["min_spend"]
            allocated = max(min_spend, per_channel)
            
            if allocated <= remaining_budget:
                allocation[channel_id] = round(allocated, 2)
                remaining_budget -= allocated
    
    elif diversification >= 0.5:
        # Moderate diversification - weighted by score
        total_score = sum(channel_scores.values())
        
        for channel_id, score in sorted_channels:
            if total_score > 0:
                proportion = score / total_score
                allocated = budget * proportion
                min_spend = CHANNELS[channel_id]["min_spend"]
                
                if allocated >= min_spend and allocated <= remaining_budget:
                    allocation[channel_id] = round(allocated, 2)
                    remaining_budget -= allocated
    
    else:
        # Low diversification - focus on top performers
        num_top = max(2, int(len(CHANNELS) * 0.3))
        
        for channel_id, _ in sorted_channels[:num_top]:
            proportion = 1.0 / num_top
            allocated = budget * proportion
            
            if allocated <= remaining_budget:
                allocation[channel_id] = round(allocated, 2)
                remaining_budget -= allocated
    
    # Allocate any remaining budget to top channel
    if remaining_budget > 10 and allocation:
        top_channel = sorted_channels[0][0]
        allocation[top_channel] = round(allocation.get(top_channel, 0) + remaining_budget, 2)
    
    return {
        "channels": allocation,
        "total_allocated": round(sum(allocation.values()), 2),
        "unallocated": round(remaining_budget, 2),
        "diversification_score": len(allocation) / len(CHANNELS)
    }


def predict_roi(
    channel_id: str,
    spend_amount: float,
    historical_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Predict ROI for a channel given spend amount
    """
    if channel_id not in CHANNELS:
        return {"ok": False, "error": "invalid_channel"}
    
    channel = CHANNELS[channel_id]
    
    # Get baseline or historical ROI
    if historical_data and channel_id in historical_data:
        base_roi = historical_data[channel_id].get("roi", channel["baseline_roi"])
    else:
        base_roi = channel["baseline_roi"]
    
    # Apply diminishing returns for large spends
    if spend_amount > 1000:
        diminishing_factor = 1 - ((spend_amount - 1000) / 10000)
        diminishing_factor = max(0.5, diminishing_factor)
        predicted_roi = base_roi * diminishing_factor
    else:
        predicted_roi = base_roi
    
    # Add variance (simulation of uncertainty)
    variance = channel["variance"]
    min_roi = predicted_roi * (1 - variance)
    max_roi = predicted_roi * (1 + variance)
    
    predicted_revenue = spend_amount * predicted_roi
    
    return {
        "ok": True,
        "channel": channel_id,
        "spend": spend_amount,
        "predicted_roi": round(predicted_roi, 2),
        "predicted_revenue": round(predicted_revenue, 2),
        "confidence_range": {
            "min_roi": round(min_roi, 2),
            "max_roi": round(max_roi, 2),
            "min_revenue": round(spend_amount * min_roi, 2),
            "max_revenue": round(spend_amount * max_roi, 2)
        }
    }


def execute_autopilot_spend(
    strategy: Dict[str, Any],
    user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute the current budget allocation
    """
    allocation = strategy["current_allocation"]["channels"]
    
    results = []
    total_spent = 0.0
    total_predicted_revenue = 0.0
    
    for channel_id, amount in allocation.items():
        # Check if user has budget
        current_aigx = float(user.get("ownership", {}).get("aigx", 0))
        
        if current_aigx < amount:
            results.append({
                "channel": channel_id,
                "status": "insufficient_funds",
                "required": amount,
                "available": current_aigx
            })
            continue
        
        # Deduct from user balance
        user["ownership"]["aigx"] = current_aigx - amount
        
        # Add ledger entry
        user["ownership"].setdefault("ledger", []).append({
            "ts": _now(),
            "amount": -amount,
            "currency": "AIGx",
            "basis": "r3_autopilot_spend",
            "channel": channel_id,
            "strategy_id": strategy["id"]
        })
        
        # Predict ROI
        prediction = predict_roi(channel_id, amount)
        
        results.append({
            "channel": channel_id,
            "status": "executed",
            "spent": amount,
            "predicted_roi": prediction["predicted_roi"],
            "predicted_revenue": prediction["predicted_revenue"]
        })
        
        total_spent += amount
        total_predicted_revenue += prediction["predicted_revenue"]
    
    # Update strategy performance
    strategy["performance"]["total_spent"] += total_spent
    
    return {
        "ok": True,
        "strategy_id": strategy["id"],
        "total_spent": round(total_spent, 2),
        "total_predicted_revenue": round(total_predicted_revenue, 2),
        "predicted_roi": round(total_predicted_revenue / total_spent, 2) if total_spent > 0 else 0,
        "results": results,
        "executed_at": _now()
    }


def rebalance_autopilot(
    strategy: Dict[str, Any],
    actual_performance: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Rebalance budget allocation based on actual performance
    """
    tier_config = strategy["tier_config"]
    monthly_budget = strategy["monthly_budget"]
    
    # Calculate new allocation with updated historical data
    new_allocation = calculate_budget_allocation(
        monthly_budget,
        tier_config,
        actual_performance
    )
    
    # Update strategy
    old_allocation = strategy["current_allocation"]
    strategy["current_allocation"] = new_allocation
    strategy["last_rebalance"] = _now()
    strategy["next_rebalance"] = (
        datetime.now(timezone.utc) + 
        timedelta(days=tier_config["rebalance_frequency_days"])
    ).isoformat()
    
    # Calculate changes
    changes = {}
    for channel in set(list(old_allocation["channels"].keys()) + list(new_allocation["channels"].keys())):
        old_amt = old_allocation["channels"].get(channel, 0)
        new_amt = new_allocation["channels"].get(channel, 0)
        change = new_amt - old_amt
        
        if abs(change) > 0.01:
            changes[channel] = {
                "old": old_amt,
                "new": new_amt,
                "change": round(change, 2),
                "change_pct": round((change / old_amt * 100), 1) if old_amt > 0 else 0
            }
    
    return {
        "ok": True,
        "strategy_id": strategy["id"],
        "rebalanced_at": _now(),
        "changes": changes,
        "new_allocation": new_allocation
    }


def get_autopilot_recommendations(
    user: Dict[str, Any],
    current_strategy: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Recommend autopilot tier and budget based on user's financials
    """
    # Get user's financial capacity
    aigx_balance = float(user.get("ownership", {}).get("aigx", 0))
    outcome_score = int(user.get("outcomeScore", 0))
    
    # Calculate suggested budget (10-20% of balance)
    suggested_budget = round(aigx_balance * 0.15, 2)
    
    # Recommend tier based on outcome score and balance
    if outcome_score >= 85 and aigx_balance >= 1000:
        recommended_tier = "experimental"
    elif outcome_score >= 70 and aigx_balance >= 500:
        recommended_tier = "aggressive"
    elif outcome_score >= 50 and aigx_balance >= 250:
        recommended_tier = "balanced"
    else:
        recommended_tier = "conservative"
    
    tier_config = AUTOPILOT_TIERS[recommended_tier]
    
    return {
        "ok": True,
        "recommended_tier": recommended_tier,
        "tier_description": tier_config["description"],
        "suggested_monthly_budget": max(suggested_budget, tier_config["min_budget"]),
        "min_budget": tier_config["min_budget"],
        "user_balance": aigx_balance,
        "outcome_score": outcome_score,
        "rationale": f"Based on your OutcomeScore ({outcome_score}) and balance (${aigx_balance})"
    }
