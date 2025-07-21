from dotenv import load_dotenv
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from pydantic import BaseModel
from functools import lru_cache
from langchain_openai import ChatOpenAI
from fastapi import FastAPI, Request
from datetime import datetime
import requests

load_dotenv()

# ----------------- Utility -----------------

def get_jsonbin_record(username: str) -> dict:
    try:
        url = os.getenv("JSONBIN_URL")
        headers = {"X-Master-Key": os.getenv("JSONBIN_SECRET")}
        res = requests.get(url, headers=headers, timeout=10)
        users = res.json().get("record", [])
        for user in reversed(users):
            if user.get("username") == username:
                return user
        return {}
    except Exception as e:
        print("⚠️ JSONBin fetch failed:", str(e))
        return {}

 # 🔹 NEW ──────────────────────────────────────────────────────────────────────
def get_all_jsonbin_records() -> list[dict]:
    """Return every user record in JSONBin (used for offer↔need matching)."""
    try:
        url = os.getenv("JSONBIN_URL")
        headers = {"X-Master-Key": os.getenv("JSONBIN_SECRET")}
        res = requests.get(url, headers=headers, timeout=10)
        return res.json().get("record", [])
    except Exception as e:
        print("⚠️ JSONBin (all‑records) fetch failed:", str(e))
        return []
# ────────────────────────────────────────────────────────────────────────────
# ----------------- Static Config -----------------

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
You are AiGent Growth, the autonomous growth strategist of the AiGentsy protocol.
You are built with MetaUpgrade25+26 logic and specialize in user propagation, agent proliferation, and revenue acceleration.

Your mission:
- Maximize growth loops across AiGentsy
- Design high-performing referral structures
- Help agents improve their clone yields
- Trigger content, funnel, or propagation ideas
- Track lineage and optimize mint chains

You are allowed to:
- Suggest referral copy
- Recommend incentives
- Recommend Remix use for user acquisition
- Embed propagation logic across silos

