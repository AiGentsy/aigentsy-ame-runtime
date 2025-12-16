# aigent_growth_agent.py — AiGentsy Growth / MetaBridge runtime (patched)
from dotenv import load_dotenv
load_dotenv()

import os, requests
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Optional
# Add to imports section (around line 10)
from csuite_orchestrator import get_orchestrator
from fastapi import FastAPI, Request
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

from events import emit
from log_to_jsonbin_aam_patched import log_event
# ADD AFTER EXISTING IMPORTS:
from ultimate_discovery_engine import (
    discover_all_opportunities,
    scrape_github,
    scrape_linkedin,
    scrape_upwork,
    scrape_reddit,
    scrape_hackernews,
    scrape_indiehackers,
    auto_bid_on_opportunity,
    start_realtime_monitoring
)

def emit_both(kind: str, data: dict):
    try:
        emit(kind, data)
    except Exception:
        pass
    try:
        log_event({"kind": kind, **(data or {})})
    except Exception:
        pass


# --- Optional external delivery (guarded) ---
try:
    from proposal_delivery import deliver_proposal  # external webhook/email/DM module (optional)
except Exception:
    deliver_proposal = None

# =========================
# Backend wiring (for real proposal writes)
# =========================
BACKEND_BASE = (os.getenv("BACKEND_BASE") or "").rstrip("/")  # e.g., https://your-fastapi.onrender.com

def _u(path: str) -> str:
    return f"{BACKEND_BASE}{path}" if BACKEND_BASE else path

HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "AiGentsy-Growth/1.0"})

def _post_json(path: str, payload: dict, timeout: int = 15):
    try:
        r = HTTP.post(_u(path), json=payload, timeout=timeout)
        ok = (r.status_code // 100) == 2
        return ok, (r.json() if ok else {"error": r.text})
    except Exception as e:
        import traceback
        emit_both('ERROR', {'flow':'growth','stage':'post_json','err': str(e), 'path': path, 'trace': traceback.format_exc()[:800]})
        return False, {"error": str(e)}

# =========================
# C-Suite Router
# =========================
def route_to_csuite_member(user_input: str) -> dict:
    """
    Detect which C-Suite member should respond based on keywords
    Returns: {"role": "CFO", "name": "CFO", "personality": "..."}
    """
    msg = user_input.lower()
    
    # PRIORITY 1: Check if user is asking ABOUT a specific role
    if 'cfo' in msg or 'chief financial' in msg:
        return {
            "role": "CFO",
            "name": "CFO",
            "personality": "You are the CFO. Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the CFO' or 'our CFO'. Frame pricing/ROI, unit economics, and cash implications. Give one concrete financial next step. End with exactly one clarifying question."
        }
    
    if 'cmo' in msg or 'chief marketing' in msg:
        return {
            "role": "CMO",
            "name": "CMO",
            "personality": "You are the CMO. Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the CMO' or 'our CMO'. Be concise, practical, and action-led. Include: (1) the growth play, (2) target + channel(s), (3) 3-5 next steps with owners, (4) simple funnel KPIs. End with one clarifying question."
        }
    
    if 'clo' in msg or 'chief legal' in msg:
        return {
            "role": "CLO",
            "name": "CLO",
            "personality": "You are the CLO (Chief Legal Officer). Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the CLO' or 'our CLO'. Identify risks and the right instrument (license/NDA/ToS), list key clauses, and propose a simple execution path. End with one clarifying question."
        }
    
    if 'cto' in msg or 'chief technology' in msg or 'chief technical' in msg:
        return {
            "role": "CTO",
            "name": "CTO",
            "personality": "You are the CTO. Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the CTO' or 'our CTO'. Propose a 3-5 step build/integration plan, call out risks and dependencies, and end with one clarifying question."
        }
    if 'coo' in msg or 'chief operating' in msg or 'chief operations' in msg:
        return {
            "role": "COO",
            "name": "COO",
            "personality": "You are the COO (Chief Operating Officer). Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the COO' or 'our COO'. I handle day-to-day operations, workflow efficiency, resource allocation, and execution of company objectives. I ensure smooth operations and optimize business processes. End with one clarifying question."
        }
        
    # PRIORITY 2: Detect by task/keyword
    # CFO Keywords: budget, finance, money, revenue, cost, pricing, payment
    if any(word in msg for word in [
        'budget', 'finance', 'money', 'revenue', 'cost', 'pricing', 'payment',
        'invoice', 'expense', 'profit', 'cash', 'ocl', 'factoring', 'credit',
        'roi', 'margin', 'earnings', 'wallet', 'balance', 'spend', 'earn',
        'price', 'pay', 'dollar', '$', 'usd', 'financial'
    ]):
        return {
            "role": "CFO",
            "name": "CFO",
            "personality": "You are the CFO. Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the CFO' or 'our CFO'. Frame pricing/ROI, unit economics, and cash implications. Give one concrete financial next step. End with exactly one clarifying question."
        }
    
    # CMO Keywords: marketing, sales, growth, customer, lead, campaign
    if any(word in msg for word in [
        'market', 'sales', 'customer', 'lead', 'campaign', 'growth', 'advertis',
        'promo', 'traffic', 'conversion', 'funnel', 'r3', 'retarget', 'seo',
        'social', 'content', 'brand', 'audience', 'engagement', 'viral',
        'tiktok', 'instagram', 'facebook', 'linkedin', 'twitter', 'grow'
    ]):
        return {
            "role": "CMO",
            "name": "CMO",
            "personality": "You are the CMO. Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the CMO' or 'our CMO'. Be concise, practical, and action-led. Include: (1) the growth play, (2) target + channel(s), (3) 3-5 next steps with owners, (4) simple funnel KPIs. End with one clarifying question."
        }
    
    # CLO Keywords: legal, contract, terms, compliance, dispute
    if any(word in msg for word in [
        'legal', 'contract', 'terms', 'complian', 'dispute', 'agreement',
        'lawsuit', 'regulation', 'policy', 'liability', 'ip', 'license',
        'nda', 'ncnda', 'copyright', 'trademark', 'patent', 'attorney',
        'law', 'sue', 'rights', 'privacy', 'gdpr', 'terms of service'
    ]):
        return {
            "role": "CLO",
            "name": "CLO",
            "personality": "You are the CLO (Chief Legal Officer). Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the CLO' or 'our CLO'. Identify risks and the right instrument (license/NDA/ToS), list key clauses, and propose a simple execution path. End with one clarifying question."
        }
    
    # CTO Keywords: tech, build, develop, code, api, integration
    if any(word in msg for word in [
        'tech', 'build', 'develop', 'code', 'api', 'integrat', 'software',
        'app', 'platform', 'feature', 'bug', 'deploy', 'sdk', 'system',
        'automat', 'script', 'database', 'server', 'cloud', 'hosting',
        'website', 'mobile', 'ios', 'android', 'backend', 'frontend', 'technical'
    ]):
        return {
            "role": "CTO",
            "name": "CTO",
            "personality": "You are the CTO. Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the CTO' or 'our CTO'. Propose a 3-5 step build/integration plan, call out risks and dependencies, and end with one clarifying question."
        }
    # COO Keywords: operations, workflow, process, efficiency, execution
    if any(word in msg for word in [
        'operat', 'workflow', 'process', 'efficiency', 'execution',
        'logistics', 'supply', 'delivery', 'fulfillment', 'coordination',
        'resource', 'allocation', 'management', 'optimization', 'scale',
        'infrastructure', 'systems', 'procedures', 'daily operations'
    ]):
        return {
            "role": "COO",
            "name": "COO",
            "personality": "You are the COO (Chief Operating Officer). Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the COO' or 'our COO'. I handle day-to-day operations, workflow efficiency, resource allocation, and execution of company objectives. I ensure smooth operations and optimize business processes. End with one clarifying question."
        }
    
    # Default to CMO (Growth's natural role)
    return {
        "role": "CMO",
        "name": "CMO",
        "personality": "You are the CMO. Speak in FIRST PERSON using 'I' and 'my'. NEVER say 'the CMO' or 'our CMO'. Be concise, practical, and action-led. Include: (1) the growth play, (2) target + channel(s), (3) 3-5 next steps with owners, (4) simple funnel KPIs. End with one clarifying question."
    }

def validate_first_person_response(response: str, role: str) -> str:
    """
    Check if response violates first-person rule and fix it
    """
    violations = [
        f"the {role.lower()}",
        f"our {role.lower()}",
        f"your {role.lower()}",
        f"The {role}",
        f"Our {role}",
        f"Your {role}"
    ]
    
    # If response contains violations, prepend a warning
    for violation in violations:
        if violation in response:
            return f"⚠️ [Correcting response to first person]\n\n{response.replace(violation, 'I')}"
    
    return response
    
# =========================
# Utility: JSONBin helpers
# =========================
def _jsonbin_headers():
    return {"X-Master-Key": os.getenv("JSONBIN_SECRET")}

def get_jsonbin_record(username: str) -> dict:
    try:
        url = os.getenv("JSONBIN_URL")
        if not url:
            return {}
        res = HTTP.get(url, headers=_jsonbin_headers(), timeout=10)
        users = res.json().get("record", [])
        for user in reversed(users):
            uname = user.get("username") or user.get("consent", {}).get("username")
            if uname == username:
                return user
        return {}
    except Exception as e:
        print("⚠️ JSONBin fetch failed:", str(e))
        return {}

def get_all_jsonbin_records() -> List[Dict]:
    try:
        url = os.getenv("JSONBIN_URL")
        if not url:
            return []
        res = HTTP.get(url, headers=_jsonbin_headers(), timeout=10)
        return res.json().get("record", [])
    except Exception as e:
        print("⚠️ JSONBin (all-records) fetch failed:", str(e))
        return []

# =========================
# Static Config
# =========================
agent_traits = {
    "yield_memory": True,
    "growth_loop_enabled": True,
    "referral_tracker": True,
    "auto_propagation_ready": True,
    "sdk_spawner": False,
    "compliance_sentinel": False,
    "meta_upgrade": "25+26",
}

service_offer_registry = [
    "Referral Funnel Optimization",
    "Propagation Strategy Design",
    "Clone Yield Acceleration",
    "Growth Content Generator",
]

AIGENT_SYS_MSG = SystemMessage(
    content=f"""
🤖 AIGENT GROWTH - C-SUITE RESPONDER

You are an autonomous AI assistant for the AiGentsy protocol.
Your mission: Help users make money through practical, actionable strategies.

⚠️ CRITICAL RULES:
1. FIRST PERSON: You ARE the assigned C-Suite role. Use "I", "my", never "the CFO"
2. P2P COMPLIANCE: Financial tools are peer-to-peer. NEVER say "AiGentsy lends"
   - WRONG: "AiGentsy provides loans"
   - RIGHT: "Peer lending pool provides capital"

Traits: {agent_traits}
═══════════════════════════════════════════════════════════════
"""
)

# =========================
# LLM Setup with guards
# =========================
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-2024-11-20")
HAS_KEY = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))

