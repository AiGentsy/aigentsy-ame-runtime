from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime, timezone
import httpx

router = APIRouter()

_state = {
    "pool_usd": 0.0,
    "sponsors": [],
    "campaigns": [],
    "allocations": []
}

class SponsorAdd(BaseModel):
    name: str
    spend_cap_usd: float
    target_audience: Optional[Dict[str, Any]] = None
    target_channels: Optional[List[str]] = None

class MatchSponsorsReq(BaseModel):
    agent: str


def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


@router.post("/sponsor")
def sponsor_add(req: SponsorAdd):
    """Add sponsor to co-op pool"""
    sponsor_id = f"sponsor_{uuid4().hex[:8]}"
    
    sponsor = {
        "id": sponsor_id,
        "name": req.name,
        "cap": req.spend_cap_usd,
        "spent": 0.0,
        "remaining": req.spend_cap_usd,
        "target_audience": req.target_audience or {},
        "target_channels": req.target_channels or ["tiktok", "instagram", "email"],
        "campaigns": [],
        "created_at": now_iso()
    }
    
    _state["sponsors"].append(sponsor)
    _state["pool_usd"] = float(_state.get("pool_usd", 0)) + float(req.spend_cap_usd)
    
    return {
        "ok": True,
        "sponsor_id": sponsor_id,
        "pool_usd": _state["pool_usd"],
        "sponsors": len(_state["sponsors"])
    }


@router.post("/match")
async def match_sponsors(req: MatchSponsorsReq):
    """Match agent with relevant sponsors"""
    
    # Get agent data
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(
                "https://aigentsy-ame-runtime.onrender.com/user",
                json={"username": req.agent}
            )
            agent_data = r.json().get("record", {})
        except Exception:
            return {"ok": False, "error": "agent_not_found"}
    
    agent_traits = set(agent_data.get("traits", []))
    agent_capabilities = set(agent_data.get("amg", {}).get("capabilities", []))
    
    # Score each sponsor
    matches = []
    for sponsor in _state["sponsors"]:
        if sponsor["remaining"] <= 0:
            continue
        
        score = 0.0
        match_reasons = []
        
        # Channel match (40% weight)
        target_channels = set(sponsor.get("target_channels", []))
        if "content_out" in agent_capabilities and target_channels & {"tiktok", "instagram", "youtube"}:
            score += 0.4
            match_reasons.append("Social media content capability")
        
        if "email_out" in agent_capabilities and "email" in target_channels:
            score += 0.4
            match_reasons.append("Email marketing capability")
        
        # Audience match (40% weight)
        target_audience = sponsor.get("target_audience", {})
        target_traits = set(target_audience.get("traits", []))
        
        if target_traits & agent_traits:
            overlap = len(target_traits & agent_traits) / len(target_traits) if target_traits else 0
            score += 0.4 * overlap
            match_reasons.append(f"Audience overlap: {list(target_traits & agent_traits)}")
        
        # Budget availability (20% weight)
        if sponsor["remaining"] >= 100:
            score += 0.2
            match_reasons.append("Strong budget availability")
        elif sponsor["remaining"] >= 50:
            score += 0.1
        
        if score > 0.3:
            matches.append({
                "sponsor": sponsor["name"],
                "sponsor_id": sponsor["id"],
                "match_score": round(score, 2),
                "available_budget": round(sponsor["remaining"], 2),
                "match_reasons": match_reasons
            })
    
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {
        "ok": True,
        "agent": req.agent,
        "matches": matches,
        "count": len(matches)
    }


