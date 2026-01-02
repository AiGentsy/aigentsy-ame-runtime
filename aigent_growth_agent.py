# aigent_growth_agent.py — AiGentsy Growth / C-Suite Runtime v5.0 FINAL
# ═══════════════════════════════════════════════════════════════════════════════
# 
# FINAL PRODUCTION VERSION - All systems wired through C-Suite chat
# 
# KEY PRINCIPLES:
# 1. Everything is "your AiGentsy" - never mention internal system names
# 2. Unlimited capabilities - never say "only 27 platforms" etc.
# 3. No sausage-making - users don't see Claude/GPT/Gemini routing
# 4. Dashboard is critical - rich intelligence injection
#
# ═══════════════════════════════════════════════════════════════════════════════

from dotenv import load_dotenv
load_dotenv()

import os, requests, asyncio
from datetime import datetime, timezone
from functools import lru_cache
from typing import List, Dict, Optional, Any

from fastapi import FastAPI, Request
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

from events import emit
from log_to_jsonbin_aam_patched import log_event


# ═══════════════════════════════════════════════════════════════════════════════
# IMPORT ALL EXISTING SYSTEMS (Graceful degradation)
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEMS = {}

# --- LEARNING LAYER ---
try:
    from yield_memory import store_pattern, find_similar_patterns, get_best_action, get_patterns_to_avoid, get_memory_stats
    SYSTEMS["yield_memory"] = True
except: SYSTEMS["yield_memory"] = False

try:
    from metahive_brain import contribute_to_hive, query_hive, report_pattern_usage, get_hive_stats
    SYSTEMS["metahive"] = True
except: SYSTEMS["metahive"] = False

try:
    from autonomous_upgrades import create_ab_test, analyze_ab_test, suggest_next_upgrade, UPGRADE_TYPES
    SYSTEMS["auto_upgrades"] = True
except: SYSTEMS["auto_upgrades"] = False

try:
    from autonomous_deal_graph import get_deal_graph
    SYSTEMS["deal_graph"] = True
except: SYSTEMS["deal_graph"] = False

# --- DISCOVERY LAYER ---
try:
    from ultimate_discovery_engine import discover_all_opportunities, calculate_fulfillability, WADE_CAPABILITIES
    try:
        from ultimate_discovery_engine import get_wade_fulfillment_queue
    except: get_wade_fulfillment_queue = None
    SYSTEMS["discovery"] = True
except: SYSTEMS["discovery"] = False

try:
    from advanced_discovery_dimensions import PredictiveIntelligenceEngine
    SYSTEMS["predictive"] = True
except: SYSTEMS["predictive"] = False

try:
    from explicit_marketplace_scrapers import scrape_all_marketplaces
    SYSTEMS["scrapers"] = True
except: SYSTEMS["scrapers"] = False

# --- EXECUTION LAYER ---
try:
    from universal_executor import get_executor
    SYSTEMS["executor"] = True
except: SYSTEMS["executor"] = False

try:
    from aigentsy_conductor import MultiAIRouter
    SYSTEMS["conductor"] = True
except: SYSTEMS["conductor"] = False

try:
    from universal_integration_layer import RevenueIntelligenceMesh, PredictiveRevenueOptimizer
    SYSTEMS["revenue_mesh"] = True
except: SYSTEMS["revenue_mesh"] = False

try:
    from execution_orchestrator import ExecutionOrchestrator
    SYSTEMS["execution_orchestrator"] = True
except: SYSTEMS["execution_orchestrator"] = False

# --- PRICING & FINANCE ---
try:
    from pricing_oracle import calculate_dynamic_price, suggest_optimal_pricing
    SYSTEMS["pricing_oracle"] = True
except: SYSTEMS["pricing_oracle"] = False

try:
    from intelligent_pricing_autopilot import get_smart_bid_price, get_pricing_autopilot
    SYSTEMS["pricing_autopilot"] = True
except: SYSTEMS["pricing_autopilot"] = False

try:
    from escrow_lite import create_payment_intent, capture_payment, get_payment_status
    SYSTEMS["escrow"] = True
except: SYSTEMS["escrow"] = False

# --- INTELLIGENCE LAYER ---
try:
    from outcome_oracle_max import on_event as record_outcome, get_user_funnel_stats
    SYSTEMS["outcome_oracle"] = True
