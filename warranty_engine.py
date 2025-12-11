# warranty_engine.py
"""
AiGentsy Warranty Engine - Feature #8

Outcome guarantees and warranties:
- Money-back guarantees (50%, 100%)
- Revision guarantees (3x, unlimited)
- Performance guarantees (results or refund)
- Warranty bond staking and slashing
- Claim filing and processing

Integrates with:
- outcome_oracle.py (warranty tracking on outcomes)
- intent_exchange_UPGRADED.py (warranty offers in bids)
- performance_bonds.py (warranty bond mechanics)
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
import json

# Warranty type definitions
WARRANTY_TYPES = {
    "money_back_100": {
        "name": "100% Money-Back Guarantee",
        "category": "refund",
        "refund_percent": 100,
        "bond_percent": 25,  # Agent stakes 25% of outcome price
        "claim_window_days": 30,
        "requires_verification": True,
        "description": "Full refund if outcome doesn't meet specifications",
        "buyer_benefit": "Zero risk - complete satisfaction or money back",
        "agent_requirement": "Must stake 25% bond, verified delivery required"
    },
    "money_back_50": {
        "name": "50% Money-Back Guarantee",
        "category": "refund",
        "refund_percent": 50,
        "bond_percent": 15,
        "claim_window_days": 30,
        "requires_verification": True,
        "description": "50% refund if dissatisfied with outcome",
        "buyer_benefit": "Partial refund available for dissatisfaction",
        "agent_requirement": "Must stake 15% bond, verified delivery required"
    },
    "unlimited_revisions": {
        "name": "Unlimited Revisions",
        "category": "revision",
        "revisions_allowed": 999,
        "revision_sla_hours": 48,
        "bond_percent": 10,
        "claim_window_days": 90,
        "requires_verification": False,
        "description": "Unlimited revisions until you're satisfied",
        "buyer_benefit": "Perfect outcome guaranteed through iterations",
        "agent_requirement": "Must deliver revisions within 48hrs"
    },
    "three_revisions": {
        "name": "3 Free Revisions",
        "category": "revision",
        "revisions_allowed": 3,
        "revision_sla_hours": 48,
        "bond_percent": 5,
        "claim_window_days": 60,
        "requires_verification": False,
        "description": "Up to 3 free revisions included",
        "buyer_benefit": "Three chances to refine outcome to perfection",
        "agent_requirement": "Must deliver revisions within 48hrs"
    },
    "performance_guarantee": {
        "name": "Performance Guarantee",
        "category": "performance",
        "refund_percent": 100,
        "bond_percent": 30,
        "requires_metrics": True,
        "requires_verification": True,
        "claim_window_days": 60,
        "description": "Measurable results or 100% money back",
        "buyer_benefit": "Guaranteed ROI - results must hit metrics",
        "agent_requirement": "Must stake 30% bond, metrics must be measurable"
    }
}

# In-memory warranty storage (use JSONBin in production)
WARRANTIES_DB = {}
WARRANTY_BONDS_DB = {}
WARRANTY_CLAIMS_DB = {}
REVISION_REQUESTS_DB = {}


def create_warranty(
    agent_username: str,
    warranty_type: str,
    outcome_price: float,
    custom_terms: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a warranty offer for an outcome.
    
    Args:
        agent_username: Agent offering warranty
        warranty_type: Type of warranty (money_back_100, unlimited_revisions, etc)
        outcome_price: Price of the outcome being warranted
        custom_terms: Optional custom warranty terms
    
    Returns:
        Warranty object with terms and bond requirement
    """
    if warranty_type not in WARRANTY_TYPES:
        raise ValueError(f"Invalid warranty type: {warranty_type}")
    
    warranty_config = WARRANTY_TYPES[warranty_type]
    
    # Calculate bond requirement
    bond_required = (outcome_price * warranty_config["bond_percent"]) / 100
    
    warranty_id = f"warranty_{agent_username}_{warranty_type}_{int(datetime.now(timezone.utc).timestamp())}"
    
    warranty = {
        "warranty_id": warranty_id,
        "agent_username": agent_username,
        "warranty_type": warranty_type,
        "warranty_name": warranty_config["name"],
        "category": warranty_config["category"],
        "outcome_price": outcome_price,
        "bond_required": bond_required,
        "bond_staked": False,
        "bond_amount": 0,
        "bond_staked_at": None,
        "terms": {
            **warranty_config,
            **(custom_terms or {})
        },
        "status": "pending",  # pending → active → claimed/expired/returned
        "created_at": datetime.now(timezone.utc).isoformat(),
        "activated_at": None,
        "expires_at": None,
        "claim_count": 0,
        "revision_count": 0,
        "outcome_id": None  # Linked when outcome delivered
    }
    
    WARRANTIES_DB[warranty_id] = warranty
    
    return warranty


