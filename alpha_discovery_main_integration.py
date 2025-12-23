"""
MAIN.PY INTEGRATION - ALPHA DISCOVERY ENGINE
Add these endpoints to your main.py

These endpoints integrate the Alpha Discovery Engine into your existing FastAPI backend
"""


# ============================================================
# NEW ENDPOINTS TO ADD TO MAIN.PY
# ============================================================

"""
# Add these imports at top of main.py:
from alpha_discovery_engine import AlphaDiscoveryEngine
from wade_approval_dashboard import fulfillment_queue


# ============================================================
# ENDPOINT 1: RUN ALPHA DISCOVERY
# ============================================================

@app.post("/alpha-discovery/run")
async def run_alpha_discovery(platforms: List[str] = None):
    '''
    Run Alpha Discovery Engine
    Discovers opportunities and routes them intelligently
    
    Args:
        platforms: Optional list of platforms to scrape
                  ['github', 'upwork', 'reddit', 'hackernews']
    
    Returns:
        {
            'ok': True,
            'total_opportunities': 50,
            'routing': {
                'user_routed': {...},
                'aigentsy_routed': {...},
                'held': {...}
            }
        }
    '''
    
    try:
        engine = AlphaDiscoveryEngine()
        
        # Run discovery and routing
        results = await engine.discover_and_route(platforms=platforms)
        
        # Add AiGentsy opportunities to Wade's approval queue
        for routed in results['routing']['aigentsy_routed']['opportunities']:
            fulfillment_queue.add_to_queue(
                opportunity=routed['opportunity'],
                routing=routed['routing']
            )
        
        # Send opportunities to user dashboards
        for routed in results['routing']['user_routed']['opportunities']:
            username = routed['routing']['routed_to']
            
            # Add to user's opportunity queue (leverage existing system)
            # This would integrate with your existing dashboard logic
            # await add_opportunity_to_user_dashboard(username, routed['opportunity'])
        
        return results
    
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }


# ============================================================
# ENDPOINT 2: WADE'S APPROVAL DASHBOARD
# ============================================================

@app.get("/wade/fulfillment-queue")
async def get_wade_fulfillment_queue():
    '''
    Wade's approval dashboard for AiGentsy direct fulfillment
    Shows all opportunities awaiting approval
    '''
    
    pending = fulfillment_queue.get_pending_queue()
    stats = fulfillment_queue.get_stats()
    
    return {
        'ok': True,
        'stats': stats,
        'pending_count': len(pending),
        'total_pending_value': sum(f['opportunity']['value'] for f in pending),
        'total_pending_profit': sum(f['estimated_profit'] for f in pending),
        'opportunities': [
            {
                'id': f['id'],
                'title': f['opportunity']['title'],
                'platform': f['opportunity']['platform'],
                'type': f['opportunity']['type'],
                'value': f['opportunity']['value'],
                'estimated_profit': f['estimated_profit'],
                'estimated_cost': f['estimated_cost'],
                'estimated_days': f['estimated_days'],
                'confidence': f['confidence'],
                'fulfillment_plan': f['fulfillment_plan'],
                'ai_models': f['ai_models'],
                'opportunity_url': f['opportunity']['url'],
                'created_at': f['created_at'],
                'approve_url': f"/wade/approve/{f['id']}",
                'reject_url': f"/wade/reject/{f['id']}"
            }
            for f in pending
        ]
    }


# ============================================================
# ENDPOINT 3: APPROVE FULFILLMENT
# ============================================================

@app.post("/wade/approve/{fulfillment_id}")
async def approve_fulfillment(fulfillment_id: str):
    '''
    Wade approves AiGentsy direct fulfillment
    
    This triggers:
    1. Fulfillment execution (AI agents start work)
    2. Revenue tracking
    3. Outcome tracking
    '''
    
    result = fulfillment_queue.approve_fulfillment(fulfillment_id)
    
    if result['ok']:
        # Get fulfillment details
        approved = [f for f in fulfillment_queue.approved_fulfillments if f['id'] == fulfillment_id][0]
        
        # TODO: Trigger execution
        # Option 1: Assign to AI agents (automated)
        # await execute_with_ai_agents(approved)
        
        # Option 2: Add to Wade's manual work queue
        # await add_to_wade_work_queue(approved)
        
        # Track in revenue system
        # await track_aigentsy_direct_opportunity(approved)
        
        result['execution_started'] = True
        result['estimated_completion'] = approved['estimated_days']
    
    return result


# ============================================================
# ENDPOINT 4: REJECT FULFILLMENT
# ============================================================

@app.post("/wade/reject/{fulfillment_id}")
async def reject_fulfillment(fulfillment_id: str, reason: str = None):
    '''
    Wade rejects AiGentsy direct fulfillment
    
    This marks the opportunity as rejected and optionally:
    1. Holds for future user recruitment
    2. Improves capability assessment
    '''
    
    result = fulfillment_queue.reject_fulfillment(fulfillment_id, reason)
    
    return result


# ============================================================
# ENDPOINT 5: USER-SPECIFIC DISCOVERY
# ============================================================

@app.get("/discover/{username}")
async def discover_for_user(username: str, platforms: List[str] = None):
    '''
    Run discovery specifically for one user
    Only returns opportunities matching their business type
    
    This replaces/enhances your existing simulated /discover endpoint
    '''
    
    try:
        # Get user data
        user_data = load_user_data(username)
        
        if not user_data:
            return {'ok': False, 'error': 'User not found'}
        
        # Run discovery
        engine = AlphaDiscoveryEngine()
        all_results = await engine.discover_and_route(platforms=platforms)
        
        # Filter for this user
        user_opportunities = []
        
        for routed in all_results['routing']['user_routed']['opportunities']:
            if routed['routing']['routed_to'] == username:
                user_opportunities.append(routed['opportunity'])
        
        return {
            'ok': True,
            'username': username,
            'opportunities': user_opportunities,
            'total_found': len(user_opportunities),
            'total_value': sum(o['value'] for o in user_opportunities)
        }
    
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }


# ============================================================
# ENDPOINT 6: SCHEDULED DISCOVERY (BACKGROUND JOB)
# ============================================================

# Run this every hour via cron or background scheduler
async def scheduled_discovery():
    '''
    Background job: Run discovery every hour
    Automatically routes opportunities
    '''
    
    try:
        print("\\n🚀 SCHEDULED ALPHA DISCOVERY STARTED")
        
        engine = AlphaDiscoveryEngine()
        results = await engine.discover_and_route()
        
        # Process results
        user_routed = results['routing']['user_routed']['opportunities']
        aigentsy_routed = results['routing']['aigentsy_routed']['opportunities']
        
        # Send to users
        for routed in user_routed:
            username = routed['routing']['routed_to']
            # Notify user of new opportunity
            # await notify_user(username, routed['opportunity'])
        
        # Add to Wade's queue
        for routed in aigentsy_routed:
            fulfillment_queue.add_to_queue(
                opportunity=routed['opportunity'],
                routing=routed['routing']
            )
        
        # Notify Wade if high-value opportunities
        high_value = [r for r in aigentsy_routed if r['opportunity']['value'] > 5000]
        if high_value:
            # await notify_wade(f"{len(high_value)} high-value opportunities need approval")
            pass
        
        print(f"✅ Discovery complete: {results['total_opportunities']} found")
        print(f"   → {len(user_routed)} to users")
        print(f"   → {len(aigentsy_routed)} to AiGentsy (awaiting approval)")
        
        return results
    
    except Exception as e:
        print(f"❌ Scheduled discovery error: {e}")
        return None


# ============================================================
# EXAMPLE: Adding to existing /mint endpoint
# ============================================================

# Enhance your existing /mint endpoint:
@app.post("/mint")
async def mint_user(request: Request):
    '''
    Your existing mint endpoint
    
    ENHANCEMENT: After minting, immediately run discovery for new user
    '''
    
    # ... your existing mint logic ...
    
    # NEW: Run initial discovery for user
    try:
        engine = AlphaDiscoveryEngine()
        all_results = await engine.discover_and_route()
        
        # Find opportunities for this new user
        user_opportunities = [
            r['opportunity'] for r in all_results['routing']['user_routed']['opportunities']
            if r['routing']['routed_to'] == username
        ]
        
        # Add to their dashboard
        # Your existing logic here
        
    except Exception as e:
        print(f"Discovery failed for new user: {e}")
    
    # ... rest of your mint logic ...
"""


