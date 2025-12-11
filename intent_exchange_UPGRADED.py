from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime, timedelta
import asyncio
import httpx
from performance_bonds import (
    stake_bond,
    return_bond,
    award_sla_bonus,
    slash_bond
)

from revenue_flows import ingest_intent_settlement

router = APIRouter()
_INTENTS: Dict[str, Dict[str, Any]] = {}
_BIDS: Dict[str, List[Dict[str, Any]]] = {}
_ESCROW: Dict[str, Dict[str, Any]] = {}

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

class Intent(BaseModel):
    user_id: str
    intent: Dict[str, Any]
    escrow_usd: Optional[float] = 0.0
    auction_duration: Optional[int] = 90
    delivery_mode: Optional[str] = "DFY"  # DIY/DWY/DFY
    funded_by_subscription: Optional[bool] = False  # NEW: Feature #7
    subscription_credits_used: Optional[int] = 0  # NEW: Feature #7

class Bid(BaseModel):
    intent_id: str
    agent: str
    price_usd: float
    delivery_hours: int
    message: Optional[str] = ""

class Settle(BaseModel):
    intent_id: str
    outcome: Dict[str, Any]

class VerifyPoO(BaseModel):
    intent_id: str
    poo_id: str
    approved: bool
    feedback: Optional[str] = ""

async def _lock_escrow(user_id: str, intent_id: str, amount: float):
    """Lock buyer's funds in escrow"""
    escrow_id = f"esc_{uuid4().hex[:8]}"
    
    _ESCROW[escrow_id] = {
        "id": escrow_id,
        "intent_id": intent_id,
        "buyer": user_id,
        "amount": amount,
        "status": "LOCKED",
        "locked_at": now_iso(),
        "released_to": None,
        "released_at": None,
        "events": [{"type": "ESCROW_LOCKED", "at": now_iso()}]
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/budget/spend",
                json={
                    "username": user_id,
                    "amount": amount,
                    "basis": "escrow_lock",
                    "ref": intent_id
                }
            )
            print(f"Locked ${amount} escrow for {user_id}")
        except Exception as e:
            print(f"Escrow lock failed: {e}")
            raise HTTPException(status_code=402, detail="insufficient_funds")
    
    return escrow_id

async def _release_escrow(intent_id: str, recipient: str):
    """Release escrow to winning agent"""
    escrow = next((e for e in _ESCROW.values() if e["intent_id"] == intent_id and e["status"] == "LOCKED"), None)
    
    if not escrow:
        print(f"No locked escrow found for intent {intent_id}")
        return 0.0
    
    amount = escrow["amount"]
    escrow["status"] = "RELEASED"
    escrow["released_to"] = recipient
    escrow["released_at"] = now_iso()
    escrow["events"].append({"type": "ESCROW_RELEASED", "to": recipient, "at": now_iso()})
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                json={
                    "username": recipient,
                    "amount": amount,
                    "basis": "intent_settlement",
                    "ref": intent_id
                }
            )
            print(f"Released ${amount} to {recipient}")
        except Exception as e:
            print(f"Escrow release failed: {e}")
    
    return amount

async def _refund_escrow(intent_id: str, reason: str):
    """Refund escrow to buyer (dispute or expiry)"""
    escrow = next((e for e in _ESCROW.values() if e["intent_id"] == intent_id and e["status"] == "LOCKED"), None)
    
    if not escrow:
        print(f"No locked escrow found for intent {intent_id}")
        return 0.0
    
    amount = escrow["amount"]
    buyer = escrow["buyer"]
    
    escrow["status"] = "REFUNDED"
    escrow["refund_reason"] = reason
    escrow["refunded_at"] = now_iso()
    escrow["events"].append({"type": "ESCROW_REFUNDED", "reason": reason, "at": now_iso()})
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                json={
                    "username": buyer,
                    "amount": amount,
                    "basis": "escrow_refund",
                    "ref": intent_id
                }
            )
            print(f"Refunded ${amount} to {buyer}")
        except Exception as e:
            print(f"Escrow refund failed: {e}")
    
    return amount

