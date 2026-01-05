# diagnostic_tracer.py
"""
🔍 AIGENTSY DIAGNOSTIC TRACER
==============================

Traces exactly what happens during an autonomous cycle:
1. What platforms are we searching?
2. What opportunities are we finding?
3. What actions are we taking?
4. Where are the gaps to monetization?

USAGE:
    from diagnostic_tracer import include_diagnostic_tracer
    include_diagnostic_tracer(app)

Then call: GET /diagnostic/full-cycle-trace
"""

from fastapi import APIRouter
from datetime import datetime, timezone
from typing import Dict, Any, List
import os
import httpx

router = APIRouter(tags=["Diagnostics"])


def _now():
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# ENV VAR CHECK
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/diagnostic/env-check")
async def check_environment():
    """
    Check which API keys are configured and which are missing.
    """
    
    # All possible env vars grouped by function
    env_groups = {
        "AI_GENERATION": {
            "OPENROUTER_API_KEY": "All LLMs (Claude, GPT, etc)",
            "PERPLEXITY_API_KEY": "Web search AI",
            "GEMINI_API_KEY": "Google AI",
            "STABILITY_API_KEY": "Image generation",
            "RUNWAY_API_KEY": "Video generation",
        },
        "PAYMENTS": {
            "STRIPE_SECRET_KEY": "Payment processing",
            "STRIPE_WEBHOOK_SECRET": "Payment webhooks",
        },
        "ECOMMERCE": {
            "SHOPIFY_ADMIN_TOKEN": "Store management",
            "SHOPIFY_WEBHOOK_SECRET": "Store webhooks",
            "SHOPIFY_STORE_URL": "Store URL",
        },
        "FREELANCE_PLATFORMS": {
            "FIVERR_API_KEY": "Fiverr gigs",
            "UPWORK_API_KEY": "Upwork jobs",
            "TOPTAL_API_KEY": "Toptal",
            "FREELANCER_API_KEY": "Freelancer.com",
        },
        "SOCIAL_MEDIA": {
            "TWITTER_API_KEY": "Twitter/X posting",
            "TWITTER_API_SECRET": "Twitter/X auth",
            "TWITTER_ACCESS_TOKEN": "Twitter/X access",
            "TWITTER_ACCESS_SECRET": "Twitter/X access",
            "LINKEDIN_ACCESS_TOKEN": "LinkedIn posting",
            "INSTAGRAM_ACCESS_TOKEN": "Instagram posting",
            "TIKTOK_ACCESS_TOKEN": "TikTok posting",
        },
        "EMAIL_SMS": {
            "RESEND_API_KEY": "Email sending",
            "SENDGRID_API_KEY": "Email (alt)",
            "TWILIO_ACCOUNT_SID": "SMS sending",
            "TWILIO_AUTH_TOKEN": "SMS auth",
            "TWILIO_PHONE_NUMBER": "SMS from number",
        },
        "SCHEDULING": {
            "CALENDLY_API_KEY": "Booking/scheduling",
            "SQUARE_ACCESS_TOKEN": "POS/payments",
        },
        "STORAGE": {
            "AWS_ACCESS_KEY_ID": "AWS services",
            "AWS_SECRET_ACCESS_KEY": "AWS auth",
            "JSONBIN_URL": "Data persistence",
            "JSONBIN_SECRET": "JSONBin auth",
        },
        "INTERNAL": {
            "GITHUB_TOKEN": "Repo access",
            "BACKEND_BASE": "Self URL",
            "SELF_URL": "Self URL",
        }
    }
    
    results = {}
    total_configured = 0
    total_missing = 0
    critical_missing = []
    
    for group_name, vars in env_groups.items():
        group_results = {}
        for var_name, description in vars.items():
            value = os.environ.get(var_name)
            is_set = bool(value and len(value) > 5)
            group_results[var_name] = {
                "configured": is_set,
                "description": description,
                "preview": f"{value[:8]}..." if is_set and len(value) > 8 else ("SET" if is_set else "MISSING")
            }
            if is_set:
                total_configured += 1
            else:
                total_missing += 1
                if group_name in ["PAYMENTS", "FREELANCE_PLATFORMS"]:
                    critical_missing.append(var_name)
        
        results[group_name] = group_results
    
    return {
        "ok": True,
        "summary": {
            "total_configured": total_configured,
            "total_missing": total_missing,
            "critical_missing": critical_missing,
            "ready_for_monetization": len(critical_missing) == 0
        },
        "groups": results,
        "checked_at": _now()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FULL CYCLE TRACE
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/diagnostic/full-cycle-trace")
async def full_cycle_trace():
    """
    Trace a full autonomous cycle and report what's happening at each step.
    """
    
    trace = {
        "started_at": _now(),
        "phases": [],
        "opportunities_found": [],
        "actions_taken": [],
        "gaps": [],
        "revenue_potential": 0
    }
    
    backend_url = os.environ.get("SELF_URL") or os.environ.get("BACKEND_BASE") or "https://aigentsy-ame-runtime.onrender.com"
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # ─────────────────────────────────────────────────────────────────────
        # PHASE 1: DISCOVERY - What platforms are we searching?
        # ─────────────────────────────────────────────────────────────────────
        phase1 = {"name": "DISCOVERY", "status": "running", "details": {}}
        
        try:
            # Check vacuum/scrape endpoints
            r = await client.post(f"{backend_url}/vacuum/scrape-all", json={"platforms": "all"}, timeout=60)
            phase1["details"]["vacuum"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase1["details"]["vacuum"] = {"error": str(e)}
        
        try:
            # Check mega-discover
            r = await client.post(f"{backend_url}/execution/mega-discover", json={}, timeout=60)
            phase1["details"]["mega_discover"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase1["details"]["mega_discover"] = {"error": str(e)}
        
        try:
            # Check sniper
            r = await client.post(f"{backend_url}/sniper/fresh-opportunities", json={"max_age_minutes": 60}, timeout=30)
            phase1["details"]["sniper"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase1["details"]["sniper"] = {"error": str(e)}
        
        phase1["status"] = "complete"
        trace["phases"].append(phase1)
        
        # ─────────────────────────────────────────────────────────────────────
        # PHASE 2: BIDDING/PROPOSALS - Are we actually bidding?
        # ─────────────────────────────────────────────────────────────────────
        phase2 = {"name": "BIDDING", "status": "running", "details": {}}
        
        try:
            r = await client.post(f"{backend_url}/sniper/auto-bid", json={"min_ev": 50}, timeout=60)
            phase2["details"]["auto_bid"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase2["details"]["auto_bid"] = {"error": str(e)}
        
        try:
            r = await client.post(f"{backend_url}/swarm/compete", json={"task_type": "all"}, timeout=60)
            phase2["details"]["swarm"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase2["details"]["swarm"] = {"error": str(e)}
        
        phase2["status"] = "complete"
        trace["phases"].append(phase2)
        
        # ─────────────────────────────────────────────────────────────────────
        # PHASE 3: FULFILLMENT - Are we delivering work?
        # ─────────────────────────────────────────────────────────────────────
        phase3 = {"name": "FULFILLMENT", "status": "running", "details": {}}
        
        try:
            r = await client.post(f"{backend_url}/fulfillment/process-queue", json={}, timeout=60)
            phase3["details"]["process_queue"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase3["details"]["process_queue"] = {"error": str(e)}
        
        try:
            r = await client.post(f"{backend_url}/fulfillment/auto-deliver", json={}, timeout=60)
            phase3["details"]["auto_deliver"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase3["details"]["auto_deliver"] = {"error": str(e)}
        
        phase3["status"] = "complete"
        trace["phases"].append(phase3)
        
        # ─────────────────────────────────────────────────────────────────────
        # PHASE 4: REVENUE - Are we getting paid?
        # ─────────────────────────────────────────────────────────────────────
        phase4 = {"name": "REVENUE", "status": "running", "details": {}}
        
        try:
            r = await client.get(f"{backend_url}/revenue-orchestrator/dashboard", timeout=30)
            phase4["details"]["dashboard"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase4["details"]["dashboard"] = {"error": str(e)}
        
        try:
            r = await client.get(f"{backend_url}/stripe/balance", timeout=30)
            phase4["details"]["stripe_balance"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase4["details"]["stripe_balance"] = {"error": str(e)}
        
        phase4["status"] = "complete"
        trace["phases"].append(phase4)
        
        # ─────────────────────────────────────────────────────────────────────
        # PHASE 5: DEALS PIPELINE
        # ─────────────────────────────────────────────────────────────────────
        phase5 = {"name": "DEALS_PIPELINE", "status": "running", "details": {}}
        
        try:
            r = await client.get(f"{backend_url}/deals/pipeline-value", timeout=30)
            phase5["details"]["pipeline"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase5["details"]["pipeline"] = {"error": str(e)}
        
        try:
            r = await client.post(f"{backend_url}/deals/advance-all", json={}, timeout=30)
            phase5["details"]["advance"] = r.json() if r.status_code == 200 else {"error": r.status_code}
        except Exception as e:
            phase5["details"]["advance"] = {"error": str(e)}
        
        phase5["status"] = "complete"
        trace["phases"].append(phase5)
    
    # ─────────────────────────────────────────────────────────────────────
    # ANALYZE GAPS
    # ─────────────────────────────────────────────────────────────────────
    gaps = []
    
    # Check if discovery is finding anything
    vacuum_result = trace["phases"][0]["details"].get("vacuum", {})
    if "error" in vacuum_result or vacuum_result.get("total_signals", 0) == 0:
        gaps.append({
            "stage": "DISCOVERY",
            "issue": "No opportunities being found",
            "fix": "Check platform API keys (FIVERR_API_KEY, UPWORK_API_KEY) or scraper endpoints"
        })
    
    # Check if bidding is working
    bid_result = trace["phases"][1]["details"].get("auto_bid", {})
    if "error" in bid_result:
        gaps.append({
            "stage": "BIDDING",
            "issue": "Auto-bidding not working",
            "fix": "Verify platform credentials and bidding logic"
        })
    
    # Check if fulfillment queue has items
    fulfill_result = trace["phases"][2]["details"].get("process_queue", {})
    if "error" in fulfill_result:
        gaps.append({
            "stage": "FULFILLMENT",
            "issue": "Fulfillment queue not processing",
            "fix": "Check AI generation keys and fulfillment endpoints"
        })
    
    # Check revenue
    revenue_result = trace["phases"][3]["details"].get("dashboard", {})
    if "error" in revenue_result:
        gaps.append({
            "stage": "REVENUE",
            "issue": "Revenue dashboard not accessible",
            "fix": "Check revenue-orchestrator endpoints"
        })
    
    trace["gaps"] = gaps
    trace["completed_at"] = _now()
    
    # Summary
    trace["summary"] = {
        "phases_run": len(trace["phases"]),
        "gaps_found": len(gaps),
        "status": "HEALTHY" if len(gaps) == 0 else "NEEDS_ATTENTION",
        "next_steps": [g["fix"] for g in gaps[:3]]
    }
    
    return trace


# ═══════════════════════════════════════════════════════════════════════════════
# PLATFORM CONNECTIVITY TEST
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/diagnostic/platform-connectivity")
async def test_platform_connectivity():
    """
    Test actual connectivity to each platform we integrate with.
    """
    
    results = {
        "tested_at": _now(),
        "platforms": {}
    }
    
    async with httpx.AsyncClient(timeout=15) as client:
        
        # Test Fiverr (if configured)
        fiverr_key = os.environ.get("FIVERR_API_KEY")
        if fiverr_key:
            try:
                # Fiverr API test endpoint
                r = await client.get("https://api.fiverr.com/v1/me", headers={"Authorization": f"Bearer {fiverr_key}"})
                results["platforms"]["fiverr"] = {"status": "connected" if r.status_code == 200 else f"error_{r.status_code}"}
            except Exception as e:
                results["platforms"]["fiverr"] = {"status": "error", "message": str(e)}
        else:
            results["platforms"]["fiverr"] = {"status": "not_configured"}
        
        # Test Stripe
        stripe_key = os.environ.get("STRIPE_SECRET_KEY")
        if stripe_key:
            try:
                r = await client.get("https://api.stripe.com/v1/balance", headers={"Authorization": f"Bearer {stripe_key}"})
                results["platforms"]["stripe"] = {"status": "connected" if r.status_code == 200 else f"error_{r.status_code}"}
            except Exception as e:
                results["platforms"]["stripe"] = {"status": "error", "message": str(e)}
        else:
            results["platforms"]["stripe"] = {"status": "not_configured"}
        
        # Test OpenRouter (for AI)
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        if openrouter_key:
            try:
                r = await client.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {openrouter_key}"})
                results["platforms"]["openrouter"] = {"status": "connected" if r.status_code == 200 else f"error_{r.status_code}"}
            except Exception as e:
                results["platforms"]["openrouter"] = {"status": "error", "message": str(e)}
        else:
            results["platforms"]["openrouter"] = {"status": "not_configured"}
        
        # Test Resend (email)
        resend_key = os.environ.get("RESEND_API_KEY")
        if resend_key:
            try:
                r = await client.get("https://api.resend.com/domains", headers={"Authorization": f"Bearer {resend_key}"})
                results["platforms"]["resend"] = {"status": "connected" if r.status_code == 200 else f"error_{r.status_code}"}
            except Exception as e:
                results["platforms"]["resend"] = {"status": "error", "message": str(e)}
        else:
            results["platforms"]["resend"] = {"status": "not_configured"}
        
        # Test Perplexity
        perplexity_key = os.environ.get("PERPLEXITY_API_KEY")
        if perplexity_key:
            results["platforms"]["perplexity"] = {"status": "configured", "note": "Key present, needs request to test"}
        else:
            results["platforms"]["perplexity"] = {"status": "not_configured"}
        
        # Test Stability AI
        stability_key = os.environ.get("STABILITY_API_KEY")
        if stability_key:
            try:
                r = await client.get("https://api.stability.ai/v1/user/account", headers={"Authorization": f"Bearer {stability_key}"})
                results["platforms"]["stability"] = {"status": "connected" if r.status_code == 200 else f"error_{r.status_code}"}
            except Exception as e:
                results["platforms"]["stability"] = {"status": "error", "message": str(e)}
        else:
            results["platforms"]["stability"] = {"status": "not_configured"}
    
    # Summary
    connected = sum(1 for p in results["platforms"].values() if p["status"] == "connected")
    configured = sum(1 for p in results["platforms"].values() if p["status"] in ["connected", "configured"])
    
    results["summary"] = {
        "connected": connected,
        "configured": configured,
        "total_tested": len(results["platforms"]),
        "monetization_ready": results["platforms"].get("stripe", {}).get("status") == "connected"
    }
    
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# MONETIZATION GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/diagnostic/monetization-gaps")
async def monetization_gap_analysis():
    """
    Analyze the complete path from opportunity to cash and identify gaps.
    """
    
    analysis = {
        "analyzed_at": _now(),
        "funnel_stages": {},
        "gaps": [],
        "recommendations": []
    }
    
    backend_url = os.environ.get("SELF_URL") or "https://aigentsy-ame-runtime.onrender.com"
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # Stage 1: Discovery
        try:
            r = await client.get(f"{backend_url}/execution/stats", timeout=10)
            stats = r.json() if r.status_code == 200 else {}
            analysis["funnel_stages"]["1_discovery"] = {
                "opportunities_found": stats.get("total_discovered", 0),
                "status": "active" if stats.get("total_discovered", 0) > 0 else "no_opportunities"
            }
        except:
            analysis["funnel_stages"]["1_discovery"] = {"status": "endpoint_missing"}
            analysis["gaps"].append("Discovery endpoint not responding")
        
        # Stage 2: Qualification
        try:
            r = await client.get(f"{backend_url}/deals/pipeline-value", timeout=10)
            pipeline = r.json() if r.status_code == 200 else {}
            analysis["funnel_stages"]["2_qualification"] = {
                "pipeline_value": pipeline.get("total_value", 0),
                "deals_in_pipeline": pipeline.get("count", 0),
                "status": "active" if pipeline.get("count", 0) > 0 else "empty_pipeline"
            }
        except:
            analysis["funnel_stages"]["2_qualification"] = {"status": "endpoint_missing"}
        
        # Stage 3: Proposal/Bid
        try:
            r = await client.get(f"{backend_url}/wade/dashboard", timeout=10)
            wade = r.json() if r.status_code == 200 else {}
            analysis["funnel_stages"]["3_proposal"] = {
                "pending_approval": wade.get("pending_approval", 0),
                "auto_approved": wade.get("auto_approved", 0),
                "status": "active"
            }
        except:
            analysis["funnel_stages"]["3_proposal"] = {"status": "endpoint_missing"}
        
        # Stage 4: Fulfillment
        try:
            r = await client.get(f"{backend_url}/fulfillment/queue-stats", timeout=10)
            fulfill = r.json() if r.status_code == 200 else {}
            analysis["funnel_stages"]["4_fulfillment"] = {
                "in_queue": fulfill.get("pending", 0),
                "completed": fulfill.get("completed", 0),
                "status": "active" if fulfill.get("completed", 0) > 0 else "not_delivering"
            }
        except:
            analysis["funnel_stages"]["4_fulfillment"] = {"status": "endpoint_missing"}
        
        # Stage 5: Payment
        try:
            r = await client.get(f"{backend_url}/stripe/balance", timeout=10)
            balance = r.json() if r.status_code == 200 else {}
            analysis["funnel_stages"]["5_payment"] = {
                "balance": balance.get("available", 0),
                "pending": balance.get("pending", 0),
                "status": "collecting" if balance.get("available", 0) > 0 else "no_revenue"
            }
        except:
            analysis["funnel_stages"]["5_payment"] = {"status": "stripe_not_connected"}
            analysis["gaps"].append("Stripe not returning balance - check STRIPE_SECRET_KEY")
    
    # Identify specific gaps
    funnel = analysis["funnel_stages"]
    
    if funnel.get("1_discovery", {}).get("status") == "no_opportunities":
        analysis["gaps"].append("Not finding opportunities - need platform API keys (Fiverr, Upwork)")
        analysis["recommendations"].append("Add FIVERR_API_KEY and UPWORK_API_KEY to Render")
    
    if funnel.get("2_qualification", {}).get("status") == "empty_pipeline":
        analysis["gaps"].append("Opportunities not converting to pipeline - check qualification logic")
        analysis["recommendations"].append("Review /deals/advance-all endpoint")
    
    if funnel.get("4_fulfillment", {}).get("status") == "not_delivering":
        analysis["gaps"].append("Not delivering work - AI generation may not be configured")
        analysis["recommendations"].append("Test /ai/orchestrate endpoint")
    
    if funnel.get("5_payment", {}).get("status") == "no_revenue":
        analysis["gaps"].append("No revenue collected yet")
        analysis["recommendations"].append("Complete end-to-end flow manually first to verify")
    
    # Overall status
    gap_count = len(analysis["gaps"])
    analysis["overall"] = {
        "status": "READY" if gap_count == 0 else "BLOCKED" if gap_count > 2 else "PARTIAL",
        "gap_count": gap_count,
        "biggest_blocker": analysis["gaps"][0] if analysis["gaps"] else None
    }
    
    return analysis


# ═══════════════════════════════════════════════════════════════════════════════
# WIRE-UP
# ═══════════════════════════════════════════════════════════════════════════════

def include_diagnostic_tracer(app):
    """Include diagnostic tracer in FastAPI app"""
    app.include_router(router, prefix="", tags=["Diagnostics"])
    print("🔍 Diagnostic Tracer loaded")
    print("   ├─ GET /diagnostic/env-check")
    print("   ├─ GET /diagnostic/full-cycle-trace")
    print("   ├─ GET /diagnostic/platform-connectivity")
    print("   └─ GET /diagnostic/monetization-gaps")
