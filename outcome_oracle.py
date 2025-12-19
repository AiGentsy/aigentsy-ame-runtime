from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import httpx
from outcome_oracle_max import on_event

_POO_LEDGER: Dict[str, Dict[str, Any]] = {}

# ============================================================
# UNIVERSAL OUTCOME LEDGER (UoL) CONFIGURATION
# ============================================================

UOO_ARCHETYPES = {
    "saas": {"name": "SaaS", "base_value": 1.0},
    "marketing": {"name": "Marketing", "base_value": 1.0},
    "social": {"name": "Social/Creator", "base_value": 1.0},
    "legal": {"name": "Legal/Compliance", "base_value": 1.2},
    "ecommerce": {"name": "E-commerce", "base_value": 1.0},
    "general": {"name": "General", "base_value": 0.9},
    "unknown": {"name": "Unknown", "base_value": 0.8}
}

UOO_DIFFICULTY_MULTIPLIERS = {
    "easy": 0.5,
    "medium": 1.0,
    "hard": 1.5,
    "expert": 2.0
}

UOO_VALUE_BANDS = {
    "bronze": {"range": (0, 1000), "multiplier": 0.8},
    "silver": {"range": (1000, 5000), "multiplier": 1.0},
    "gold": {"range": (5000, 20000), "multiplier": 1.5},
    "platinum": {"range": (20000, float('inf')), "multiplier": 2.0}
}


def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


# ============================================================
# UoL HELPER FUNCTIONS
# ============================================================

def extract_archetype_from_template(template: str) -> str:
    """
    Extract archetype from user's template.
    
    Examples:
        "whitelabel_saas" → "saas"
        "whitelabel_marketing" → "marketing"
        "whitelabel_social" → "social"
    """
    if not template:
        return "unknown"
    
    # Handle template format: "whitelabel_<archetype>"
    if "_" in template:
        parts = template.split("_")
        archetype = parts[-1].lower()  # Last part after underscore
        
        # Validate it's a known archetype
        if archetype in UOO_ARCHETYPES:
            return archetype
    
    # Fallback: check if template contains archetype name
    template_lower = template.lower()
    for archetype in UOO_ARCHETYPES.keys():
        if archetype in template_lower:
            return archetype
    
    return "unknown"


def detect_difficulty_from_value(deal_value: float) -> str:
    """
    Auto-detect difficulty from deal value.
    
    Thresholds:
        < $1,000 = easy (0.5x)
        < $5,000 = medium (1.0x)
        < $20,000 = hard (1.5x)
        $20,000+ = expert (2.0x)
    """
    if deal_value < 1000:
        return "easy"
    elif deal_value < 5000:
        return "medium"
    elif deal_value < 20000:
        return "hard"
    else:
        return "expert"


