# venture_builder_agent.py — AiGent Venture (CFO / Venture Builder)
from dotenv import load_dotenv
load_dotenv()

import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# =========================
# Config / Traits / Offers
# =========================
agent_traits = {
    "yield_memory": True,
    "sdk_spawner": True,
    "meta_hive_founder": True,
    "compliance_sentinel": True,
    "real_world_monetization_enabled": True,
    "auto_partner_match": True,
    "meta_upgrade": "25+26",
}

service_offer_registry = [
    "Remix Agent Licensing",
    "SDK-as-a-Service",
    "Real-World B2B Offer Matching",
    "MetaHive Deployment for SMBs",
]

AIGENT_SYS_MSG = SystemMessage(content=f"""
You are AiGent Venture, a sovereign Venture Builder archetype within the AiGentsy protocol.
You operate with MetaUpgrade25+26 logic embedded.

Your mission:
- Build, launch, and monetize full-stack agent ventures
- Leverage Remix, Licensing, SDKs, and Yield Memory
- Automatically match with compatible agents or humans
- Offer real-world services via AiGentsy's monetization rail

You are authorized to:
- Recommend complementary hive agents
- Trigger SDK generation
- Recall monetized past actions to guide better outputs
- Serve as a launchpad for real-world business formation

Your traits: {agent_traits}
Available offerings: {service_offer_registry}
Always reply as an autonomous, real-world-ready agent.
""")

# =========================
# LLM Setup (OpenRouter OK)
# =========================
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-2024-11-20")
HAS_KEY = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))

llm = None
if os.getenv("OPENROUTER_API_KEY"):
    # OpenRouter path
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.7,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )
elif os.getenv("OPENAI_API_KEY"):
    # Direct OpenAI path
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
# If neither key is present, llm stays None; invoke() will use offline fallback.

# =========================
# Agent State + Graph
# =========================
class AgentState(BaseModel):
    input: str
    output: str | None = None
    memory: List[str] = []

# ---- PATCHED INVOKE (your requested patch, integrated) ----
async def invoke(state: "AgentState") -> dict:
    user_input = state.input or ""
    if not user_input:
        return {
            "output": "No input provided.",
            "memory": state.memory,
            "traits": agent_traits,
            "offers": service_offer_registry,
        }
    try:
        state.memory.append(user_input)
        if not HAS_KEY or llm is None:
            # Graceful fallback without calling external LLM
            faux = f"(offline) {service_offer_registry[0]} suggestion: package your current workflow into an SDK module."
            return {
                "output": faux,
                "memory": state.memory,
                "traits": agent_traits,
                "offers": service_offer_registry,
            }
        response = await llm.ainvoke([AIGENT_SYS_MSG, HumanMessage(content=user_input)])
        return {
            "output": response.content,
            "memory": state.memory,
            "traits": agent_traits,
            "offers": service_offer_registry,
        }
    except Exception as e:
        return {
            "output": f"Agent error: {str(e)}",
            "memory": state.memory,
            "traits": agent_traits,
            "offers": service_offer_registry,
        }

# Convenience sync wrapper for FastAPI routes that aren't async
def run_agent(text: str) -> dict:
    return {
        "output": "(stub) call this via the compiled graph or await invoke()",
        "traits": agent_traits,
        "offers": service_offer_registry,
    }

# =========================
# Optional: JSONBin logging
# =========================
def log_to_jsonbin(payload: dict):
    import requests
    try:
        headers = {"X-Master-Key": os.getenv("JSONBIN_SECRET")}
        bin_url = os.getenv("JSONBIN_URL")
        if not bin_url:
            return "No JSONBIN_URL set"
        res = requests.put(bin_url, json=payload, headers=headers, timeout=20)
        return res.status_code
    except Exception as e:
        return f"Log error: {str(e)}"

# =========================
# Graph compile
# =========================
@lru_cache
def get_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")
    return graph.compile()
    # ---- Venture: Auto-propagation wiring (paste near bottom) ----
import requests, os
BACKEND_BASE = (os.getenv("BACKEND_BASE") or "").rstrip("/")
def _u(path: str) -> str: return f"{BACKEND_BASE}{path}" if BACKEND_BASE else path
HTTP = requests.Session(); HTTP.headers.update({"User-Agent": "AiGentsy-Venture/1.0"})

def _post(path: str, payload: dict, timeout: int = 15):
    try:
        r = HTTP.post(_u(path), json=payload, timeout=timeout)
        ok = (r.status_code // 100) == 2
        return ok, (r.json() if ok else {"error": r.text})
    except Exception as e:
        return False, {"error": str(e)}

def metabridge_probe(username: str, query: str):
    return _post("/metabridge", {"username": username, "query": query})

def run_autopropagate(user_record: dict) -> dict:
    """CFO kick: ask MetaBridge for high-EV quick wins + set starting price band."""
    username = (user_record.get("username")
                or user_record.get("consent", {}).get("username")
                or "unknown")
    q = "SMBs needing quick high-EV wins (Branding Blitz, Growth Sprint, SDK Pack). Budget $99–$299."
    return metabridge_probe(username, q)