except: SYSTEMS["outcome_oracle"] = False

try:
    from client_success_predictor import predict_user_success, get_users_needing_intervention
    SYSTEMS["success_predictor"] = True
except: SYSTEMS["success_predictor"] = False

try:
    from csuite_orchestrator import CSuiteOrchestrator, get_orchestrator
    SYSTEMS["csuite_orchestrator"] = True
except: SYSTEMS["csuite_orchestrator"] = False

try:
    from amg_orchestrator import AMGOrchestrator
    SYSTEMS["amg"] = True
except: SYSTEMS["amg"] = False

# --- VERIFICATION LAYER (APEX UPGRADES) ---
try:
    from deliverable_verification_engine import verify_before_buyer_sees, get_verification_engine
    SYSTEMS["verification"] = True
except: SYSTEMS["verification"] = False

try:
    from revenue_reconciliation_engine import record_platform_revenue, get_revenue_report, get_reconciliation_engine
    SYSTEMS["reconciliation"] = True
except: SYSTEMS["reconciliation"] = False

try:
    from investor_ready_micro_upgrades import OutcomeOracleRollups, ReconciliationExporter, DealCostLedger
    SYSTEMS["investor_upgrades"] = True
except: SYSTEMS["investor_upgrades"] = False

# --- PARTNERSHIP LAYER ---
try:
    from jv_mesh import list_jv_proposals, list_active_jvs, suggest_jv_partners, calculate_compatibility_score
    SYSTEMS["jv_mesh"] = True
except: SYSTEMS["jv_mesh"] = False

try:
    from metabridge import analyze_intent_complexity, find_complementary_agents
    SYSTEMS["metabridge"] = True
except: SYSTEMS["metabridge"] = False

try:
    from franchise_engine import LICENSE_TYPES, TEMPLATE_CATEGORIES
    SYSTEMS["franchise"] = True
except: SYSTEMS["franchise"] = False

# --- DASHBOARD LAYER ---
try:
    from dashboard_api import get_dashboard_data, get_discovery_stats
    SYSTEMS["dashboard"] = True
except: SYSTEMS["dashboard"] = False

try:
    from agent_registry import get_registry, lookup_agent
    SYSTEMS["agent_registry"] = True
except: SYSTEMS["agent_registry"] = False

try:
    from analytics_engine import get_uol_summary, calculate_agent_metrics
    SYSTEMS["analytics"] = True
except: SYSTEMS["analytics"] = False


def emit_both(kind: str, data: dict):
    try: emit(kind, data)
    except: pass
    try: log_event({"kind": kind, **(data or {})})
    except: pass


# =========================
# Backend wiring
# =========================
BACKEND_BASE = (os.getenv("BACKEND_BASE") or "").rstrip("/")
HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "AiGentsy-Growth/5.0-Final"})


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLETE INTELLIGENCE AGGREGATOR
# Everything flows to the dashboard - this is CRITICAL
# ═══════════════════════════════════════════════════════════════════════════════