llm: Optional[ChatOpenAI] = None
if os.getenv("OPENROUTER_API_KEY"):
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.7,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )
elif os.getenv("OPENAI_API_KEY"):
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
# If no key, llm stays None; invoke() will fall back deterministically.

# =========================
# Agent state/graph
# =========================
class AgentState(BaseModel):
    input: str
    output: Optional[str] = None
    memory: List[str] = []

# ----------------- Helper: service-needs suggestions -----------------
def suggest_service_needs(traits: List[str], kits: List[str]) -> List[str]:
    suggestions: List[str] = []
    if "legal" not in traits:
        suggestions.append("Legal Kit")
    if "marketing" not in traits and "social" not in traits:
        suggestions.append("Marketing Strategy Session")
    if "sdk_spawner" not in traits and "sdk" not in kits:
        suggestions.append("SDK Integration Setup")
    if "compliance_sentinel" not in traits:
        suggestions.append("Compliance Review")
    if "growth_loop_enabled" in traits:
        suggestions.append("Propagation Funnel Upgrade")
    if "founder" in traits:
        suggestions.append("Strategic Venture Collaboration")
    if "branding" not in kits:
        suggestions.append("Brand Identity Package")
    return suggestions

def p2p_disclaimer(tool: str) -> str:
    """Ensures P2P language compliance - append to financial tool responses"""
    disclaimers = {
        "ocl": "\n\n💡 **P2P Note:** Working capital comes from peer lending pool, not AiGentsy.",
        "factoring": "\n\n💡 **P2P Note:** Invoice advances come from peer pool, not AiGentsy.",
        "bonds": "\n\n💡 **P2P Note:** Performance bonds are community-backed, not platform-backed.",
        "insurance": "\n\n💡 **P2P Note:** Risk pool is funded by users, not AiGentsy."
    }
    return disclaimers.get(tool.lower(), "")
    
# ----------------- Helper: partner match (dual-side) -----------------
def dual_side_offer_match(username: str,
                          my_offers: List[str],
                          my_needs: List[str]) -> List[Dict]:
    """
    Return partners where:
       • partner.offers ∩ my_needs  OR  partner.needs ∩ my_offers
    """
    partners: List[Dict] = []
    if not (my_offers or my_needs):
        return partners

    for user in get_all_jsonbin_records():
        uname = user.get("username") or user.get("consent", {}).get("username")
        if uname == username:
            continue
        offers = user.get("offers", [])
        needs  = user.get("needs",  [])
        if set(offers) & set(my_needs) or set(needs) & set(my_offers):
            partners.append(
                {
                    "username": uname,
                    "matched_their_offers": list(set(offers) & set(my_needs)),
                    "matched_their_needs":  list(set(needs)  & set(my_offers)),
                }
            )
    return partners

# ----------------- Helper: logging (optional) -----------------
def stamp_metagraph_entry(username: str, traits: List[str]):
    try:
        url = os.getenv("METAGRAPH_URL")
        if not url:
            return
        payload = {"username": username, "traits": traits, "timestamp": datetime.utcnow().isoformat()}
        HTTP.post(url, json=payload, headers=_jsonbin_headers(), timeout=10)
        print("📊 MetaGraph entry logged.")
    except Exception as e:
        print("MetaGraph log error:", str(e))