def stake_warranty_bond(
    warranty_id: str,
    agent_username: str,
    amount: float,
    payment_method: str = "stripe"
) -> Dict[str, Any]:
    """
    Stake warranty bond to activate warranty.
    
    Args:
        warranty_id: Warranty ID
        agent_username: Agent staking bond
        amount: Bond amount to stake
        payment_method: Payment method used
    
    Returns:
        Bond staking confirmation
    """
    if warranty_id not in WARRANTIES_DB:
        raise ValueError(f"Warranty not found: {warranty_id}")
    
    warranty = WARRANTIES_DB[warranty_id]
    
    # Verify agent
    if warranty["agent_username"] != agent_username:
        raise ValueError(f"Agent mismatch: {agent_username} cannot stake bond for {warranty['agent_username']}")
    
    # Verify amount
    if amount < warranty["bond_required"]:
        raise ValueError(
            f"Insufficient bond amount. Required: ${warranty['bond_required']}, "
            f"Provided: ${amount}"
        )
    
    # Check if already staked
    if warranty["bond_staked"]:
        raise ValueError(f"Bond already staked for warranty: {warranty_id}")
    
    # Create bond record
    bond_id = f"bond_{warranty_id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    bond = {
        "bond_id": bond_id,
        "warranty_id": warranty_id,
        "agent_username": agent_username,
        "amount": amount,
        "payment_method": payment_method,
        "status": "staked",  # staked → returned/slashed
        "staked_at": datetime.now(timezone.utc).isoformat(),
        "returned_at": None,
        "slashed_at": None,
        "slash_reason": None
    }
    
    WARRANTY_BONDS_DB[bond_id] = bond
    
    # Update warranty
    warranty["bond_staked"] = True
    warranty["bond_amount"] = amount
    warranty["bond_staked_at"] = datetime.now(timezone.utc).isoformat()
    warranty["status"] = "active"
    
    WARRANTIES_DB[warranty_id] = warranty
    
    return {
        "success": True,
        "bond_id": bond_id,
        "warranty_id": warranty_id,
        "amount_staked": amount,
        "warranty_status": "active",
        "message": f"Bond staked: ${amount:.2f}. Warranty now active."
    }


def calculate_bond_requirement(warranty_type: str, outcome_price: float) -> Dict[str, Any]:
    """
    Calculate bond requirement for a warranty type and price.
    
    Args:
        warranty_type: Type of warranty
        outcome_price: Price of outcome
    
    Returns:
        Bond calculation details
    """
    if warranty_type not in WARRANTY_TYPES:
        raise ValueError(f"Invalid warranty type: {warranty_type}")
    
    warranty_config = WARRANTY_TYPES[warranty_type]
    
    bond_amount = (outcome_price * warranty_config["bond_percent"]) / 100
    
    return {
        "warranty_type": warranty_type,
        "warranty_name": warranty_config["name"],
        "outcome_price": outcome_price,
        "bond_percent": warranty_config["bond_percent"],
        "bond_amount": bond_amount,
        "bond_display": f"${bond_amount:.2f}",
        "calculation": f"{warranty_config['bond_percent']}% of ${outcome_price:.2f} = ${bond_amount:.2f}"
    }