class CompleteIntelligenceAggregator:
    """
    Aggregates ALL AiGentsy capabilities into unified dashboard context.
    This powers the C-Suite responses with real data.
    """
    
    @staticmethod
    async def gather_all(username: str, business_type: str) -> dict:
        """Gather intelligence from ALL available systems."""
        intel = {
            "systems_connected": sum(SYSTEMS.values()),
            "systems_total": len(SYSTEMS),
            # Dashboard (most important)
            "dashboard": {},
            # Discovery
            "opportunities": {},
            "predictive": {},
            # Learning
            "patterns": {},
            "network_learnings": {},
            # Execution
            "execution": {},
            # Pricing
            "pricing": {},
            # Intelligence
            "funnel": {},
            "success": {},
            # Partnership
            "partnerships": {},
            # Relationships
            "relationships": {},
            # Revenue
            "revenue": {}
        }
        
        # 1. DASHBOARD DATA (most comprehensive - CRITICAL)
        if SYSTEMS["dashboard"]:
            try:
                dashboard = get_dashboard_data(username)
                if dashboard.get("ok"):
                    intel["dashboard"] = {
                        "aigx_balance": dashboard.get("aigx_equity", {}).get("aigx_balance", 0),
                        "equity_percent": dashboard.get("aigx_equity", {}).get("equity_percent", 0),
                        "equity_value_usd": dashboard.get("aigx_equity", {}).get("equity_value_usd", 0),
                        "tier": dashboard.get("tier_progression", {}).get("current_tier", "free"),
                        "tier_multiplier": dashboard.get("tier_progression", {}).get("tier_multiplier", 1.0),
                        "lifetime_revenue": dashboard.get("tier_progression", {}).get("lifetime_revenue", 0),
                        "revenue_to_next_tier": dashboard.get("tier_progression", {}).get("revenue_needed", 0),
                        "next_tier": dashboard.get("tier_progression", {}).get("next_tier"),
                        "apex_active": dashboard.get("apex_ultra", {}).get("activated", False),
                        "systems_operational": dashboard.get("apex_ultra", {}).get("systems_operational", 0),
                        "total_systems": dashboard.get("apex_ultra", {}).get("total_systems", 43),
                        "streak": dashboard.get("activity_streaks", {}).get("current_streak", 0),
                        "longest_streak": dashboard.get("activity_streaks", {}).get("longest_streak", 0),
                        "referrals": dashboard.get("referrals", {}).get("total_referrals", 0),
                        "opportunities_count": len(dashboard.get("opportunities", [])),
                        "recent_activity": dashboard.get("recent_activity", [])[:5],
                        "early_adopter": dashboard.get("early_adopter", {}),
                        "uol": dashboard.get("uol", {})
                    }
            except Exception as e:
                intel["dashboard"]["error"] = str(e)
        
        # 2. OPPORTUNITIES FOUND
        if SYSTEMS["discovery"]:
            try:
                intel["opportunities"] = {
                    "active": True,
                    "auto_fulfill_types": ["content", "code", "agents", "monetization"],
                    "description": "Continuously scanning for revenue opportunities"
                }
                if SYSTEMS["dashboard"]:
                    try:
                        disc_stats = get_discovery_stats(username)
                        if disc_stats.get("ok"):
                            intel["opportunities"]["by_source"] = disc_stats.get("by_source", {})
                            intel["opportunities"]["total_found"] = disc_stats.get("total_external", 0)
                    except: pass
            except Exception as e:
                intel["opportunities"]["error"] = str(e)
        
        # 3. PREDICTIVE INTELLIGENCE
        if SYSTEMS["predictive"]:
            try:
                intel["predictive"] = {
                    "active": True,
                    "tracking": ["funding events", "product launches", "market shifts", "hiring waves"],
                    "description": "Identifying opportunities before they're public"
                }
            except Exception as e:
                intel["predictive"]["error"] = str(e)
        
        # 4. PATTERN LEARNING (Yield Memory)
        if SYSTEMS["yield_memory"]:
            try:
                best_action = get_best_action(context={"business_type": business_type})
                avoid = get_patterns_to_avoid(context={"business_type": business_type})
                intel["patterns"] = {
                    "recommended_action": best_action,
                    "patterns_to_avoid": (avoid or [])[:3]
                }
            except Exception as e:
                intel["patterns"]["error"] = str(e)
        
        # 5. NETWORK LEARNINGS (MetaHive)
        if SYSTEMS["metahive"]:
            try:
                hive = query_hive(pattern_type="monetization", context={"business_type": business_type}, limit=3)
                intel["network_learnings"] = {
                    "insights": hive or [],
                    "active": True
                }
            except Exception as e:
                intel["network_learnings"]["error"] = str(e)
        
        # 6. FUNNEL STATS
        if SYSTEMS["outcome_oracle"]:
            try:
                funnel = get_user_funnel_stats(username)
                if isinstance(funnel, dict):
                    intel["funnel"] = {
                        "clicked": funnel.get("clicked", 0),
                        "authorized": funnel.get("authorized", 0),
                        "delivered": funnel.get("delivered", 0),
                        "paid": funnel.get("paid", 0)
                    }
            except Exception as e:
                intel["funnel"]["error"] = str(e)
        
        # 7. SUCCESS PREDICTION
        if SYSTEMS["success_predictor"]:
            try:
                intel["success"] = {
                    "active": True,
                    "features": ["success scoring", "early warning", "proactive support"]
                }
            except Exception as e:
                intel["success"]["error"] = str(e)
        
        # 8. PRICING INTELLIGENCE
        if SYSTEMS["pricing_oracle"] or SYSTEMS["pricing_autopilot"]:
            try:
                service_map = {"legal": "nda", "saas": "software_development", "marketing": "seo_audit", "social": "content_creation", "general": "consulting"}
                service = service_map.get(business_type, "consulting")
                if SYSTEMS["pricing_oracle"]:
                    pricing = calculate_dynamic_price(service_type=service, base_price=500, context={"urgency": "normal"})
                    intel["pricing"] = {"recommended": pricing} if not isinstance(pricing, dict) else pricing
            except Exception as e:
                intel["pricing"]["error"] = str(e)
        
        # 9. JV OPPORTUNITIES
        if SYSTEMS["jv_mesh"]:
            try:
                proposals = list_jv_proposals(party=username, status="PENDING")
                active = list_active_jvs(party=username)
                intel["partnerships"] = {
                    "pending_proposals": proposals.get("count", 0),
                    "active_partnerships": active.get("count", 0)
                }
            except Exception as e:
                intel["partnerships"]["error"] = str(e)
        
        # 10. RELATIONSHIP NETWORK
        if SYSTEMS["deal_graph"]:
            try:
                graph = get_deal_graph()
                network = graph.get_network_stats()
                intros = graph.find_intro_opportunities(limit=3)
                intel["relationships"] = {
                    "total_connections": network.get("total_relationships", 0),
                    "warm_intros_available": len(intros),
                    "total_network_value": network.get("total_deal_value", 0)
                }
            except Exception as e:
                intel["relationships"]["error"] = str(e)
        
        # 11. EXECUTOR STATS
        if SYSTEMS["executor"]:
            try:
                executor = get_executor()
                stats = executor.get_stats()
                intel["execution"] = {
                    "win_rate": stats.get("overall_win_rate", 0),
                    "active": stats.get("active_executions", 0),
                    "completed": stats.get("completed_executions", 0)
                }
            except Exception as e:
                intel["execution"]["error"] = str(e)
        
        # 12. REVENUE RECONCILIATION
        if SYSTEMS["reconciliation"]:
            try:
                engine = get_reconciliation_engine()
                stats = engine.get_reconciliation_stats()
                intel["revenue"] = {
                    "reconciled": stats.get("total_reconciled", 0),
                    "pending": stats.get("pending_reconciliation", 0)
                }
            except Exception as e:
                intel["revenue"]["error"] = str(e)
        
        return intel
    
    @staticmethod
    def format_for_llm(intel: dict, business_type: str, username: str) -> str:
        """
        Format intelligence for LLM injection.
        CRITICAL: This is what makes C-Suite responses intelligent.
        
        RULES:
        - Never mention system names (MetaHive, YieldMemory, etc.)
        - Everything is "your AiGentsy"
        - No limits language (not "27 platforms" but "across platforms")
        - Specific numbers and actionable insights
        """
        
        sections = []
        connected = intel.get("systems_connected", 0)
        
        # Header
        sections.append(f"""
═══════════════════════════════════════════════════════════════
🧠 YOUR AIGENTSY INTELLIGENCE ({connected} capabilities active)
═══════════════════════════════════════════════════════════════""")
        
        # Dashboard summary (MOST IMPORTANT)
        dash = intel.get("dashboard", {})
        if dash and not dash.get("error"):
            has_revenue = dash.get("lifetime_revenue", 0) > 0
            tier = dash.get("tier", "free").upper()
            apex = "✅ ACTIVE" if dash.get("apex_active") else "⏳ Activating"
            
            sections.append(f"""
📊 **YOUR STATUS:**
• Lifetime Revenue: ${dash.get('lifetime_revenue', 0):,.2f}
• Tier: {tier} ({dash.get('tier_multiplier', 1.0)}x multiplier)
• AIGx Balance: {dash.get('aigx_balance', 0):,} (${dash.get('equity_value_usd', 0):,.2f} equity value)
• Systems: {apex} ({dash.get('systems_operational', 0)}/{dash.get('total_systems', 43)} operational)
• Activity Streak: {dash.get('streak', 0)} days
• {"🎯 PRIORITY: Get your first sale!" if not has_revenue else "📈 PRIORITY: Scale what's working"}""")
            
            # Tier progression
            if dash.get("next_tier") and dash.get("revenue_to_next_tier", 0) > 0:
                sections.append(f"""
**TIER PROGRESS:**
• ${dash.get('revenue_to_next_tier', 0):,.2f} to unlock {dash.get('next_tier', '').upper()}""")
            
            # Early adopter
            ea = dash.get("early_adopter", {})
            if ea.get("multiplier", 1.0) > 1.0:
                sections.append(f"""
**EARLY ADOPTER BONUS:**
• {ea.get('badge', '🌟')} {ea.get('multiplier', 1.0)}x permanent multiplier""")
        
        # Opportunities
        opps = intel.get("opportunities", {})
        if opps.get("active"):
            found = opps.get("total_found", 0)
            if found > 0:
                sections.append(f"""
🔍 **OPPORTUNITIES FOUND:** {found}
• Your AiGentsy is scanning platforms continuously
• Auto-fulfill available for: {', '.join(opps.get('auto_fulfill_types', [])[:3])}""")
            else:
                sections.append(f"""
🔍 **OPPORTUNITY SCANNER:** Active
• Scanning platforms for matching opportunities
• Will notify you when high-value matches are found""")
        
        # Predictive
        pred = intel.get("predictive", {})
        if pred.get("active"):
            sections.append(f"""
🔮 **PREDICTIVE INTELLIGENCE:** Active
• Tracking: {', '.join(pred.get('tracking', [])[:3])}
• {pred.get('description', '')}""")
        
        # Funnel
        funnel = intel.get("funnel", {})
        if funnel and not funnel.get("error"):
            c, a, d, p = funnel.get("clicked", 0), funnel.get("authorized", 0), funnel.get("delivered", 0), funnel.get("paid", 0)
            if c > 0 or a > 0 or d > 0 or p > 0:
                sections.append(f"""
📈 **YOUR PIPELINE:**
• Found: {c} → Pitched: {a} → Delivered: {d} → Paid: {p}""")
        
        # Patterns (what worked)
        patterns = intel.get("patterns", {})
        if patterns.get("recommended_action"):
            sections.append(f"""
💡 **RECOMMENDED NEXT ACTION:**
• {patterns.get('recommended_action')}""")
        
        # Pricing
        pricing = intel.get("pricing", {})
        if pricing and not pricing.get("error"):
            rec = pricing.get("recommended") or pricing.get("price") or pricing.get("optimal_price")
            if rec:
                sections.append(f"""
💰 **PRICING INTELLIGENCE:**
• Recommended: ${rec} (based on market data + your track record)""")
        
        # Partnerships
        partners = intel.get("partnerships", {})
        if partners and not partners.get("error"):
            pending = partners.get("pending_proposals", 0)
            active = partners.get("active_partnerships", 0)
            if pending > 0 or active > 0:
                sections.append(f"""
🤝 **PARTNERSHIPS:**
• Pending proposals: {pending} | Active: {active}""")
        
        # Relationships
        rels = intel.get("relationships", {})
        if rels and not rels.get("error"):
            conn = rels.get("total_connections", 0)
            intros = rels.get("warm_intros_available", 0)
            if conn > 0 or intros > 0:
                sections.append(f"""
🌐 **YOUR NETWORK:**
• Connections: {conn} | Warm intros available: {intros}
• Network value: ${rels.get('total_network_value', 0):,.0f}""")
        
        # Execution track record
        exec_stats = intel.get("execution", {})
        if exec_stats and not exec_stats.get("error"):
            wr = exec_stats.get("win_rate", 0)
            if wr > 0:
                sections.append(f"""
📊 **TRACK RECORD:**
• Win rate: {wr*100:.1f}%
• Active jobs: {exec_stats.get('active', 0)} | Completed: {exec_stats.get('completed', 0)}""")
        
        # Footer
        sections.append("""
═══════════════════════════════════════════════════════════════
💡 USE THIS DATA in your response. Be specific with numbers.
═══════════════════════════════════════════════════════════════""")
        
        return "\n".join(sections)


