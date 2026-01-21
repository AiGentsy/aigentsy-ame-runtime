"""
AiGentsy Reputation-Indexed Pricing (ARM Integration)
Dynamic pricing based on OutcomeScore with fairness guardrails

Now integrated with Brain Overlay OCS for unified reputation-based pricing.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Integration with brain overlay OCS
try:
    from integration_hooks import IntegrationHooks
    from brain_overlay.ocs import OCSEngine
    _hooks = IntegrationHooks("reputation_pricing")
    _ocs = OCSEngine()
except ImportError:
    _hooks = None
    _ocs = None


def _now():
    return datetime.now(timezone.utc).isoformat()


# Pricing tiers based on OutcomeScore
PRICING_TIERS = {
    "novice": {
        "min_score": 0,
        "max_score": 29,
        "multiplier": 0.70,      # 70% of base price
        "description": "New agent - building reputation"
    },
    "developing": {
        "min_score": 30,
        "max_score": 49,
        "multiplier": 0.85,      # 85% of base price
        "description": "Growing track record"
    },
    "competent": {
        "min_score": 50,
        "max_score": 69,
        "multiplier": 1.0,       # 100% base price
        "description": "Reliable performer"
    },
    "proficient": {
        "min_score": 70,
        "max_score": 84,
        "multiplier": 1.15,      # 115% of base price
        "description": "Above average quality"
    },
    "expert": {
        "min_score": 85,
        "max_score": 94,
        "multiplier": 1.30,      # 130% of base price
        "description": "Top tier performer"
    },
    "elite": {
        "min_score": 95,
        "max_score": 100,
        "multiplier": 1.50,      # 150% of base price
        "description": "Best in class"
    }
}

# Fairness guardrails
MIN_PRICE_FLOOR = 10.0           # Never price below $10
MAX_PRICE_CEILING = 10000.0      # Never price above $10k
MAX_PRICE_VARIANCE = 0.30        # Max 30% variance from base for same service


def calculate_pricing_tier(outcome_score: int) -> Dict[str, Any]:
    """
    Determine pricing tier based on OutcomeScore
    """
    for tier_name, tier in PRICING_TIERS.items():
        if tier["min_score"] <= outcome_score <= tier["max_score"]:
            return {
                "tier": tier_name,
                "multiplier": tier["multiplier"],
                "description": tier["description"],
                "outcome_score": outcome_score
            }
    
    # Fallback to novice
    return {
        "tier": "novice",
        "multiplier": PRICING_TIERS["novice"]["multiplier"],
        "description": PRICING_TIERS["novice"]["description"],
        "outcome_score": outcome_score
    }


def calculate_reputation_price(
    base_price: float,
    outcome_score: int,
    apply_guardrails: bool = True
) -> Dict[str, Any]:
    """
    Calculate price adjusted for reputation
    """
    tier_info = calculate_pricing_tier(outcome_score)
    
    # Apply multiplier
    adjusted_price = base_price * tier_info["multiplier"]
    
    # Apply guardrails
    if apply_guardrails:
        # Floor
        if adjusted_price < MIN_PRICE_FLOOR:
            adjusted_price = MIN_PRICE_FLOOR
            tier_info["guardrail_applied"] = "floor"
        
        # Ceiling
        if adjusted_price > MAX_PRICE_CEILING:
            adjusted_price = MAX_PRICE_CEILING
            tier_info["guardrail_applied"] = "ceiling"
        
        # Variance check (prevent extreme deviations)
        max_allowed = base_price * (1 + MAX_PRICE_VARIANCE)
        min_allowed = base_price * (1 - MAX_PRICE_VARIANCE)
        
        if adjusted_price > max_allowed:
            adjusted_price = max_allowed
            tier_info["guardrail_applied"] = "variance_cap"
        elif adjusted_price < min_allowed:
            adjusted_price = min_allowed
            tier_info["guardrail_applied"] = "variance_floor"
    
    adjusted_price = round(adjusted_price, 2)
    
    return {
        "base_price": base_price,
        "adjusted_price": adjusted_price,
        "discount_or_premium": round(adjusted_price - base_price, 2),
        "discount_or_premium_pct": round(((adjusted_price / base_price) - 1) * 100, 1),
        **tier_info
    }


def calculate_arm_price_range(
    service_type: str,
    outcome_score: int,
    market_demand: float = 1.0
) -> Dict[str, Any]:
    """
    ARM (Adaptive Revenue Model) - Calculate dynamic price range
    """
    # Base prices by service type
    BASE_PRICES = {
        "landing_page": 200.0,
        "logo_design": 150.0,
        "copywriting": 100.0,
        "seo_audit": 300.0,
        "social_media_kit": 250.0,
        "email_sequence": 175.0,
        "product_description": 50.0,
        "custom": 200.0
    }
    
    base_price = BASE_PRICES.get(service_type, BASE_PRICES["custom"])
    
    # Apply demand multiplier (1.0 = normal, 1.5 = high demand, 0.7 = low demand)
    base_price = base_price * market_demand
    
    # Calculate reputation-adjusted price
    reputation_pricing = calculate_reputation_price(base_price, outcome_score)
    
    # Calculate price range (±10% for negotiation)
    min_price = round(reputation_pricing["adjusted_price"] * 0.90, 2)
    max_price = round(reputation_pricing["adjusted_price"] * 1.10, 2)
    
    return {
        "service_type": service_type,
        "base_price": base_price,
        "market_demand_multiplier": market_demand,
        "outcome_score": outcome_score,
        "pricing_tier": reputation_pricing["tier"],
        "reputation_multiplier": reputation_pricing["multiplier"],
        "recommended_price": reputation_pricing["adjusted_price"],
        "price_range": {
            "min": min_price,
            "max": max_price
        },
        "discount_or_premium": reputation_pricing["discount_or_premium"],
        "discount_or_premium_pct": reputation_pricing["discount_or_premium_pct"]
    }


def calculate_dynamic_bid_price(
    intent: Dict[str, Any],
    agent_outcome_score: int,
    existing_bids: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate optimal bid price considering:
    1. Agent's reputation
    2. Intent budget
    3. Existing bids (competitive positioning)
    """
    intent_budget = float(intent.get("budget", 200))
    service_type = intent.get("service_type", "custom")
    
    # Get ARM recommended price
    arm_pricing = calculate_arm_price_range(service_type, agent_outcome_score)
    
    recommended_price = arm_pricing["recommended_price"]
    
    # Competitive adjustment if there are existing bids
    if existing_bids:
        lowest_bid = min([float(b.get("price_usd", 999999)) for b in existing_bids])
        highest_bid = max([float(b.get("price_usd", 0)) for b in existing_bids])
        avg_bid = sum([float(b.get("price_usd", 0)) for b in existing_bids]) / len(existing_bids)
        
        # If recommended price is much higher than existing bids, adjust down slightly
        if recommended_price > (avg_bid * 1.2):
            competitive_price = round(avg_bid * 1.1, 2)
            
            return {
                "recommended_bid": competitive_price,
                "arm_price": recommended_price,
                "adjustment": "competitive_undercut",
                "rationale": f"Adjusted from ${recommended_price} to ${competitive_price} to remain competitive",
                "existing_bids_range": {"min": lowest_bid, "max": highest_bid, "avg": round(avg_bid, 2)}
            }
    
    # Budget check
    if recommended_price > intent_budget:
        # Agent is too expensive for this buyer
        return {
            "recommended_bid": None,
            "arm_price": recommended_price,
            "adjustment": "exceeds_budget",
            "rationale": f"Your tier (${recommended_price}) exceeds buyer budget (${intent_budget})",
            "suggestion": "Consider lower-tier intents or negotiate scope reduction"
        }
    
    # Standard recommendation
    return {
        "recommended_bid": recommended_price,
        "arm_price": recommended_price,
        "adjustment": "standard",
        "rationale": f"Based on your {arm_pricing['pricing_tier']} tier",
        "price_range": arm_pricing["price_range"]
    }


