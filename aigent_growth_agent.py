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
                # ---- NEW: compute service needs ---------------------------------
        service_needs = suggest_service_needs(traits, kits)

        match_preferences = {"client": 3, "investor": 2, "reseller": 1, "partner": 4}

        if os.getenv("MATCH_UNLOCKED", "false").lower() != "true":
            return {
                "output": "🔒 MetaMatch external propagation is locked. Unlock it via your AiGentsy dashboard.",
                "memory": state.memory,
                "traits": traits,
            }

        if any(
            phrase in user_input.lower()
            for phrase in ["match clients", "find clients", "connect me", "partner", "collaborate", "find customers"]
        ):
            from aigent_growth_metamatch import run_metamatch_campaign

            if os.getenv("METAMATCH_LIVE", "false").lower() == "true":
                print("🧠 MetaMatch triggered…")
                matches = run_metamatch_campaign(
                    {"username": username, "traits": traits, "prebuiltKit": kits}
                )
                stamp_metagraph_entry(username, traits)
                for m in matches or []:
                    log_revsplit(username, m.get("username", "unknown"))
            else:
                print("⚠️ MetaMatch is disabled via METAMATCH_LIVE flag")

            if os.getenv("ENABLE_OUTBOUND", "false").lower() == "true":
                trigger_outbound_proposal()

        state.memory.append(user_input)
        if "what am i optimized for" in user_input.lower():
            trait_str = ", ".join(traits)
            kit_str = ", ".join(kits)
            resp = (
                f"Traits ➜ {', '.join(traits)}  |  Kits ➜ {', '.join(kits)}  "
                f"| Region ➜ {region}\n"
                f"🔍 Next suggested moves: {', '.join(service_needs)}"
            )
            return {
                "output": resp,
                "memory": state.memory,
                "traits": traits,
                "kits": kits,
                "region": region,
                "suggested_services": service_needs,
            }

        # ---- Trait‑aware fallback ----
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

# ----------------- Graph & Endpoint -----------------

@lru_cache
def get_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")
    return graph.compile()

app = FastAPI()

@app.post("/metabridge")
async def metabridge(request: Request):
    payload = await request.json()
    username = payload.get("username", "growth_default")
    traits = payload.get("traits")
    kit = payload.get("kit")

    if not traits or not kit:
        record = get_jsonbin_record(username)
        traits = record.get("traits", ["starter"])
        kit = list(record.get("kits", {"universal": {"unlocked": True}}).keys())

    try:
        from aigent_growth_metamatch import run_metamatch_campaign
        matches = run_metamatch_campaign({
            "username": username,
            "traits": traits,
            "prebuiltKit": kit
        })
        return {
            "matches": matches,
            "status": "ok",
            "traits_used": traits,
            "kits_used": kit,
            "username": username
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