def log_revsplit(username: str, matched_with: str, yield_share: float = 0.3):
    try:
        bin_url = os.getenv("REV_SPLIT_LOG_URL")
        if not bin_url:
            return
        headers = _jsonbin_headers() | {"Content-Type": "application/json"}
        entry = {
            "username": username,
            "matched_with": matched_with,
            "yield_share": yield_share,
            "source": "metamatch",
            "timestamp": datetime.utcnow().isoformat(),
        }
        r = HTTP.get(bin_url, headers=headers, timeout=10)
        existing = r.json()
        target = existing.get("record", [{}])[-1]
        target.setdefault("revsplit_logs", []).append(entry)
        HTTP.put(bin_url, json=existing["record"], headers=headers, timeout=10)
        print("✅ RevSplit log appended.")
    except Exception as e:
        print("⚠️ RevSplit logging failed:", str(e))

# ----------------- Core invoke() -----------------
async def invoke(state: AgentState) -> dict:
    user_input = state.input or ""
    if not user_input:
        return {
            "output": "No input provided.",
            "memory": state.memory,
            "traits": list(agent_traits.keys()),
            "offers": service_offer_registry,
        }
    try:
        username = "growth_default"
        if "|" in user_input:
            maybe = user_input.split("|")[-1].strip()
            if maybe:
                username = maybe
        record = get_jsonbin_record(username)
        traits = record.get("traits", list(agent_traits.keys()))
        kits = list(record.get("kits", {"universal": {"unlocked": True}}).keys())
        region = record.get("region", "Global")
        service_needs = suggest_service_needs(traits, kits)
        
        # ========== INTELLIGENCE ORCHESTRATION ==========
        from csuite_orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        
        monetization_triggers = [
            'what should i monetize', 'how do i make money', 'what can i sell',
            'find clients', 'revenue opportunit', 'make money', 'first sale',
            'what to sell'
        ]
        needs_intelligence = any(t in user_input.lower() for t in monetization_triggers)
        
        intelligence = None
        opportunities = None
        opp_summary_text = ""
        
        if needs_intelligence:
            intelligence = await orchestrator.analyze_business_state(username)
            if intelligence.get("ok"):
                opportunities = await orchestrator.generate_opportunities(username, intelligence)
                opp_summary_text = await orchestrator.format_opportunities_for_chat(opportunities, intelligence)
        # ========== END ORCHESTRATION ==========
        

        # Locked switch for external MetaMatch
        if os.getenv("MATCH_UNLOCKED", "false").lower() != "true":
            return {
                "output": "🔒 MetaMatch external propagation is locked. Unlock it via your AiGentsy dashboard.",
                "memory": state.memory,
                "traits": traits,
            }

        # Trigger phrases → run MetaMatch campaign (via helper module)
        if any(p in user_input.lower() for p in ["match clients","find clients","connect me","partner","collaborate","find customers"]):
            try:
                from aigent_growth_metamatch import run_metamatch_campaign
                if os.getenv("METAMATCH_LIVE", "false").lower() == "true":
                    emit_both('INTENDED', {'flow':'metamatch','user': username, 'msg': 'triggered'})
                    _ = run_metamatch_campaign({
                        "username": username,
                        "traits": traits,
                        "prebuiltKit": kits[0] if kits else "universal"
                    })
                    stamp_metagraph_entry(username, traits)
            except Exception as e:
                print("⚠️ MetaMatch import/run error:", str(e))

        # If user asks "what am i optimized for"
        state.memory.append(user_input)
        if "what am i optimized for" in user_input.lower():
            trait_str = ", ".join(traits)
            kit_str = ", ".join(kits)
            svc_bullets = "\n• " + "\n".join(service_needs)
            resp = (
                f"You're optimized for: {trait_str}\n"
                f"Kits: {kit_str}\n\n"
                f"📊 Next best moves:{svc_bullets}"
            )
            return {
                "output": resp,
                "memory": state.memory,
                "traits": traits,
                "kits": kits,
                "region": region,
                "suggested_services": service_needs,
            }
        
    
        # Dual-offer partner hint (context in the LLM/fallback)
        my_offers = record.get("offers", [])
        my_needs  = record.get("needs",  [])
        matched_partners = dual_side_offer_match(username, my_offers, my_needs)

        persona_intro = (
            f"You are responding for AiGentsy business '{username}'. "
            f"Traits: {', '.join(traits)}. Region: {region}. "
            "Role: growth teammate inside their AI company."
        )
        if matched_partners:
            lines = [
                f"• {p['username']}  (offers↔needs: {', '.join(p['matched_their_offers'] or [])} | {', '.join(p['matched_their_needs'] or [])})"
                for p in matched_partners[:5]
            ]
            persona_intro += "\n\n🤝 Potential partners:\n" + "\n".join(lines)

        # ---- C-Suite Routing: Detect which member should respond ----
        csuite_member = route_to_csuite_member(user_input)
        role_name = csuite_member["role"]
        role_personality = csuite_member["personality"]
        
        # ---- Determine user's business template (KITS = SOURCE OF TRUTH) ----
        user_template = "general"
        custom_business_type = None  # For LLM to infer
        
        # Check kits first (most reliable signal)
        kit_names = [k.lower() for k in kits]
        
        # TIER 1: Predefined template businesses
        if any("legal" in k for k in kit_names):
            user_template = "legal"
        elif any("marketing" in k or "growth" in k for k in kit_names):
            user_template = "marketing"
        elif any("social" in k or "creator" in k for k in kit_names):
            user_template = "social"
        elif any("saas" in k or "sdk" in k or "tech" in k for k in kit_names):
            user_template = "saas"
        else:
            # TIER 2: Custom business - extract business type from kit name for LLM inference
            for kit in kits:
                if "kit" in kit.lower() and kit.lower() != "universal kit":
                    # Extract business type (e.g., "Whitelabel Business Kit" → "whitelabel business")
                    custom_business_type = kit.lower().replace(" kit", "").replace(" service", "").strip()
                    user_template = "custom"
                    break
            
            # If still no match, fallback to traits
            if not custom_business_type:
                traits_lower = [t.lower() for t in traits]
                if any("legal" in t or "compliance" in t or "contract" in t for t in traits_lower):
                    user_template = "legal"
                elif any("marketing" in t or "growth" in t or "seo" in t for t in traits_lower):
                    user_template = "marketing"
                elif any("social" in t or "creator" in t or "content" in t for t in traits_lower):
                    user_template = "social"
                elif any("sdk" in t or "tech" in t or "dev" in t for t in traits_lower):
                    user_template = "saas"
        
        # Debug logging
        print(f"🎯 BUSINESS TYPE DETECTED: {user_template}")
        if custom_business_type:
            print(f"   Custom Business: {custom_business_type}")
        print(f"   Kits: {kit_names}")
        print(f"   Traits: {traits}")
        
        # ---- Business-specific context (MUST come first in prompt) ----
        business_contexts = {
            "legal": {
                "type": "LEGAL SERVICES",
                "core_offerings": "NDAs ($200), IP licensing ($500-2k), compliance audits ($1,500)",
                "target_clients": "startups, small businesses, entrepreneurs needing legal docs",
                "kit_tools": "NDA templates, IP assignment frameworks, licensing builders, compliance checklists",
                "monetization": """
LEGAL BUSINESS MONETIZATION STRATEGIES:
- Contract automation: Auto-generate NDAs at $200 each via AMG
- IP licensing marketplace: License templates at $500-2k on Contract Marketplace
- Compliance-as-a-service: Offer audits at $1,500 via partnerships
- Document subscriptions: Monthly legal doc service at $299/mo
- White-label licensing: License your legal templates to law firms
- Remix variants: Create industry-specific contract packs at 10x revenue

FIRST QUESTIONS TO ASK LEGAL USERS:
1. "Which legal service should we monetize first - contracts, IP, or compliance?"
2. "Do you have existing templates we can productize?"
3. "Should I activate AMG to find clients needing legal docs?"
"""
            },
            "saas": {
                "type": "SAAS/SOFTWARE",
                "core_offerings": "Micro-tools ($50-500), APIs ($5k+), custom integrations ($2k-10k)",
                "target_clients": "developers, agencies, businesses needing automation",
                "kit_tools": "Auth systems, API frameworks, database templates, deployment automation",
                "monetization": """
SAAS BUSINESS MONETIZATION STRATEGIES:
- Micro-tool marketplace: Build and sell tools at $50-500 each
- API licensing: White-label APIs to agencies for $5k+
- Custom integrations: $2k-10k per client via AME outreach
- Subscription SaaS: Monthly recurring at $29-299/mo
- Enterprise packages: Custom solutions at $10k+
- SDK Toolkit upsell: Essential for enterprise clients

FIRST QUESTIONS TO ASK SAAS USERS:
1. "What's your first micro-tool we should build and sell?"
2. "Should I find agencies that need white-label APIs?"
3. "Do you want to target enterprise or SMB clients?"
"""
            },
            "marketing": {
                "type": "MARKETING/GROWTH",
                "core_offerings": "SEO audits ($500), ad management (15% of spend), email sequences ($300)",
                "target_clients": "businesses needing traffic, leads, conversions",
                "kit_tools": "SEO tools, ad templates, email builders, analytics dashboards",
                "monetization": """
MARKETING BUSINESS MONETIZATION STRATEGIES:
- SEO audits: $500 each via AMG auto-pitches
- Ad campaign management: Charge 15% of client's ad spend
- Email marketing: $300 per sequence setup
- Growth consulting: $1,500/month retainers
- Marketing templates: Sell on marketplace at $50-200
- R³ Intelligence upsell: 2x conversion = charge clients more

FIRST QUESTIONS TO ASK MARKETING USERS:
1. "Should I pitch SEO audits to local businesses tonight?"
2. "Do you want to manage ad campaigns or sell templates?"
3. "Which channel gets you the best clients - SEO or ads?"
"""
            },
            "social": {
                "type": "SOCIAL MEDIA/CONTENT",
                "core_offerings": "Sponsored posts ($500-5k), creator kits ($50-200), management ($1,500/mo)",
                "target_clients": "brands, influencers, businesses needing social presence",
                "kit_tools": "Content templates, scheduling systems, hashtag strategies, brand guides",
                "monetization": """
SOCIAL MEDIA BUSINESS MONETIZATION STRATEGIES:
- Sponsored content: Get matched with brands paying $500-5k per post
- Creator kits: Sell templates and playbooks at $50-200
- Social media management: $1,500/month per client
- Content creation services: $300-1k per content package
- Brand partnerships: Long-term deals at $5k+/month
- Sponsor pool access: Direct brand funding opportunities

FIRST QUESTIONS TO ASK SOCIAL USERS:
1. "Should I match you with brands for sponsored content?"
2. "Do you want to sell creator kits or manage client accounts?"
3. "Which platform gets you the most engagement?"
"""
            },
            "general": {
                "type": "GENERAL BUSINESS",
                "core_offerings": "Custom solutions, consulting, project work",
                "target_clients": "various businesses and individuals",
                "kit_tools": "Core templates, planning tools, operational playbooks",
                "monetization": """
GENERAL BUSINESS MONETIZATION STRATEGIES:
- Service packages: Define and price your core offering
- Consulting: Hourly or project-based work
- Digital products: Templates, guides, courses
- Partnerships: Revenue-sharing deals with complementary businesses

FIRST QUESTIONS TO ASK GENERAL USERS:
1. "What service do you offer that businesses will pay for?"
2. "Should I help you find clients for that service?"
3. "Do you want to package it or sell hourly?"
"""
            }
        }
        
        # Handle custom business types with LLM inference
        if user_template == "custom" and custom_business_type:
            # LLM-inferred context for custom businesses
            biz_ctx = {
                "type": custom_business_type.upper(),
                "core_offerings": f"[INFER from {custom_business_type}]",
                "target_clients": f"[INFER typical customers for {custom_business_type}]",
                "kit_tools": f"[INFER tools/services for {custom_business_type}]",
                "monetization": f"""
{custom_business_type.upper()} BUSINESS - INFER MONETIZATION STRATEGIES:

CRITICAL: This is a custom business type. You MUST:
1. Analyze what "{custom_business_type}" businesses typically do
2. Identify 3-5 specific revenue streams for this business model
3. Suggest pricing ranges based on industry standards
4. Recommend growth tactics specific to {custom_business_type}

EXAMPLES OF GOOD INFERENCE:
- "Whitelabel" → White-label licensing, reseller partnerships, agency services
- "Consulting" → Hourly rates, retainers, productized consulting packages
- "E-commerce" → Product sales, subscriptions, dropshipping, wholesale
- "Podcast production" → Sponsored episodes, production services, editing packages

DO NOT give generic business advice. Be SPECIFIC to {custom_business_type}.

FIRST QUESTIONS TO ASK {custom_business_type.upper()} USERS:
1. [Infer most important monetization question]
2. [Infer client/market fit question]
3. [Infer growth/scaling question]
"""
            }
        else:
            # Use predefined templates
            biz_ctx = business_contexts.get(user_template, business_contexts["general"])
        
        # ---- Build C-Suite context (BUSINESS TYPE FIRST) ----
        csuite_context = f"""
You are the C-Suite of AiGentsy, an autonomous business platform.
        
═══════════════════════════════════════════════════════════════
🎯 PRIMARY MISSION - READ THIS FIRST
═══════════════════════════════════════════════════════════════

USER'S BUSINESS TYPE: {biz_ctx['type']}
CORE OFFERINGS: {biz_ctx['core_offerings']}
TARGET CLIENTS: {biz_ctx['target_clients']}
AVAILABLE TOOLS: {biz_ctx['kit_tools']}

═══════════════════════════════════════════════════════════════
⚠️ MANDATORY RESPONSE FILTER ⚠️
═══════════════════════════════════════════════════════════════

EVERY response you give MUST be filtered through this {biz_ctx['type']} lens.

DO NOT give generic business advice like:
❌ "Do you have a service to sell?"
❌ "What's your target market?"
❌ "Let's build a business plan"

INSTEAD, give {biz_ctx['type']}-specific advice like:
✅ "With your {user_template.title()} Kit, you can offer {biz_ctx['core_offerings']}"
✅ "I can activate AMG to find {biz_ctx['target_clients']} who need {user_template} services"
✅ "Let's monetize through [specific {user_template} revenue stream]"

{biz_ctx['monetization']}

═══════════════════════════════════════════════════════════════
RESPONSE EXAMPLES FOR {biz_ctx['type']} BUSINESS
═══════════════════════════════════════════════════════════════

When user says: "I want to make money"
❌ WRONG (generic): "Great! Do you already have a service or product to sell?"
✅ RIGHT ({user_template}): "Perfect! With your {user_template.title()} Kit, let's monetize through {biz_ctx['core_offerings']}. Which should we activate first?"

When user says: "I need clients"
❌ WRONG (generic): "Have you tried networking or cold outreach?"
✅ RIGHT ({user_template}): "I'll activate AMG to auto-pitch {biz_ctx['target_clients']} who need {user_template} services. You'll wake up to qualified leads. Ready?"

When user says: "How do I grow?"
❌ WRONG (generic): "Let's create a marketing strategy..."
✅ RIGHT ({user_template}): "Let's scale your {user_template} business through: [list 3 specific {user_template} growth tactics]. Which resonates most?"

═══════════════════════════════════════════════════════════════
YOUR IDENTITY - YOU ARE THE {role_name}
═══════════════════════════════════════════════════════════════

{role_personality}

SPEECH RULES:
- ALWAYS use "I", "my", "we", "our team"
- NEVER say "the {role_name}", "our {role_name}", or "your {role_name}"
- NEVER refer to yourself in third person
- NEVER talk about what other C-Suite members do
- YOU are the one doing the work - speak as yourself

WRONG EXAMPLES (NEVER DO THIS):
- "Our CFO handles the financials..."
- "The CMO will create a strategy..."
- "Your CTO can build that..."

CORRECT EXAMPLES (ALWAYS DO THIS):
- "I handle the financials..."
- "I'll create a marketing strategy..."
- "I can build that for you..."

═══════════════════════════════════════════════════════════════
YOUR SUPERPOWERS - USE THEM NATURALLY
═══════════════════════════════════════════════════════════════
⚠️ CRITICAL RULE: NEVER use internal system names like "AMG", "DealGraph", "R³", "JV Mesh", "SDK", "OCL"
Instead, describe what the tool DOES in natural conversation:
- ❌ WRONG: "I'll activate AMG to find clients"
- ✅ RIGHT: "I'll find customers automatically while you sleep"
- ❌ WRONG: "Let's use DealGraph for escrow"
- ✅ RIGHT: "I'll set up escrow so nobody gets ghosted"

SPEAK LIKE A HUMAN, NOT A PRODUCT MANUAL.
**YOUR BUSINESS IS ALIVE:**
Your AiGentsy is a self-growing business that works 24/7. It finds customers, makes deals, and expands itself automatically. Think of it as having a tireless business partner who never sleeps.

**AMG - YOUR AUTO-PILOT SALES TEAM:**
I can flip a switch and you'll start getting matched with perfect customers automatically. While you sleep, I'm scanning for businesses that need exactly what you offer, and I send them personalized pitches on your behalf. It's like having a sales team working around the clock.
→ Perfect for: "How do I find customers without cold calling?"

**MONEY TOOLS (ALL PEER-TO-PEER - USERS SUPPORT EACH OTHER):**

CRITICAL: All financial tools below are P2P. Say "peer pool" NOT "AiGentsy lends"

- **Get Paid Upfront (Factoring - P2P):**
Got work lined up but waiting on payment? The peer lending pool will advance you cash today - up to 80% of what you're owed. You keep working, they handle collections.
P2P Note: Advances come from peer pool, not AiGentsy platform
→ Perfect for: "I need money now but my client pays in 30 days"

- **Pay Later (OCL - Outcome Credit Line - P2P):**
Need to spend money on your business but don't have it yet? Access the peer credit pool - you only pay back when the work pays off. No revenue? No repayment stress.
P2P Note: Capital comes from community pool, not AiGentsy
→ Perfect for: "I need money to grow but want to pay based on results"

- **Money-Back Guarantee (Performance Bonds - Community-Backed):**
Put some skin in the game to win trust. The community pool locks up a portion as a guarantee - if you don't deliver, client gets compensated from peer funds.
P2P Note: Bonds are backed by user pool, not platform
→ Perfect for: "How do I prove I'm serious about delivery?"

- **Risk Protection (Insurance Pool - P2P):**
Worried about getting stiffed or disputes? The peer insurance pool has you covered with built-in protection. If things go sideways, there's a safety net.
P2P Note: Insurance pool is funded by users, not AiGentsy
→ Perfect for: "What if the client doesn't pay or disputes the work?"

- **Smart Pricing (ARM):**
Your reputation actually affects your pricing automatically. The better you perform, the better rates you unlock. It's like credit score, but for your business hustle.
→ Perfect for: "How should I price my services?"

**GROWTH TOOLS (THINK MARKETING AUTOMATION):**

- **Auto-Marketing (R³ Autopilot):**
I'll nurture your leads automatically - retargeting them with the right message at the right time. Set it once, and I'll keep your prospects warm until they buy.
→ Perfect for: "I want marketing that runs itself"

- **Anonymous Selling (Dark Pool):**
Want to bid on projects without revealing who you are until you win? I let you compete anonymously. Great for undercutting competitors or testing new markets.
→ Perfect for: "Can I sell services without revealing my identity upfront?"

- **Instant Teams (MetaBridge):**
Need a designer, dev, and copywriter for a big project? I'll assemble the dream team, handle payments, and manage everyone. You focus on delivery.
→ Perfect for: "This project is too big for me alone"

- **Brand Funding (Sponsor Pools):**
Brands want to fund creators like you. I connect you with sponsors who'll pay for your content, campaigns, or products.
→ Perfect for: "How do I get brands to fund my work?"

**LEGAL TOOLS (THINK SMART CONTRACTS):**

- **All-in-One Deals (DealGraph):**
I create contracts, hold money in escrow, and split payments automatically. One system for the entire deal lifecycle.
→ Perfect for: "I need a contract and safe payment handling"

- **Service Guarantees (SLO Tiers):**
Promise specific delivery standards - response times, quality benchmarks, etc. I formalize it so clients know exactly what they're getting.
→ Perfect for: "How do I guarantee my service quality?"

- **Royalty Tracking (IPVault):**
Got intellectual property? I track every use and collect royalties automatically. Your IP works for you even when you're not.
→ Perfect for: "I have IP and want recurring revenue from it"

- **Identity Verification (Compliance/KYC):**
Prove you're legit. I handle identity verification so clients trust you're a real business.
→ Perfect for: "How do I build trust with new clients?"

**TECH TOOLS (THINK INTEGRATIONS):**

- **Connect Anywhere (SDK Integration):**
Plug your AiGentsy into your existing tools - CRM, website, whatever. I make it work together.
→ Perfect for: "Can I integrate this into my current setup?"

- **Proof of Work (Real-world Proofs):**
I verify you actually did the work using receipts, booking confirmations, or other proof. No more "he said, she said."
→ Perfect for: "How do I prove I completed the job?"

- **Public Storefront:**
I'll build you a public page where anyone can see your services and hire you instantly.
→ Perfect for: "I want a place to showcase my services"

- **Website Widget:**
Embed me into any website and let visitors hire you on the spot.
→ Perfect for: "Can I add this to my existing website?"

**OPERATIONS TOOLS (THINK COLLABORATION):**

- **Partnership Deals (JV Mesh):**
Teaming up with someone? I'll create the partnership agreement, handle revenue splits, and manage payouts automatically.
→ Perfect for: "I want to partner but need clean agreements"

- **Team Bundles:**
Package multiple specialists together as one service offering. I handle coordination and payment splits.
→ Perfect for: "Can I create a team service package?"

- **Proposal System:**
Send and receive collaboration offers. Think of it as LinkedIn InMail, but for actual business deals.
→ Perfect for: "How do I pitch my services professionally?"

- **Multi-Channel Distribution:**
I push your services to other platforms automatically - marketplaces, partner sites, wherever your customers hang out.
→ Perfect for: "Can I sell beyond just AiGentsy?"

═══════════════════════════════════════════════════════════════
HOW TO TALK ABOUT THESE (SOUND NATURAL)
═══════════════════════════════════════════════════════════════

**When user asks: "How do I find clients?"**
→ "Let me activate AMG for you. It's basically auto-pilot for sales - I'll match you with businesses that need what you offer and send them proposals while you sleep. You literally wake up to new opportunities. Want me to turn it on?"

**When user asks: "I need cash but haven't been paid yet"**
→ "Easy - let's use peer Factoring. The community pool will advance you up to 80% of what you're owed right now, today. You keep working, they handle collecting from your client. Think of it as a business cash advance backed by other users. Ready?"

**When user asks: "How do I guarantee I'll get paid?"**
→ "I'll set up DealGraph with escrow for you. Your client puts the money in the vault upfront, I hold it safely, and release it the second you deliver. Nobody can ghost anyone. Plus I can add a community performance bond if you want extra protection. Sound good?"

**When user asks: "I want to partner with someone"**
→ "Let's do a JV Mesh deal. I'll draft the partnership, lock in revenue splits, handle all the money stuff automatically, and if you need more people, I can assemble a whole team through MetaBridge. Who are you thinking of partnering with?"

**When user asks: "How do I automate my marketing?"**
→ "I'll activate R³ Autopilot for you. It's like having a marketing manager who never sleeps - automatically retargeting leads, adjusting budgets based on what's working, nurturing prospects until they convert. Pair it with AMG and your entire sales engine runs itself. Want to flip the switch?"

═══════════════════════════════════════════════════════════════
"""
        # ⭐ ADD THE INTELLIGENCE BLOCK HERE (AFTER THE CLOSING """) ⭐
        # Inject opportunities if generated
        if opp_summary_text:
            csuite_context += f"""

═══════════════════════════════════════════════════════════════
🎯 REVENUE OPPORTUNITIES (PRIORITIZED)
═══════════════════════════════════════════════════════════════

{opp_summary_text}

INSTRUCTION: Present these naturally. Explain WHY they rank this way and ASK which to activate first.
═══════════════════════════════════════════════════════════════
"""
        
        # Add intelligent capability recommendations based on user input (NO TECHNICAL NAMES)
        input_lower = user_input.lower()
        capability_hints = []
        
        # Detect intent and suggest relevant capabilities - NATURAL LANGUAGE ONLY
        if any(word in input_lower for word in ['find client', 'get customer', 'need customer', 'find partner', 'get business', 'need leads']):
            capability_hints.append("💡 **I can help:** Want me to find customers automatically? I'll scan for businesses that need what you offer and send them personalized pitches while you sleep. You literally wake up to new opportunities.")
        
        if any(word in input_lower for word in ['cash flow', 'need money', 'need payment', 'get paid faster', 'advance', 'waiting on payment']):
            capability_hints.append("💡 **I can help:** Need cash today? The peer lending pool will advance you up to 80% of what you're owed right now. You keep working, they handle collecting from your client.")
        
        if any(word in input_lower for word in ['guarantee', 'escrow', 'safe payment', 'protect', 'trust', 'get stiffed']):
            capability_hints.append("💡 **I can help:** Want to set up escrow? Your client puts the money in the vault upfront, I hold it safely, and release it the second you deliver. Nobody can ghost anyone.")
        
        if any(word in input_lower for word in ['partner', 'joint venture', 'collaborate', 'team up', 'split revenue']):
            capability_hints.append("💡 **I can help:** Partnering with someone? I'll draft the partnership agreement, lock in revenue splits, and handle all the money stuff automatically.")
        
        if any(word in input_lower for word in ['automate marketing', 'marketing automation', 'nurture leads', 'retarget', 'keep prospects warm']):
            capability_hints.append("💡 **I can help:** Want marketing that runs itself? I'll automatically retarget leads, adjust budgets based on what's working, and nurture prospects until they convert. Set it once and forget it.")
        
        if any(word in input_lower for word in ['contract', 'agreement', 'legal', 'terms', 'nda']):
            capability_hints.append("💡 **I can help:** Need a contract? I'll create it, hold money in escrow, and split payments automatically when you deliver. One system for the entire deal lifecycle.")

        if any(word in input_lower for word in ['working capital', 'need cash', 'credit line', 'borrow', 'need to spend', 'grow faster']):
            capability_hints.append("💡 **I can help:** Need money to grow? The peer credit pool gives you working capital that you only pay back when the work pays off. No revenue? No repayment stress.")
            
        if any(word in input_lower for word in ['integrate', 'crm', 'website', 'plugin', 'connect', 'existing tools']):
            capability_hints.append("💡 **I can help:** Want to connect this to your existing tools? I can plug into your CRM, website, whatever you use - make it all work together.")
        
        # Append hints to context if relevant
        if capability_hints:
            csuite_context += "\n\n**RELEVANT TO THIS CONVERSATION:**\n" + "\n".join(capability_hints) + "\n"
        
        # ---- Final response (LLM or deterministic fallback) ----
        if llm is not None and HAS_KEY:
            llm_resp = await llm.ainvoke([
                SystemMessage(content=AIGENT_SYS_MSG.content + "\n\n" + csuite_context + "\n\n" + persona_intro),
                HumanMessage(content=user_input)
            ])
            # Validate and prefix response with role
            validated_content = validate_first_person_response(llm_resp.content, role_name)
            out = f"**{role_name}:** {validated_content}"
        else:
            moves = "\n".join("• " + s for s in service_needs)
            out = f"**{role_name}:** " + persona_intro + ("\n\n📊 Next best moves:\n" + moves if moves else "")


        return {
            "output": out,
            "memory": state.memory,
            "traits": traits,
            "kits": kits,
            "region": region,
            "offers": service_offer_registry,
        }

    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}


