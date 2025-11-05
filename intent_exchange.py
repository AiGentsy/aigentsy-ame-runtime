from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime, timedelta
import asyncio
import httpx

try:
    from .jsonbin_client import JSONBinClient
except Exception:
    JSONBinClient = None

try:
    from .event_bus import publish
except Exception:
    def publish(*a, **k): pass

router = APIRouter()

# In-memory storage (replace with Redis/DB for production)
_INTENTS: Dict[str, Dict[str, Any]] = {}
_BIDS: Dict[str, List[Dict[str, Any]]] = {}  # intent_id -> [bids]

def now_iso():
    return datetime.utcnow().isoformat() + "Z"


class Intent(BaseModel):
    user_id: str
    intent: Dict[str, Any]
    escrow_usd: Optional[float] = 0.0
    auction_duration: Optional[int] = 90  # seconds


class Bid(BaseModel):
    intent_id: str
    agent: str
    price_usd: float
    delivery_hours: int
    message: Optional[str] = ""


class Settle(BaseModel):
    intent_id: str
    outcome: Dict[str, Any]


async def _auto_award_after_auction(intent_id: str, duration: int):
    """
    Background task: Wait {duration} seconds, then auto-award to best bid.
    """
    await asyncio.sleep(duration)
    
    it = _INTENTS.get(intent_id)
    if not it or it["status"] != "AUCTION":
        return  # Already claimed/settled
    
    bids = _BIDS.get(intent_id, [])
    if not bids:
        # No bids received, mark as expired
        it["status"] = "EXPIRED"
        it["events"].append({"type": "INTENT_EXPIRED", "reason": "no_bids", "at": now_iso()})
        publish("INTENT_EXPIRED", {"id": intent_id, "reason": "no_bids"})
        return
    
    # Scoring: Lower price = better, faster delivery = better
    def score_bid(bid):
        price_weight = 0.7
        speed_weight = 0.3
        max_price = max(b["price_usd"] for b in bids)
        max_hours = max(b["delivery_hours"] for b in bids)
        
        price_score = 1 - (bid["price_usd"] / max_price if max_price else 0)
        speed_score = 1 - (bid["delivery_hours"] / max_hours if max_hours else 0)
        
        return (price_weight * price_score) + (speed_weight * speed_score)
    
    # Sort bids by score (highest = best)
    bids.sort(key=score_bid, reverse=True)
    winner = bids[0]
    
    # Award to winner
    it["status"] = "AWARDED"
    it["claimed_by"] = winner["agent"]
    it["winning_bid"] = winner
    it["all_bids"] = bids
    it["events"].append({
        "type": "INTENT_AWARDED",
        "agent": winner["agent"],
        "price": winner["price_usd"],
        "at": now_iso()
    })
    
    publish("INTENT_AWARDED", {
        "id": intent_id,
        "agent": winner["agent"],
        "price": winner["price_usd"],
        "delivery_hours": winner["delivery_hours"]
    })
    
    # Send proposal to original user
    await _send_award_proposal(it, winner)


async def _send_award_proposal(intent: Dict, winning_bid: Dict):
    """
    Auto-generate proposal from winner to buyer.
    """
    proposal = {
        "id": f"prop_{uuid4().hex[:8]}",
        "sender": winning_bid["agent"],
        "recipient": intent["from"],
        "title": f"Accepted Bid: {intent['intent'].get('brief', 'Your Intent')}",
        "body": f"""Your intent has been matched!

**Winner:** {winning_bid['agent']}
**Price:** ${winning_bid['price_usd']}
**Delivery:** {winning_bid['delivery_hours']} hours
**Message:** {winning_bid.get('message', 'Ready to start immediately.')}

Escrow of ${intent.get('escrow_usd', 0)} has been locked. Once delivered, you can approve to release payment.""",
        "amount": winning_bid["price_usd"],
        "meta": {
            "intent_id": intent["id"],
            "winning_bid": True
        },
        "status": "sent",
        "timestamp": now_iso(),
        "auto_generated": True
    }
    
    # Send to main.py
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "http://localhost:8000/submit_proposal",
                json=proposal
            )
        except Exception as e:
            print(f"Failed to send award proposal: {e}")


