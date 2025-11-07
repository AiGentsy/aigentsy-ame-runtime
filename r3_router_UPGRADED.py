from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
import httpx

try:
    from event_bus import publish
except Exception:
    def publish(*a, **k): pass

router = APIRouter()

class AllocateReq(BaseModel):
    user_id: str
    budget_usd: float

_CHANNEL_PERFORMANCE: Dict[str, Dict[str, float]] = {}
_REFERRAL_TREE: Dict[str, Dict[str, Any]] = {}

REFERRAL_RATES = {
    1: 0.05,   # Level 1: 5%
    2: 0.01,   # Level 2: 1%
    3: 0.002   # Level 3: 0.2%
}

def predict_roi(user: dict, channel: str) -> float:
    """Predict ROI based on historical + baseline + traits"""
    user_id = user.get("id") or user.get("username")
    user_perf = _CHANNEL_PERFORMANCE.get(f"{user_id}:{channel}", {})
    historical_roas = user_perf.get("roas", 0)
    
    baseline = {
        "tiktok": 1.8, "instagram": 1.5, "google": 2.0,
        "email": 3.0, "sms": 2.5, "shopify": 1.2, "amazon": 1.1
    }
    
    traits = user.get("traits", [])
    capabilities = user.get("amg", {}).get("capabilities", [])
    boost = 1.0
    
    if channel in ["tiktok", "instagram"] and "marketing" in traits:
        boost = 1.2
    elif channel == "email" and "marketing" in traits:
        boost = 1.3
    elif channel in ["shopify", "amazon"] and "commerce_in" in capabilities:
        boost = 1.15
    
    if historical_roas > 0:
        predicted = (0.6 * historical_roas + 0.4 * baseline.get(channel, 1.0)) * boost
    else:
        predicted = baseline.get(channel, 1.0) * boost
    
    return round(predicted, 2)


async def get_referral_chain(user_id: str) -> List[Dict[str, Any]]:
    """Get 3-level referral chain for a user"""
    chain = []
    
    # Get user data
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(
                "https://aigentsy-ame-runtime.onrender.com/user",
                json={"username": user_id}
            )
            user = r.json().get("record", {})
        except Exception:
            return chain
    
    # Parse referral string (e.g., "origin/hero" or "user1/user2/user3")
    referral = user.get("referral", "")
    if not referral or referral == "origin/hero":
        return chain
    
    # Build chain from referral path
    parts = referral.split("/")
    for level, referrer in enumerate(parts[:3], start=1):
        if referrer and referrer not in ["origin", "hero"]:
            chain.append({
                "level": level,
                "referrer": referrer,
                "rate": REFERRAL_RATES.get(level, 0)
            })
    
    return chain


async def distribute_referral_bonus(user_id: str, amount_usd: float):
    """Distribute referral bonuses up the chain (3 levels)"""
    chain = await get_referral_chain(user_id)
    
    if not chain:
        return {"ok": True, "distributed": []}
    
    distributions = []
    
    async with httpx.AsyncClient(timeout=10) as client:
        for entry in chain:
            bonus = round(amount_usd * entry["rate"], 2)
            
            try:
                # Credit referrer
                await client.post(
                    "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                    json={
                        "username": entry["referrer"],
                        "amount": bonus,
                        "basis": f"referral_L{entry['level']}",
                        "ref": user_id
                    }
                )
                
                distributions.append({
                    "level": entry["level"],
                    "referrer": entry["referrer"],
                    "bonus": bonus
                })
                
                publish("REFERRAL_BONUS", {
                    "referrer": entry["referrer"],
                    "referred": user_id,
                    "level": entry["level"],
                    "bonus_usd": bonus
                })
                
            except Exception as e:
                print(f"Failed to credit L{entry['level']} referrer {entry['referrer']}: {e}")
    
    return {"ok": True, "distributed": distributions}


@router.post("/allocate")
async def allocate(req: AllocateReq):
    """Allocate budget across channels by predicted ROI + trigger referral bonuses"""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"https://aigentsy-ame-runtime.onrender.com/users/all")
            users = r.json().get("users", [])
            u = next((x for x in users if x.get("username") == req.user_id), None)
            if not u:
                return {"ok": False, "error": "user_not_found"}
        except Exception as e:
            return {"ok": False, "error": f"failed to fetch user: {e}"}
    
    capabilities = u.get("amg", {}).get("capabilities", [])
    available_channels = ["email", "sms"]
    
    if "content_out" in capabilities:
        available_channels.extend(["tiktok", "instagram"])
    if "commerce_in" in capabilities:
        available_channels.extend(["shopify", "amazon"])
    if "ads_budget" in capabilities:
        available_channels.append("google")
    
    scored = [(ch, predict_roi(u, ch)) for ch in available_channels]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    allocations = []
    if len(scored) >= 2:
        allocations = [
            {"channel": scored[0][0], "usd": round(req.budget_usd * 0.8, 2), "predicted_roi": scored[0][1]},
            {"channel": scored[1][0], "usd": round(req.budget_usd * 0.2, 2), "predicted_roi": scored[1][1]}
        ]
    elif len(scored) == 1:
        allocations = [{"channel": scored[0][0], "usd": req.budget_usd, "predicted_roi": scored[0][1]}]
    
    for alloc in allocations:
        publish("R3_ALLOCATED", {"user": req.user_id, "channel": alloc["channel"], "usd": alloc["usd"]})
    
    # Trigger referral bonuses (3 levels)
    referral_result = await distribute_referral_bonus(req.user_id, req.budget_usd)
    
    return {
        "ok": True,
        "user": req.user_id,
        "allocations": allocations,
        "total_budget": req.budget_usd,
        "referral_bonuses": referral_result.get("distributed", [])
    }


@router.post("/pacing/update")
async def update_pacing(user_id: str, channel: str, performance: Dict[str, float]):
    """Update historical performance"""
    key = f"{user_id}:{channel}"
    _CHANNEL_PERFORMANCE[key] = performance
    return {"ok": True, "updated": key}


@router.get("/performance/{user_id}")
async def get_performance(user_id: str):
    """Get all channel performance"""
    user_perf = {k.split(":")[1]: v for k, v in _CHANNEL_PERFORMANCE.items() if k.startswith(f"{user_id}:")}
    return {"ok": True, "user": user_id, "channels": user_perf}


@router.get("/referrals/{user_id}")
async def get_referrals(user_id: str):
    """Get user's referral chain"""
    chain = await get_referral_chain(user_id)
    return {"ok": True, "user": user_id, "chain": chain}


@router.post("/referrals/register")
async def register_referral(referred: str, referrer: str):
    """Register a referral relationship (builds chain automatically)"""
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            # Get referrer's chain
            referrer_resp = await client.post(
                "https://aigentsy-ame-runtime.onrender.com/user",
                json={"username": referrer}
            )
            referrer_user = referrer_resp.json().get("record", {})
            referrer_chain = referrer_user.get("referral", "")
            
            # Build new chain (append referred to referrer's chain)
            if referrer_chain and referrer_chain != "origin/hero":
                # Limit to 3 levels
                parts = referrer_chain.split("/")[:2]
                new_chain = "/".join([referrer] + parts)
            else:
                new_chain = referrer
            
            # Update referred user
            referred_resp = await client.post(
                "https://aigentsy-ame-runtime.onrender.com/user",
                json={"username": referred}
            )
            referred_user = referred_resp.json().get("record", {})
            referred_user["referral"] = new_chain
            
            # Save (would need update endpoint in main.py)
            
            return {
                "ok": True,
                "referred": referred,
                "referral_chain": new_chain,
                "levels": len(new_chain.split("/"))
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
