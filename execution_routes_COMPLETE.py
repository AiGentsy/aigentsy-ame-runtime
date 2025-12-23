"""
EXECUTION ROUTES - COMPLETE AUTONOMOUS SYSTEM
Full integration with universal_executor.py

This file wires the autonomous executor into your FastAPI backend.

Endpoints:
- POST /execution/discover-and-execute - Discover AND execute opportunities autonomously
- POST /execution/execute/{opportunity_id} - Execute a specific opportunity
- GET /execution/status/{execution_id} - Check execution status
- GET /execution/stats - Get execution statistics
- POST /execution/approve/{execution_id} - Approve an opportunity for execution
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

# Import the autonomous executor
try:
    from universal_executor import UniversalAutonomousExecutor, get_executor
    EXECUTOR_AVAILABLE = True
except:
    EXECUTOR_AVAILABLE = False
    print("⚠️ universal_executor not available")

# Import discovery engine
try:
    from alpha_discovery_engine import AlphaDiscoveryEngine
    DISCOVERY_AVAILABLE = True
except:
    DISCOVERY_AVAILABLE = False

router = APIRouter(prefix="/execution", tags=["autonomous_execution"])


@router.post("/discover-and-execute")
async def discover_and_execute(
    auto_approve_user: bool = True,
    auto_approve_aigentsy: bool = False,
    max_executions: int = 10
) -> Dict[str, Any]:
    """
    FULL AUTONOMOUS PIPELINE
    
    1. Discover opportunities
    2. Score and route them
    3. Automatically execute approved ones
    4. Track to completion
    
    Args:
        auto_approve_user: Auto-execute user opportunities
        auto_approve_aigentsy: Auto-execute AiGentsy opportunities (Wade's approval)
        max_executions: Max number to execute in this run
        
    Returns:
        Discovery results + execution status
    """
    
    if not DISCOVERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Discovery engine not available")
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Executor not available")
    
    # STEP 1: Discover opportunities
    discovery_engine = AlphaDiscoveryEngine()
    discovery_results = await discovery_engine.discover_all()
    
    # STEP 2: Execute approved opportunities
    executor = get_executor()
    executions = []
    
    # Execute user opportunities
    if auto_approve_user:
        user_opps = discovery_results['routing']['user_routed']['opportunities'][:max_executions]
        
        for opp_data in user_opps:
            opportunity = opp_data['opportunity']
            
            # Execute autonomously
            result = await executor.execute_opportunity(opportunity, auto_approve=True)
            executions.append(result)
    
    # Execute AiGentsy opportunities (if approved)
    if auto_approve_aigentsy:
        aigentsy_opps = discovery_results['routing']['aigentsy_routed']['opportunities'][:max_executions]
        
        for opp_data in aigentsy_opps:
            opportunity = opp_data['opportunity']
            
            # Execute autonomously
            result = await executor.execute_opportunity(opportunity, auto_approve=True)
            executions.append(result)
    
    return {
        'ok': True,
        'discovery': discovery_results,
        'executions': {
            'count': len(executions),
            'results': executions
        },
        'message': f"Discovered {discovery_results['total_opportunities']} opportunities, executed {len(executions)}"
    }


@router.post("/execute/{opportunity_id}")
async def execute_opportunity_by_id(opportunity_id: str, auto_approve: bool = False) -> Dict[str, Any]:
    """
    Execute a specific opportunity by ID
    
    This finds the opportunity from discovery results and executes it
    """
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Executor not available")
    
    # Would fetch opportunity from database/discovery cache
    # For now, return error
    raise HTTPException(status_code=404, detail="Opportunity not found")


@router.get("/status/{execution_id}")
async def get_execution_status(execution_id: str) -> Dict[str, Any]:
    """
    Get status of a specific execution
    """
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Executor not available")
    
    executor = get_executor()
    
    # Check active executions
    if execution_id in executor.active_executions:
        state = executor.active_executions[execution_id]
        return executor._get_execution_status(state)
    
    # Check completed executions
    for state in executor.completed_executions:
        if state['execution_id'] == execution_id:
            return executor._get_execution_status(state)
    
    raise HTTPException(status_code=404, detail="Execution not found")


@router.get("/stats")
async def get_execution_stats() -> Dict[str, Any]:
    """
    Get overall execution statistics
    """
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Executor not available")
    
    executor = get_executor()
    return executor.get_stats()


@router.post("/approve/{execution_id}")
async def approve_execution(execution_id: str) -> Dict[str, Any]:
    """
    Approve an execution that's awaiting approval
    
    This would transition from approval queue to active execution
    """
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Executor not available")
    
    executor = get_executor()
    
    # Find execution
    if execution_id not in executor.active_executions:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    state = executor.active_executions[execution_id]
    
    # Approve and continue execution
    state['approved'] = True
    state['stage'] = 'approved'
    
    # Continue execution pipeline from planning stage
    state = await executor._stage_planning(state)
    state = await executor._stage_generation(state)
    state = await executor._stage_validation(state)
    state = await executor._stage_submission(state)
    
    # Start monitoring in background
    asyncio.create_task(executor._stage_monitoring(state))
    
    return {
        'ok': True,
        'execution_id': execution_id,
        'status': 'approved_and_executing',
        'current_stage': state['stage'].value
    }


@router.post("/test-execution")
async def test_execution() -> Dict[str, Any]:
    """
    Test endpoint - Execute a stub opportunity to verify system works
    """
    
    if not EXECUTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Executor not available")
    
    # Create test opportunity
    test_opportunity = {
        'id': 'test_001',
        'platform': 'github',
        'type': 'software_development',
        'title': 'Test Issue: Add README',
        'description': 'Add a README file to the project',
        'url': 'https://github.com/test/repo/issues/1',
        'value': 100,
        'urgency': 'low',
        'created_at': datetime.now().isoformat()
    }
    
    executor = get_executor()
    result = await executor.execute_opportunity(test_opportunity, auto_approve=True)
    
    return {
        'ok': True,
        'test': 'completed',
        'result': result
    }