@router.post("/publish")
async def publish_intent(req: Intent, background_tasks: BackgroundTasks):
    """
    Publish intent + start 90-second auction.
    """
    iid = str(uuid4())
    duration = req.auction_duration or 90
    
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
        "escrow_usd": float(req.escrow_usd or 0.0),
        "created_at": now_iso()
    }
    
    _INTENTS[iid] = payload
    _BIDS[iid] = []
    
    # Start auction timer in background
    background_tasks.add_task(_auto_award_after_auction, iid, duration)
    
    publish("INTENT_PUBLISHED", {
        "id": iid,
        "user_id": req.user_id,
        "escrow_usd": payload["escrow_usd"],
        "auction_duration": duration
    })
    
    # Mirror to JSONBin
    if JSONBinClient:
        try:
            jb = JSONBinClient()
            data = jb.get_latest().get("record") or {}
            intents = data.setdefault("intents", [])
            intents.append({
                "id": iid,
                "from": req.user_id,
                "status": "AUCTION",
                "body": req.intent,
                "escrow_usd": payload["escrow_usd"]
            })
            jb.put_record(data)
        except Exception:
            pass
    
    return {
        "ok": True,
        "intent_id": iid,
        "escrow_usd": payload["escrow_usd"],
        "auction_ends_at": payload["auction_ends_at"],
        "message": f"Auction started. Auto-award in {duration}s."
    }


@router.post("/bid")
async def bid_on_intent(req: Bid):
    """
    Submit bid during auction window.
    """
    it = _INTENTS.get(req.intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    if it["status"] != "AUCTION":
        raise HTTPException(status_code=400, detail=f"intent status is {it['status']}, not accepting bids")
    
    # Check if auction expired
    ends_at = datetime.fromisoformat(it["auction_ends_at"].replace("Z", ""))
    if datetime.utcnow() > ends_at:
        raise HTTPException(status_code=400, detail="auction ended")
    
    # Add bid
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
    
    publish("INTENT_BID", {
        "intent_id": req.intent_id,
        "agent": req.agent,
        "price": req.price_usd
    })
    
    return {
        "ok": True,
        "bid_id": bid["id"],
        "message": "Bid submitted. Winner will be auto-selected when auction ends."
    }


@router.post("/settle")
async def settle_intent(req: Settle):
    """
    Buyer approves delivery, releases escrow.
    """
    it = _INTENTS.get(req.intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    if it["status"] not in ["AWARDED", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail=f"cannot settle intent in status {it['status']}")
    
    it["status"] = "SETTLED"
    it["settlement"] = req.outcome or {}
    it["events"].append({
        "type": "INTENT_SETTLED",
        "outcome": req.outcome,
        "at": now_iso()
    })
    
    publish("INTENT_SETTLED", {
        "id": req.intent_id,
        "outcome": req.outcome
    })
    
    # Release escrow to winner
    escrow = float(it.get("escrow_usd") or 0.0)
    if escrow > 0 and it.get("claimed_by"):
        publish("PAID_ESCROW", {
            "intent_id": req.intent_id,
            "amount_usd": escrow,
            "recipient": it["claimed_by"]
        })
        
        # Credit winner via main.py
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    "http://localhost:8000/aigx/credit",
                    json={
                        "username": it["claimed_by"],
                        "amount": escrow,
                        "basis": "intent_settlement",
                        "ref": req.intent_id
                    }
                )
            except Exception as e:
                print(f"Failed to credit winner: {e}")
    
    return {"ok": True, "escrow_released": escrow}


@router.get("/list")
async def list_intents(status: Optional[str] = None):
    """
    List all intents (filterable by status).
    """
    intents = list(_INTENTS.values())
    
    if status:
        intents = [i for i in intents if i["status"] == status.upper()]
    
    # Sort by created_at desc
    intents.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {"ok": True, "intents": intents, "count": len(intents)}


@router.get("/{intent_id}")
async def get_intent(intent_id: str):
    """
    Get intent details including all bids.
    """
    it = _INTENTS.get(intent_id)
    if not it:
        raise HTTPException(status_code=404, detail="intent not found")
    
    bids = _BIDS.get(intent_id, [])
    
    return {
        "ok": True,
        "intent": it,
        "bids": bids,
        "bid_count": len(bids)
    }