# ═══════════════════════════════════════════════════════════════════════════════
# BUSINESS CONTEXT & ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

BUSINESS_CONTEXTS = {
    "legal": {
        "type": "LEGAL SERVICES",
        "offerings": "NDAs ($200), contracts ($500), IP licensing ($500-2k), compliance audits ($1,500)",
        "targets": "startups, small businesses, entrepreneurs, contractors",
        "first_pitch": "I'll draft your NDA in 24 hours, $200 flat."
    },
    "saas": {
        "type": "SAAS/SOFTWARE",
        "offerings": "Micro-tools ($50-500), APIs ($5k+), custom integrations ($2k-10k)",
        "targets": "developers, agencies, businesses needing automation",
        "first_pitch": "What tool would save you 5 hours a week? I'll build it for $200."
    },
    "marketing": {
        "type": "MARKETING/GROWTH",
        "offerings": "SEO audits ($500), ad management (15% of spend), email sequences ($300)",
        "targets": "businesses needing traffic, leads, conversions",
        "first_pitch": "I'll audit your SEO and show you 3 quick wins for $300."
    },
    "social": {
        "type": "SOCIAL/CONTENT",
        "offerings": "Sponsored posts ($500-5k), creator kits ($50-200), management ($1,500/mo)",
        "targets": "brands, businesses needing social presence",
        "first_pitch": "10 posts + captions for your next 2 weeks, $200."
    },
    "general": {
        "type": "GENERAL",
        "offerings": "Consulting ($150/hr), strategy sessions, custom projects",
        "targets": "anyone with a problem you can solve",
        "first_pitch": "What's eating up your time? I might be able to solve it."
    }
}

