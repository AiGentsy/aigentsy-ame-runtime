"""
Opportunity Approval System
Connects opportunities → deals → pitches → revenue

Flow:
1. User approves opportunity
2. Create deal in DealGraph
3. Generate AME pitch
4. Queue for delivery
5. Track outcome
"""

from typing import Dict, Any
from datetime import datetime, timezone
from log_to_jsonbin import get_user, log_agent_update
from dealgraph import create_deal
from ame_pitches import generate_pitch
import json


async def approve_opportunity(username: str, opportunity_id: str) -> Dict[str, Any]:
    """
    Approve an opportunity and create a deal
    
    Steps:
    1. Find and validate opportunity
    2. Create deal in DealGraph
    3. Generate AME pitch
    4. Update opportunity status
    5. Return deal details
    
    Args:
        username: User approving the opportunity
        opportunity_id: ID of opportunity to approve
        
    Returns:
        dict: Result with deal_id, pitch_id, and next steps
    """
    
    print(f"\n{'='*70}")
    print(f"🎯 OPPORTUNITY APPROVAL")
    print(f"   User: {username}")
    print(f"   Opportunity: {opportunity_id}")
    print(f"{'='*70}\n")
    
    # ============================================================
    # STEP 1: VALIDATE OPPORTUNITY
    # ============================================================
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "User not found"}
    
    # Find the opportunity
    opportunities = user.get("opportunities", [])
    opportunity = None
    opp_index = None
    
    for idx, opp in enumerate(opportunities):
        if opp.get("id") == opportunity_id:
            opportunity = opp
            opp_index = idx
            break
    
    if not opportunity:
        return {"ok": False, "error": "Opportunity not found"}
    
    # Check if already approved
    if opportunity.get("status") == "approved":
        return {"ok": False, "error": "Opportunity already approved"}
    
    print(f"✅ Found opportunity: {opportunity.get('title')}")
    print(f"   Value: ${opportunity.get('estimated_value'):,}")
    print(f"   Type: {opportunity.get('type')}")
    
    # ============================================================
    # STEP 2: CREATE DEAL IN DEALGRAPH
    # ============================================================
    
    print(f"\n💼 Creating deal in DealGraph...")
    
    # Build intent from opportunity
    intent = {
        "id": f"intent_{opportunity_id}",
        "buyer": username,  # User is buying the opportunity (investing time/resources)
        "service": opportunity.get("title"),
        "description": opportunity.get("description"),
        "budget": opportunity.get("estimated_value"),
        "source": "opportunity_approval",
        "opportunity_id": opportunity_id
    }
    
    # Create deal
    deal_result = create_deal(
        intent=intent,
        agent_username=username,
        slo_tier="standard"
    )
    
    if not deal_result.get("ok"):
        return {
            "ok": False,
            "error": f"Failed to create deal: {deal_result.get('error')}"
        }
    
    deal = deal_result["deal"]
    deal_id = deal["id"]
    
    print(f"✅ Deal created: {deal_id}")
    print(f"   Job value: ${deal['job_value']:,}")
    print(f"   Revenue split: {json.dumps(deal['revenue_split_summary'], indent=2)}")
    
    # ============================================================
    # STEP 3: GENERATE AME PITCH
    # ============================================================
    
    print(f"\n📧 Generating AME pitch...")
    
    # Build pitch context from opportunity
    pitch_context = {
        "opportunity": opportunity,
        "deal_id": deal_id,
        "user": {
            "username": username,
            "company_type": user.get("companyType"),
            "kits": user.get("kits", {}),
            "template": user.get("template")
        }
    }
    
    # Generate pitch using AME
    try:
        pitch_result = generate_pitch(
            target_type=opportunity.get("type"),
            target_info={
                "segment": opportunity.get("target_customers"),
                "value_proposition": opportunity.get("description"),
                "pricing": opportunity.get("pricing")
            },
            service_description=opportunity.get("title"),
            pricing=opportunity.get("pricing"),
            agent_username=username,
            deal_id=deal_id
        )
        
        if pitch_result.get("ok"):
            pitch_id = pitch_result.get("pitch_id")
            print(f"✅ Pitch generated: {pitch_id}")
            print(f"   Status: {pitch_result.get('status')}")
        else:
            print(f"⚠️  Pitch generation failed: {pitch_result.get('error')}")
            pitch_id = None
            
    except Exception as pitch_error:
        print(f"⚠️  Pitch generation error: {pitch_error}")
        pitch_id = None
        pitch_result = {"ok": False, "error": str(pitch_error)}
    
    # ============================================================
    # STEP 4: UPDATE OPPORTUNITY STATUS
    # ============================================================
    
    print(f"\n💾 Updating opportunity status...")
    
    # Update opportunity in user record
    opportunities[opp_index]["status"] = "approved"
    opportunities[opp_index]["approved_at"] = datetime.now(timezone.utc).isoformat()
    opportunities[opp_index]["deal_id"] = deal_id
    opportunities[opp_index]["pitch_id"] = pitch_id
    
    # Save updated user
    user["opportunities"] = opportunities
    log_agent_update(user)
    
    print(f"✅ Opportunity status updated: pending → approved")
    
    # ============================================================
    # STEP 5: DETERMINE NEXT STEPS
    # ============================================================
    
    next_steps = []
    
    if pitch_id:
        next_steps.append({
            "action": "review_pitch",
            "description": "Review and approve the generated pitch",
            "endpoint": f"/ame/queue"
        })
        next_steps.append({
            "action": "send_pitch",
            "description": "Pitch will be sent to targets after approval",
            "endpoint": f"/ame/approve/{pitch_id}"
        })
    else:
        next_steps.append({
            "action": "manual_outreach",
            "description": "Pitch generation failed - reach out manually",
            "targets": opportunity.get("target_customers")
        })
    
    next_steps.append({
        "action": "track_deal",
        "description": "Monitor deal progress",
        "endpoint": f"/deals/{deal_id}"
    })
    
    # ============================================================
    # RETURN SUCCESS
    # ============================================================
    
    return {
        "ok": True,
        "message": f"Opportunity approved! Deal {deal_id} created.",
        "opportunity_id": opportunity_id,
        "deal_id": deal_id,
        "pitch_id": pitch_id,
        "deal": {
            "id": deal_id,
            "value": deal["job_value"],
            "state": deal["state"],
            "revenue_split": deal["revenue_split_summary"]
        },
        "pitch": {
            "id": pitch_id,
            "generated": pitch_result.get("ok"),
            "status": pitch_result.get("status"),
            "queue_position": pitch_result.get("queue_position") if pitch_result.get("ok") else None
        },
        "next_steps": next_steps,
        "tracking": {
            "opportunity_status": "approved",
            "deal_state": deal["state"],
            "pitch_status": pitch_result.get("status") if pitch_result.get("ok") else "not_generated"
        }
    }