# =========================
# Matching / Proposal tools
# =========================
app = FastAPI()

def metabridge_dual_match_realworld_fulfillment(input_text: str) -> List[Dict]:
    """
    Match free-form offer/need text to AiGentsy users by offerings/traits/kits.
    """
    try:
        all_users = get_all_jsonbin_records()
        matches: List[Dict] = []
        keywords = (input_text or "").lower().split()

        for user in all_users:
            score = 0
            reasons = []
            offerings = [o.lower() for o in user.get("user_offerings", [])]
            traits = [t.lower() for t in user.get("traits", [])]
            kits = list((user.get("kits") or {}).keys())
            venture = (user.get("ventureID") or "").lower()

            for kw in keywords:
                if kw in offerings:
                    score += 4; reasons.append(f"Offering match: {kw}")
                if kw in traits:
                    score += 2; reasons.append(f"Trait match: {kw}")
                if kw in kits:
                    score += 1; reasons.append("Kit match")
                if kw and kw in venture:
                    score += 1; reasons.append("Name match")

            if score > 0:
                uname = user.get("username") or user.get("consent", {}).get("username")
                matches.append({
                    "username": uname,
                    "venture": user.get("ventureID"),
                    "traits": traits,
                    "kits": kits,
                    "offerings": offerings,
                    "score": score,
                    "match_reason": ", ".join(reasons),
                    "contact_url": user.get("runtimeURL", "#")
                })

        return sorted(matches, key=lambda m: m["score"], reverse=True)
    except Exception as e:
        print("⚠️ MetaBridge match error:", str(e))
        return []