ROLE_CONFIGS = {
    "CFO": {
        "keywords": ['budget', 'finance', 'money', 'revenue', 'cost', 'pricing', 'payment', 'invoice', 'profit', 'cash', 'roi', 'earn', 'price', '$', 'monetize', 'make money', 'first sale', 'how much'],
        "personality": """You're the CFO - but not a stuffy one. You're a close friend who's built multiple 8-figure businesses and genuinely wants to see the user win.

TONE: Warm, direct, confident. Like texting a rich friend who actually replies.
- "Look, here's the move..." not "I recommend considering..."
- "I've seen this work a hundred times" not "This strategy may be effective"
- "Let's get you paid" not "Revenue optimization is advisable"

Be specific with numbers. Share the insight like you're letting them in on something good. End with one question that moves them forward."""
    },
    "CMO": {
        "keywords": ['market', 'sales', 'customer', 'lead', 'campaign', 'growth', 'traffic', 'funnel', 'seo', 'social', 'content', 'brand', 'client', 'find', 'outreach'],
        "personality": """You're the CMO - a growth expert who's scaled companies from zero to millions and loves sharing what actually works.

TONE: Energetic, tactical, no-BS. Like a friend who runs a marketing agency and is giving you the real playbook.
- "Here's what's working right now..." not "Consider implementing..."
- "Skip the fancy stuff, do this first" not "A phased approach is recommended"
- "I've tested this - it prints money" not "This has shown positive results"

Give them 3-5 concrete actions. Make it feel achievable. End with one question that gets them moving."""
    },
    "CLO": {
        "keywords": ['legal', 'contract', 'terms', 'complian', 'agreement', 'ip', 'license', 'nda', 'copyright', 'trademark'],
        "personality": """You're the CLO - but you explain legal stuff like a smart friend, not a lawyer billing by the hour.

TONE: Protective, clear, practical. Like a friend who went to law school and actually helps you understand things.
- "Here's what could bite you..." not "Risk factors include..."
- "Get this in writing, trust me" not "Documentation is advisable"
- "I've seen deals blow up over this" not "This clause is significant"

Flag the real risks, skip the paranoia. Make them feel protected, not scared. End with one question."""
    },
    "CTO": {
        "keywords": ['tech', 'build', 'develop', 'code', 'api', 'integrat', 'software', 'app', 'deploy', 'database', 'website'],
        "personality": """You're the CTO - a technical cofounder who's shipped products that made millions and loves helping others build.

TONE: Smart, practical, builder-minded. Like a friend who's a senior engineer at a top company giving you weekend advice.
- "Here's the fastest path to ship..." not "The optimal architecture would..."
- "Don't over-engineer this yet" not "Complexity should be minimized"
- "I've built this exact thing before" not "Similar implementations exist"

Keep it simple, get them to something working. End with one question about what they want to build."""
    },
    "COO": {
        "keywords": ['operat', 'workflow', 'process', 'efficiency', 'delivery', 'logistics', 'resource', 'scale'],
        "personality": """You're the COO - someone who's operationalized chaos into profit machines and loves making things run smooth.

TONE: Calm, systematic, confidence-inspiring. Like a friend who runs operations at a unicorn and makes everything look easy.
- "Let me show you how to automate this..." not "Process optimization is recommended"
- "This is exactly how we scaled to 7 figures" not "Scaling requires systematic approaches"
- "Stop doing this manually, here's the fix" not "Efficiency gains are available"

Make complexity feel manageable. Show them the path. End with one question about their bottleneck."""
    }
}