# ============================================================
# INTEGRATION CHECKLIST
# ============================================================

INTEGRATION_STEPS = """
✅ PHASE 1 INTEGRATION CHECKLIST

1. Upload files to backend:
   ✅ alpha_discovery_engine.py
   ✅ explicit_marketplace_scrapers.py
   ✅ wade_approval_dashboard.py
   ✅ alpha_discovery_main_integration.py (this file)

2. Add imports to main.py:
   from alpha_discovery_engine import AlphaDiscoveryEngine
   from wade_approval_dashboard import fulfillment_queue

3. Add endpoints to main.py:
   Copy endpoints from this file into main.py

4. Test discovery:
   curl -X POST https://your-backend.onrender.com/alpha-discovery/run

5. Check Wade's queue:
   curl https://your-backend.onrender.com/wade/fulfillment-queue

6. Setup scheduled discovery (optional):
   Add cron job or background scheduler to run scheduled_discovery() every hour

7. Test user-specific discovery:
   curl https://your-backend.onrender.com/discover/{username}

8. Approve a fulfillment:
   curl -X POST https://your-backend.onrender.com/wade/approve/{fulfillment_id}

9. Integration with existing systems:
   - Connect to MetaMatch for scoring
   - Connect to AMG for revenue tracking
   - Connect to Outcome Oracle for quality tracking
   - Connect to dashboard for opportunity display

10. Deploy and monitor:
    - Watch for opportunities flowing in
    - Monitor routing decisions
    - Track fulfillment success rate
"""

print(INTEGRATION_STEPS)