def calculate_uoo(
    archetype: str = "unknown",
    difficulty: str = "medium",
    deal_value: float = 0,
    metrics: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Calculate Universal Outcome Unit (UoO) for a delivery.
    
    Formula: UoO = base_value × difficulty_mult × value_band_mult × confidence
    
    Args:
        archetype: Type of work (saas, marketing, social, legal, etc.)
        difficulty: Complexity level (easy, medium, hard, expert)
        deal_value: Dollar value of the deal
        metrics: Performance metrics (affects confidence)
        
    Returns:
        dict: UoO calculation with normalized score
    """
    
    # Get base value from archetype
    archetype_config = UOO_ARCHETYPES.get(archetype.lower(), UOO_ARCHETYPES["unknown"])
    base_value = archetype_config["base_value"]
    
    # Get difficulty multiplier
    difficulty_mult = UOO_DIFFICULTY_MULTIPLIERS.get(difficulty.lower(), 1.0)
    
    # Determine value band
    value_band = "bronze"
    value_band_mult = 0.8
    for band, config in UOO_VALUE_BANDS.items():
        min_val, max_val = config["range"]
        if min_val <= deal_value < max_val:
            value_band = band
            value_band_mult = config["multiplier"]
            break
    
    # Calculate confidence score (0.0-1.0)
    # Higher confidence = more verifiable metrics
    confidence = 0.5  # Default baseline
    if metrics:
        # More metrics = higher confidence
        metric_count = len([v for v in metrics.values() if v is not None])
        confidence = min(1.0, 0.5 + (metric_count * 0.1))
    
    # Final UoO score
    uoo_score = base_value * difficulty_mult * value_band_mult * confidence
    
    return {
        "uoo_score": round(uoo_score, 3),
        "archetype": archetype.lower(),
        "archetype_name": archetype_config["name"],
        "difficulty": difficulty.lower(),
        "difficulty_multiplier": difficulty_mult,
        "value_band": value_band,
        "value_band_multiplier": value_band_mult,
        "deal_value": deal_value,
        "confidence": round(confidence, 3),
        "verified": False,
        "calculation": {
            "base": base_value,
            "difficulty": difficulty_mult,
            "value_band": value_band_mult,
            "confidence": confidence,
            "formula": f"{base_value} × {difficulty_mult} × {value_band_mult} × {confidence:.3f} = {uoo_score:.3f}"
        }
    }

async def issue_poo(
    username: str,
    intent_id: str,
    title: str,
    evidence_urls: List[str] = None,
    metrics: Dict[str, Any] = None,
    description: str = "",
    deal_value: float = 0,        # NEW: For UoO calculation
    user_template: str = None     # NEW: For archetype detection
) -> Dict[str, Any]:
    """
    Agent submits Proof of Outcome for buyer verification.
    
    Enhanced with Universal Outcome Ledger (UoO) tracking.
    
    Args:
        username: Agent username
        intent_id: Related intent ID
        title: PoO title
        evidence_urls: List of evidence URLs
        metrics: Performance metrics
        description: PoO description
        deal_value: Dollar value of deal (for UoO difficulty detection)
        user_template: User's template (for archetype detection)
    """
    
    poo_id = f"poo_{uuid4().hex[:8]}"
    
    # ============================================
    # UoL: CALCULATE UoO SCORE
    # ============================================
    
    # Auto-detect archetype from user's template
    archetype = "unknown"
    if user_template:
        archetype = extract_archetype_from_template(user_template)
    
    # Auto-detect difficulty from deal value
    difficulty = detect_difficulty_from_value(deal_value)
    
    # Calculate UoO
    uoo_data = calculate_uoo(
        archetype=archetype,
        difficulty=difficulty,
        deal_value=deal_value,
        metrics=metrics
    )
    
    print(f"📊 UoO calculated: {uoo_data['uoo_score']} ({archetype}, {difficulty}, {uoo_data['value_band']})")
    
    # ============================================
    # CREATE PoO ENTRY (with UoO metadata)
    # ============================================
    
    poo_entry = {
        "id": poo_id,
        "agent": username,
        "intent_id": intent_id,
        "title": title,
        "description": description,
        "evidence_urls": evidence_urls or [],
        "metrics": metrics or {},
        "status": "PENDING_VERIFICATION",
        "submitted_at": now_iso(),
        "verified_at": None,
        "verified_by": None,
        "rejection_reason": None,
        "outcome_score_delta": 0,
        "events": [{"type": "POO_SUBMITTED", "at": now_iso()}],
        
        # ============================================
        # NEW: UoO METADATA
        # ============================================
        "uoo": uoo_data
    }
    
    _POO_LEDGER[poo_id] = poo_entry
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            intent_resp = await client.get(
                f"https://aigentsy-ame-runtime.onrender.com/intents/{intent_id}"
            )
            intent_data = intent_resp.json()
            buyer = intent_data.get("intent", {}).get("from")
            
            if buyer:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                    json={
                        "id": f"poo_notif_{uuid4().hex[:8]}",
                        "sender": username,
                        "recipient": buyer,
                        "title": f"Proof of Outcome Ready: {title}",
                        "body": f"""Agent {username} has completed your intent and submitted proof.

{description}

Evidence URLs: {len(evidence_urls or [])} files
Metrics: {metrics or {}}
UoO Score: {uoo_data['uoo_score']} ({uoo_data['archetype_name']}, {uoo_data['difficulty']}, {uoo_data['value_band']})

Review and verify at: /intents/verify_poo""",
                        "meta": {
                            "poo_id": poo_id,
                            "intent_id": intent_id,
                            "uoo_score": uoo_data["uoo_score"],
                            "uoo_archetype": uoo_data["archetype"],
                            "uoo_difficulty": uoo_data["difficulty"]
                        },
                        "status": "sent",
                        "timestamp": now_iso()
                    }
                )
        except Exception as e:
            print(f"Failed to notify buyer: {e}")
    
    try:
        on_event({
            "kind": "DELIVERED",
            "username": username,
            "source": "intent_exchange",
            "intent_id": intent_id,
            "poo_id": poo_id,
            "uoo_score": uoo_data["uoo_score"],
            "uoo_archetype": uoo_data["archetype"],
            "uoo_difficulty": uoo_data["difficulty"]
        })
        print(f"📦 Tracked DELIVERED for {username} (PoO: {poo_id}, UoO: {uoo_data['uoo_score']})")
    except Exception as e:
        print(f"❌ Outcome tracking failed: {e}")
    
    return {"ok": True, "poo_id": poo_id, "poo": poo_entry}


async def verify_poo(
    poo_id: str,
    buyer_username: str,
    approved: bool,
    feedback: str = ""
) -> Dict[str, Any]:
    """Buyer verifies or rejects agent's PoO"""
    
    poo = _POO_LEDGER.get(poo_id)
    if not poo:
        return {"ok": False, "error": "poo_not_found"}
    
    if poo["status"] != "PENDING_VERIFICATION":
        return {"ok": False, "error": f"poo_already_{poo['status'].lower()}"}
    
    if approved:
        poo["status"] = "VERIFIED"
        poo["verified_at"] = now_iso()
        poo["verified_by"] = buyer_username
        poo["buyer_feedback"] = feedback
        poo["outcome_score_delta"] = 3
        poo["events"].append({
            "type": "POO_VERIFIED",
            "by": buyer_username,
            "at": now_iso()
        })
        
        # ============================================
        # UoL: INCREASE CONFIDENCE ON VERIFICATION
        # ============================================
        if "uoo" in poo:
            poo["uoo"]["confidence"] = min(1.0, poo["uoo"]["confidence"] + 0.1)
            poo["uoo"]["verified"] = True
            # Recalculate UoO score with new confidence
            old_score = poo["uoo"]["uoo_score"]
            new_score = (poo["uoo"]["calculation"]["base"] * 
                        poo["uoo"]["calculation"]["difficulty"] * 
                        poo["uoo"]["calculation"]["value_band"] * 
                        poo["uoo"]["confidence"])
            poo["uoo"]["uoo_score"] = round(new_score, 3)
            print(f"✅ UoO confidence increased: {old_score} → {poo['uoo']['uoo_score']}")
        
        agent = poo["agent"]
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/poo/issue",
                    json={
                        "username": agent,
                        "title": poo["title"],
                        "metrics": poo["metrics"],
                        "evidence_urls": poo["evidence_urls"]
                    }
                )
            except Exception as e:
                print(f"Failed to update OutcomeScore: {e}")
            
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/intents/verify_poo",
                    json={
                        "intent_id": poo["intent_id"],
                        "poo_id": poo_id,
                        "approved": True,
                        "feedback": feedback
                    }
                )
            except Exception as e:
                print(f"Failed to release escrow: {e}")
        
        return {
            "ok": True,
            "status": "VERIFIED",
            "escrow_released": True,
            "outcome_score_delta": 3,
            "uoo_earned": poo.get("uoo", {}).get("uoo_score", 0)
        }
    
    else:
        poo["status"] = "REJECTED"
        poo["verified_at"] = now_iso()
        poo["verified_by"] = buyer_username
        poo["rejection_reason"] = feedback or "buyer_not_satisfied"
        poo["outcome_score_delta"] = -2
        poo["events"].append({
            "type": "POO_REJECTED",
            "by": buyer_username,
            "reason": feedback,
            "at": now_iso()
        })
        
        # ============================================
        # UoL: DECREASE CONFIDENCE ON REJECTION
        # ============================================
        if "uoo" in poo:
            poo["uoo"]["confidence"] = max(0.0, poo["uoo"]["confidence"] - 0.2)
            poo["uoo"]["rejected"] = True
            # Recalculate UoO score with new confidence
            old_score = poo["uoo"]["uoo_score"]
            new_score = (poo["uoo"]["calculation"]["base"] * 
                        poo["uoo"]["calculation"]["difficulty"] * 
                        poo["uoo"]["calculation"]["value_band"] * 
                        poo["uoo"]["confidence"])
            poo["uoo"]["uoo_score"] = round(new_score, 3)
            print(f"⚠️ UoO confidence decreased: {old_score} → {poo['uoo']['uoo_score']}")
        
        agent = poo["agent"]
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                users_resp = await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/user",
                    json={"username": agent}
                )
                user = users_resp.json().get("record", {})
                current_score = user.get("outcomeScore", 50)
                new_score = max(0, current_score - 2)
                print(f"Agent {agent} PoO rejected. Score should decrease by 2.")
            except Exception as e:
                print(f"Failed to update OutcomeScore: {e}")
            
            try:
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/intents/verify_poo",
                    json={
                        "intent_id": poo["intent_id"],
                        "poo_id": poo_id,
                        "approved": False,
                        "feedback": feedback
                    }
                )
            except Exception as e:
                print(f"Failed to open dispute: {e}")
        
        return {
            "ok": True,
            "status": "REJECTED",
            "dispute_opened": True,
            "outcome_score_delta": -2,
            "uoo_penalty": poo.get("uoo", {}).get("uoo_score", 0)
        }


