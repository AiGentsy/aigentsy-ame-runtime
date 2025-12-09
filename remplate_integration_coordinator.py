"""
Template Integration Coordinator
Ultra-thin layer that connects templates to your existing 140+ AiGentsy systems

This doesn't rebuild anything - it just calls what you already have:
- CSuiteOrchestrator (business intelligence + opportunities)
- AMGOrchestrator (10-stage revenue loop)
- AiGentsy Conductor (multi-device execution)
- MetaBridge, MetaHive, JV Mesh, etc (all your existing systems)
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from log_to_jsonbin import get_user, log_agent_update


async def coordinate_template_activation(
    template_id: str,
    username: str,
    user_data: Dict = None
) -> Dict[str, Any]:
    """
    Ultra-thin coordinator that leverages ALL your existing systems
    
    Flow:
    1. CSuiteOrchestrator generates kit-specific opportunities
    2. AMGOrchestrator runs full 10-stage cycle
    3. AiGentsy Conductor creates execution plan
    4. Store results in dashboard
    
    This is ~50 lines because YOU ALREADY BUILT EVERYTHING!
    """
    
    print(f"\n{'='*70}")
    print(f"🔗 TEMPLATE INTEGRATION COORDINATOR")
    print(f"   Template: {template_id}")
    print(f"   User: {username}")
    print(f"{'='*70}\n")
    
    if not user_data:
        user_data = get_user(username)
    
    results = {
        "ok": True,
        "template_id": template_id,
        "username": username,
        "systems_triggered": []
    }
    
    # ============================================================
    # STEP 1: BUSINESS INTELLIGENCE (Use CSuiteOrchestrator)
    # ============================================================
    
    print("🧠 Analyzing business state...")
    
    from csuite_orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    
    # Get comprehensive intelligence
    intelligence = await orchestrator.analyze_business_state(username)
    
    if not intelligence.get("ok"):
        return {"ok": False, "error": "Intelligence analysis failed"}
    
    # Generate kit-specific opportunities
    opportunities = await orchestrator.generate_opportunities(username, intelligence)
    
    results["intelligence"] = {
        "kit_type": intelligence["capabilities"]["kit_type"],
        "tier": intelligence["capabilities"]["tier"],
        "reputation": intelligence["reputation"],
        "apex_ready": intelligence["systems"]["apex_ultra_active"]
    }
    results["opportunities_generated"] = len(opportunities)
    results["systems_triggered"].append("CSuiteOrchestrator")
    
    print(f"   ✅ Intelligence: {intelligence['capabilities']['kit_type']} kit, Rep {intelligence['reputation']}")
    print(f"   ✅ Opportunities: {len(opportunities)} found")
    
    # ============================================================
    # STEP 2: REVENUE LOOP (Use AMGOrchestrator)
    # ============================================================
    
    print("\n💰 Running AMG revenue cycle...")
    
    from amg_orchestrator import AMGOrchestrator
    
    amg = AMGOrchestrator(username)
    
    # Initialize graph if needed
    if not amg.user.get("amg", {}).get("graph_initialized"):
        await amg.initialize_graph()
    
    # Run full 10-stage cycle
    amg_result = await amg.run_cycle()
    
    results["amg"] = {
        "cycle_complete": amg_result.get("cycle_complete"),
        "opportunities_detected": amg_result.get("results", {}).get("sense", {}).get("opportunities_found", 0),
        "actions_executed": amg_result.get("results", {}).get("route", {}).get("actions_executed", 0),
        "revenue": amg_result.get("results", {}).get("settle", {}).get("revenue", 0)
    }
    results["systems_triggered"].append("AMGOrchestrator")
    
    print(f"   ✅ AMG: {results['amg']['opportunities_detected']} opportunities detected")
    print(f"   ✅ AMG: {results['amg']['actions_executed']} actions executed")
    
    # ============================================================
    # STEP 3: MULTI-DEVICE COORDINATION (Use AiGentsy Conductor)
    # ============================================================
    
    print("\n🔧 Scanning device capabilities...")
    
    from aigentsy_conductor import scan_opportunities, create_execution_plan
    
    # Get device_id from user (or default)
    device_id = user_data.get("primary_device_id", "web_dashboard")
    
    try:
        # Scan for device-specific opportunities
        device_opps = await scan_opportunities(username, device_id)
        
        if device_opps.get("ok"):
            # Create execution plan
            plan = await create_execution_plan(
                username=username,
                device_id=device_id,
                opportunities=device_opps.get("opportunities", []),
                max_actions=10
            )
            
            results["conductor"] = {
                "device_opportunities": device_opps.get("count", 0),
                "execution_plan_created": plan.get("ok"),
                "plan_id": plan.get("plan_id"),
                "auto_approved": plan.get("summary", {}).get("auto_approved", 0),
                "needs_approval": plan.get("summary", {}).get("needs_approval", 0)
            }
            results["systems_triggered"].append("AiGentsyConductor")
            
            print(f"   ✅ Conductor: {results['conductor']['device_opportunities']} device opportunities")
            print(f"   ✅ Conductor: Plan {plan.get('plan_id')} created")
        
    except Exception as e:
        print(f"   ⚠️  Conductor optional, skipped: {e}")
        results["conductor"] = {"skipped": True, "reason": str(e)}
    
    # ============================================================
    # STEP 4: STORE IN DASHBOARD
    # ============================================================
    
    print("\n💾 Storing opportunities in dashboard...")
    
    # Add opportunities to user dashboard
    if "opportunities" not in user_data:
        user_data["opportunities"] = []
    
    # Convert CSuite opportunities to dashboard format
    for opp in opportunities[:5]:  # Top 5
        dashboard_opp = {
            "id": f"opp_{opp['opportunity_id']}",
            "source": "template_activation",
            "template_id": template_id,
            "type": opp["opportunity_id"],
            "title": opp["title"],
            "description": opp["description"],
            "estimated_value": opp["revenue_potential"],
            "timeframe_days": 30,  # Default
            "confidence": opp["confidence"],
            "pricing": opp["pricing"],
            "target_customers": opp["target_customers"],
            "status": "pending",
            "readiness": opp["readiness_status"],
            "unlock_requirements": opp.get("unlock_requirements"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        user_data["opportunities"].append(dashboard_opp)
    
    # Save to JSONBin
    log_agent_update(user_data)
    
    results["dashboard_updated"] = True
    results["opportunities_stored"] = len(opportunities[:5])
    
    print(f"   ✅ Dashboard: {results['opportunities_stored']} opportunities stored")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    
    print(f"\n{'='*70}")
    print(f"✅ COORDINATION COMPLETE")
    print(f"   Systems triggered: {', '.join(results['systems_triggered'])}")
    print(f"   Opportunities created: {results['opportunities_stored']}")
    print(f"   User ready to: Approve opportunities → Make money")
    print(f"{'='*70}\n")
    
    return results


# ============================================================
# MINT INTEGRATION (Auto-trigger on signup)
# ============================================================

async def auto_trigger_on_mint(username: str, template: str, user_data: Dict) -> Dict:
    """
    Called from /mint endpoint to auto-trigger integration
    
    This is THE KEY: User signs up → Everything fires automatically
    """
    
    print(f"🚀 AUTO-TRIGGERING template integration for {username} at mint")
    
    # Run coordination
    result = await coordinate_template_activation(
        template_id=template,
        username=username,
        user_data=user_data
    )
    
    return {
        "ok": True,
        "auto_triggered": True,
        "template": template,
        "coordination_result": result,
        "message": f"Welcome! {result['opportunities_stored']} opportunities ready for you."
    }


# ============================================================
# EXTERNAL TARGET DISCOVERY (For Question 1)
# ============================================================

async def discover_all_targets(username: str, template_context: Dict) -> Dict:
    """
    Discover targets across ALL 4 types:
    1. On-platform agents
    2. On-platform humans
    3. Off-platform (MetaMatch finds them)
    4. Inbound (they find us)
    
    This calls your EXISTING MetaBridge, Growth Agent, etc.
    """
    
    from log_to_jsonbin import list_users
    
    targets = {
        "on_platform_agents": [],
        "on_platform_humans": [],
        "off_platform_discovered": [],
        "inbound_leads": []
    }
    
    # 1. ON-PLATFORM AGENTS (Use MetaBridge)
    try:
        from metabridge import find_complementary_agents
        
        agents = find_complementary_agents(
            intent={"service": template_context.get("service_type")},
            all_agents=list_users()
        )
        
        targets["on_platform_agents"] = agents if agents.get("ok") else []
        
    except Exception as e:
        print(f"   ⚠️  MetaBridge unavailable: {e}")
    
    # 2. ON-PLATFORM HUMANS
    all_users = list_users()
    for user in all_users:
        if not user.get("apex_ultra", {}).get("activated"):
            # This is a human user
            targets["on_platform_humans"].append({
                "username": user["username"],
                "needs": user.get("needs", [])
            })
    
    # 3. OFF-PLATFORM DISCOVERY (Use Growth Agent)
    try:
        from aigent_growth_agent import metabridge_dual_match_realworld_fulfillment
        
        external_matches = metabridge_dual_match_realworld_fulfillment(
            query=template_context.get("search_query", f"need {template_context.get('service_type')}")
        )
        
        targets["off_platform_discovered"] = external_matches if isinstance(external_matches, list) else []
        
    except Exception as e:
        print(f"   ⚠️  Growth Agent unavailable: {e}")
    
    # 4. INBOUND (Would come from MetaMatch Reddit/Upwork scrapers)
    # This is passive - they find us through SEO, ads, etc.
    # For now, placeholder
    targets["inbound_leads"] = []
    
    return {
        "ok": True,
        "targets": targets,
        "total_discovered": sum(len(v) if isinstance(v, list) else 0 for v in targets.values())
    }


# ============================================================
# AGENT-TO-AGENT AUTO-NEGOTIATION (For Question 1)
# ============================================================

async def auto_negotiate_agent_deal(
    proposer: str,
    target_agent: str,
    service: str,
    terms: Dict
) -> Dict:
    """
    AI-to-AI negotiation without human approval
    
    Uses your existing JV Mesh for this
    """
    
    from jv_mesh import auto_propose_jv, calculate_compatibility_score
    from log_to_jsonbin import list_users
    
    # Calculate compatibility
    compatibility = calculate_compatibility_score(proposer, target_agent)
    
    if not compatibility.get("ok") or compatibility.get("score", 0) < 0.7:
        return {
            "ok": False,
            "reason": "low_compatibility",
            "score": compatibility.get("score", 0)
        }
    
    # Auto-propose JV
    jv_result = await auto_propose_jv(
        agent=proposer,
        service=service,
        all_agents=list_users()
    )
    
    return {
        "ok": jv_result.get("ok"),
        "jv_created": True,
        "compatibility_score": compatibility.get("score"),
        "auto_negotiated": True,
        "human_approval_required": False
    }


# ============================================================
# SIGNUP FUNNEL INTEGRATION (For Question 1)
# ============================================================

def generate_signup_link(
    referrer_username: str,
    template_id: str,
    target_platform: str
) -> str:
    """
    Generate signup link for external targets
    
    When they sign up, deal is auto-created
    """
    
    return f"https://aigentsy.com/signup?ref={referrer_username}&deal={template_id}&source={target_platform}"


async def process_referral_signup(
    new_username: str,
    referrer_username: str,
    deal_template: str
) -> Dict:
    """
    Process signup from referral link
    Auto-create deal between referrer and new user
    
    This gets called from /mint when ref= is present
    """
    
    from dealgraph import create_deal
    
    # Create deal automatically
    deal = create_deal(
        intent={
            "id": f"intent_{new_username}_{deal_template}",
            "buyer": new_username,
            "service": deal_template,
            "budget": 500  # Default
        },
        agent_username=referrer_username,
        slo_tier="standard"
    )
    
    return {
        "ok": True,
        "deal_created": True,
        "deal_id": deal.get("deal", {}).get("id"),
        "referrer": referrer_username,
        "new_user": new_username,
        "auto_created": True
    }
