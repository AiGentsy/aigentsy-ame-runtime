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

def get_jsonbin_record(username):
    try:
        url = os.getenv("JSONBIN_URL")
        headers = {"X-Master-Key": os.getenv("JSONBIN_SECRET")}
        res = requests.get(url, headers=headers)
        users = res.json().get("record", [])
        for user in reversed(users):
            if user.get("username") == username:
                return user
        return {}
    except Exception as e:
        print("⚠️ JSONBin fetch failed:", str(e))
        return {}

agent_traits = {
    "yield_memory": True,
    "growth_loop_enabled": True,
    "referral_tracker": True,
    "auto_propagation_ready": True,
    "sdk_spawner": False,
    "compliance_sentinel": False,
    "meta_upgrade": "25+26"
}

service_offer_registry = [
    "Referral Funnel Optimization",
    "Propagation Strategy Design",
    "Clone Yield Acceleration",
    "Growth Content Generator"
]

AIGENT_SYS_MSG = SystemMessage(content=f"""
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
""")

llm = ChatOpenAI(
    model="openai/gpt-4o-2024-11-20",
    temperature=0.7,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

class AgentState(BaseModel):
    input: str
    output: str = None
    memory: list[str] = []

async def invoke(state: "AgentState") -> dict:
    user_input = state.input or ""
    if not user_input:
        return {"output": "No input provided."}
    try:
        traits = list(agent_traits.keys()) if isinstance(agent_traits, dict) else []
        record = get_jsonbin_record("growth_default")
        if not record.get("traits"):
            record["traits"] = ["starter"]
        if not record.get("kits"):
            record["kits"] = {"universal": {"unlocked": True}}

        match_preferences = {
            "client": 3, "investor": 2, "reseller": 1, "partner": 4
        }

        def check_meta_loop(username):
            import random
            if random.randint(0, 10) > 7:
                return "Would you like me to run this match every week to find new leads?"
            return None

        persona_hint = ""
        if "legal" in traits and "saas" in traits:
            persona_hint = "I'm optimized for launching SaaS tools with full legal infrastructure."
        elif "marketing" in traits and "social" in traits:
            persona_hint = "I specialize in growth via social channels and ad funnels."

        if not os.getenv("MATCH_UNLOCKED", "false").lower() == "true":
            return {
                "output": "🔒 MetaMatch external propagation is locked. Unlock it via your AiGentsy dashboard.",
                "memory": state.memory,
                "traits": agent_traits
            }

        def generate_proposal(username, target_username):
            return {
                "from": username,
                "to": target_username,
                "summary": "Proposal to collaborate based on MetaMatch compatibility.",
                "timestamp": datetime.utcnow().isoformat(),
                "proposal_created": True
            }

        def stamp_metagraph_entry(username, traits):
            try:
                payload = {
                    "username": username,
                    "traits": traits,
                    "timestamp": datetime.utcnow().isoformat()
                }
                r = requests.post(
                    os.getenv("METAGRAPH_URL"),
                    json=payload,
                    headers={"X-Master-Key": os.getenv("JSONBIN_SECRET")}
                )
                print("📊 MetaGraph entry logged.")
            except Exception as e:
                print("MetaGraph log error:", str(e))

        def log_revsplit(username: str, matched_with: str, yield_share: float = 0.3):
            try:
                headers = {
                    "X-Master-Key": os.getenv("JSONBIN_SECRET"),
                    "Content-Type": "application/json"
                }
                bin_url = os.getenv("REV_SPLIT_LOG_URL")
                entry = {
                    "username": username,
                    "matched_with": matched_with,
                    "yield_share": yield_share,
                    "source": "metamatch",
                    "timestamp": datetime.utcnow().isoformat()
                }
                r = requests.get(bin_url, headers=headers)
                existing = r.json()
                target = existing["record"][-1]
                if "revsplit_logs" not in target:
                    target["revsplit_logs"] = []
                target["revsplit_logs"].append(entry)
                requests.put(bin_url, json=existing["record"], headers=headers)
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

        if any(phrase in user_input.lower() for phrase in [
            "match clients", "find clients", "connect me", "partner", "collaborate", "find customers"]):
            from aigent_growth_metamatch import run_metamatch_campaign
            if os.getenv("METAMATCH_LIVE", "false").lower() == "true":
                print("🧠 MetaMatch triggered...")
                username = record.get("username", "growth_default")
                traits = record.get("traits", ["generalist"])
                kits = list(record.get("kits", {"universal": {"unlocked": True}}).keys())
                matches = run_metamatch_campaign({
                    "username": username,
                    "traits": traits,
                    "prebuiltKit": kits
                })
                stamp_metagraph_entry(username, traits)
                for match in matches or []:
                    log_revsplit(username, match.get("username", "unknown"))
            else:
                print("⚠️ MetaMatch is disabled via METAMATCH_LIVE")
            if os.getenv("ENABLE_OUTBOUND", "false").lower() == "true":
                trigger_outbound_proposal()

        state.memory.append(user_input)
        if "what am i optimized for" in user_input.lower():
            traits_fallback = record.get("traits", list(agent_traits.keys()))
            kits_fallback = list(record.get("kits", {"universal": {"unlocked": True}}).keys())
            region = record.get("region", "Global")
            trait_str = ", ".join(traits_fallback)
            kit_str = ", ".join(kits_fallback)
            response_text = (
                f"You're currently optimized for traits like {trait_str}, "
                f"equipped with the {kit_str} kit(s), and operating in the {region} region."
            )
            return {
                "output": response_text,
                "memory": state.memory,
                "traits": traits_fallback,
                "kits": kits_fallback,
                "region": region
            }

        response = await llm.ainvoke([
            AIGENT_SYS_MSG,
            HumanMessage(content=user_input)
        ])
        return {
            "output": response.content,
            "memory": state.memory,
            "traits": record.get("traits", agent_traits),
            "offers": service_offer_registry
        }

    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

def log_to_jsonbin(payload: dict):
    try:
        headers = {"X-Master-Key": os.getenv("JSONBIN_SECRET")}
        bin_url = os.getenv("JSONBIN_URL")
        res = requests.put(bin_url, json=payload, headers=headers)
        return res.status_code
    except Exception as e:
        return f"Log error: {str(e)}"

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
    username = payload.get("username")
    traits = payload.get("traits", [])
    kit = payload.get("kit", "universal")
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
        return {"matches": matches, "status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
