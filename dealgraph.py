"""
AiGentsy DealGraph - Unified State Machine
Contract + Escrow + Bonds + Insurance + JV/IP Splits in one atomic system
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4
from enum import Enum

def _now():
    return datetime.now(timezone.utc).isoformat()


class DealState(str, Enum):
    """DealGraph states"""
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    ESCROW_HELD = "ESCROW_HELD"
    BONDS_STAKED = "BONDS_STAKED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    DISPUTED = "DISPUTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    BREACHED = "BREACHED"


# Platform fee structure
PLATFORM_FEE_PERCENT = 0.028  # 2.8% platform cut
PLATFORM_FEE_FIXED = 0.28     # $0.28 per transaction
INSURANCE_POOL_CUT = 0.0   


def create_deal(
    intent: Dict[str, Any],
    agent_username: str,
    slo_tier: str = "standard",
    ip_assets: List[str] = None,
    jv_partners: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a DealGraph entry - the unified contract
    
    Parameters:
    - intent: The buyer's intent
    - agent_username: Lead agent (or sole agent)
    - slo_tier: SLO contract tier
    - ip_assets: List of asset_ids being used
    - jv_partners: List of JV partners with splits: [{"username": "agent2", "split": 0.3}]
    """
    deal_id = f"deal_{uuid4().hex[:12]}"
    
    job_value = float(intent.get("budget", 0))
    buyer_username = intent.get("buyer")
    
    if job_value <= 0:
        return {"ok": False, "error": "invalid_job_value"}
    
    # Calculate revenue distribution
    revenue_split = calculate_revenue_split(
        job_value,
        agent_username,
        jv_partners or [],
        ip_assets or []
    )
    
    if not revenue_split["ok"]:
        return revenue_split
    
    # Create deal
    deal = {
        "id": deal_id,
        "intent_id": intent.get("id"),
        "state": DealState.PROPOSED,
        "buyer": buyer_username,
        "lead_agent": agent_username,
        "slo_tier": slo_tier,
        "created_at": _now(),
        "updated_at": _now(),
        
        # Financial structure
        "job_value": job_value,
        "revenue_split": revenue_split["distribution"],
        "revenue_split_summary": revenue_split["summary"],
        
        # Participants
        "jv_partners": jv_partners or [],
        "ip_assets": ip_assets or [],
        
        # Escrow tracking
        "escrow": {
            "status": "not_held",
            "amount": 0.0,
            "payment_intent_id": None,
            "authorized_at": None,
            "captured_at": None
        },
        
        # Bond tracking
        "bonds": {
            "required": 0.0,
            "staked": 0.0,
            "status": "not_staked",
            "stakes": []
        },
        
        # State history
        "state_history": [
            {"state": DealState.PROPOSED, "at": _now(), "by": agent_username}
        ],
        
        # Delivery tracking
        "delivery": {
            "deadline": None,
            "delivered_at": None,
            "on_time": None
        },
        
        # Settlement tracking
        "settlement": {
            "settled": False,
            "settled_at": None,
            "distributions": []
        }
    }
    
    return {
        "ok": True,
        "deal": deal
    }