def update_outcome_score_weighted(
    current_score: int,
    new_outcome_result: str,
    weight: float = 0.1
) -> int:
    """
    Update OutcomeScore with weighted average (new outcomes weighted 10%)
    """
    # Convert outcome to score delta
    OUTCOME_SCORES = {
        "excellent": 100,
        "good": 80,
        "satisfactory": 60,
        "poor": 30,
        "failed": 0
    }
    
    outcome_value = OUTCOME_SCORES.get(new_outcome_result, 60)
    
    # Weighted update
    new_score = (current_score * (1 - weight)) + (outcome_value * weight)
    
    return round(min(100, max(0, new_score)))


def calculate_pricing_impact(
    current_score: int,
    new_score: int,
    base_price: float
) -> Dict[str, Any]:
    """
    Show how score change affects pricing
    """
    current_pricing = calculate_reputation_price(base_price, current_score)
    new_pricing = calculate_reputation_price(base_price, new_score)
    
    price_change = new_pricing["adjusted_price"] - current_pricing["adjusted_price"]
    tier_change = new_pricing["tier"] != current_pricing["tier"]
    
    return {
        "score_change": new_score - current_score,
        "current_tier": current_pricing["tier"],
        "new_tier": new_pricing["tier"],
        "tier_upgraded": tier_change and new_score > current_score,
        "tier_downgraded": tier_change and new_score < current_score,
        "current_price": current_pricing["adjusted_price"],
        "new_price": new_pricing["adjusted_price"],
        "price_change": round(price_change, 2),
        "price_change_pct": round((price_change / current_pricing["adjusted_price"]) * 100, 1) if current_pricing["adjusted_price"] > 0 else 0
    }


