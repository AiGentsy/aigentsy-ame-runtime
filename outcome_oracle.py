from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import httpx
from outcome_oracle_max import on_event

_POO_LEDGER: Dict[str, Dict[str, Any]] = {}

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"

async def issue_poo(
    username: str,
    intent_id: str,
    title: str,
    evidence_urls: List[str] = None,
    metrics: Dict[str, Any] = None,
    description: str = ""
) -> Dict[str, Any]:
    """Agent submits Proof of Outcome for buyer verification"""
    
    poo_id = f"poo_{uuid4().hex[:8]}"
    
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
        "events": [{"type": "POO_SUBMITTED", "at": now_iso()}]
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

Review and verify at: /intents/verify_poo""",
                        "meta": {"poo_id": poo_id, "intent_id": intent_id},
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
            "poo_id": poo_id
        })
        print(f"📦 Tracked DELIVERED for {username} (PoO: {poo_id})")
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
            "outcome_score_delta": 3
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
            "outcome_score_delta": -2
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
    """Get agent's PoO verification stats"""
    agent_poos = [p for p in _POO_LEDGER.values() if p["agent"] == username]
    
    total = len(agent_poos)
    verified = len([p for p in agent_poos if p["status"] == "VERIFIED"])
    rejected = len([p for p in agent_poos if p["status"] == "REJECTED"])
    pending = len([p for p in agent_poos if p["status"] == "PENDING_VERIFICATION"])
    
    verification_rate = round(verified / total * 100, 1) if total > 0 else 0.0
    
    return {
        "ok": True,
        "agent": username,
        "stats": {
            "total_submitted": total,
            "verified": verified,
            "rejected": rejected,
            "pending": pending,
            "verification_rate": verification_rate
        }
    }
