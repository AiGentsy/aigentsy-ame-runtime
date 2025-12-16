"""
Template Integration Coordinator - UPGRADED
Now includes external discovery engine + template system

Leverages YOUR existing 160+ systems:
- CSuiteOrchestrator ✅
- AMGOrchestrator ✅
- AiGentsy Conductor ✅
- MetaBridge, MetaHive, JV Mesh ✅

NEW: External opportunity discovery via Growth Agent (GitHub, LinkedIn, Upwork, Reddit, HN)
"""

import os
from typing import Dict, Any, List
from datetime import datetime, timezone
from log_to_jsonbin import get_user, log_agent_update


async def coordinate_template_activation(
    template_id: str,
    username: str,
    user_data: Dict = None
) -> Dict[str, Any]:
    """
    UPGRADED: Now returns both internal + external opportunities
    
    Flow:
    1. CSuiteOrchestrator generates internal opportunities ✅
    2. Growth Agent Discovery Engine scrapes external platforms 🆕
    3. AMGOrchestrator runs full 10-stage cycle ✅
    4. AiGentsy Conductor creates execution plan ✅
    5. Store EVERYTHING in dashboard
    """
    
    print(f"\n{'='*70}")
    print(f"🔗 TEMPLATE INTEGRATION COORDINATOR (UPGRADED)")
    print(f"   Template: {template_id}")
    print(f"   User: {username}")
    print(f"{'='*70}\n")
    
    if not user_data:
        user_data = get_user(username)
    
    results = {
        "ok": True,
        "template_id": template_id,
        "username": username,
        "systems_triggered": [],
        "opportunities": {
            "internal": [],
            "external": []
        }
    }
    
    # ============================================================
    # STEP 1: INTERNAL OPPORTUNITIES (CSuite - YOUR CODE)
    # ============================================================
    
    print("🧠 Analyzing business state (CSuite)...")
    
    try:
        from csuite_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        # Get comprehensive intelligence
        intelligence = await orchestrator.analyze_business_state(username)
        
        if intelligence.get("ok"):
            # Generate kit-specific opportunities
            opportunities = await orchestrator.generate_opportunities(username, intelligence)
            
            results["intelligence"] = {
                "kit_type": intelligence["capabilities"]["kit_type"],
                "tier": intelligence["capabilities"]["tier"],
                "reputation": intelligence["reputation"],
                "apex_ready": intelligence["systems"]["apex_ultra_active"]
            }
            results["opportunities"]["internal"] = opportunities
            results["systems_triggered"].append("CSuiteOrchestrator")
            
            print(f"   ✅ Intelligence: {intelligence['capabilities']['kit_type']} kit")
            print(f"   ✅ Internal opportunities: {len(opportunities)}")
    
    except Exception as e:
        print(f"   ⚠️  CSuite error: {e}")
        results["opportunities"]["internal"] = []
    
    # ============================================================
    # STEP 2: EXTERNAL OPPORTUNITIES (NEW - GROWTH AGENT DISCOVERY)
    # ============================================================
    
    print("\n🔍 Discovering external opportunities (Growth Agent)...")
    
    try:
        import httpx
        
        BACKEND_BASE = os.getenv("BACKEND_BASE", "http://localhost:8000").rstrip("/")
        
        async with httpx.AsyncClient() as client:
            discovery_payload = {
                "username": username,
                "platforms": ["github", "upwork", "reddit", "hackernews"],
                "auto_bid": False  # Don't auto-bid at mint
            }
            
            discovery_response = await client.post(
                f"{BACKEND_BASE}/discover",
                json=discovery_payload,
                timeout=30.0
            )
            
            if discovery_response.status_code == 200:
                discovery_result = discovery_response.json()
                
                if discovery_result.get("status") == "ok":
                    external_opps = discovery_result.get("opportunities", [])
                    
                    results["opportunities"]["external"] = external_opps
                    results["external_count"] = len(external_opps)
                    results["platforms_scraped"] = discovery_result.get("platforms_scraped", [])
                    results["systems_triggered"].append("GrowthAgentDiscovery")
                    
                    print(f"   ✅ External opportunities: {len(external_opps)}")
                    if results.get("platforms_scraped"):
                        print(f"   ✅ Platforms: {', '.join(results['platforms_scraped'])}")
                else:
                    print(f"   ⚠️  Discovery returned: {discovery_result.get('status')}")
                    results["opportunities"]["external"] = []
            else:
                print(f"   ⚠️  Discovery endpoint: {discovery_response.status_code}")
                results["opportunities"]["external"] = []
    
    except Exception as e:
        print(f"   ⚠️  Growth Agent discovery error: {e}")
        results["opportunities"]["external"] = []
    
    # ============================================================
    # STEP 3: AMG REVENUE LOOP (YOUR CODE)
    # ============================================================
    
    print("\n💰 Running AMG revenue cycle...")
    
    try:
        from amg_orchestrator import AMGOrchestrator
        
        amg = AMGOrchestrator(username)
        
        if not amg.user.get("amg", {}).get("graph_initialized"):
            await amg.initialize_graph()
        
        amg_result = await amg.run_cycle()
        
        results["amg"] = {
            "cycle_complete": amg_result.get("cycle_complete"),
            "opportunities_detected": amg_result.get("results", {}).get("sense", {}).get("opportunities_found", 0),
            "actions_executed": amg_result.get("results", {}).get("route", {}).get("actions_executed", 0),
            "revenue": amg_result.get("results", {}).get("settle", {}).get("revenue", 0)
        }
        results["systems_triggered"].append("AMGOrchestrator")
        
        print(f"   ✅ AMG: {results['amg']['opportunities_detected']} opportunities detected")
    
    except Exception as amg_error:
        print(f"   ⚠️  AMG cycle skipped: {amg_error}")
        results["amg"] = {"skipped": True, "error": str(amg_error)}
    
    # ============================================================
    # STEP 4: CONDUCTOR COORDINATION (YOUR CODE)
    # ============================================================
    
    print("\n🔧 Creating execution plan (Conductor)...")
    
    try:
        from aigentsy_conductor import scan_opportunities, create_execution_plan
        
        device_id = user_data.get("primary_device_id", "web_dashboard")
        device_opps = await scan_opportunities(username, device_id)
        
        if device_opps.get("ok"):
            plan = await create_execution_plan(
                username=username,
                device_id=device_id,
                opportunities=device_opps.get("opportunities", []),
                max_actions=10
            )
            
            results["conductor"] = {
                "device_opportunities": device_opps.get("count", 0),
                "plan_id": plan.get("plan_id"),
                "auto_approved": plan.get("summary", {}).get("auto_approved", 0),
                "needs_approval": plan.get("summary", {}).get("needs_approval", 0)
            }
            results["systems_triggered"].append("AiGentsyConductor")
            
            print(f"   ✅ Conductor: Plan {plan.get('plan_id')} created")
    
    except Exception as conductor_error:
        print(f"   ⚠️  Conductor skipped: {conductor_error}")
        results["conductor"] = {"skipped": True}
    
    # ============================================================
    # STEP 5: STORE IN DASHBOARD
    # ============================================================
    
    print("\n💾 Storing in dashboard...")
    
    if "opportunities" not in user_data:
        user_data["opportunities"] = []
    
    # Store internal opportunities
    for opp in results["opportunities"]["internal"][:5]:
        dashboard_opp = {
            "id": f"internal_{opp['opportunity_id']}",
            "source": "template_activation",
            "type": opp["opportunity_id"],
            "title": opp["title"],
            "description": opp["description"],
            "estimated_value": opp["revenue_potential"],
            "confidence": opp["confidence"],
            "status": "pending_approval",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        user_data["opportunities"].append(dashboard_opp)
    
    # Store external opportunities (already formatted correctly from Growth Agent)
    for opp in results["opportunities"]["external"]:
        user_data["opportunities"].append(opp)
    
    log_agent_update(user_data)
    
    total_stored = len(results["opportunities"]["internal"][:5]) + len(results["opportunities"]["external"])
    
    print(f"   ✅ Stored {total_stored} opportunities")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    
    print(f"\n{'='*70}")
    print(f"✅ COORDINATION COMPLETE")
    print(f"   Systems: {', '.join(results['systems_triggered'])}")
    print(f"   Internal: {len(results['opportunities']['internal'])}")
    print(f"   External: {len(results['opportunities']['external'])}")
    print(f"   Total: {total_stored} ready for approval")
    print(f"{'='*70}\n")
    
    return results


# ============================================================
# MINT INTEGRATION (UNCHANGED - ALREADY WORKS)
# ============================================================

async def auto_trigger_on_mint(username: str, company_type: str) -> Dict:
    """
    Called from /mint endpoint
    Now returns internal + external opportunities via Growth Agent
    """
    
    print(f"🚀 AUTO-TRIGGERING at mint for {username}")
    
    result = await coordinate_template_activation(
        template_id=company_type,
        username=username,
        user_data=get_user(username)
    )
    
    internal_count = len(result["opportunities"]["internal"])
    external_count = len(result["opportunities"]["external"])
    total_count = internal_count + external_count
    
    return {
        "ok": True,
        "auto_triggered": True,
        "template": company_type,
        "opportunities": {
            "internal": internal_count,
            "external": external_count,
            "total": total_count
        },
        "message": f"Welcome! {total_count} opportunities ready ({internal_count} internal + {external_count} external)"
    }


# ============================================================
# REFERRAL SIGNUP (UNCHANGED)
# ============================================================

def generate_signup_link(
    referrer_username: str,
    template_id: str,
    target_platform: str
) -> str:
    """Generate signup link for external targets"""
    return f"https://aigentsy.com/signup?ref={referrer_username}&deal={template_id}&source={target_platform}"


async def process_referral_signup(
    new_username: str,
    referrer_username: str,
    deal_template: str
) -> Dict:
    """Process signup from referral link"""
    from dealgraph import create_deal
    
    deal = create_deal(
        intent={
            "id": f"intent_{new_username}_{deal_template}",
            "buyer": new_username,
            "service": deal_template,
            "budget": 500
        },
        agent_username=referrer_username,
        slo_tier="standard"
    )
    
    return {
        "ok": True,
        "deal_created": True,
        "deal_id": deal.get("deal", {}).get("id"),
        "referrer": referrer_username,
        "new_user": new_username
    }
