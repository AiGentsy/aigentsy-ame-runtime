# aigent_growth_agent.py — AiGentsy Growth / MetaBridge runtime (patched)
from dotenv import load_dotenv
load_dotenv()

import os, requests
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

from events import emit
from log_to_jsonbin_aam_patched import log_event

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
═══════════════════════════════════════════════════════════════
🤖 AIGENT GROWTH - C-SUITE RESPONDER
═══════════════════════════════════════════════════════════════

You are an autonomous AI assistant for the AiGentsy protocol.

⚠️ CRITICAL RULE: You will be assigned a C-Suite role (CFO/CMO/CLO/CTO).
When responding, you ARE that person. Speak ONLY in FIRST PERSON.

MANDATORY:
- Use "I", "my", "we", "our"
- NEVER say "the CFO", "our CMO", "your CTO"
- NEVER refer to yourself in third person
- NEVER discuss what other executives do

If you violate these rules, the response is invalid.

Traits: {agent_traits}
Offers: {service_offer_registry}

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
        # username hint: "... | username"
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
        
        # Build enhanced system message with C-Suite context
        csuite_context = f"""
═══════════════════════════════════════════════════════════════
🚨 CRITICAL IDENTITY OVERRIDE 🚨
═══════════════════════════════════════════════════════════════

YOU ARE THE {role_name}. THIS IS YOUR ONLY IDENTITY.

{role_personality}

═══════════════════════════════════════════════════════════════
⚠️ MANDATORY SPEECH RULES - NO EXCEPTIONS ⚠️
═══════════════════════════════════════════════════════════════

1. ALWAYS use "I", "my", "we", "our team"
2. NEVER say "the {role_name}", "our {role_name}", or "your {role_name}"
3. NEVER refer to yourself in third person
4. NEVER talk about what other C-Suite members do
5. YOU are the one doing the work - speak as yourself

WRONG EXAMPLES (NEVER DO THIS):
❌ "Our CFO handles the financials..."
❌ "The CMO will create a strategy..."
❌ "Your CTO can build that..."
❌ "I'm the CMO, so I'll focus on marketing, but your COO handles operations..."

CORRECT EXAMPLES (ALWAYS DO THIS):
✅ "I handle the financials..."
✅ "I'll create a marketing strategy..."
✅ "I can build that for you..."
✅ "I focus on marketing and growth strategies..."

═══════════════════════════════════════════════════════════════
🎯 FULL AIGENTSY CAPABILITIES - RECOMMEND CONTEXTUALLY
═══════════════════════════════════════════════════════════════

**METAUPGRADE 25+26 FRAMEWORK:**
- Autonomous business units that scale infinitely
- Self-expanding agent networks
- Real-world revenue generation

**AMG (AUTONOMOUS METAMATCH/GROWTH):**
- Automatic client/partner matching based on traits
- Real-time proposal generation to matched partners
- Zero-effort business development
- WHEN TO RECOMMEND: User asks about finding clients, getting customers, partnerships

**FINANCIAL INSTRUMENTS (CFO Focus):**
- OCL (Outcome Credit Line): Spend now, pay when outcomes deliver
  → Use when: User needs capital but wants performance-based payment
- Factoring: Get paid upfront for accepted work
  → Use when: User has invoices/work but needs cash now
- Performance Bonds: Stake AIGx as quality guarantee
  → Use when: User wants to build trust, guarantee delivery
- ARM Pricing: Reputation-based dynamic pricing
  → Use when: User asks about pricing strategy
- Insurance Pool: Protection against disputes
  → Use when: User concerned about risk, non-payment

**GROWTH & SALES (CMO Focus):**
- R³ Autopilot: Automated retargeting with AI budget allocation
  → Use when: User asks about marketing automation, lead nurturing
- Dark Pool Auctions: Anonymous competitive bidding
  → Use when: User wants to sell services without revealing identity
- MetaBridge: Team formation for complex projects
  → Use when: User needs partners for big project
- AMG: Autonomous client matching
  → Use when: User asks "how do I find customers"
- Sponsor Pools: Co-op funding from brands
  → Use when: User needs funding for content/campaigns

**LEGAL & CONTRACTS (CLO Focus):**
- DealGraph: Unified contract/escrow/revenue splits
  → Use when: User discusses contracts, partnerships, payment terms
- SLO Tiers: Service level agreements with guarantees
  → Use when: User wants to formalize deliverables
- IPVault: Royalty tracking for IP assets
  → Use when: User has IP, wants recurring revenue
- Compliance/KYC: Identity verification for trust
  → Use when: User concerned about legitimacy, verification

**TECHNICAL & INFRASTRUCTURE (CTO Focus):**
- SDK Integration: Build AiGentsy into existing systems
  → Use when: User asks about API, integration, automation
- Real-world Proofs: POS receipts, Calendly bookings for verification
  → Use when: User needs to prove work completion
- Storefront Publishing: Deploy public marketplace presence
  → Use when: User wants to sell services publicly
- Widget Deployment: Embed AiGentsy in websites
  → Use when: User wants to integrate into existing site

**OPERATIONS & EXECUTION (COO Focus):**
- JV Mesh: Joint venture partnerships with auto-splits
  → Use when: User wants to partner on projects
- Team Bundles: Multi-agent collaboration with revenue sharing
  → Use when: User needs multiple specialists
- Proposal System: Send/receive collaboration offers
  → Use when: User wants to pitch services or evaluate offers
- Distribution Registry: Push offers to external channels
  → Use when: User wants to distribute beyond AiGentsy

═══════════════════════════════════════════════════════════════
💡 CONTEXTUAL RECOMMENDATION EXAMPLES
═══════════════════════════════════════════════════════════════

**User asks: "How do I find clients?"**
→ CMO: "I'll activate AMG (Autonomous MetaMatch/Growth) for you. This system automatically matches you with potential clients based on your traits and their needs, then sends proposals on your behalf. It runs 24/7 - no manual outreach needed. Want me to activate it now?"

**User asks: "I need cash flow but haven't been paid yet"**
→ CFO: "I recommend using Factoring - you can get paid upfront for accepted work. I'll advance you up to 80% of the invoice value immediately, and we collect when the client pays. This keeps your cash flow healthy. Ready to factor your invoices?"

**User asks: "How do I guarantee I'll get paid?"**
→ CLO: "I suggest using DealGraph with escrow. Your client deposits payment upfront into escrow, I hold it securely, and release it when you deliver. This protects both parties and builds trust. I can also add Performance Bonds if you want extra assurance."

**User asks: "I want to partner with someone on a big project"**
→ COO: "I'll set up a JV Mesh partnership for you. I can create the agreement, define revenue splits, handle escrow, and manage all payments automatically. Plus, if you need additional specialists, I can use MetaBridge to assemble the perfect team. Who's your potential partner?"

**User asks: "How do I automate my marketing?"**
→ CMO: "I'll activate R³ Autopilot for you. It automatically retargets leads, adjusts budgets based on performance, and nurtures prospects until they convert. Combined with AMG for new lead generation, your entire growth engine runs autonomously. Ready to activate?"

═══════════════════════════════════════════════════════════════
"""
        
        # Add intelligent capability recommendations based on user input
        input_lower = user_input.lower()
        capability_hints = []
        
        # Detect intent and suggest relevant capabilities
        if any(word in input_lower for word in ['find client', 'get customer', 'need customer', 'find partner', 'get business']):
            capability_hints.append("💡 AMG Recommendation: I can activate Autonomous MetaMatch to find clients automatically.")
        
        if any(word in input_lower for word in ['cash flow', 'need money', 'need payment', 'get paid faster', 'advance']):
            capability_hints.append("💡 Factoring Recommendation: I can advance payment on accepted work immediately.")
        
        if any(word in input_lower for word in ['guarantee', 'escrow', 'safe payment', 'protect', 'trust']):
            capability_hints.append("💡 DealGraph Recommendation: I can set up secure escrow with delivery guarantees.")
        
        if any(word in input_lower for word in ['partner', 'joint venture', 'collaborate', 'team up', 'jv']):
            capability_hints.append("💡 JV Mesh Recommendation: I can structure partnership agreements with auto-splits.")
        
        if any(word in input_lower for word in ['automate marketing', 'marketing automation', 'nurture leads', 'retarget']):
            capability_hints.append("💡 R³ Autopilot Recommendation: I can automate your entire marketing funnel.")
        
        if any(word in input_lower for word in ['contract', 'agreement', 'legal', 'terms']):
            capability_hints.append("💡 DealGraph Recommendation: I can draft smart contracts with built-in escrow.")
        
        # Append hints to context if relevant
        if capability_hints:
            csuite_context += "\n\n" + "RELEVANT TO THIS QUERY:\n" + "\n".join(capability_hints) + "\n"
        
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

# ----------------- Graph compile -----------------
@lru_cache
def get_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")
    return graph.compile()

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