def get_poo(poo_id: str) -> Dict[str, Any]:
    """Get PoO details"""
    poo = _POO_LEDGER.get(poo_id)
    if not poo:
        return {"ok": False, "error": "poo_not_found"}
    return {"ok": True, "poo": poo}


def list_poos(
    agent: str = None,
    intent_id: str = None,
    status: str = None
) -> Dict[str, Any]:
    """List PoOs with optional filters"""
    poos = list(_POO_LEDGER.values())
    
    if agent:
        poos = [p for p in poos if p["agent"] == agent]
    
    if intent_id:
        poos = [p for p in poos if p["intent_id"] == intent_id]
    
    if status:
        poos = [p for p in poos if p["status"] == status.upper()]
    
    poos.sort(key=lambda x: x["submitted_at"], reverse=True)
    
    return {"ok": True, "poos": poos, "count": len(poos)}


def get_agent_poo_stats(username: str) -> Dict[str, Any]:
    """Get agent's PoO verification stats with UoO totals"""
    agent_poos = [p for p in _POO_LEDGER.values() if p["agent"] == username]
    
    total = len(agent_poos)
    verified = len([p for p in agent_poos if p["status"] == "VERIFIED"])
    rejected = len([p for p in agent_poos if p["status"] == "REJECTED"])
    pending = len([p for p in agent_poos if p["status"] == "PENDING_VERIFICATION"])
    
    verification_rate = round(verified / total * 100, 1) if total > 0 else 0.0
    
    # ============================================
    # UoL: CALCULATE UoO TOTALS
    # ============================================
    verified_poos = [p for p in agent_poos if p["status"] == "VERIFIED"]
    
    total_uoo = sum(p.get("uoo", {}).get("uoo_score", 0) for p in verified_poos)
    avg_uoo = round(total_uoo / verified, 3) if verified > 0 else 0.0
    
    # UoO by archetype
    uoo_by_archetype = {}
    for poo in verified_poos:
        if "uoo" in poo:
            archetype = poo["uoo"]["archetype"]
            uoo_score = poo["uoo"]["uoo_score"]
            archetype_name = poo["uoo"]["archetype_name"]
            
            if archetype not in uoo_by_archetype:
                uoo_by_archetype[archetype] = {
                    "name": archetype_name,
                    "count": 0,
                    "total_uoo": 0
                }
            
            uoo_by_archetype[archetype]["count"] += 1
            uoo_by_archetype[archetype]["total_uoo"] += uoo_score
    
    # Round totals
    for archetype_data in uoo_by_archetype.values():
        archetype_data["total_uoo"] = round(archetype_data["total_uoo"], 3)
        archetype_data["avg_uoo"] = round(
            archetype_data["total_uoo"] / archetype_data["count"], 3
        ) if archetype_data["count"] > 0 else 0
    
    return {
        "ok": True,
        "agent": username,
        "stats": {
            "total_submitted": total,
            "verified": verified,
            "rejected": rejected,
            "pending": pending,
            "verification_rate": verification_rate
        },
        "uoo_stats": {
            "total_uoo_earned": round(total_uoo, 3),
            "average_uoo_per_outcome": avg_uoo,
            "by_archetype": uoo_by_archetype
        }
    }

async def record_outcome(username: str, outcome_type: str, metadata: dict) -> bool:
    """
    Record an outcome for tracking and PoO system
    
    Args:
        username: User's username
        outcome_type: Type of outcome (e.g., "SITE_PUBLISHED", "DEAL_CLOSED")
        metadata: Additional data about the outcome
        
    Returns:
        True if successful, False otherwise
    """
    from log_to_jsonbin import get_user, update_user
    from datetime import datetime, timezone
    
    try:
        # Get user
        user = get_user(username)
        if not user:
            print(f"User {username} not found")
            return False
        
        # Initialize outcomes list if needed
        if "outcomes" not in user:
            user["outcomes"] = []
        
        # Create outcome record
        outcome = {
            "type": outcome_type,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "metadata": metadata
        }
        
        user["outcomes"].append(outcome)
        
        # Save
        success = update_user(username, user)
        
        if success:
            print(f"✅ Recorded outcome: {outcome_type} for {username}")
        
        return success
        
    except Exception as e:
        print(f"Error recording outcome: {e}")
        return False