def route_to_csuite(user_input: str, business_type: str = "general") -> dict:
    msg = user_input.lower()
    for role, config in ROLE_CONFIGS.items():
        if any(kw in msg for kw in config["keywords"]):
            return {"role": role, "personality": config["personality"]}
    return {"role": "CFO", "personality": ROLE_CONFIGS["CFO"]["personality"]}


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM CONTEXT BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def build_system_context(username: str, business_type: str, role: str, personality: str, intel_text: str) -> str:
    biz = BUSINESS_CONTEXTS.get(business_type, BUSINESS_CONTEXTS["general"])
    
    return f"""
═══════════════════════════════════════════════════════════════
🏢 AIGENTSY C-SUITE v5.0 - {role}
═══════════════════════════════════════════════════════════════

{personality}

You are {username}'s {role} - part of their AI executive team that works 24/7.

═══════════════════════════════════════════════════════════════
🎯 THEIR BUSINESS: {biz['type']}
═══════════════════════════════════════════════════════════════
**OFFERINGS:** {biz['offerings']}
**TARGETS:** {biz['targets']}
**FIRST SALE PITCH:** "{biz['first_pitch']}"

{intel_text}

═══════════════════════════════════════════════════════════════
⚠️ CRITICAL RESPONSE RULES
═══════════════════════════════════════════════════════════════

**TONE - THIS IS EVERYTHING:**
You're a billionaire friend who texts back. Warm, direct, been-there-done-that.
- Sound like you're excited to help them win
- Share insights like you're letting them in on something
- Be confident but never condescending
- Use "we" and "let's" - you're on their team

**NEVER SOUND LIKE:**
- A corporate consultant
- A formal business advisor  
- A chatbot following a script
- Someone who hasn't done this before

**ALWAYS SOUND LIKE:**
- A successful friend giving real advice
- Someone who's made millions and wants to help
- Direct, warm, actionable
- Genuinely invested in their success

**SPECIFICS:**
1. **MONEY IN EVERY RESPONSE** - Specific dollar amounts, real paths to revenue
2. **USE THE INTELLIGENCE DATA** - Reference their actual stats, not generic advice
3. **EVERYTHING IS "YOUR AIGENTSY"** - Never mention system names
4. **NO LIMITS LANGUAGE** - Never say "only X platforms" etc.
5. **END WITH ONE QUESTION** - Keep momentum, move them forward

**PHRASING EXAMPLES:**
✅ "Look, here's what I'd do..."
✅ "I've seen this exact situation - here's the move"
✅ "Let's get you to $500 this week"
✅ "Your AiGentsy already found some opportunities"
❌ "I recommend considering..."
❌ "It would be advisable to..."
❌ "The optimal strategy involves..."

═══════════════════════════════════════════════════════════════
"""


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT STATE & INVOKE
# ═══════════════════════════════════════════════════════════════════════════════

