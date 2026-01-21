"""
AIGENTSY FABRIC API ROUTES
==========================

Exposes the unified AiGentsy Fabric to the REST API.
"""

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger("aigentsy_fabric_routes")

router = APIRouter(prefix="/fabric-unified", tags=["aigentsy-fabric"])


# ============================================================================
# SMART EXECUTION ENDPOINTS
# ============================================================================

@router.post("/execute")
async def smart_execute(body: Dict[str, Any] = Body(...)):
    """
    Smart execution with AI enhancement and COI fulfillment.

    Request body:
    - outcome_type: Type of outcome (send_email, send_sms, etc.)
    - params: Parameters for the outcome
    - use_ai: Whether to use AI enhancement (default: true)
    - ai_task_category: AI task category for enhancement
    - username: User context for pattern learning
    - idempotency_key: Unique key for idempotent execution
    """
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    outcome_type = body.get("outcome_type")
    params = body.get("params", {})

    if not outcome_type:
        return {"ok": False, "error": "outcome_type_required"}

    return await fabric.execute_smart(
        outcome_type=outcome_type,
        params=params,
        use_ai=body.get("use_ai", True),
        ai_task_category=body.get("ai_task_category", "fulfillment"),
        username=body.get("username"),
        idempotency_key=body.get("idempotency_key")
    )


@router.post("/send-email")
async def smart_email(body: Dict[str, Any] = Body(...)):
    """
    Send email with AI enhancement and Resend delivery.

    Required: to, subject, body
    Optional: html, use_ai, username
    """
    from aigentsy_coi_integration import smart_email as _smart_email

    to = body.get("to")
    subject = body.get("subject")
    email_body = body.get("body")

    if not to or not subject:
        return {"ok": False, "error": "to_and_subject_required"}

    return await _smart_email(
        to=to,
        subject=subject,
        body=email_body or "",
        use_ai=body.get("use_ai", True),
        username=body.get("username")
    )


# ============================================================================
# AME INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/ame/deliver/{pitch_id}")
async def ame_deliver(pitch_id: str, body: Dict[str, Any] = Body(default={})):
    """Deliver an AME pitch via COI connectors"""
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    channel = body.get("channel", "email")
    return await fabric.ame_deliver_pitch(pitch_id, channel)


@router.post("/ame/auto-pipeline")
async def ame_auto_pipeline(body: Dict[str, Any] = Body(...)):
    """
    Full AME pipeline: Generate pitches and deliver via COI.

    Required: matches (list of match objects), originator
    """
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    matches = body.get("matches", [])
    originator = body.get("originator")

    if not matches or not originator:
        return {"ok": False, "error": "matches_and_originator_required"}

    return await fabric.ame_auto_pipeline(matches, originator)


# ============================================================================
# AMG INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/amg/execute-action")
async def amg_execute_action(body: Dict[str, Any] = Body(...)):
    """
    Execute an AMG action via COI.

    Required: username, action_type
    Optional: params
    """
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    username = body.get("username")
    action_type = body.get("action_type")
    params = body.get("params", {})

    if not username or not action_type:
        return {"ok": False, "error": "username_and_action_type_required"}

    return await fabric.amg_execute_action(username, action_type, params)


@router.post("/amg/run-cycle")
async def amg_run_cycle(body: Dict[str, Any] = Body(...)):
    """Run full AMG cycle with COI-powered fulfillment"""
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    username = body.get("username")
    if not username:
        return {"ok": False, "error": "username_required"}

    return await fabric.amg_run_with_coi(username)


# ============================================================================
# METABRIDGE INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/metabridge/dispatch")
async def metabridge_dispatch(body: Dict[str, Any] = Body(...)):
    """
    MetaBridge deal dispatch with COI-powered delivery.

    Required: query, originator
    Optional: mesh_session_id
    """
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    query = body.get("query")
    originator = body.get("originator")

    if not query or not originator:
        return {"ok": False, "error": "query_and_originator_required"}

    return await fabric.metabridge_dispatch_with_coi(
        query=query,
        originator=originator,
        mesh_session_id=body.get("mesh_session_id")
    )


# ============================================================================
# JV MESH INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/jv/propose")
async def jv_propose(body: Dict[str, Any] = Body(...)):
    """
    Create JV proposal and notify via COI.

    Required: proposer, partner, title, description, revenue_split
    """
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    required = ["proposer", "partner", "title", "description", "revenue_split"]
    for field in required:
        if field not in body:
            return {"ok": False, "error": f"{field}_required"}

    return await fabric.jv_propose_with_coi(
        proposer=body["proposer"],
        partner=body["partner"],
        title=body["title"],
        description=body["description"],
        revenue_split=body["revenue_split"]
    )