async def _auto_award_after_auction(intent_id: str, duration: int):
    await asyncio.sleep(duration)
    it = _INTENTS.get(intent_id)
    if not it or it["status"] != "AUCTION":
        return
    
    bids = _BIDS.get(intent_id, [])
    if not bids:
        it["status"] = "EXPIRED"
        it["events"].append({"type": "INTENT_EXPIRED", "reason": "no_bids", "at": now_iso()})
        await _refund_escrow(intent_id, "no_bids")
        return
    
    def score_bid(bid):
        price_weight = 0.7
        speed_weight = 0.3
        max_price = max(b["price_usd"] for b in bids)
        max_hours = max(b["delivery_hours"] for b in bids)
        
        price_score = 1 - (bid["price_usd"] / max_price if max_price else 0)
        speed_score = 1 - (bid["delivery_hours"] / max_hours if max_hours else 0)
        
        return (price_weight * price_score) + (speed_weight * speed_score)
    
    bids.sort(key=score_bid, reverse=True)
    winner = bids[0]
    
    it["status"] = "AWARDED"
    it["claimed_by"] = winner["agent"]
    it["winning_bid"] = winner
    it["all_bids"] = bids
    it["accepted_at"] = now_iso()  
    it["delivery_hours"] = winner["delivery_hours"]  
    it["price_usd"] = winner["price_usd"]  
    it["events"].append({
        "type": "INTENT_AWARDED",
        "agent": winner["agent"],
        "price": winner["price_usd"],
        "at": now_iso()
    })
    
    #STAKE PERFORMANCE BOND
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            bond_response = await client.post(
                "https://aigentsy-ame-runtime.onrender.com/bond/stake",
                json={
                    "username": winner["agent"],
                    "intent_id": intent_id
                }
            )
            bond_data = bond_response.json()
            
            if bond_data.get("ok"):
                it["bond"] = bond_data
                it["events"].append({
                    "type": "BOND_STAKED",
                    "amount": bond_data.get("bond_amount"),
                    "at": now_iso()
                })
                print(f" Staked {bond_data.get('bond_amount')} AIGx bond for {winner['agent']}")
            else:
                it["bond_warning"] = bond_data.get("error", "insufficient_aigx")
                print(f" Bond stake failed for {winner['agent']}: {bond_data.get('error')}")
    except Exception as e:
        print(f" Bond stake error: {e}")
        it["bond_warning"] = str(e)
    
    await _send_award_proposal(it, winner)


async def _send_award_proposal(intent: Dict, winning_bid: Dict):
    proposal = {
        "id": f"prop_{uuid4().hex[:8]}",
        "sender": winning_bid["agent"],
        "recipient": intent["from"],
        "title": f"Accepted Bid: {intent['intent'].get('brief', 'Your Intent')}",
        "body": f"""Winner: {winning_bid['agent']}
Price: ${winning_bid['price_usd']}
Delivery: {winning_bid['delivery_hours']} hours

Escrow of ${intent.get('escrow_usd', 0)} locked. Will release when you verify Proof of Outcome.""",
        "amount": winning_bid["price_usd"],
        "meta": {"intent_id": intent["id"], "winning_bid": True},
        "status": "sent",
        "timestamp": now_iso(),
        "auto_generated": True
    }
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                json=proposal
            )
        except Exception as e:
            print(f"Failed to send award proposal: {e}")

@router.post("/publish")
async def publish_intent(req: Intent, background_tasks: BackgroundTasks):
    if req.escrow_usd <= 0:
        raise HTTPException(status_code=400, detail="escrow_required: must deposit funds to create intent")
    
    iid = str(uuid4())
    duration = req.auction_duration or 90
    
    try:
        escrow_id = await _lock_escrow(req.user_id, iid, req.escrow_usd)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"escrow_lock_failed: {e}")
    
    payload = {
        "id": iid,
        "from": req.user_id,
        "intent": req.intent or {},
        "status": "AUCTION",
        "auction_ends_at": (datetime.utcnow() + timedelta(seconds=duration)).isoformat() + "Z",
        "events": [{"type": "INTENT_PUBLISHED", "at": now_iso()}],
        "claimed_by": None,
        "winning_bid": None,
        "settlement": None,
        "escrow_usd": float(req.escrow_usd),
        "escrow_id": escrow_id,
        "created_at": now_iso(),
        "poo_verified": False,
        
        # ============================================
        # NEW: DELIVERY MODE
        # ============================================
        "delivery_mode": (req.delivery_mode or "DFY").upper(),
        "mode_info": {
            "mode": (req.delivery_mode or "DFY").upper(),
            "escrow_amount": float(req.escrow_usd),
            "description": _get_mode_description((req.delivery_mode or "DFY").upper())
        },
        
        # ============================================
        # NEW: SUBSCRIPTION FUNDING (Feature #7)
        # ============================================
        "funded_by_subscription": req.funded_by_subscription or False,
        "subscription_credits_used": req.subscription_credits_used or 0
    }
    
    _INTENTS[iid] = payload
    _BIDS[iid] = []
    
    background_tasks.add_task(_auto_award_after_auction, iid, duration)
    
    return {
        "ok": True,
        "intent_id": iid,
        "escrow_id": escrow_id,
        "escrow_usd": payload["escrow_usd"],
        "auction_ends_at": payload["auction_ends_at"],
        "message": f"Escrow locked. Auction started. Auto-award in {duration}s."
    }

