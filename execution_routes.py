"""
EXECUTION ROUTES - COMPLETE MERGED VERSION
Combines Wade's existing 4-stage approval workflow with new features:
- Payment tracking
- System health monitoring
- Revenue reconciliation

This KEEPS your existing approval logic and ADDS new capabilities.
"""

# MUST import FastAPI FIRST, before any prints
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import sys

# Now debug prints
print("=" * 50)
print("LOADING EXECUTION_ROUTES.PY (MERGED VERSION)")
print("=" * 50)

# Import execution infrastructure with error handling
try:
    from execution_orchestrator import ExecutionOrchestrator
    print("✓ ExecutionOrchestrator imported")
except Exception as e:
    print(f"✗ ExecutionOrchestrator import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from execution_scorer import ExecutionScorer
    print("✓ ExecutionScorer imported")
except Exception as e:
    print(f"✗ ExecutionScorer import failed: {e}")
    sys.exit(1)

try:
    from alpha_discovery_engine import AlphaDiscoveryEngine
    print("✓ AlphaDiscoveryEngine imported")
except Exception as e:
    print(f"✗ AlphaDiscoveryEngine import failed: {e}")
    sys.exit(1)

# Import NEW systems (with graceful fallbacks)
try:
    from payment_collector import get_payment_collector, record_revenue, mark_paid, get_revenue_stats
    PAYMENT_AVAILABLE = True
    print("✓ Payment collector imported")
except:
    PAYMENT_AVAILABLE = False
    print("⚠️ Payment collector not available")

try:
    from system_health_checker import test_all_systems, quick_health_check
    HEALTH_CHECK_AVAILABLE = True
    print("✓ System health checker imported")
except:
    HEALTH_CHECK_AVAILABLE = False
    print("⚠️ System health checker not available")

# Create router
router = APIRouter(prefix="/execution", tags=["execution"])

# Initialize engines with error handling
try:
    orchestrator = ExecutionOrchestrator()
    print("✓ ExecutionOrchestrator initialized")
except Exception as e:
    print(f"✗ ExecutionOrchestrator initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    scorer = ExecutionScorer()
    print("✓ ExecutionScorer initialized")
except Exception as e:
    print(f"✗ ExecutionScorer initialization failed: {e}")
    sys.exit(1)

try:
    discovery_engine = AlphaDiscoveryEngine()
    print("✓ AlphaDiscoveryEngine initialized")
except Exception as e:
    print(f"✗ AlphaDiscoveryEngine initialization failed: {e}")
    sys.exit(1)

print("=" * 50)
print("EXECUTION_ROUTES.PY LOADED SUCCESSFULLY")
print("=" * 50)

# In-memory state (would use JSONBin in production)
PENDING_USER_APPROVALS = {}  # {opportunity_id: {...}}
PENDING_WADE_APPROVALS = {}  # {opportunity_id: {...}}
EXECUTION_STAGES = {}  # {execution_id: {stage, data}}


# ============================================================
# USER APPROVAL ENDPOINTS (EXISTING - KEPT AS-IS)
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
    
    # Record revenue (NEW)
    if PAYMENT_AVAILABLE:
        await record_revenue(
            execution_id=opportunity_id,
            platform=opp_data['opportunity'].get('platform'),
            value=opp_data['opportunity'].get('value', 0),
            user=username
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
# WADE APPROVAL ENDPOINTS (EXISTING - KEPT AS-IS)
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
    
    4-STAGE APPROVAL PROCESS (EXISTING - KEPT AS-IS):
    1. score_and_price - Initial approval
    2. engage - Approve engagement
    3. execute - Approve execution
    4. deliver - Approve delivery
    """
    
    body = body or {}
    stage = body.get('stage', 'score_and_price')
    
    # Get opportunity
    opp_data = PENDING_WADE_APPROVALS.get(opportunity_id)
    
    if not opp_data:
        raise HTTPException(404, "Opportunity not found")
    
    # STAGE 1: Initial approval (score + price)
    if stage == 'score_and_price':
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
    
    # Record revenue (NEW)
    if PAYMENT_AVAILABLE:
        await record_revenue(
            execution_id=opportunity_id,
            platform=opportunity.get('platform'),
            value=amount,
            user=None  # AiGentsy opportunity
        )
        
        # Mark as paid when delivered
        await mark_paid(
            execution_id=opportunity_id,
            actual_amount=amount
        )
    
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
# DISCOVERY WITH APPROVAL ROUTING (EXISTING - KEPT AS-IS)
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
# EXECUTION STATUS (EXISTING - KEPT AS-IS)
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
            'next_action': stage_data.get('awaiting_wade_approval', 'score_and_price'),
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


# ============================================================
# NEW ENDPOINTS - PAYMENT TRACKING
# ============================================================

@router.get("/revenue/stats")
async def get_revenue_statistics():
    """
    NEW: Get revenue statistics from executions
    Shows total revenue tracked, paid, pending
    """
    
    if not PAYMENT_AVAILABLE:
        return {
            'ok': False,
            'error': 'Payment collector not available'
        }
    
    stats = await get_revenue_stats()
    
    return {
        'ok': True,
        'stats': stats
    }


@router.post("/revenue/{execution_id}/mark-paid")
async def mark_execution_paid(
    execution_id: str,
    stripe_charge_id: Optional[str] = None,
    actual_amount: Optional[float] = None
):
    """
    NEW: Mark an execution as paid
    Called when payment is confirmed
    """
    
    if not PAYMENT_AVAILABLE:
        return {
            'ok': False,
            'error': 'Payment collector not available'
        }
    
    result = await mark_paid(execution_id, stripe_charge_id, actual_amount)
    
    return {
        'ok': True,
        'execution_id': execution_id,
        'result': result
    }


@router.get("/revenue/reconcile")
async def reconcile_revenue(
    date: Optional[str] = Query(None, description="Date to reconcile (YYYY-MM-DD)")
):
    """
    NEW: Reconcile revenue for a specific date
    Compares expected vs actual revenue
    """
    
    if not PAYMENT_AVAILABLE:
        return {
            'ok': False,
            'error': 'Payment collector not available'
        }
    
    collector = get_payment_collector()
    result = await collector.reconcile_daily_revenue(date)
    
    return {
        'ok': True,
        'reconciliation': result
    }


# ============================================================
# NEW ENDPOINTS - SYSTEM HEALTH
# ============================================================

@router.get("/health")
async def system_health():
    """
    NEW: Full system health check
    Tests all 30+ systems to see which are working
    """
    
    if not HEALTH_CHECK_AVAILABLE:
        return {
            'ok': False,
            'error': 'Health checker not available'
        }
    
    results = await test_all_systems()
    
    return {
        'ok': True,
        'health': results
    }


@router.get("/health/quick")
async def quick_health():
    """
    NEW: Quick health check (just counts)
    Faster than full health check
    """
    
    if not HEALTH_CHECK_AVAILABLE:
        return {
            'ok': False,
            'error': 'Health checker not available'
        }
    
    results = await quick_health_check()
    
    return {
        'ok': True,
        'health': results
    }