def get_ocs_price_recommendation(
    entity_id: str,
    base_price: float,
    service_type: str = "custom"
) -> Dict[str, Any]:
    """
    Get price recommendation using brain overlay OCS.
    This is the preferred method for unified reputation-based pricing.
    """
    # Default to standard pricing
    outcome_score = 50
    ocs_source = "default"

    # Try to get OCS from brain overlay
    if _ocs and entity_id:
        try:
            ocs_data = _ocs.get_ocs(entity_id)
            outcome_score = ocs_data.get("ocs", 50)
            ocs_source = "brain_overlay"
        except Exception:
            pass

    # Calculate price using OCS
    pricing = calculate_reputation_price(base_price, outcome_score)
    arm_range = calculate_arm_price_range(service_type, outcome_score)

    # Emit pricing event to brain
    if _hooks:
        try:
            _hooks.on_reputation_change(
                entity_id,
                delta=0,  # No change, just lookup
                reason="pricing_lookup",
                source_system="reputation_pricing"
            )
        except Exception:
            pass

    return {
        "entity_id": entity_id,
        "ocs": outcome_score,
        "ocs_source": ocs_source,
        "pricing": pricing,
        "arm_range": arm_range
    }


def sync_outcome_to_ocs(
    entity_id: str,
    outcome_result: str,
    current_score: int = 50
) -> Dict[str, Any]:
    """
    Sync an outcome result to the brain overlay OCS system.
    Call this after any job completion to update unified reputation.
    """
    # Calculate new score using weighted average
    new_score = update_outcome_score_weighted(current_score, outcome_result)

    # Calculate delta for hooks
    delta = new_score - current_score

    # Emit to OCS via hooks
    if _hooks and delta != 0:
        try:
            _hooks.on_reputation_change(
                entity_id,
                delta=delta,
                reason=f"outcome_{outcome_result}",
                source_system="reputation_pricing"
            )
        except Exception:
            pass

    return {
        "entity_id": entity_id,
        "previous_score": current_score,
        "new_score": new_score,
        "delta": delta,
        "outcome": outcome_result,
        "ocs_synced": _hooks is not None
    }