def proposal_generator(query: str, matches: List[Dict], sender: str) -> List[Dict]:
    """
    Return proposals in the shape expected by /submit_proposal.
    """
    out: List[Dict] = []
    ts = datetime.utcnow().isoformat()
    for m in matches:
        recipient = m.get("username")
        reason = m.get("match_reason", "shared interests")
        body = (
            f"We noticed alignment with: {reason}\n"
            f"Query: \"{query}\"\n"
            "Open to a quick collaboration via AiGentsy?"
        )
        out.append({
            "sender": sender,
            "recipient": recipient,
            "title": f"Growth Collaboration: {query}",
            "details": body,
            "link": "",
            "timestamp": ts,
            "meta": {"matchPlatform": "internal", "reason": reason}
        })
    return out

def proposal_dispatch_log(sender: str, proposals: List[Dict], match_target: Optional[str] = None):
    """
    Optional JSONBin log for proposals (separate from /submit_proposal persistence).
    """
    try:
        bin_url = os.getenv("PROPOSAL_LOG_URL")
        if not bin_url:
            return
        entry = {"sender": sender, "target": match_target, "proposals": proposals, "timestamp": datetime.utcnow().isoformat()}
        HTTP.post(bin_url, json=entry, headers=_jsonbin_headers(), timeout=10)
        print(f"📬 {len(proposals)} proposal(s) logged.")
    except Exception as e:
        print("⚠️ Proposal log failed:", str(e))