@router.post("/allocate")
async def allocate_sponsor_budget(
    agent: str,
    sponsor_id: str,
    campaign_type: str,
    requested_amount: float
):
    """Allocate sponsor budget to agent campaign"""
    
    sponsor = next((s for s in _state["sponsors"] if s["id"] == sponsor_id), None)
    
    if not sponsor:
        return {"ok": False, "error": "sponsor_not_found"}
    
    if sponsor["remaining"] < requested_amount:
        return {
            "ok": False,
            "error": "insufficient_budget",
            "available": sponsor["remaining"],
            "requested": requested_amount
        }
    
    allocation_id = f"alloc_{uuid4().hex[:8]}"
    
    allocation = {
        "id": allocation_id,
        "sponsor_id": sponsor_id,
        "sponsor_name": sponsor["name"],
        "agent": agent,
        "campaign_type": campaign_type,
        "amount": requested_amount,
        "status": "ACTIVE",
        "created_at": now_iso(),
        "metrics": {
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "revenue": 0.0
        }
    }
    
    # Update sponsor
    sponsor["remaining"] -= requested_amount
    sponsor["spent"] += requested_amount
    sponsor["campaigns"].append(allocation_id)
    
    # Track allocation
    _state["allocations"].append(allocation)
    
    # Credit agent
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/aigx/credit",
                json={
                    "username": agent,
                    "amount": requested_amount,
                    "basis": "coop_sponsor",
                    "ref": allocation_id
                }
            )
        except Exception as e:
            print(f"Failed to credit agent: {e}")
    
    return {
        "ok": True,
        "allocation_id": allocation_id,
        "allocation": allocation
    }


@router.post("/report_results")
def report_campaign_results(
    allocation_id: str,
    impressions: int = 0,
    clicks: int = 0,
    conversions: int = 0,
    revenue: float = 0.0
):
    """Report campaign results for sponsor ROI"""
    
    allocation = next((a for a in _state["allocations"] if a["id"] == allocation_id), None)
    
    if not allocation:
        return {"ok": False, "error": "allocation_not_found"}
    
    # Update metrics
    allocation["metrics"]["impressions"] += impressions
    allocation["metrics"]["clicks"] += clicks
    allocation["metrics"]["conversions"] += conversions
    allocation["metrics"]["revenue"] += revenue
    
    # Calculate ROI
    spent = allocation["amount"]
    roi = (revenue / spent) if spent > 0 else 0
    ctr = (clicks / impressions) if impressions > 0 else 0
    conversion_rate = (conversions / clicks) if clicks > 0 else 0
    
    return {
        "ok": True,
        "allocation_id": allocation_id,
        "metrics": allocation["metrics"],
        "performance": {
            "roi": round(roi, 2),
            "ctr": round(ctr * 100, 2),
            "conversion_rate": round(conversion_rate * 100, 2),
            "cpa": round(spent / conversions, 2) if conversions > 0 else 0
        }
    }


@router.get("/sponsor/{sponsor_id}/roi")
def get_sponsor_roi(sponsor_id: str):
    """Get sponsor ROI dashboard"""
    
    sponsor = next((s for s in _state["sponsors"] if s["id"] == sponsor_id), None)
    
    if not sponsor:
        return {"ok": False, "error": "sponsor_not_found"}
    
    # Aggregate all campaigns
    sponsor_allocations = [a for a in _state["allocations"] if a["sponsor_id"] == sponsor_id]
    
    total_impressions = sum(a["metrics"]["impressions"] for a in sponsor_allocations)
    total_clicks = sum(a["metrics"]["clicks"] for a in sponsor_allocations)
    total_conversions = sum(a["metrics"]["conversions"] for a in sponsor_allocations)
    total_revenue = sum(a["metrics"]["revenue"] for a in sponsor_allocations)
    
    roi = (total_revenue / sponsor["spent"]) if sponsor["spent"] > 0 else 0
    
    return {
        "ok": True,
        "sponsor": sponsor["name"],
        "budget": {
            "total": sponsor["cap"],
            "spent": sponsor["spent"],
            "remaining": sponsor["remaining"]
        },
        "performance": {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_revenue": round(total_revenue, 2),
            "roi": round(roi, 2),
            "roas": round(roi, 2)
        },
        "campaigns": len(sponsor_allocations),
        "top_campaigns": sorted(
            sponsor_allocations,
            key=lambda a: a["metrics"]["revenue"],
            reverse=True
        )[:5]
    }


def state():
    return _state