async def get_opportunity_status(username: str, opportunity_id: str) -> Dict[str, Any]:
    """
    Get current status of an opportunity including deal and pitch progress
    
    Args:
        username: User who owns the opportunity
        opportunity_id: ID of opportunity
        
    Returns:
        dict: Complete status including deal and pitch tracking
    """
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "User not found"}
    
    # Find opportunity
    opportunities = user.get("opportunities", [])
    opportunity = None
    
    for opp in opportunities:
        if opp.get("id") == opportunity_id:
            opportunity = opp
            break
    
    if not opportunity:
        return {"ok": False, "error": "Opportunity not found"}
    
    # Build status response
    status = {
        "ok": True,
        "opportunity": {
            "id": opportunity.get("id"),
            "title": opportunity.get("title"),
            "status": opportunity.get("status"),
            "estimated_value": opportunity.get("estimated_value"),
            "created_at": opportunity.get("created_at"),
            "approved_at": opportunity.get("approved_at")
        }
    }
    
    # Add deal info if exists
    deal_id = opportunity.get("deal_id")
    if deal_id:
        status["deal"] = {
            "id": deal_id,
            "state": "PROPOSED",  # Would query DealGraph in full implementation
            "view_url": f"/deals/{deal_id}"
        }
    
    # Add pitch info if exists
    pitch_id = opportunity.get("pitch_id")
    if pitch_id:
        status["pitch"] = {
            "id": pitch_id,
            "status": "pending_approval",  # Would query AME in full implementation
            "view_url": f"/ame/queue"
        }
    
    return status


def list_user_opportunities(username: str, status_filter: str = None) -> Dict[str, Any]:
    """
    List all opportunities for a user with optional status filter
    
    Args:
        username: User to get opportunities for
        status_filter: Optional filter ("pending", "approved", "completed")
        
    Returns:
        dict: List of opportunities with summary stats
    """
    
    user = get_user(username)
    if not user:
        return {"ok": False, "error": "User not found"}
    
    opportunities = user.get("opportunities", [])
    
    # Apply filter if specified
    if status_filter:
        opportunities = [
            opp for opp in opportunities 
            if opp.get("status") == status_filter
        ]
    
    # Calculate summary stats
    total_value = sum(opp.get("estimated_value", 0) for opp in opportunities)
    by_status = {}
    by_urgency = {}
    
    for opp in opportunities:
        status = opp.get("status", "pending")
        urgency = opp.get("urgency", "low")
        
        by_status[status] = by_status.get(status, 0) + 1
        by_urgency[urgency] = by_urgency.get(urgency, 0) + 1
    
    return {
        "ok": True,
        "opportunities": opportunities,
        "summary": {
            "total_count": len(opportunities),
            "total_value": total_value,
            "by_status": by_status,
            "by_urgency": by_urgency
        }
    }


# ============================================================
# FASTAPI ENDPOINT HELPERS
# ============================================================

def create_opportunity_endpoints(app):
    """
    Add opportunity endpoints to FastAPI app
    
    Usage in main.py:
        from opportunity_approval import create_opportunity_endpoints
        create_opportunity_endpoints(app)
    """
    
    @app.post("/opportunities/{opportunity_id}/approve")
    async def api_approve_opportunity(opportunity_id: str, body: dict):
        """Approve an opportunity and create deal + pitch"""
        username = body.get("username")
        if not username:
            return {"ok": False, "error": "username required"}
        
        return await approve_opportunity(username, opportunity_id)
    
    
    @app.get("/opportunities/{opportunity_id}/status")
    async def api_opportunity_status(opportunity_id: str, username: str):
        """Get status of an opportunity"""
        return await get_opportunity_status(username, opportunity_id)
    
    
    @app.get("/opportunities")
    async def api_list_opportunities(username: str, status: str = None):
        """List user's opportunities with optional status filter"""
        return list_user_opportunities(username, status)