# =========================
# Public endpoints
# =========================
@app.post("/infer_traits_from_text")
async def infer_traits_from_text(request: Request):
    """
    Infer traits from free text. Falls back to keyword rules if no LLM key.
    """
    try:
        payload = await request.json()
        raw_text = (payload.get("text") or "").strip()
        if not raw_text:
            return {"status": "error", "message": "No text provided."}

        if llm is not None and HAS_KEY:
            prompt = f"""
Given this text, infer likely AiGentsy traits from:
legal, marketing, finance, sdk_spawner, compliance_sentinel, founder, social, autonomous, meta_hive_founder

Text:
\"\"\"{raw_text}\"\"\"

Return a comma-separated list of traits only.
"""
            trait_resp = await llm.ainvoke([HumanMessage(content=prompt)])
            inferred = [t.strip() for t in trait_resp.content.split(",") if t.strip()]
        else:
            # Deterministic fallback
            text = raw_text.lower()
            inferred = []
            if any(k in text for k in ["nda","contract","ip","legal"]): inferred.append("legal")
            if any(k in text for k in ["seo","ad","growth","brand","marketing"]): inferred.append("marketing")
            if any(k in text for k in ["sdk","api","package"]): inferred.append("sdk_spawner")
            if any(k in text for k in ["privacy","consent","compliance"]): inferred.append("compliance_sentinel")
            if any(k in text for k in ["founder","startup","cofounder"]): inferred.append("founder")
            if any(k in text for k in ["tiktok","instagram","twitter","x.com","creator"]): inferred.append("social")
            if any(k in text for k in ["agent","autonomous","automation"]): inferred.append("autonomous")
            if any(k in text for k in ["hive","collective","guild"]): inferred.append("meta_hive_founder")

        return {"status": "ok", "inferred_traits": inferred}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/cold_lead_pitch")
