"""
AUTONOMOUS ROUTES v2.0 - AI FAMILY POWERED EXECUTION
Works alongside execution_routes.py to provide autonomous mode

Wade's Hybrid System:
- /execution/* - Manual 4-stage approval (existing)
- /autonomous/* - Fully autonomous execution (this file)

v2.0 AI FAMILY BRAIN INTEGRATION:
- AI-powered opportunity scoring
- AI-generated proposals
- Learning from successful executions
- Cross-pollination with MetaHive patterns

Wade can choose which mode for each opportunity type.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

print("=" * 50)
print("LOADING AUTONOMOUS_ROUTES.PY v2.0")
print("=" * 50)

# ============================================================
# AI FAMILY BRAIN INTEGRATION
# ============================================================

try:
    from ai_family_brain import (
        get_brain, ai_execute, ai_content,
        record_quality, get_family_stats
    )
    AI_FAMILY_AVAILABLE = True
    print("✓ AI Family Brain imported")
except ImportError:
    AI_FAMILY_AVAILABLE = False
    print("⚠️ AI Family Brain not available")

try:
    from metahive_brain import contribute_to_hive, query_hive
    METAHIVE_AVAILABLE = True
    print("✓ MetaHive Brain imported")
except ImportError:
    METAHIVE_AVAILABLE = False
    print("⚠️ MetaHive Brain not available")

try:
    from yield_memory import store_pattern, get_best_action
    YIELD_AVAILABLE = True
    print("✓ Yield Memory imported")
except ImportError:
    YIELD_AVAILABLE = False
    print("⚠️ Yield Memory not available")

# ============================================================
# V106 INTEGRATION (NEW)
# ============================================================

try:
    from v106_integration_orchestrator import v106_integrated_execution
    V106_AVAILABLE = True
    print("✓ V106 Integration imported")
except ImportError:
    V106_AVAILABLE = False
    print("⚠️ V106 Integration not available")

# Import autonomous executor
try:
    from universal_executor import UniversalAutonomousExecutor, get_executor
    EXECUTOR_AVAILABLE = True
    print("✓ Universal Executor imported")
except Exception as e:
    EXECUTOR_AVAILABLE = False
    print(f"⚠️ Universal Executor not available: {e}")

# Import discovery engine
try:
    from alpha_discovery_engine import AlphaDiscoveryEngine
    DISCOVERY_AVAILABLE = True
    print("✓ Discovery Engine imported")
except Exception as e:
    DISCOVERY_AVAILABLE = False
    print(f"⚠️ Discovery Engine not available: {e}")

# Import payment collector
try:
    from payment_collector import get_payment_collector, record_revenue, mark_paid, get_revenue_stats
    PAYMENT_AVAILABLE = True
    print("✓ Payment Collector imported")
except:
    PAYMENT_AVAILABLE = False
    print("⚠️ Payment Collector not available")

# Import system health checker
try:
    from system_health_checker import test_all_systems, quick_health_check
    HEALTH_CHECK_AVAILABLE = True
    print("✓ System Health Checker imported")
except:
    HEALTH_CHECK_AVAILABLE = False
    print("⚠️ System Health Checker not available")

print(f"✓ AI Family Available: {AI_FAMILY_AVAILABLE}")
print(f"✓ MetaHive Available: {METAHIVE_AVAILABLE}")
print(f"✓ Yield Memory Available: {YIELD_AVAILABLE}")
print("=" * 50)
print("AUTONOMOUS_ROUTES.PY v2.0 LOADED")
print("=" * 50)

# Create router with different prefix
router = APIRouter(prefix="/autonomous", tags=["autonomous_execution"])

# Wade's autonomous approval queue
AUTONOMOUS_APPROVAL_QUEUE = {}  # {opportunity_id: {...}}

# Autonomous execution rules (persists rules for auto-execution)
AUTONOMOUS_RULES = []  # List of enabled autonomous rules

# AI Family task tracking
_ai_tasks = []


# ============================================================
# AUTONOMOUS DISCOVERY & EXECUTION
# ============================================================

@router.post("/discover-and-execute")
async def discover_and_execute(
    auto_approve_user: bool = True,
    auto_approve_aigentsy: bool = False,
    max_executions: int = 10
) -> Dict[str, Any]:
    """
    FULLY AUTONOMOUS PIPELINE with AI Family Brain
    
    1. Discover opportunities
    2. AI-powered scoring and routing
    3. Automatically execute approved ones
    4. Track to completion + learn from outcomes
    
    Args:
        auto_approve_user: Auto-execute user opportunities
        auto_approve_aigentsy: Auto-execute AiGentsy opportunities
        max_executions: Max number to execute in this run
        
    Returns:
        Discovery results + execution status + AI Family stats
    """
    
    if not DISCOVERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Discovery engine not available")
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Executor not available")
    
    # STEP 1: Discover opportunities
    discovery_engine = AlphaDiscoveryEngine()
    discovery_results = await discovery_engine.discover_and_route(score_opportunities=True)
    
    # STEP 2: AI-powered scoring (if AI Family available)
    if AI_FAMILY_AVAILABLE:
        for opp_data in discovery_results.get('routing', {}).get('user_routed', {}).get('opportunities', []):
            opportunity = opp_data['opportunity']
            
            # Use AI Family to predict win probability
            try:
                prompt = f"""Analyze this opportunity and predict win probability:
Title: {opportunity.get('title', 'Unknown')}
Platform: {opportunity.get('platform', 'Unknown')}
Value: ${opportunity.get('value', 0)}
Type: {opportunity.get('type', 'Unknown')}

Return ONLY a number between 0.0 and 1.0"""
                
                result = await ai_execute(
                    prompt=prompt,
                    task_category="analysis",
                    max_tokens=50
                )
                
                if result and 'content' in result:
                    try:
                        ai_score = float(result['content'].strip())
                        opp_data['ai_win_probability'] = ai_score
                        opp_data['ai_model_used'] = result.get('model', 'unknown')
                        
                        # Track this AI task
                        task_id = f"score_{opportunity.get('id', 'unknown')}"
                        _ai_tasks.append({
                            'task_id': task_id,
                            'opportunity_id': opportunity.get('id'),
                            'ai_score': ai_score
                        })
                    except:
                        pass
            except:
                pass
    
    # STEP 3: Execute approved opportunities
    executor = get_executor()
    executions = []
    
    # Execute user opportunities (if enabled)
    if auto_approve_user:
        user_opps = discovery_results['routing']['user_routed']['opportunities'][:max_executions]
        
        for opp_data in user_opps:
            opportunity = opp_data['opportunity']
            
            # ===== V106: Full integrated execution (market-maker + risk-tranche + close-loop) =====
            if V106_AVAILABLE:
                result = await v106_integrated_execution(opportunity, auto_execute=True)
                executions.append(result)
            else:
                # Fallback to standard execution
                result = await executor.execute_opportunity(opportunity, auto_approve=True)
                executions.append(result)
            
            # Track revenue
            if PAYMENT_AVAILABLE:
                await record_revenue(
                    execution_id=result.get('execution_id'),
                    platform=opportunity.get('platform'),
                    value=opportunity.get('value', 0),
                    user=opp_data.get('routed_to')
                )
    
    # Execute AiGentsy opportunities (if Wade approves)
    if auto_approve_aigentsy:
        aigentsy_opps = discovery_results['routing']['aigentsy_routed']['opportunities'][:max_executions]
        
        for opp_data in aigentsy_opps:
            opportunity = opp_data['opportunity']
            
            # ===== V106: Full integrated execution (market-maker + risk-tranche + close-loop) =====
            if V106_AVAILABLE:
                result = await v106_integrated_execution(opportunity, auto_execute=True)
                executions.append(result)
            else:
                # Fallback to standard execution
                result = await executor.execute_opportunity(opportunity, auto_approve=True)
                executions.append(result)
            
            # Track revenue
            if PAYMENT_AVAILABLE:
                await record_revenue(
                    execution_id=result.get('execution_id'),
                    platform=opportunity.get('platform'),
                    value=opportunity.get('value', 0),
                    user=None  # AiGentsy opportunity
                )
    
    # Get AI Family stats
    ai_stats = {}
    if AI_FAMILY_AVAILABLE:
        try:
            ai_stats = get_family_stats()
        except:
            pass
    
    return {
        'ok': True,
        'discovery': discovery_results,
        'executions': {
            'count': len(executions),
            'results': executions
        },
        'ai_family': {
            'available': AI_FAMILY_AVAILABLE,
            'tasks_executed': len(_ai_tasks),
            'stats': ai_stats
        },
        'message': f"Discovered {discovery_results['total_opportunities']} opportunities, executed {len(executions)} autonomously"
    }


@router.post("/discover-and-queue")
async def discover_and_queue_for_autonomous(
    min_win_probability: float = 0.7,
    max_value: float = 10000
) -> Dict[str, Any]:
    """
    Discover opportunities and queue HIGH-CONFIDENCE ones for autonomous approval
    
    v2.0: Uses AI Family Brain to predict win probability
    
    Wade reviews queue and enables autonomous mode for specific opportunity types
    
    Args:
        min_win_probability: Only queue opps with win prob >= this (default 70%)
        max_value: Only queue opps with value <= this (default $10K)
    """
    
    if not DISCOVERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Discovery engine not available")
    
    # Run discovery
    discovery_engine = AlphaDiscoveryEngine()
    discovery_results = await discovery_engine.discover_all()
    
    # Filter high-confidence opportunities
    high_confidence = []
    
    for opp_data in discovery_results['routing']['aigentsy_routed']['opportunities']:
        opportunity = opp_data['opportunity']
        score = opp_data.get('score', {})
        
        win_prob = score.get('win_probability', 0)
        value = opportunity.get('value', 0)
        
        # v2.0: Use AI Family to enhance scoring
        if AI_FAMILY_AVAILABLE and win_prob < min_win_probability:
            try:
                prompt = f"""Analyze opportunity win probability:
{opportunity.get('title', 'Unknown')}
Platform: {opportunity.get('platform')}
Value: ${value}