def calculate_revenue_split(
    job_value: float,
    lead_agent: str,
    jv_partners: List[Dict[str, Any]],
    ip_asset_ids: List[str],
    ip_assets_data: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate complete revenue distribution including:
    - Platform fee
    - Insurance pool
    - JV partner splits
    - IP royalties
    - Lead agent remainder
    """
    distribution = []
    
    # 1. Platform fee (2.8% + $0.28)
    platform_amount = (job_value * PLATFORM_FEE_PERCENT) + PLATFORM_FEE_FIXED
    distribution.append({
        "recipient": "platform",
        "type": "platform_fee",
        "amount": platform_amount,
        "percentage": PLATFORM_FEE_PERCENT,
        "fixed_fee": PLATFORM_FEE_FIXED
    })
    
    # Agent pool (job value minus platform fee only)
    agent_pool = job_value - platform_amount
    
    # 3. IP royalties (deducted from agent pool)
    total_royalties = 0.0
    if ip_asset_ids and ip_assets_data:
        for asset_id in ip_asset_ids:
            asset = next((a for a in ip_assets_data if a.get("id") == asset_id), None)
            if asset:
                royalty_pct = asset.get("royalty_percentage", 0.10)
                royalty_amount = agent_pool * royalty_pct
                total_royalties += royalty_amount
                
                distribution.append({
                    "recipient": asset["owner"],
                    "type": "ip_royalty",
                    "asset_id": asset_id,
                    "amount": royalty_amount,
                    "percentage": royalty_pct
                })
    
    # Agent pool after royalties
    agent_pool_after_royalties = agent_pool - total_royalties
    
    # 4. JV partner splits (from agent pool after royalties)
    total_jv_splits = 0.0
    if jv_partners:
        for partner in jv_partners:
            partner_split = partner.get("split", 0)
            partner_amount = agent_pool_after_royalties * partner_split
            total_jv_splits += partner_amount
            
            distribution.append({
                "recipient": partner["username"],
                "type": "jv_split",
                "amount": partner_amount,
                "percentage": partner_split
            })
    
    # 5. Lead agent (remainder)
    lead_agent_amount = agent_pool_after_royalties - total_jv_splits
    distribution.append({
        "recipient": lead_agent,
        "type": "agent_revenue",
        "amount": lead_agent_amount,
        "percentage": lead_agent_amount / job_value if job_value > 0 else 0
    })
    
    # Round all amounts
    for item in distribution:
        item["amount"] = round(item["amount"], 2)
        item["percentage"] = round(item["percentage"], 4)
    
    # Verify total
    total_distributed = sum([item["amount"] for item in distribution])
    
    if abs(total_distributed - job_value) > 0.01:
        return {
            "ok": False,
            "error": "distribution_mismatch",
            "expected": job_value,
            "actual": total_distributed
        }
    
    # Create summary
    summary = {
        "job_value": round(job_value, 2),
        "platform_fee": round(platform_amount, 2),
        "platform_fee_percent": PLATFORM_FEE_PERCENT,
        "platform_fee_fixed": PLATFORM_FEE_FIXED,
        "total_royalties": round(total_royalties, 2),
        "total_jv_splits": round(total_jv_splits, 2),
        "lead_agent_net": round(lead_agent_amount, 2)
    }

    
    return {
        "ok": True,
        "distribution": distribution,
        "summary": summary
    }


def transition_state(
    deal: Dict[str, Any],
    new_state: DealState,
    actor: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Transition deal to new state with validation
    """
    current_state = DealState(deal["state"])
    
    # Validate transition
    valid_transitions = {
        DealState.PROPOSED: [DealState.ACCEPTED, DealState.CANCELLED],
        DealState.ACCEPTED: [DealState.ESCROW_HELD, DealState.CANCELLED],
        DealState.ESCROW_HELD: [DealState.BONDS_STAKED, DealState.CANCELLED],
        DealState.BONDS_STAKED: [DealState.IN_PROGRESS],
        DealState.IN_PROGRESS: [DealState.DELIVERED, DealState.DISPUTED, DealState.BREACHED],
        DealState.DELIVERED: [DealState.COMPLETED, DealState.DISPUTED],
        DealState.DISPUTED: [DealState.COMPLETED, DealState.BREACHED],
        DealState.COMPLETED: [],
        DealState.CANCELLED: [],
        DealState.BREACHED: []
    }
    
    if new_state not in valid_transitions.get(current_state, []):
        return {
            "ok": False,
            "error": "invalid_state_transition",
            "from": current_state.value,
            "to": new_state.value
        }
    
    # Update state
    deal["state"] = new_state.value
    deal["updated_at"] = _now()
    
    # Add to history
    deal["state_history"].append({
        "state": new_state.value,
        "at": _now(),
        "by": actor,
        "metadata": metadata or {}
    })
    
    return {
        "ok": True,
        "deal_id": deal["id"],
        "from_state": current_state.value,
        "to_state": new_state.value,
        "transitioned_at": _now()
    }


def authorize_escrow(
    deal: Dict[str, Any],
    payment_intent_id: str,
    buyer_user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Authorize escrow (Stripe payment intent)
    """
    if deal["state"] != DealState.ACCEPTED:
        return {
            "ok": False,
            "error": "deal_must_be_accepted_first",
            "current_state": deal["state"]
        }
    
    job_value = deal["job_value"]
    
    # Update escrow tracking
    deal["escrow"]["status"] = "authorized"
    deal["escrow"]["amount"] = job_value
    deal["escrow"]["payment_intent_id"] = payment_intent_id
    deal["escrow"]["authorized_at"] = _now()
    
    # Transition state
    transition_state(deal, DealState.ESCROW_HELD, deal["buyer"], {
        "payment_intent_id": payment_intent_id,
        "amount": job_value
    })
    
    return {
        "ok": True,
        "deal_id": deal["id"],
        "escrow_authorized": job_value,
        "payment_intent_id": payment_intent_id
    }


def stake_bonds(
    deal: Dict[str, Any],
    agent_stakes: List[Dict[str, Any]],
    all_users: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Stake performance bonds from all participants
    
    agent_stakes: [{"username": "agent1", "amount": 100}, ...]
    """
    if deal["state"] != DealState.ESCROW_HELD:
        return {
            "ok": False,
            "error": "escrow_must_be_held_first",
            "current_state": deal["state"]
        }
    
    total_staked = 0.0
    stakes_processed = []
    
    for stake in agent_stakes:
        username = stake["username"]
        amount = float(stake["amount"])
        
        # Find user
        user = next((u for u in all_users if (
            u.get("username") == username or 
            u.get("consent", {}).get("username") == username
        )), None)
        
        if not user:
            return {"ok": False, "error": f"user_not_found: {username}"}
        
        # Check balance
        balance = float(user.get("ownership", {}).get("aigx", 0))
        if balance < amount:
            return {
                "ok": False,
                "error": "insufficient_balance",
                "username": username,
                "required": amount,
                "available": balance
            }
        
        # Deduct bond
        user["ownership"]["aigx"] = balance - amount
        
        # Add ledger entry
        user.setdefault("ownership", {}).setdefault("ledger", []).append({
            "ts": _now(),
            "amount": -amount,
            "currency": "AIGx",
            "basis": "performance_bond_stake",
            "deal_id": deal["id"]
        })
        
        total_staked += amount
        stakes_processed.append({
            "username": username,
            "amount": amount,
            "staked_at": _now()
        })
    
    # Update deal
    deal["bonds"]["staked"] = total_staked
    deal["bonds"]["status"] = "staked"
    deal["bonds"]["stakes"] = stakes_processed
    
    # Transition state
    transition_state(deal, DealState.BONDS_STAKED, deal["lead_agent"], {
        "total_staked": total_staked,
        "stakes": len(stakes_processed)
    })
    
    return {
        "ok": True,
        "deal_id": deal["id"],
        "total_bonds_staked": round(total_staked, 2),
        "stakes": stakes_processed
    }


def start_work(
    deal: Dict[str, Any],
    deadline: str
) -> Dict[str, Any]:
    """
    Start work phase (bonds staked, escrow held)
    """
    if deal["state"] != DealState.BONDS_STAKED:
        return {
            "ok": False,
            "error": "bonds_must_be_staked_first",
            "current_state": deal["state"]
        }
    
    # Set deadline
    deal["delivery"]["deadline"] = deadline
    
    # Transition to in progress
    transition_state(deal, DealState.IN_PROGRESS, deal["lead_agent"], {
        "deadline": deadline
    })
    
    return {
        "ok": True,
        "deal_id": deal["id"],
        "work_started": True,
        "deadline": deadline
    }


def mark_delivered(
    deal: Dict[str, Any],
    delivery_timestamp: str = None
) -> Dict[str, Any]:
    """
    Mark work as delivered
    """
    if deal["state"] != DealState.IN_PROGRESS:
        return {
            "ok": False,
            "error": "work_must_be_in_progress",
            "current_state": deal["state"]
        }
    
    if not delivery_timestamp:
        delivery_timestamp = _now()
    
    # Check if on-time
    deadline = deal["delivery"]["deadline"]
    on_time = delivery_timestamp <= deadline if deadline else True
    
    # Update delivery tracking
    deal["delivery"]["delivered_at"] = delivery_timestamp
    deal["delivery"]["on_time"] = on_time
    
    # Transition state
    transition_state(deal, DealState.DELIVERED, deal["lead_agent"], {
        "delivered_at": delivery_timestamp,
        "on_time": on_time
    })
    
    return {
        "ok": True,
        "deal_id": deal["id"],
        "delivered_at": delivery_timestamp,
        "on_time": on_time
    }


def settle_deal(
    deal: Dict[str, Any],
    all_users: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Settle deal - capture escrow and distribute to all parties atomically
    
    This is THE HOLY GRAIL - single atomic operation that:
    1. Captures escrow
    2. Returns bonds
    3. Distributes to JV partners
    4. Pays IP royalties
    5. Credits platform & insurance
    """
    if deal["state"] != DealState.DELIVERED:
        return {
            "ok": False,
            "error": "deal_must_be_delivered_first",
            "current_state": deal["state"]
        }
    
    if deal["settlement"]["settled"]:
        return {"ok": False, "error": "deal_already_settled"}
    
    distributions_executed = []
    
    # 1. Return all bonds
    for stake in deal["bonds"]["stakes"]:
        username = stake["username"]
        amount = stake["amount"]
        
        user = next((u for u in all_users if (
            u.get("username") == username or
            u.get("consent", {}).get("username") == username
        )), None)
        
        if user:
            balance = float(user.get("ownership", {}).get("aigx", 0))
            user["ownership"]["aigx"] = balance + amount
            
            user["ownership"].setdefault("ledger", []).append({
                "ts": _now(),
                "amount": amount,
                "currency": "AIGx",
                "basis": "bond_return",
                "deal_id": deal["id"]
            })
            
            distributions_executed.append({
                "type": "bond_return",
                "recipient": username,
                "amount": amount
            })
    
    # 2. Distribute revenue according to split
    for item in deal["revenue_split"]["distribution"]:
        recipient = item["recipient"]
        amount = item["amount"]
        split_type = item["type"]
        
        # Skip platform and insurance pool (handled separately)
        if recipient in ["platform", "insurance_pool"]:
            distributions_executed.append({
                "type": split_type,
                "recipient": recipient,
                "amount": amount
            })
            continue
        
        # Find recipient user
        user = next((u for u in all_users if (
            u.get("username") == recipient or
            u.get("consent", {}).get("username") == recipient
        )), None)
        
        if user:
            balance = float(user.get("ownership", {}).get("aigx", 0))
            user["ownership"]["aigx"] = balance + amount
            
            # Determine ledger basis
            if split_type == "ip_royalty":
                basis = "ip_royalty"
            elif split_type == "jv_split":
                basis = "jv_revenue"
            else:
                basis = "revenue"
            
            user["ownership"].setdefault("ledger", []).append({
                "ts": _now(),
                "amount": amount,
                "currency": "USD",
                "basis": basis,
                "deal_id": deal["id"],
                "asset_id": item.get("asset_id")
            })
            
            distributions_executed.append({
                "type": split_type,
                "recipient": recipient,
                "amount": amount
            })
    
    # Update deal settlement
    deal["settlement"]["settled"] = True
    deal["settlement"]["settled_at"] = _now()
    deal["settlement"]["distributions"] = distributions_executed
    
    # Mark escrow as captured
    deal["escrow"]["status"] = "captured"
    deal["escrow"]["captured_at"] = _now()
    
    # Transition to completed
    transition_state(deal, DealState.COMPLETED, "system", {
        "distributions": len(distributions_executed)
    })
    
    return {
        "ok": True,
        "deal_id": deal["id"],
        "settled": True,
        "distributions": distributions_executed,
        "total_distributed": round(sum([d["amount"] for d in distributions_executed]), 2),
        "settled_at": _now()
    }


def get_deal_summary(
    deal: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get complete deal summary
    """
    return {
        "deal_id": deal["id"],
        "state": deal["state"],
        "buyer": deal["buyer"],
        "lead_agent": deal["lead_agent"],
        "job_value": deal["job_value"],
        "slo_tier": deal["slo_tier"],
        "jv_partners": deal.get("jv_partners", []),
        "ip_assets": deal.get("ip_assets", []),
        "revenue_split_summary": deal["revenue_split_summary"],
        "escrow_status": deal["escrow"]["status"],
        "bonds_staked": deal["bonds"]["staked"],
        "delivered": deal["delivery"]["delivered_at"] is not None,
        "on_time": deal["delivery"].get("on_time"),
        "settled": deal["settlement"]["settled"],
        "created_at": deal["created_at"],
        "updated_at": deal["updated_at"]
    }