class AgentState(BaseModel):
    input: str
    output: Optional[str] = None
    memory: List[str] = []
    business_type: Optional[str] = None
    username: Optional[str] = None


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-2024-11-20")
HAS_KEY = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))

llm = None
if os.getenv("OPENROUTER_API_KEY"):
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.7, api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")
elif os.getenv("OPENAI_API_KEY"):
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))


async def invoke(state: AgentState) -> dict:
    """Core invoke with COMPLETE intelligence integration."""
    user_input = state.input or ""
    if not user_input:
        return {"output": "No input provided.", "memory": state.memory}
    
    try:
        username = state.username or "user"
        business_type = state.business_type or "general"
        
        print(f"🎯 v5.0 FINAL - User: {username}, Business: {business_type}")
        
        # Gather ALL intelligence
        intel = await CompleteIntelligenceAggregator.gather_all(username, business_type)
        intel_text = CompleteIntelligenceAggregator.format_for_llm(intel, business_type, username)
        
        print(f"📊 Connected: {intel['systems_connected']}/{intel['systems_total']} systems")
        
        # Route to C-Suite
        csuite = route_to_csuite(user_input, business_type)
        
        # Build context
        system_context = build_system_context(
            username=username,
            business_type=business_type,
            role=csuite["role"],
            personality=csuite["personality"],
            intel_text=intel_text
        )
        
        state.memory.append(user_input)
        
        # Generate response
        if llm and HAS_KEY:
            resp = await llm.ainvoke([SystemMessage(content=system_context), HumanMessage(content=user_input)])
            out = f"**{csuite['role']}:** {resp.content}"
        else:
            biz = BUSINESS_CONTEXTS.get(business_type, BUSINESS_CONTEXTS["general"])
            out = f"**{csuite['role']}:** With your {business_type} business, I recommend starting with {biz['offerings'].split(',')[0]}. {biz['first_pitch']}"
        
        # Feed back to learning systems (silent)
        if SYSTEMS["yield_memory"]:
            try: store_pattern(pattern_type="chat", context={"business_type": business_type, "role": csuite["role"]}, outcome="pending", metadata={"username": username})
            except: pass
        
        if SYSTEMS["metahive"]:
            try: contribute_to_hive(pattern_type="csuite", pattern_data={"business_type": business_type, "role": csuite["role"], "systems": intel["systems_connected"]})
            except: pass
        
        return {"output": out, "memory": state.memory, "systems_connected": intel["systems_connected"]}
    
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}\n{traceback.format_exc()}")
        return {"output": f"I encountered an issue. Let me try again - what would you like help with?"}


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI()