@router.post("/jv/auto-match")
async def jv_auto_match(body: Dict[str, Any] = Body(...)):
    """
    Auto-match JV partners and propose via COI.

    Required: agent (agent object), all_agents (list of agent objects)
    """
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    agent = body.get("agent")
    all_agents = body.get("all_agents", [])

    if not agent:
        return {"ok": False, "error": "agent_required"}

    return await fabric.jv_auto_match_with_coi(agent, all_agents)


# ============================================================================
# METAHIVE INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/metahive/distribute")
async def metahive_distribute():
    """Distribute MetaHive rewards using COI for notifications"""
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    return await fabric.metahive_distribute_with_coi()


@router.post("/metahive/record")
async def metahive_record(body: Dict[str, Any] = Body(...)):
    """
    Record MetaHive contribution.

    Required: username, contribution_type
    Optional: value
    """
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    username = body.get("username")
    contribution_type = body.get("contribution_type")

    if not username or not contribution_type:
        return {"ok": False, "error": "username_and_contribution_type_required"}

    return await fabric.metahive_record_with_coi(
        username=username,
        contribution_type=contribution_type,
        value=body.get("value", 1.0)
    )


# ============================================================================
# AI FAMILY BRAIN INTEGRATION ENDPOINTS
# ============================================================================

@router.post("/ai/execute-with-fulfillment")
async def ai_execute_with_fulfillment(body: Dict[str, Any] = Body(...)):
    """
    Execute AI task and optionally fulfill the result via COI.

    Required: prompt
    Optional: task_category, fulfill_result, fulfillment_type, fulfillment_params
    """
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    prompt = body.get("prompt")
    if not prompt:
        return {"ok": False, "error": "prompt_required"}

    return await fabric.ai_execute_with_fulfillment(
        prompt=prompt,
        task_category=body.get("task_category", "content_generation"),
        fulfill_result=body.get("fulfill_result", False),
        fulfillment_type=body.get("fulfillment_type"),
        fulfillment_params=body.get("fulfillment_params")
    )


@router.post("/ai/research-and-act")
async def ai_research_and_act(body: Dict[str, Any] = Body(...)):
    """
    Research with AI then act via COI.

    Required: research_query, action_type, action_params
    Optional: username
    """
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    research_query = body.get("research_query")
    action_type = body.get("action_type")
    action_params = body.get("action_params", {})

    if not research_query or not action_type:
        return {"ok": False, "error": "research_query_and_action_type_required"}

    return await fabric.ai_research_and_act(
        research_query=research_query,
        action_type=action_type,
        action_params=action_params,
        username=body.get("username")
    )


# ============================================================================
# STATUS AND METRICS ENDPOINTS
# ============================================================================

@router.get("/status")
async def fabric_status():
    """Get comprehensive fabric status"""
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    if not fabric.coi_runtime:
        await fabric.initialize()

    return fabric.get_fabric_status()


@router.get("/metrics")
async def fabric_metrics():
    """Get fabric metrics"""
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    return {"ok": True, "metrics": fabric.get_metrics()}


@router.post("/initialize")
async def initialize_fabric():
    """Explicitly initialize the fabric"""
    from aigentsy_coi_integration import get_fabric

    fabric = get_fabric()
    return await fabric.initialize()


# ============================================================================
# REGISTRATION FUNCTION
# ============================================================================

def include_aigentsy_fabric(app):
    """Include AiGentsy Fabric routes in FastAPI app"""
    app.include_router(router)

    logger.info("AiGentsy Fabric routes registered at /fabric-unified/*")
    logger.info("  - POST /fabric-unified/execute (smart execution)")
    logger.info("  - POST /fabric-unified/send-email (AI-enhanced email)")
    logger.info("  - POST /fabric-unified/ame/* (AME integration)")
    logger.info("  - POST /fabric-unified/amg/* (AMG integration)")
    logger.info("  - POST /fabric-unified/metabridge/* (MetaBridge integration)")
    logger.info("  - POST /fabric-unified/jv/* (JV Mesh integration)")
    logger.info("  - POST /fabric-unified/metahive/* (MetaHive integration)")
    logger.info("  - POST /fabric-unified/ai/* (AI Family Brain integration)")
    logger.info("  - GET  /fabric-unified/status (full status)")