def file_warranty_claim(
    buyer_username: str,
    outcome_id: str,
    warranty_id: str,
    claim_reason: str,
    evidence: Optional[str] = None,
    desired_resolution: str = "refund"
) -> Dict[str, Any]:
    """
    File a warranty claim for an outcome.
    
    Args:
        buyer_username: Buyer filing claim
        outcome_id: Outcome ID
        warranty_id: Warranty ID
        claim_reason: Reason for claim
        evidence: Supporting evidence (optional)
        desired_resolution: refund or revision
    
    Returns:
        Claim record
    """
    if warranty_id not in WARRANTIES_DB:
        raise ValueError(f"Warranty not found: {warranty_id}")
    
    warranty = WARRANTIES_DB[warranty_id]
    
    # Check warranty status
    if warranty["status"] != "active":
        raise ValueError(f"Warranty not active: {warranty['status']}")
    
    # Check claim window
    if warranty["activated_at"]:
        activated = datetime.fromisoformat(warranty["activated_at"])
        claim_window_end = activated + timedelta(days=warranty["terms"]["claim_window_days"])
        
        if datetime.now(timezone.utc) > claim_window_end:
            raise ValueError(f"Claim window expired. Must file within {warranty['terms']['claim_window_days']} days.")
    
    claim_id = f"claim_{warranty_id}_{int(datetime.now(timezone.utc).timestamp())}"
    
    claim = {
        "claim_id": claim_id,
        "warranty_id": warranty_id,
        "outcome_id": outcome_id,
        "buyer_username": buyer_username,
        "agent_username": warranty["agent_username"],
        "claim_reason": claim_reason,
        "evidence": evidence,
        "desired_resolution": desired_resolution,
        "warranty_type": warranty["warranty_type"],
        "status": "pending",  # pending → approved/denied
        "filed_at": datetime.now(timezone.utc).isoformat(),
        "reviewed_at": None,
        "reviewed_by": None,
        "resolution": None,
        "refund_amount": 0,
        "refund_processed_at": None
    }
    
    WARRANTY_CLAIMS_DB[claim_id] = claim
    
    # Increment claim count
    warranty["claim_count"] += 1
    WARRANTIES_DB[warranty_id] = warranty
    
    return claim


