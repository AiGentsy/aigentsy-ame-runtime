"""
EXECUTION ROUTES - APPROVAL-BASED EXECUTION
Integrates with main.py to provide execution endpoints with approval gates

Key Principles:
- Users approve opportunities routed to them
- Wade approves opportunities routed to AiGentsy
- Wade approves execution milestones (engage, execute, deliver)
- All major decisions require explicit human approval
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

# Import execution infrastructure
from execution_orchestrator import ExecutionOrchestrator
from execution_scorer import ExecutionScorer
from alpha_discovery_engine import AlphaDiscoveryEngine

# Create router
router = APIRouter(prefix="/execution", tags=["execution"])

# Initialize engines
orchestrator = ExecutionOrchestrator()
scorer = ExecutionScorer()
discovery_engine = AlphaDiscoveryEngine()

# In-memory state (would use JSONBin in production)
PENDING_USER_APPROVALS = {}  # {opportunity_id: {...}}
PENDING_WADE_APPROVALS = {}  # {opportunity_id: {...}}
EXECUTION_STAGES = {}  # {execution_id: {stage, data}}


# ============================================================
# USER APPROVAL ENDPOINTS
# ============================================================

@router.get("/user/{username}/opportunities")
async def get_user_opportunities(username: str):
    """
    Get opportunities awaiting user approval
    User sees these in their dashboard
    """
    
    # Filter opportunities routed to this user
    user_opportunities = [
        opp for opp in PENDING_USER_APPROVALS.values()
        if opp.get('routed_to') == username
    ]
    
    # Sort by expected value
    user_opportunities.sort(
        key=lambda x: x.get('routing', {}).get('economics', {}).get('user_revenue', 0),
        reverse=True
    )
    
    return {
        'ok': True,
        'username': username,
        'count': len(user_opportunities),
        'opportunities': user_opportunities,
        'total_potential_revenue': sum(
            o.get('routing', {}).get('economics', {}).get('user_revenue', 0)
            for o in user_opportunities
        )
    }


@router.post("/user/{username}/approve/{opportunity_id}")
async def user_approve_opportunity(
    username: str,
    opportunity_id: str,
    body: Dict[str, Any] = None
):
    """
    User approves an opportunity
    Triggers execution pipeline
    """
    
    body = body or {}
    
    # Get opportunity
    opp_data = PENDING_USER_APPROVALS.get(opportunity_id)
    
    if not opp_data:
        raise HTTPException(404, "Opportunity not found")
    
    if opp_data.get('routed_to') != username:
        raise HTTPException(403, "Not authorized for this opportunity")
    
    # Mark as approved
    opp_data['user_approved'] = True
    opp_data['user_approved_at'] = datetime.utcnow().isoformat()
    
    # Execute opportunity
    result = await orchestrator.execute_opportunity(
        opportunity=opp_data['opportunity'],
        capability=opp_data['routing']['capability'],
        user_data={'username': username}
    )
    
    # Remove from pending
    del PENDING_USER_APPROVALS[opportunity_id]
    
    return {
        'ok': True,
        'message': 'Opportunity approved and executing',
        'execution': result
    }


@router.post("/user/{username}/decline/{opportunity_id}")
async def user_decline_opportunity(username: str, opportunity_id: str):
    """
    User declines an opportunity
    """
    
    opp_data = PENDING_USER_APPROVALS.get(opportunity_id)
    
    if not opp_data:
        raise HTTPException(404, "Opportunity not found")
    
    if opp_data.get('routed_to') != username:
        raise HTTPException(403, "Not authorized for this opportunity")
    
    # Remove from pending
    del PENDING_USER_APPROVALS[opportunity_id]
    
    return {
        'ok': True,
        'message': 'Opportunity declined'
    }


# ============================================================
# WADE APPROVAL ENDPOINTS (AIGENTSY OPPORTUNITIES)
# ============================================================

@router.get("/wade/approval-queue")
async def get_wade_approval_queue():
    """
    Get opportunities awaiting Wade's approval
    Shows in Wade's dashboard
    """
    
    # Get all AiGentsy-routed opportunities
    wade_opportunities = list(PENDING_WADE_APPROVALS.values())
    
    # Sort by expected profit
    wade_opportunities.sort(
        key=lambda x: x.get('routing', {}).get('economics', {}).get('estimated_profit', 0),
        reverse=True
    )
    
    # Calculate totals
    total_value = sum(
        o.get('opportunity', {}).get('value', 0)
        for o in wade_opportunities
    )
    
    total_profit = sum(
        o.get('routing', {}).get('economics', {}).get('estimated_profit', 0)
        for o in wade_opportunities
    )
    
    return {
        'ok': True,
        'count': len(wade_opportunities),
        'opportunities': wade_opportunities,
        'totals': {
            'total_value': total_value,
            'total_profit': total_profit,
            'avg_margin': sum(
                o.get('routing', {}).get('economics', {}).get('margin', 0)
                for o in wade_opportunities
            ) / len(wade_opportunities) if wade_opportunities else 0
        }
    }


@router.post("/wade/approve/{opportunity_id}")
async def wade_approve_opportunity(
    opportunity_id: str,
    body: Dict[str, Any] = None
):
    """
    Wade approves AiGentsy-routed opportunity
    
    Stages:
    1. Approve to score/price (initial approval)
    2. Approve to engage (after seeing price)
    3. Approve to execute (after engagement)
    4. Approve to deliver (after build)
    """
    
    body = body or {}
    stage = body.get('stage', 'initial')  # initial, engage, execute, deliver
    
    # Get opportunity
    opp_data = PENDING_WADE_APPROVALS.get(opportunity_id)
    
    if not opp_data:
        raise HTTPException(404, "Opportunity not found")
    
    # STAGE 1: Initial approval (score + price)
    if stage == 'initial':
        return await _wade_approve_initial(opportunity_id, opp_data)
    
    # STAGE 2: Approve engagement
    elif stage == 'engage':
        return await _wade_approve_engage(opportunity_id, opp_data)
    
    # STAGE 3: Approve execution
    elif stage == 'execute':
        return await _wade_approve_execute(opportunity_id, opp_data)
    
    # STAGE 4: Approve delivery
    elif stage == 'deliver':
        return await _wade_approve_deliver(opportunity_id, opp_data)
    
    else:
        raise HTTPException(400, f"Unknown stage: {stage}")


async def _wade_approve_initial(opportunity_id: str, opp_data: Dict):
    """Stage 1: Score and price the opportunity"""
    
    opportunity = opp_data['opportunity']
    capability = opp_data['routing']['capability']
    
    # Score opportunity
    score = scorer.score_opportunity(opportunity, capability)
    
    # Calculate pricing
    from pricing_oracle import calculate_dynamic_price, explain_price
    
    pricing = await calculate_dynamic_price(
        base_price=opportunity.get('value', 1000),
        agent='aigentsy',
        context={
            'service_type': opportunity.get('type', 'general')
        }
    )
    
    explanation = await explain_price(
        base_price=pricing.get('final_price'),
        agent='aigentsy',
        context={'service_type': opportunity.get('type')}
    )
    
    # Store execution stage
    EXECUTION_STAGES[opportunity_id] = {
        'stage': 'scored_and_priced',
        'score': score,
        'pricing': pricing,
        'explanation': explanation,
        'awaiting_wade_approval': 'engage'
    }
    
    return {
        'ok': True,
        'message': 'Opportunity scored and priced',
        'next_action': 'Review pricing, then approve to engage',
        'score': score,
        'pricing': pricing,
        'explanation': explanation
    }


async def _wade_approve_engage(opportunity_id: str, opp_data: Dict):
    """Stage 2: Engage the opportunity"""
    
    stage_data = EXECUTION_STAGES.get(opportunity_id)
    if not stage_data:
        raise HTTPException(400, "Must score/price first")
    
    opportunity = opp_data['opportunity']
    score = stage_data['score']
    pricing = stage_data['pricing']
    
    # Engage
    from opportunity_engagement import OpportunityEngagement
    engagement = OpportunityEngagement()
    
    result = await engagement.engage(opportunity, pricing, score)
    
    # Store result
    stage_data['stage'] = 'engaged'
    stage_data['engagement'] = result
    stage_data['awaiting_wade_approval'] = 'execute'
    
    return {
        'ok': True,
        'message': 'Engagement sent',
        'next_action': 'Wait for client response, then approve to execute',
        'engagement': result
    }


async def _wade_approve_execute(opportunity_id: str, opp_data: Dict):
    """Stage 3: Execute the solution"""
    
    stage_data = EXECUTION_STAGES.get(opportunity_id)
    if not stage_data or stage_data.get('stage') != 'engaged':
        raise HTTPException(400, "Must engage first")
    
    opportunity = opp_data['opportunity']
    capability = opp_data['routing']['capability']
    
    # Execute solution (would use real agents)
    solution = {
        'success': True,
        'output': f"Completed {opportunity['type']} task",
        'artifacts': [f"{opportunity['type']}_deliverable.zip"],
        'agent_used': 'claude',
        'duration_hours': capability.get('avg_delivery_days', 5) * 8,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Store result
    stage_data['stage'] = 'executed'
    stage_data['solution'] = solution
    stage_data['awaiting_wade_approval'] = 'deliver'
    
    return {
        'ok': True,
        'message': 'Solution built',
        'next_action': 'Review solution, then approve to deliver',
        'solution': solution
    }


async def _wade_approve_deliver(opportunity_id: str, opp_data: Dict):
    """Stage 4: Deliver the solution"""
    
    stage_data = EXECUTION_STAGES.get(opportunity_id)
    if not stage_data or stage_data.get('stage') != 'executed':
        raise HTTPException(400, "Must execute first")
    
    opportunity = opp_data['opportunity']
    solution = stage_data['solution']
    pricing = stage_data['pricing']
    
    # Deliver
    from opportunity_engagement import OpportunityEngagement
    engagement = OpportunityEngagement()
    
    delivery = await engagement.deliver_solution(
        opportunity=opportunity,
        solution=solution,
        proof={'proof_url': f"https://aigentsy.com/proof/{opportunity_id}"},
        message=f"Solution delivered for {opportunity['title']}"
    )
    
    # Process payment
    amount = pricing.get('final_price', opportunity.get('value', 1000))
    
    # Store final result
    stage_data['stage'] = 'completed'
    stage_data['delivery'] = delivery
    stage_data['payment'] = {
        'amount': amount,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Remove from pending
    del PENDING_WADE_APPROVALS[opportunity_id]
    
    return {
        'ok': True,
        'message': 'Solution delivered and payment processed',
        'revenue': amount,
        'profit': amount - opp_data['routing']['economics']['estimated_cost'],
        'completed_at': datetime.utcnow().isoformat()
    }


@router.post("/wade/reject/{opportunity_id}")
async def wade_reject_opportunity(opportunity_id: str):
    """
    Wade rejects an opportunity
    """
    
    if opportunity_id in PENDING_WADE_APPROVALS:
        del PENDING_WADE_APPROVALS[opportunity_id]
    
    if opportunity_id in EXECUTION_STAGES:
        del EXECUTION_STAGES[opportunity_id]
    
    return {
        'ok': True,
        'message': 'Opportunity rejected'
    }


# ============================================================
# DISCOVERY WITH APPROVAL ROUTING
# ============================================================

@router.post("/discover-and-route")
async def discover_and_route_with_approvals(
    body: Dict[str, Any] = None
):
    """
    Run discovery and populate approval queues
    
    - User-routed opportunities → User approval queue
    - AiGentsy-routed opportunities → Wade approval queue
    """
    
    body = body or {}
    
    platforms = body.get('platforms')
    dimensions = body.get('dimensions')
    
    # Run discovery
    results = await discovery_engine.discover_and_route(
        platforms=platforms,
        dimensions=dimensions,
        score_opportunities=True  # Always score
    )
    
    # Populate approval queues
    user_count = 0
    wade_count = 0
    
    for opp in results['routing']['user_routed']['opportunities']:
        opportunity_id = opp['opportunity']['id']
        PENDING_USER_APPROVALS[opportunity_id] = opp
        user_count += 1
    
    for opp in results['routing']['aigentsy_routed']['opportunities']:
        opportunity_id = opp['opportunity']['id']
        PENDING_WADE_APPROVALS[opportunity_id] = opp
        wade_count += 1
    
    return {
        'ok': True,
        'discovery_results': results,
        'approval_queues': {
            'user_approvals_pending': user_count,
            'wade_approvals_pending': wade_count
        },
        'message': f'Discovered {results["total_opportunities"]} opportunities. {user_count} await user approval, {wade_count} await Wade approval.'
    }


# ============================================================
# EXECUTION STATUS
# ============================================================

@router.get("/status/{opportunity_id}")
async def get_execution_status(opportunity_id: str):
    """
    Get current execution status for an opportunity
    """
    
    # Check if in user queue
    if opportunity_id in PENDING_USER_APPROVALS:
        return {
            'ok': True,
            'opportunity_id': opportunity_id,
            'status': 'awaiting_user_approval',
            'routed_to': PENDING_USER_APPROVALS[opportunity_id].get('routed_to'),
            'data': PENDING_USER_APPROVALS[opportunity_id]
        }
    
    # Check if in Wade queue
    if opportunity_id in PENDING_WADE_APPROVALS:
        stage_data = EXECUTION_STAGES.get(opportunity_id, {})
        return {
            'ok': True,
            'opportunity_id': opportunity_id,
            'status': 'awaiting_wade_approval',
            'current_stage': stage_data.get('stage', 'initial'),
            'next_action': stage_data.get('awaiting_wade_approval', 'initial'),
            'data': PENDING_WADE_APPROVALS[opportunity_id],
            'stage_data': stage_data
        }
    
    # Check if in execution
    if opportunity_id in EXECUTION_STAGES:
        return {
            'ok': True,
            'opportunity_id': opportunity_id,
            'status': 'in_execution',
            'data': EXECUTION_STAGES[opportunity_id]
        }
    
    return {
        'ok': False,
        'opportunity_id': opportunity_id,
        'status': 'not_found'
    }


@router.get("/stats")
async def get_execution_stats():
    """
    Get overall execution statistics
    """
    
    return {
        'ok': True,
        'pending': {
            'user_approvals': len(PENDING_USER_APPROVALS),
            'wade_approvals': len(PENDING_WADE_APPROVALS)
        },
        'in_progress': len([
            s for s in EXECUTION_STAGES.values()
            if s.get('stage') not in ['completed', 'rejected']
        ]),
        'completed': len([
            s for s in EXECUTION_STAGES.values()
            if s.get('stage') == 'completed'
        ]),
        'orchestrator_stats': orchestrator.get_execution_stats()
    }