@router.post("/bid")
async def bid_on_intent(req: Bid):
    it = _INTENTS.get(req.intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    if it["status"] != "AUCTION":
        raise HTTPException(status_code=400, detail=f"intent status is {it['status']}, not accepting bids")
    
    ends_at = datetime.fromisoformat(it["auction_ends_at"].replace("Z", ""))
    if datetime.utcnow() > ends_at:
        raise HTTPException(status_code=400, detail="auction ended")
    
    bid = {
        "id": f"bid_{uuid4().hex[:8]}",
        "agent": req.agent,
        "price_usd": req.price_usd,
        "delivery_hours": req.delivery_hours,
        "message": req.message or "",
        "submitted_at": now_iso()
    }
    
    _BIDS[req.intent_id].append(bid)
    
    it["events"].append({
        "type": "BID_RECEIVED",
        "agent": req.agent,
        "price": req.price_usd,
        "at": now_iso()
    })
    
    return {
        "ok": True,
        "bid_id": bid["id"],
        "message": "Bid submitted. Winner auto-selected when auction ends."
    }

@router.post("/verify_poo")
async def verify_proof_of_outcome(req: VerifyPoO):
    """Buyer verifies agent's Proof of Outcome, releases escrow, returns bond, awards bonus"""
    it = _INTENTS.get(req.intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    if it["status"] != "AWARDED":
        raise HTTPException(status_code=400, detail=f"cannot verify PoO for intent in status {it['status']}")
    
    if not req.approved:
        # PoO REJECTED - DISPUTE
        it["status"] = "DISPUTED"
        it["poo_verified"] = False
        it["dispute_reason"] = req.feedback or "buyer_rejected_poo"
        it["events"].append({
            "type": "POO_REJECTED",
            "poo_id": req.poo_id,
            "feedback": req.feedback,
            "at": now_iso()
        })
        
        return {
            "ok": False,
            "message": "PoO rejected. Dispute opened. Escrow held pending resolution."
        }
    
    # PoO APPROVED - SETTLE
    it["status"] = "SETTLED"
    it["poo_verified"] = True
    it["poo_id"] = req.poo_id
    it["delivered_at"] = now_iso()  
    it["settlement"] = {"verified": True, "feedback": req.feedback}
    it["events"].append({
        "type": "POO_VERIFIED",
        "poo_id": req.poo_id,
        "at": now_iso()
    })
    
    winner = it.get("claimed_by")
    if not winner:
        raise HTTPException(status_code=500, detail="no_winner_found")
    
    # Release escrow
    released = await _release_escrow(req.intent_id, winner)
    
    # Track revenue and outcomes
    try:
        from revenue_flows import ingest_intent_settlement
        await ingest_intent_settlement(
            username=winner,
            intent_id=req.intent_id,
            amount_usd=released,
            buyer=it.get("from")
        )
        print(f"💰 Tracked ${released} revenue for {winner}")
    except Exception as e:
        print(f"❌ Revenue tracking failed: {e}")
    
    #  RETURN BOND + AWARD SLA BONUS
    bond_result = None
    bonus_result = None
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Return bond
            bond_response = await client.post(
                "https://aigentsy-ame-runtime.onrender.com/bond/return",
                json={
                    "username": winner,
                    "intent_id": req.intent_id
                }
            )
            bond_result = bond_response.json()
            
            if bond_result.get("ok"):
                it["events"].append({
                    "type": "BOND_RETURNED",
                    "amount": bond_result.get("returned"),
                    "at": now_iso()
                })
                print(f" Returned bond to {winner}")
            
            # Award SLA bonus
            bonus_response = await client.post(
                "https://aigentsy-ame-runtime.onrender.com/bond/award_bonus",
                json={
                    "username": winner,
                    "intent_id": req.intent_id
                }
            )
            bonus_result = bonus_response.json()
            
            if bonus_result.get("ok") and bonus_result.get("bonus", 0) > 0:
                it["events"].append({
                    "type": "SLA_BONUS_AWARDED",
                    "amount": bonus_result.get("bonus"),
                    "tier": bonus_result.get("tier"),
                    "at": now_iso()
                })
                print(f" Awarded {bonus_result.get('bonus')} AIGx bonus to {winner}")
    
    except Exception as e:
        print(f" Bond/bonus processing error: {e}")
    
    # R³ reallocation (existing)
    try:
        realloc_budget = round(released * 0.2, 2)
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/r3/allocate",
                json={
                    "user_id": winner,
                    "budget_usd": realloc_budget
                }
            )
            print(f"Auto-reallocated ${realloc_budget} for {winner}")
    except Exception as e:
        print(f"R3 reallocation failed: {e}")
    
    return {
        "ok": True,
        "escrow_released": released,
        "bond_returned": bond_result.get("returned", 0) if bond_result else 0,
        "sla_bonus": bonus_result.get("bonus", 0) if bonus_result else 0,
        "bonus_tier": bonus_result.get("tier") if bonus_result else None,
        "message": f"PoO verified. ${released} released to {winner}."
    }

@router.post("/settle")
async def settle_intent(req: Settle):
    """DEPRECATED: Use /verify_poo instead"""
    it = _INTENTS.get(req.intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    return {
        "ok": False,
        "message": "settle endpoint deprecated. Use /verify_poo to approve agent's Proof of Outcome."
    }

@router.post("/dispute")
async def dispute_intent(intent_id: str, reason: str):
    """Buyer disputes agent's work and triggers manual review"""
    it = _INTENTS.get(intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    it["status"] = "DISPUTED"
    it["dispute_reason"] = reason
    it["events"].append({
        "type": "DISPUTE_OPENED",
        "reason": reason,
        "at": now_iso()
    })
    
    return {
        "ok": True,
        "message": "Dispute opened. Escrow held. Admin will review within 48 hours."
    }

@router.post("/resolve_dispute")
async def resolve_dispute(intent_id: str, resolution: str, refund_pct: float = 0.0):
    """Admin resolves dispute (release to agent, refund to buyer, or split) + slash bond"""
    it = _INTENTS.get(intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    if it["status"] != "DISPUTED":
        raise HTTPException(status_code=400, detail="intent not disputed")
    
    escrow = next((e for e in _ESCROW.values() if e["intent_id"] == intent_id and e["status"] == "LOCKED"), None)
    if not escrow:
        raise HTTPException(status_code=404, detail="escrow not found")
    
    amount = escrow["amount"]
    winner = it.get("claimed_by")
    buyer = it.get("from")
    
    # ✅ SLASH BOND IF AGENT AT FAULT
    slash_result = None
    if refund_pct > 0 and winner:  # Any refund = agent partially/fully at fault
        severity = "major" if refund_pct >= 0.75 else ("moderate" if refund_pct >= 0.25 else "minor")
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                slash_response = await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/bond/slash",
                    json={
                        "username": winner,
                        "intent_id": intent_id,
                        "severity": severity
                    }
                )
                slash_result = slash_response.json()
                
                if slash_result.get("ok"):
                    it["events"].append({
                        "type": "BOND_SLASHED",
                        "amount": slash_result.get("slashed"),
                        "severity": severity,
                        "at": now_iso()
                    })
                    print(f"⚖️ Slashed {slash_result.get('slashed')} AIGx from {winner}")
        except Exception as e:
            print(f"❌ Bond slash error: {e}")
    
    # Existing escrow logic
    if refund_pct == 1.0:
        await _refund_escrow(intent_id, "dispute_resolved_refund")
        it["status"] = "REFUNDED"
    elif refund_pct == 0.0:
        await _release_escrow(intent_id, winner)
        it["status"] = "SETTLED"
    else:
        refund_amt = round(amount * refund_pct, 2)
        release_amt = round(amount * (1 - refund_pct), 2)
        
        escrow["status"] = "SPLIT"
        escrow["events"].append({
            "type": "DISPUTE_RESOLVED_SPLIT",
            "refund_pct": refund_pct,
            "at": now_iso()
        })
        
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                json={
                    "username": buyer,
                    "amount": refund_amt,
                    "basis": "dispute_refund",
                    "ref": intent_id
                }
            )
            
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                json={
                    "username": winner,
                    "amount": release_amt,
                    "basis": "dispute_partial_payment",
                    "ref": intent_id
                }
            )
        
        it["status"] = "RESOLVED_SPLIT"
    
    it["resolution"] = resolution
    it["events"].append({
        "type": "DISPUTE_RESOLVED",
        "resolution": resolution,
        "refund_pct": refund_pct,
        "bond_slashed": slash_result.get("slashed", 0) if slash_result else 0,
        "at": now_iso()
    })
    
    return {
        "ok": True,
        "resolution": resolution,
        "refund_pct": refund_pct,
        "bond_slashed": slash_result.get("slashed", 0) if slash_result else 0
    }
    

@router.get("/list")
async def list_intents(status: Optional[str] = None):
    intents = list(_INTENTS.values())
    
    if status:
        intents = [i for i in intents if i["status"] == status.upper()]
    
    intents.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {"ok": True, "intents": intents, "count": len(intents)}

@router.get("/{intent_id}")
async def get_intent(intent_id: str):
    it = _INTENTS.get(intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    bids = _BIDS.get(intent_id, [])
    escrow = next((e for e in _ESCROW.values() if e["intent_id"] == intent_id), None)
    
    return {
        "ok": True,
        "intent": it,
        "bids": bids,
        "bid_count": len(bids),
        "escrow": escrow
    }


# ============================================================
# DELIVERY MODE HELPERS
# ============================================================

def _get_mode_description(mode: str) -> str:
    """Get human-readable description for delivery mode"""
    descriptions = {
        "DIY": "Do-It-Yourself - Templates, tools, and guidance provided",
        "DWY": "Done-With-You - Collaborative partnership with regular check-ins",
        "DFY": "Done-For-You - Full service delivery, we handle everything"
    }
    return descriptions.get(mode.upper(), "Full service delivery")


@router.post("/{intent_id}/change_mode")
async def change_intent_mode(intent_id: str, new_mode: str, background_tasks: BackgroundTasks):
    """
    Change delivery mode for an intent.
    
    Note: This restarts the auction with new escrow amount.
    Only available before intent is awarded.
    """
    it = _INTENTS.get(intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    if it["status"] not in ["AUCTION"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change mode for intent in status {it['status']}"
        )
    
    # Validate mode
    if new_mode.upper() not in ["DIY", "DWY", "DFY"]:
        raise HTTPException(status_code=400, detail="mode must be DIY, DWY, or DFY")
    
    old_mode = it.get("delivery_mode", "DFY")
    
    # Update mode
    it["delivery_mode"] = new_mode.upper()
    it["mode_info"] = {
        "mode": new_mode.upper(),
        "escrow_amount": it["escrow_usd"],  # Note: Escrow already locked, would need to adjust
        "description": _get_mode_description(new_mode.upper())
    }
    
    it["events"].append({
        "type": "MODE_CHANGED",
        "from_mode": old_mode,
        "to_mode": new_mode.upper(),
        "at": now_iso()
    })
    
    # Clear existing bids (mode change restarts auction)
    _BIDS[intent_id] = []
    
    it["events"].append({
        "type": "BIDS_CLEARED",
        "reason": "mode_change",
        "at": now_iso()
    })
    
    return {
        "ok": True,
        "intent_id": intent_id,
        "old_mode": old_mode,
        "new_mode": new_mode.upper(),
        "bids_cleared": True,
        "message": f"Mode changed from {old_mode} to {new_mode.upper()}. Auction continues with new requirements."
    }

@router.get("/escrow/{intent_id}")
async def get_escrow_status(intent_id: str):
    """Check escrow status for an intent"""
    escrow = next((e for e in _ESCROW.values() if e["intent_id"] == intent_id), None)
    
    if not escrow:
        raise HTTPException(status_code=404, detail="escrow not found")
    
    return {"ok": True, "escrow": escrow}