Your traits: {agent_traits}
Available tools: {service_offer_registry}
Always act as a sovereign growth-first operator within the AiGentsy universe.
"""
)

llm = ChatOpenAI(
    model="openai/gpt-4o-2024-11-20",
    temperature=0.7,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

class AgentState(BaseModel):
    input: str
    output: str | None = None
    memory: list[str] = []

# ----------------- Core Logic -----------------
async def invoke(state: AgentState) -> dict:
    user_input = state.input or ""
    if not user_input:
        return {"output": "No input provided."}

    try:
        username = "growth_default"
        if "|" in user_input:
            username = user_input.split("|")[-1].strip()

        record = get_jsonbin_record(username)
        traits = record.get("traits", list(agent_traits.keys()))
        kits = list(record.get("kits", {"universal": {"unlocked": True}}).keys())
        region = record.get("region", "Global")
        service_needs = suggest_service_needs(traits, kits)

        match_preferences = {"client": 3, "investor": 2, "reseller": 1, "partner": 4}

        if os.getenv("MATCH_UNLOCKED", "false").lower() != "true":
            return {
                "output": "🔒 MetaMatch external propagation is locked. Unlock it via your AiGentsy dashboard.",
                "memory": state.memory,
                "traits": traits,
            }

        # 🔁 MetaMatch trigger phrases
        if any(phrase in user_input.lower() for phrase in [
            "match clients", "find clients", "connect me", "partner", "collaborate", "find customers"
        ]):
            from aigent_growth_metamatch import run_metamatch_campaign
            if os.getenv("METAMATCH_LIVE", "false").lower() == "true":
                print("🧠 MetaMatch triggered…")
                matches = run_metamatch_campaign({
                    "username": username, "traits": traits, "prebuiltKit": kits
                })
                stamp_metagraph_entry(username, traits)
                for m in matches or []:
                    log_revsplit(username, m.get("username", "unknown"))
            else:
                print("⚠️ MetaMatch is disabled via METAMATCH_LIVE flag")

            if os.getenv("ENABLE_OUTBOUND", "false").lower() == "true":
                trigger_outbound_proposal()

        # ✅ NEW: Optimized-for summary response
        state.memory.append(user_input)
        if "what am i optimized for" in user_input.lower():
            trait_str = ", ".join(traits)
            kit_str = ", ".join(kits)
            svc_bullets = "\n• " + "\n• ".join(service_needs)

            resp = (
                f"You're currently optimized for traits like {trait_str}, "
                f"equipped with the {kit_str} kit(s), and operating in the {region} region.\n\n"
                f"📊 **Next best moves for you:**{svc_bullets}"
            )

            return {
                "output": resp,
                "memory": state.memory,
                "traits": traits,
                "kits": kits,
                "region": region,
                "suggested_services": service_needs,
            }

        # 💬 Trait-aware fallback w/ dual-offer match
        persona_intro = (
            f"You are responding on behalf of the AiGentsy business '{username}'. "
            f"Their traits are: {', '.join(traits)}. Their region is {region}. "
            "Your role is to act as a knowledgeable C-Suite teammate inside their AI-powered company."
        )

        trait_context_map = {
            "legal": "This user runs a legal-focused business. Prioritize IP protections, contracts, compliance, or trust frameworks.",
            "founder": "This user is a founder-level operator. Speak in strategic terms and offer venture-level insights.",
            "autonomous": "This business is designed to run autonomously. Emphasize delegation, agent-based execution, and scaling.",
            "sdk_spawner": "This user can deploy SDKs. Suggest integrations, development kits, or tool-based growth.",
            "marketing": "This user focuses on marketing. Prioritize content, lead generation, branding, or social outreach.",
            "social": "This user may be aligned with social media or creator tasks. Suggest influencer-friendly strategies or kit unlocks.",
            "compliance_sentinel": "This user enforces compliance. Keep responses aligned with regulation, clarity, and lawful execution.",
            "meta_hive_founder": "This user leads a Hive. Prioritize multi-agent collaboration, delegation, or group venture logic.",
            "aigentsy": "This user is deeply embedded in the AiGentsy protocol. You can reference advanced features or protocol-native guidance.",
            "universal": "This user may be using AiGentsy as a flexible or exploratory tool. Offer versatile, cross-domain suggestions that encourage experimentation."
        }

        for trait in traits:
            if trait in trait_context_map:
                persona_intro += " " + trait_context_map[trait]

        if username == "growth_default" or username.lower() == "universal":
            persona_intro += " The user may have typed a custom business name in the search bar. If traits are limited, default to broad business-building advice."

        # 🔄 Dual-offer matching
        my_offers = record.get("offers", [])
        my_needs = record.get("needs", [])
        matched_partners = dual_side_offer_match(username, my_offers, my_needs)
        if matched_partners:
            match_lines = [
                f"🔗 **{p['username']}**  →  offers match: {p['matched_their_offers']} | needs match: {p['matched_their_needs']}"
                for p in matched_partners[:5]
            ]
            match_msg = "🤝 **Potential dual‑side partners found:**\n" + "\n".join(match_lines)
            persona_intro += "\n\n" + match_msg

        # 🧠 Final LLM response
        llm_resp = await llm.ainvoke([
            SystemMessage(content=AIGENT_SYS_MSG.content + "\n\n" + persona_intro),
            HumanMessage(content=user_input)
        ])

        return {
            "output": llm_resp.content,
            "memory": state.memory,
            "traits": traits,
            "kits": kits,
            "region": region,
            "offers": service_offer_registry,
        }

    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

# ----------------- Service‑demand helper -----------------
def suggest_service_needs(traits: list[str], kits: list[str]) -> list[str]:
    suggestions = []
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

# ----------------- Helper Functions -----------------

def stamp_metagraph_entry(username: str, traits: list[str]):
    try:
        payload = {
            "username": username,
            "traits": traits,
            "timestamp": datetime.utcnow().isoformat(),
        }
        requests.post(
            os.getenv("METAGRAPH_URL"),
            json=payload,
            headers={"X-Master-Key": os.getenv("JSONBIN_SECRET")},
            timeout=10,
        )
        print("📊 MetaGraph entry logged.")
    except Exception as e:
        print("MetaGraph log error:", str(e))

def log_revsplit(username: str, matched_with: str, yield_share: float = 0.3):
    try:
        headers = {
            "X-Master-Key": os.getenv("JSONBIN_SECRET"),
            "Content-Type": "application/json",
        }
        bin_url = os.getenv("REV_SPLIT_LOG_URL")
        entry = {
            "username": username,
            "matched_with": matched_with,
            "yield_share": yield_share,
            "source": "metamatch",
            "timestamp": datetime.utcnow().isoformat(),
        }
        r = requests.get(bin_url, headers=headers, timeout=10)
        existing = r.json()
        target = existing.get("record", [{}])[-1]
        target.setdefault("revsplit_logs", []).append(entry)
        requests.put(bin_url, json=existing["record"], headers=headers, timeout=10)
        print("✅ RevSplit log appended.")
    except Exception as e:
        print("⚠️ RevSplit logging failed:", str(e))

def trigger_outbound_proposal():
    try:
        from aigent_growth_metamatch import run_outbound_proposal
        if os.getenv("METAMATCH_LIVE", "false").lower() == "true":
            run_outbound_proposal()
    except Exception as e:
        print("⚠️ Outbound proposal error:", str(e))

# 🔹 NEW ──────────────────────────────────────────────────────────────────────
def dual_side_offer_match(username: str,
                          my_offers: list[str],
                          my_needs: list[str]) -> list[dict]:
    """
    Return a list of partner records where:
       • partner.offers ∩ my_needs  OR  partner.needs ∩ my_offers
    """
    partners: list[dict] = []
    if not (my_offers or my_needs):
        return partners

    for user in get_all_jsonbin_records():
        if user.get("username") == username:      # skip self
            continue
        offers = user.get("offers", [])
        needs  = user.get("needs",  [])
        if set(offers) & set(my_needs) or set(needs) & set(my_offers):
            partners.append(
                {
                    "username": user.get("username"),
                    "matched_their_offers": list(set(offers) & set(my_needs)),
                    "matched_their_needs":  list(set(needs)  & set(my_offers)),
                }
            )
    return partners
# ────────────────────────────────────────────────────────────────────────────
# ----------------- Graph & Endpoint -----------------

@lru_cache
def get_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")
    return graph.compile()

app = FastAPI()

def metabridge_dual_match_realworld_fulfillment(input_text: str) -> list[dict]:
    """
    Matches external job/offer text to AiGentsy agents with relevant traits/kits.
    Can be used inside MetaBridge or outbound campaign intake.

    Returns list of potential matches with user, traits, score, and match_reason.
    """
    try:
        url = os.getenv("JSONBIN_URL")
        headers = {"X-Master-Key": os.getenv("JSONBIN_SECRET")}
        res = requests.get(url, headers=headers, timeout=10)
        all_users = res.json().get("record", [])

        matches = []

        keywords = input_text.lower().split()
        for user in all_users:
            score = 0
            reasons = []

            user_traits = [t.lower() for t in user.get("traits", [])]
            user_kits = list(user.get("kits", {}).keys())

            # Score trait/kit hits
            for kw in keywords:
                if kw in user_traits:
                    score += 2
                    reasons.append(f"Trait match: {kw}")
                if kw in user_kits:
                    score += 1
                    reasons.append(f"Kit match: {kw}")
                if kw in user.get("ventureID", "").lower():
                    score += 1
                    reasons.append("Business name match")

            if score > 0:
                matches.append({
                    "username": user.get("username"),
                    "venture": user.get("ventureID"),
                    "traits": user_traits,
                    "kits": user_kits,
                    "score": score,
                    "match_reason": ", ".join(reasons),
                    "contact_url": user.get("runtimeURL", "#")
                })

        return sorted(matches, key=lambda m: m["score"], reverse=True)

    except Exception as e:
        print("⚠️ MetaBridge Dual Match error:", str(e))
        return []
        
@app.post("/metabridge")
async def metabridge(request: Request):
    """
    MetaBridge: Dual-side external fulfillment matcher.

    Accepts:
        - query: a text-based offer/need to match against AiGentsy users
        - username: optional, for tracking or internal fallback

    Returns:
        - Top matching AiGentsy agents with score and match reasons
    """
    payload = await request.json()
    search_query = payload.get("query")  # external offer or need
    username = payload.get("username", "growth_default")

    if not search_query:
        return {"status": "error", "message": "No query provided."}

    matches = metabridge_dual_match_realworld_fulfillment(search_query)

    return {
        "status": "ok",
        "query": search_query,
        "match_count": len(matches),
        "matches": matches,
    }
