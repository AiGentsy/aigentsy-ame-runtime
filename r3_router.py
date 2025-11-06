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

class ChannelPacingReq(BaseModel):
    user_id: str
    channel: str
    performance: Dict[str, float]  # {"roas": 2.5, "cpa": 15.0}

# Historical performance cache (in production, use Redis)
_CHANNEL_PERFORMANCE: Dict[str, Dict[str, float]] = {}

def predict_roi(user: dict, channel: str) -> float:
    """
    Predict ROI based on:
    1. Historical user performance on this channel
    2. Global channel baseline
    3. User traits/capabilities match
    """
    # Get user's historical performance
    user_perf = _CHANNEL_PERFORMANCE.get(f"{user.get('id')}:{channel}", {})
    historical_roas = user_perf.get("roas", 0)
    
    # Channel baselines
    baseline = {
        "tiktok": 1.8,
        "instagram": 1.5,
        "google": 2.0,
        "email": 3.0,
        "sms": 2.5,
        "shopify": 1.2,
        "amazon": 1.1
    }
    
    # Trait boost
    traits = user.get("traits", [])
    boost = 1.0
    if channel in ["tiktok", "instagram"] and "marketing" in traits:
        boost = 1.2
    elif channel == "email" and "marketing" in traits:
        boost = 1.3
    elif channel in ["shopify", "amazon"] and "commerce_in" in (user.get("amg", {}).get("capabilities", [])):
        boost = 1.15
    
    # Weighted average: 60% historical, 40% baseline
    if historical_roas > 0:
        predicted = (0.6 * historical_roas + 0.4 * baseline.get(channel, 1.0)) * boost
    else:
        predicted = baseline.get(channel, 1.0) * boost
    
    return round(predicted, 2)


@router.post("/allocate")
async def allocate(req: AllocateReq):
    """
    Allocate budget across channels based on predicted ROI.
    """
    # Fetch user from main.py
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"https://aigentsy-ame-runtime.onrender.com/users/all")
            users = r.json().get("users", [])
            u = next((x for x in users if x.get("username") == req.user_id), None)
            if not u:
                return {"ok": False, "error": "user_not_found"}
        except Exception as e:
            return {"ok": False, "error": f"failed to fetch user: {e}"}
    
    # Channels to consider
    capabilities = u.get("amg", {}).get("capabilities", [])
    available_channels = ["email", "sms"]  # Always available
    
    if "content_out" in capabilities:
        available_channels.extend(["tiktok", "instagram"])
    if "commerce_in" in capabilities:
        available_channels.extend(["shopify", "amazon"])
    if "ads_budget" in capabilities:
        available_channels.append("google")
    
    # Score each channel
    scored = [(ch, predict_roi(u, ch)) for ch in available_channels]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Allocate budget (80% to best, 20% to runner-up for testing)
    allocations = []
    if len(scored) >= 2:
        best = scored[0]
        runner = scored[1]
        allocations = [
            {"channel": best[0], "usd": round(req.budget_usd * 0.8, 2), "predicted_roi": best[1]},
            {"channel": runner[0], "usd": round(req.budget_usd * 0.2, 2), "predicted_roi": runner[1]}
        ]
    elif len(scored) == 1:
        allocations = [
            {"channel": scored[0][0], "usd": req.budget_usd, "predicted_roi": scored[0][1]}
        ]
    
    # Emit allocation events for Outcome Oracle
    for alloc in allocations:
        publish("R3_ALLOCATED", {
            "user": req.user_id,
            "channel": alloc["channel"],
            "usd": alloc["usd"]
        })
    
    return {
        "ok": True,
        "user": req.user_id,
        "allocations": allocations,
        "total_budget": req.budget_usd
    }


@router.post("/pacing/update")
async def update_pacing(req: ChannelPacingReq):
    """
    Update historical performance for a user+channel.
    Called by Outcome Oracle when revenue is attributed.
    """
    key = f"{req.user_id}:{req.channel}"
    _CHANNEL_PERFORMANCE[key] = req.performance
    
    return {"ok": True, "updated": key, "performance": req.performance}


@router.get("/performance/{user_id}")
async def get_performance(user_id: str):
    """
    Get all channel performance for a user.
    """
    user_perf = {k.split(":")[1]: v for k, v in _CHANNEL_PERFORMANCE.items() if k.startswith(f"{user_id}:")}
    return {"ok": True, "user": user_id, "channels": user_perf}