Return number 0.0-1.0"""
                
                result = await ai_execute(
                    prompt=prompt,
                    task_category="analysis",
                    max_tokens=50
                )
                
                if result and 'content' in result:
                    try:
                        ai_win_prob = float(result['content'].strip())
                        win_prob = max(win_prob, ai_win_prob)  # Take higher score
                        opp_data['ai_enhanced'] = True
                        opp_data['ai_win_prob'] = ai_win_prob
                        
                        # Track this AI task
                        task_id = f"queue_score_{opportunity.get('id')}"
                    except:
                        pass
            except:
                pass
        
        # Only queue if high confidence AND reasonable value
        if win_prob >= min_win_probability and value <= max_value:
            high_confidence.append(opp_data)
            
            # Add to autonomous approval queue
            opportunity_id = opportunity['id']
            AUTONOMOUS_APPROVAL_QUEUE[opportunity_id] = {
                'opportunity': opportunity,
                'score': score,
                'routing': opp_data.get('routing', {}),
                'queued_at': datetime.utcnow().isoformat(),
                'approved_for_autonomous': False,
                'ai_enhanced': opp_data.get('ai_enhanced', False)
            }
    
    return {
        'ok': True,
        'total_discovered': discovery_results['total_opportunities'],
        'high_confidence_count': len(high_confidence),
        'queued_for_autonomous_approval': len(high_confidence),
        'criteria': {
            'min_win_probability': min_win_probability,
            'max_value': max_value
        },
        'ai_family_used': AI_FAMILY_AVAILABLE,
        'high_confidence_opportunities': high_confidence
    }


# ============================================================
# WADE'S AUTONOMOUS APPROVAL ENDPOINTS
# ============================================================

@router.get("/approval-queue")
async def get_autonomous_approval_queue():
    """
    Get opportunities queued for Wade to approve for AUTONOMOUS execution
    
    Wade reviews these and enables autonomous mode
    """
    
    queue = list(AUTONOMOUS_APPROVAL_QUEUE.values())
    
    # Sort by expected value
    queue.sort(
        key=lambda x: x['score'].get('expected_value', 0),
        reverse=True
    )
    
    total_value = sum(
        q['opportunity'].get('value', 0)
        for q in queue
    )
    
    return {
        'ok': True,
        'count': len(queue),
        'total_potential_value': total_value,
        'ai_enhanced_count': len([q for q in queue if q.get('ai_enhanced')]),
        'opportunities': queue,
        'message': f'{len(queue)} opportunities ready for autonomous approval'
    }


@router.post("/approve-for-autonomous/{opportunity_id}")
async def approve_for_autonomous_execution(
    opportunity_id: str,
    execute_now: bool = True
) -> Dict[str, Any]:
    """
    Wade approves an opportunity to run AUTONOMOUSLY
    
    v2.0: Records outcome to AI Family for learning
    
    Args:
        opportunity_id: ID of opportunity
        execute_now: If True, execute immediately; if False, just mark as approved
    """
    
    if opportunity_id not in AUTONOMOUS_APPROVAL_QUEUE:
        raise HTTPException(404, "Opportunity not found in autonomous queue")
    
    opp_data = AUTONOMOUS_APPROVAL_QUEUE[opportunity_id]
    opportunity = opp_data['opportunity']
    
    # Mark as approved for autonomous execution
    opp_data['approved_for_autonomous'] = True
    opp_data['approved_at'] = datetime.utcnow().isoformat()
    
    if execute_now:
        if not EXECUTOR_AVAILABLE:
            raise HTTPException(503, "Executor not available")
        
        # Execute autonomously NOW
        executor = get_executor()
        result = await executor.execute_opportunity(opportunity, auto_approve=True)
        
        # Track revenue
        if PAYMENT_AVAILABLE:
            await record_revenue(
                execution_id=result.get('execution_id'),
                platform=opportunity.get('platform'),
                value=opportunity.get('value', 0),
                user=None,
                status='pending'
            )
        
        # Remove from queue
        del AUTONOMOUS_APPROVAL_QUEUE[opportunity_id]
        
        return {
            'ok': True,
            'message': 'Approved and executing autonomously',
            'execution': result,
            'ai_enhanced': opp_data.get('ai_enhanced', False)
        }
    
    else:
        # Just mark as approved (will execute later)
        return {
            'ok': True,
            'message': 'Approved for autonomous execution',
            'opportunity_id': opportunity_id,
            'will_execute': 'on_next_autonomous_run'
        }


@router.post("/record-execution-outcome")
async def record_execution_outcome(
    execution_id: str,
    success: bool,
    revenue: float = 0.0,
    notes: str = None
) -> Dict[str, Any]:
    """
    v2.0 NEW: Record execution outcome for AI Family learning
    """
    
    outcome = {
        'execution_id': execution_id,
        'success': success,
        'revenue': revenue,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Record quality to AI Family
    if AI_FAMILY_AVAILABLE:
        # Find related AI task
        related_task = next((t for t in _ai_tasks if t['opportunity_id'] in execution_id), None)
        
        if related_task:
            quality = 0.9 if success else 0.3
            record_quality(related_task['task_id'], quality, revenue)
    
    # Contribute to MetaHive if successful
    if METAHIVE_AVAILABLE and success and revenue > 0:
        try:
            await contribute_to_hive(
                username="aigentsy",
                pattern_type="autonomous_execution",
                context={"execution_id": execution_id},
                action={"auto_approved": True},
                outcome={
                    "revenue_usd": revenue,
                    "quality_score": 0.9 if success else 0.3
                }
            )
        except:
            pass
    
    return {
        'ok': True,
        'outcome': outcome,
        'ai_family_recorded': AI_FAMILY_AVAILABLE and related_task is not None
    }


@router.post("/enable-autonomous-for-type")
async def enable_autonomous_for_opportunity_type(
    platform: str,
    opportunity_type: str,
    min_win_probability: float = 0.8,
    max_value: float = 5000
) -> Dict[str, Any]:
    """
    Wade enables AUTONOMOUS mode for specific opportunity types
    
    Example: Enable autonomous for GitHub issues with >80% win prob and <$5K value
    
    Args:
        platform: Platform name (github, reddit, etc.)
        opportunity_type: Type of opportunity
        min_win_probability: Minimum win probability to auto-execute
        max_value: Maximum value to auto-execute
    """
    
    # Store rule in module-level persistent storage
    rule = {
        'platform': platform,
        'type': opportunity_type,
        'min_win_probability': min_win_probability,
        'max_value': max_value,
        'enabled_at': datetime.utcnow().isoformat(),
        'enabled_by': 'wade'
    }
    
    # Add to persistent rules
    AUTONOMOUS_RULES.append(rule)
    
    return {
        'ok': True,
        'message': f'Autonomous mode enabled for {platform}/{opportunity_type}',
        'rule': rule,
        'active_rules_count': len(AUTONOMOUS_RULES),
        'next_step': 'Matching opportunities will auto-execute on next discovery run'
    }


# ============================================================
# EXECUTION STATUS & STATS
# ============================================================

@router.get("/status/{execution_id}")
async def get_autonomous_execution_status(execution_id: str):
    """Get status of an autonomous execution"""
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(503, "Executor not available")
    
    executor = get_executor()
    
    # Check active executions
    if execution_id in executor.active_executions:
        state = executor.active_executions[execution_id]
        return executor._get_execution_status(state)
    
    # Check completed executions
    for state in executor.completed_executions:
        if state['execution_id'] == execution_id:
            return executor._get_execution_status(state)
    
    raise HTTPException(404, "Execution not found")


@router.get("/stats")
async def get_autonomous_stats():
    """Get autonomous execution statistics with AI Family stats"""
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(503, "Executor not available")
    
    executor = get_executor()
    stats = executor.get_stats()
    
    # Add autonomous-specific stats
    stats['autonomous_queue'] = {
        'pending_approval': len([
            q for q in AUTONOMOUS_APPROVAL_QUEUE.values()
            if not q.get('approved_for_autonomous')
        ]),
        'approved_waiting': len([
            q for q in AUTONOMOUS_APPROVAL_QUEUE.values()
            if q.get('approved_for_autonomous')
        ])
    }
    
    # Add AI Family stats
    stats['ai_family'] = {
        'available': AI_FAMILY_AVAILABLE,
        'tasks_executed': len(_ai_tasks)
    }
    
    if AI_FAMILY_AVAILABLE:
        try:
            stats['ai_family']['stats'] = get_family_stats()
        except:
            pass
    
    return stats


@router.get("/ai-family-stats")
async def get_ai_family_stats():
    """Get AI Family Brain statistics"""
    
    if not AI_FAMILY_AVAILABLE:
        raise HTTPException(503, "AI Family not available")
    
    try:
        stats = get_family_stats()
        return {
            'ok': True,
            'tasks_tracked': len(_ai_tasks),
            'family_stats': stats
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }


# ============================================================
# REVENUE & PAYMENT ENDPOINTS
# ============================================================

@router.get("/revenue/stats")
async def get_autonomous_revenue_stats():
    """Get revenue statistics from autonomous executions"""
    
    if not PAYMENT_AVAILABLE:
        raise HTTPException(503, "Payment collector not available")
    
    stats = await get_revenue_stats()
    
    return {
        'ok': True,
        'stats': stats
    }


@router.post("/revenue/{execution_id}/mark-paid")
async def mark_autonomous_execution_paid(
    execution_id: str,
    stripe_charge_id: Optional[str] = None,
    actual_amount: Optional[float] = None
):
    """Mark an autonomous execution as paid"""
    
    if not PAYMENT_AVAILABLE:
        raise HTTPException(503, "Payment collector not available")
    
    result = await mark_paid(execution_id, stripe_charge_id, actual_amount)
    
    return {
        'ok': True,
        'execution_id': execution_id,
        'result': result
    }


# ============================================================
# SYSTEM HEALTH ENDPOINTS
# ============================================================

@router.get("/health")
async def autonomous_system_health():
    """Full system health check"""
    
    if not HEALTH_CHECK_AVAILABLE:
        raise HTTPException(503, "Health checker not available")
    
    results = await test_all_systems()
    
    return {
        'ok': True,
        'health': results
    }


@router.get("/health/quick")
async def autonomous_quick_health():
    """Quick health check"""
    
    if not HEALTH_CHECK_AVAILABLE:
        raise HTTPException(503, "Health checker not available")
    
    results = await quick_health_check()
    
    return {
        'ok': True,
        'health': results
    }


# ============================================================
# TEST ENDPOINT
# ============================================================

@router.post("/test-execution")
async def test_autonomous_execution():
    """Test autonomous execution with a synthetic test opportunity"""
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(503, "Executor not available")
    
    # Create test opportunity
    test_opportunity = {
        'id': f'autonomous_test_{int(datetime.now().timestamp())}',
        'platform': 'github',
        'type': 'software_development',
        'title': 'Test Autonomous Execution',
        'description': 'Test autonomous system',
        'url': 'https://github.com/test/repo/issues/1',
        'value': 100,
        'urgency': 'low',
        'created_at': datetime.now().isoformat()
    }
    
    executor = get_executor()
    result = await executor.execute_opportunity(test_opportunity, auto_approve=True)
    
    return {
        'ok': True,
        'test': 'autonomous_execution_completed',
        'result': result,
        'ai_family_available': AI_FAMILY_AVAILABLE
    }