def process_warranty_claim(
    claim_id: str,
    approved: bool,
    reviewer: str = "aigentsy_admin",
    review_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process (approve or deny) a warranty claim.
    
    Args:
        claim_id: Claim ID
        approved: True to approve, False to deny
        reviewer: Who reviewed the claim
        review_notes: Notes about the decision
    
    Returns:
        Claim processing result
    """
    if claim_id not in WARRANTY_CLAIMS_DB:
        raise ValueError(f"Claim not found: {claim_id}")
    
    claim = WARRANTY_CLAIMS_DB[claim_id]
    
    if claim["status"] != "pending":
        raise ValueError(f"Claim already processed: {claim['status']}")
    
    warranty = WARRANTIES_DB[claim["warranty_id"]]
    
    claim["status"] = "approved" if approved else "denied"
    claim["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    claim["reviewed_by"] = reviewer
    claim["resolution"] = review_notes or ("Claim approved" if approved else "Claim denied")
    
    result = {
        "claim_id": claim_id,
        "warranty_id": claim["warranty_id"],
        "approved": approved,
        "reviewed_by": reviewer
    }
    
    if approved:
        # Calculate refund
        refund_percent = warranty["terms"].get("refund_percent", 0)
        refund_amount = (warranty["outcome_price"] * refund_percent) / 100
        
        claim["refund_amount"] = refund_amount
        claim["refund_processed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Slash warranty bond
        bond = _find_warranty_bond(claim["warranty_id"])
        if bond:
            bond["status"] = "slashed"
            bond["slashed_at"] = datetime.now(timezone.utc).isoformat()
            bond["slash_reason"] = claim["claim_reason"]
            WARRANTY_BONDS_DB[bond["bond_id"]] = bond
        
        # Update warranty status
        warranty["status"] = "claimed"
        WARRANTIES_DB[claim["warranty_id"]] = warranty
        
        result.update({
            "refund_amount": refund_amount,
            "refund_percent": refund_percent,
            "bond_slashed": True,
            "message": f"Claim approved. Refunding ${refund_amount:.2f} to buyer. Agent bond slashed."
        })
    else:
        result.update({
            "refund_amount": 0,
            "bond_slashed": False,
            "message": "Claim denied. No refund issued. Agent bond protected."
        })
    
    WARRANTY_CLAIMS_DB[claim_id] = claim
    
    return result


def request_revision(
    buyer_username: str,
    outcome_id: str,
    warranty_id: str,
    revision_feedback: str,
    revision_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Request a revision under warranty terms.
    
    Args:
        buyer_username: Buyer requesting revision
        outcome_id: Outcome ID
        warranty_id: Warranty ID
        revision_feedback: Feedback for revision
        revision_details: Detailed revision requirements
    
    Returns:
        Revision request record
    """
    if warranty_id not in WARRANTIES_DB:
        raise ValueError(f"Warranty not found: {warranty_id}")
    
    warranty = WARRANTIES_DB[warranty_id]
    
    # Check if warranty allows revisions
    if warranty["category"] != "revision":
        raise ValueError(f"Warranty type {warranty['warranty_type']} does not include revisions")
    
    # Check revision limit
    revisions_allowed = warranty["terms"]["revisions_allowed"]
    revisions_used = warranty["revision_count"]
    
    if revisions_used >= revisions_allowed:
        raise ValueError(
            f"Revision limit reached. {revisions_used}/{revisions_allowed} revisions used."
        )
    
    revision_id = f"revision_{warranty_id}_{revisions_used + 1}_{int(datetime.now(timezone.utc).timestamp())}"
    
    # Calculate SLA deadline
    sla_hours = warranty["terms"]["revision_sla_hours"]
    sla_deadline = datetime.now(timezone.utc) + timedelta(hours=sla_hours)
    
    revision_request = {
        "revision_id": revision_id,
        "warranty_id": warranty_id,
        "outcome_id": outcome_id,
        "buyer_username": buyer_username,
        "agent_username": warranty["agent_username"],
        "revision_number": revisions_used + 1,
        "revision_feedback": revision_feedback,
        "revision_details": revision_details or {},
        "status": "requested",  # requested → delivered → accepted/rejected
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "sla_deadline": sla_deadline.isoformat(),
        "sla_hours": sla_hours,
        "delivered_at": None,
        "accepted_at": None,
        "sla_met": None
    }
    
    REVISION_REQUESTS_DB[revision_id] = revision_request
    
    # Increment revision count
    warranty["revision_count"] += 1
    WARRANTIES_DB[warranty_id] = warranty
    
    return {
        "success": True,
        "revision_id": revision_id,
        "revision_number": revisions_used + 1,
        "revisions_remaining": revisions_allowed - (revisions_used + 1),
        "sla_deadline": sla_deadline.isoformat(),
        "sla_hours": sla_hours,
        "message": f"Revision #{revisions_used + 1} requested. Agent has {sla_hours}hrs to deliver."
    }


def deliver_revision(
    agent_username: str,
    revision_id: str,
    revised_outcome: Dict[str, Any],
    revision_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Agent delivers a revision.
    
    Args:
        agent_username: Agent delivering revision
        revision_id: Revision request ID
        revised_outcome: Revised outcome data
        revision_notes: Notes about the revision
    
    Returns:
        Revision delivery confirmation
    """
    if revision_id not in REVISION_REQUESTS_DB:
        raise ValueError(f"Revision request not found: {revision_id}")
    
    revision = REVISION_REQUESTS_DB[revision_id]
    
    # Verify agent
    if revision["agent_username"] != agent_username:
        raise ValueError(f"Agent mismatch: {agent_username} cannot deliver for {revision['agent_username']}")
    
    # Check status
    if revision["status"] != "requested":
        raise ValueError(f"Revision not in requested status: {revision['status']}")
    
    # Check SLA
    sla_deadline = datetime.fromisoformat(revision["sla_deadline"])
    delivered_at = datetime.now(timezone.utc)
    sla_met = delivered_at <= sla_deadline
    
    revision["status"] = "delivered"
    revision["delivered_at"] = delivered_at.isoformat()
    revision["revised_outcome"] = revised_outcome
    revision["revision_notes"] = revision_notes
    revision["sla_met"] = sla_met
    
    REVISION_REQUESTS_DB[revision_id] = revision
    
    return {
        "success": True,
        "revision_id": revision_id,
        "delivered_at": delivered_at.isoformat(),
        "sla_met": sla_met,
        "sla_deadline": sla_deadline.isoformat(),
        "message": f"Revision delivered. SLA {'met' if sla_met else 'MISSED'}."
    }


def return_warranty_bond(warranty_id: str) -> Dict[str, Any]:
    """
    Return warranty bond to agent after claim window expires.
    
    Called automatically 30 days after outcome delivery (no claims filed).
    
    Args:
        warranty_id: Warranty ID
    
    Returns:
        Bond return confirmation
    """
    if warranty_id not in WARRANTIES_DB:
        raise ValueError(f"Warranty not found: {warranty_id}")
    
    warranty = WARRANTIES_DB[warranty_id]
    
    # Check warranty status
    if warranty["status"] == "claimed":
        raise ValueError("Cannot return bond - warranty was claimed")
    
    # Find bond
    bond = _find_warranty_bond(warranty_id)
    
    if not bond:
        raise ValueError(f"No bond found for warranty: {warranty_id}")
    
    if bond["status"] != "staked":
        raise ValueError(f"Bond already processed: {bond['status']}")
    
    # Return bond
    bond["status"] = "returned"
    bond["returned_at"] = datetime.now(timezone.utc).isoformat()
    WARRANTY_BONDS_DB[bond["bond_id"]] = bond
    
    # Update warranty
    warranty["status"] = "expired"
    WARRANTIES_DB[warranty_id] = warranty
    
    return {
        "success": True,
        "bond_id": bond["bond_id"],
        "warranty_id": warranty_id,
        "amount_returned": bond["amount"],
        "agent_username": warranty["agent_username"],
        "message": f"Bond returned: ${bond['amount']:.2f}. No claims filed within window."
    }


def _find_warranty_bond(warranty_id: str) -> Optional[Dict[str, Any]]:
    """Helper to find bond for warranty."""
    for bond in WARRANTY_BONDS_DB.values():
        if bond["warranty_id"] == warranty_id:
            return bond
    return None


def get_warranty_terms(warranty_id: str) -> Dict[str, Any]:
    """Get detailed warranty terms."""
    if warranty_id not in WARRANTIES_DB:
        raise ValueError(f"Warranty not found: {warranty_id}")
    
    warranty = WARRANTIES_DB[warranty_id]
    
    return {
        "warranty_id": warranty_id,
        "warranty_name": warranty["warranty_name"],
        "warranty_type": warranty["warranty_type"],
        "category": warranty["category"],
        "agent_username": warranty["agent_username"],
        "outcome_price": warranty["outcome_price"],
        "bond_required": warranty["bond_required"],
        "bond_staked": warranty["bond_staked"],
        "status": warranty["status"],
        "terms": warranty["terms"],
        "claim_count": warranty["claim_count"],
        "revision_count": warranty["revision_count"],
        "created_at": warranty["created_at"]
    }


def get_agent_warranties(agent_username: str) -> Dict[str, Any]:
    """Get all warranties offered by an agent."""
    agent_warranties = [
        w for w in WARRANTIES_DB.values()
        if w["agent_username"] == agent_username
    ]
    
    # Sort by creation date
    agent_warranties.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Calculate totals
    total_bonds_staked = sum(
        w["bond_amount"] for w in agent_warranties
        if w["bond_staked"]
    )
    
    total_claims = sum(w["claim_count"] for w in agent_warranties)
    
    active_warranties = [w for w in agent_warranties if w["status"] == "active"]
    
    return {
        "agent_username": agent_username,
        "total_warranties": len(agent_warranties),
        "active_warranties": len(active_warranties),
        "total_bonds_staked": total_bonds_staked,
        "total_claims": total_claims,
        "warranties": agent_warranties
    }


def get_all_warranty_types() -> Dict[str, Any]:
    """Get all available warranty types."""
    return WARRANTY_TYPES


def get_buyer_claims(buyer_username: str) -> Dict[str, Any]:
    """Get all warranty claims filed by a buyer."""
    buyer_claims = [
        c for c in WARRANTY_CLAIMS_DB.values()
        if c["buyer_username"] == buyer_username
    ]
    
    buyer_claims.sort(key=lambda x: x["filed_at"], reverse=True)
    
    approved_claims = [c for c in buyer_claims if c["status"] == "approved"]
    total_refunds = sum(c.get("refund_amount", 0) for c in approved_claims)
    
    return {
        "buyer_username": buyer_username,
        "total_claims": len(buyer_claims),
        "approved_claims": len(approved_claims),
        "total_refunds": total_refunds,
        "claims": buyer_claims
    }


# Example usage
if __name__ == "__main__":
    # Create warranty
    warranty = create_warranty("agent_alice", "money_back_100", 1000.0)
    print(f"Created warranty: {warranty['warranty_id']}")
    print(f"Bond required: ${warranty['bond_required']:.2f}")
    
    # Stake bond
    bond = stake_warranty_bond(warranty["warranty_id"], "agent_alice", 250.0)
    print(f"\nBond staked: {bond['message']}")
    
    # File claim
    claim = file_warranty_claim(
        "buyer_bob",
        "outcome_123",
        warranty["warranty_id"],
        "Outcome did not meet specifications",
        "Screenshots attached showing missing features"
    )
    print(f"\nClaim filed: {claim['claim_id']}")
    
    # Process claim
    result = process_warranty_claim(claim["claim_id"], approved=True)
    print(f"\nClaim processed: {result['message']}")
    
    # Request revision
    warranty2 = create_warranty("agent_charlie", "unlimited_revisions", 500.0)
    stake_warranty_bond(warranty2["warranty_id"], "agent_charlie", 50.0)
    
    revision = request_revision(
        "buyer_david",
        "outcome_456",
        warranty2["warranty_id"],
        "Please adjust color scheme to brand colors"
    )
    print(f"\nRevision requested: {revision['message']}")
    
    # All warranty types
    types = get_all_warranty_types()
    print(f"\nAvailable warranty types: {', '.join(types.keys())}")