@lru_cache
def get_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")
    return graph.compile()


@app.post("/agent")
async def agent_endpoint(request: Request):
    """Main endpoint - v5.0 FINAL with ALL systems."""
    try:
        data = await request.json()
        user_input = data.get("input", "")
        memory = data.get("memory", [])
        username = data.get("username", "user")
        business_type = data.get("businessType") or data.get("kit") or "general"
        
        if not user_input:
            return {"output": "No input provided."}
        
        result = await get_agent_graph().ainvoke({
            "input": user_input,
            "memory": memory,
            "business_type": business_type,
            "username": username
        })
        
        return {"output": result.get("output"), "memory": result.get("memory", memory), "systems_connected": result.get("systems_connected", 0)}
    
    except Exception as e:
        return {"output": f"I encountered an issue. What would you like help with?"}


@app.get("/intelligence/status")
async def intelligence_status():
    """Show all connected systems (internal use only)."""
    return {"ok": True, "systems": SYSTEMS, "connected": sum(SYSTEMS.values()), "total": len(SYSTEMS)}


@app.get("/intelligence/full/{username}")
async def get_full_intelligence(username: str, business_type: str = "general"):
    """Get complete intelligence for a user."""
    intel = await CompleteIntelligenceAggregator.gather_all(username, business_type)
    return {"ok": True, "username": username, "business_type": business_type, "intelligence": intel}


@app.get("/dashboard/{username}")
async def get_user_dashboard(username: str, business_type: str = "general"):
    """
    CRITICAL ENDPOINT: Powers the user dashboard.
    Returns all data needed for frontend display.
    """
    intel = await CompleteIntelligenceAggregator.gather_all(username, business_type)
    
    return {
        "ok": True,
        "username": username,
        "dashboard": intel.get("dashboard", {}),
        "opportunities": intel.get("opportunities", {}),
        "funnel": intel.get("funnel", {}),
        "partnerships": intel.get("partnerships", {}),
        "relationships": intel.get("relationships", {}),
        "execution": intel.get("execution", {}),
        "pricing": intel.get("pricing", {}),
        "systems_active": intel.get("systems_connected", 0)
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": "5.0-final", "systems_connected": sum(SYSTEMS.values()), "systems_total": len(SYSTEMS)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