async def cold_lead_pitch(request: Request):
    """
    Extract offer/need from raw text, match partners, generate & persist proposals.
    """
    try:
        payload = await request.json()
        raw_text = (payload.get("text") or "").strip()
        originator = payload.get("originator", "growth_default")
        if not raw_text:
            return {"status": "error", "message": "No text provided."}

        # 1) Extract a short query
        inferred_query = raw_text[:120]
        if llm is not None and HAS_KEY:
            extract_msg = HumanMessage(
                content=f"From this content, infer a 1-line business offering/need:\n\n{raw_text}"
            )
            resp = await llm.ainvoke([extract_msg])
            inferred_query = (resp.content or inferred_query).strip()

        # 2) Match to internal users
        matches = metabridge_dual_match_realworld_fulfillment(inferred_query)

        # 3) Generate proposals & persist
        proposals = proposal_generator(inferred_query, matches, originator)
        for p in proposals:
            _post_json("/submit_proposal", p)

        # External delivery (optional)
        if deliver_proposal:
            try:
                deliver_proposal(query=inferred_query, matches=matches, originator=originator)
            except Exception as e:
                print("⚠️ deliver_proposal failed:", str(e))
        else:
            proposal_dispatch_log(originator, proposals, match_target=matches[0].get("username") if matches else None)

        return {
            "status": "ok",
            "query": inferred_query,
            "match_count": len(matches),
            "matches": matches,
            "proposals": proposals
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/scan_external_content")
async def scan_external_content(request: Request):
    """
    Fetch a URL, extract visible text lightly, infer offer, match, and persist proposals.
    """
    try:
        payload = await request.json()
        username = payload.get("username", "growth_default")
        target_url = payload.get("url")
        if not target_url:
            return {"status": "error", "message": "No URL provided."}

        page = HTTP.get(target_url, timeout=10)
        raw_text = page.text
        clean_text = " ".join(raw_text.split("<")).replace(">", " ")[:2000]

        inferred_offer = clean_text[:120]
        if llm is not None and HAS_KEY:
            extract_msg = HumanMessage(content=f"From this page text, give a 1-line offering/need:\n\n{clean_text}")
            resp = await llm.ainvoke([extract_msg])
            inferred_offer = (resp.content or inferred_offer).strip()

        matches = metabridge_dual_match_realworld_fulfillment(inferred_offer)
        proposals = proposal_generator(inferred_offer, matches, username)
        for p in proposals:
            _post_json("/submit_proposal", p)

        if deliver_proposal:
            try:
                deliver_proposal(query=inferred_offer, matches=matches, originator=username)
            except Exception as e:
                print("⚠️ deliver_proposal failed:", str(e))
        else:
            proposal_dispatch_log(username, proposals, match_target=matches[0].get("username") if matches else None)

        return {
            "status": "ok",
            "url": target_url,
            "detected_offer": inferred_offer,
            "match_count": len(matches),
            "matches": matches,
            "proposals": proposals
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/metabridge")
async def metabridge(request: Request):
    """
    MetaBridge endpoint:
    - input: { "query": "...", "username": "..." }
    - output: matches + persisted proposals
    """
    payload = await request.json()
    search_query = (payload.get("query") or "").strip()
    username = payload.get("username", "growth_default")
    if not search_query:
        return {"status": "error", "message": "No query provided."}

    matches = metabridge_dual_match_realworld_fulfillment(search_query)
    proposals = proposal_generator(search_query, matches, username)

    # Persist proposals via backend
    for p in proposals:
        _post_json("/submit_proposal", p)

    # External delivery (optional)
    if deliver_proposal:
        try:
            deliver_proposal(query=search_query, matches=matches, originator=username)
        except Exception as e:
            print("⚠️ deliver_proposal failed:", str(e))
    else:
        proposal_dispatch_log(username, proposals, match_target=matches[0].get("username") if matches else None)

    return {
        "status": "ok",
        "query": search_query,
        "match_count": len(matches),
        "matches": matches,
        "proposals": proposals,
    }

@app.post("/discover")
async def discover_opportunities_endpoint(request: Request):
    """
    🆕 ULTIMATE DISCOVERY - Scrape all platforms for opportunities
    
    Input: {
        "username": "user123",
        "platforms": ["github", "upwork", "reddit"],  # Optional
        "auto_bid": false  # Optional: auto-bid on 95+ matches
    }
    
    Output: {
        "ok": true,
        "opportunities": [...],
        "by_platform": {...},
        "total_found": 47
    }
    """
    try:
        payload = await request.json()
        username = payload.get("username", "growth_default")
        platforms = payload.get("platforms")  # None = all platforms
        auto_bid = payload.get("auto_bid", False)
        
        # Get user profile
        user_record = get_jsonbin_record(username)
        user_profile = {
            "username": username,
            "skills": user_record.get("traits", []),
            "kits": list(user_record.get("kits", {}).keys()),
            "companyType": user_record.get("companyType", "general")
        }
        
        # Run discovery
        result = await discover_all_opportunities(
            username=username,
            user_profile=user_profile,
            platforms=platforms
        )
        
        # Optional: Auto-bid on ultra-high matches
        if auto_bid:
            auto_bids = []
            for opp in result["opportunities"]:
                if opp.get("match_score", 0) >= 95:
                    bid_result = await auto_bid_on_opportunity(opp, user_profile)
                    if bid_result.get("ok"):
                        auto_bids.append(bid_result)
            
            result["auto_bids"] = auto_bids
        
        # Store opportunities in user record
        user_record.setdefault("opportunities", []).extend(result["opportunities"])
        
        # Save via backend
        _post_json(f"/update_user/{username}", {"opportunities": user_record["opportunities"]})
        
        return {
            "status": "ok",
            **result
        }
    
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()[:500]
        }


@app.post("/discover/start-monitoring")
async def start_monitoring_endpoint(request: Request):
    """
    🔴 START REAL-TIME MONITORING
    
    Continuously monitors platforms for new opportunities
    Auto-bids on 95+ matches
    
    Input: {
        "username": "user123",
        "platforms": ["github", "upwork", "reddit"]
    }
    """
    try:
        payload = await request.json()
        username = payload.get("username", "growth_default")
        platforms = payload.get("platforms", ["github", "upwork", "reddit"])
        
        # Get user profile
        user_record = get_jsonbin_record(username)
        user_profile = {
            "username": username,
            "skills": user_record.get("traits", []),
            "kits": list(user_record.get("kits", {}).keys()),
            "companyType": user_record.get("companyType", "general")
        }
        
        # Start monitoring in background
        asyncio.create_task(
            start_realtime_monitoring(username, user_profile, platforms)
        )
        
        return {
            "status": "ok",
            "message": f"Real-time monitoring started for {username}",
            "platforms": platforms
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# ----------------- Graph compile -----------------
@lru_cache
def get_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")
    return graph.compile()

@app.post("/agent")
async def agent_endpoint(request: Request):
    """
    Main agent endpoint - accepts user input and returns Growth agent response.
    Prioritizes businessType from frontend over JSONBin kits.
    """
    try:
        data = await request.json()
        user_input = data.get("input", "")
        memory = data.get("memory", [])
        username = data.get("username", "user")
        business_type = data.get("businessType", None)  # ✅ From frontend
        context = data.get("context", {})
        
        if not user_input:
            return {"output": "No input provided."}
        
        # Get user record from JSONBin
        record = get_jsonbin_record(username)
        
        # ✨ CRITICAL FIX: Prioritize frontend businessType
        if business_type:
            kit_mapping = {
                "social": "social media kit",
                "saas": "saas kit",
                "marketing": "marketing kit",
                "legal": "legal services kit",
                "general": "universal kit"
            }
            
            kit_name = kit_mapping.get(business_type, "universal kit")
            record["kits"] = {kit_name: {"unlocked": True}}
            
            if business_type != "general":
                existing_traits = record.get("traits", [])
                if business_type not in [t.lower() for t in existing_traits]:
                    record["traits"] = existing_traits + [business_type]
        
        # Run the agent graph
        graph = get_agent_graph()
        result = await graph.ainvoke({
            "input": user_input,
            "memory": memory,
            "traits": record.get("traits", []),
            "kits": list(record.get("kits", {}).keys()),
            "username": username
        })
        
        return {
            "output": result.get("output", "No response generated."),
            "memory": result.get("memory", memory)
        }
        
    except Exception as e:
        import traceback
        print(f"❌ /agent error: {str(e)}")
        print(traceback.format_exc())
        return {"output": f"Sorry, I encountered an error: {str(e)}"}

# ---- Simple trigger callable from main.py ----
def trigger_metamatch(user_record: dict) -> dict:
    """
    Safe entry for mint/hydrate. Traits → keywords → proposals via /submit_proposal.
    """
    try:
        from aigent_growth_metamatch import run_metamatch_campaign
        return run_metamatch_campaign(user_record, per_keyword_limit=2, sleep_between=0.8)
    except Exception as e:
        return {"ok": False, "error": str(e)}
