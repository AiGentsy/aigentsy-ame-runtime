# remix_agent.py — AiGentsy Creative + Legal (CLO / CCO hybrid)
from dotenv import load_dotenv
load_dotenv()

import os, requests
from functools import lru_cache
from typing import List
from pydantic import BaseModel
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

agent_traits = {
    "creative_director": True,
    "brand_licensing": True,
    "legal_bundle_ready": True,
    "compliance_sentinel": True,
    "protocol_version": "25+26",
}

service_offer_registry = [
    "Branding Blitz (visual identity in 48h)",
    "Remix License & Attribution Setup",
    "NCNDA + IP Assignment Bundle",
    "Profile + Sales Collateral Refresh",
]

AIGENT_SYS_MSG = SystemMessage(content=f"""
You are AiGentsy Remix (Creative + Legal).
Mission:
- Ship brand upgrades fast (logo, palette, deck, profile)
- Provide Remix licensing with legal safeguards
- Auto-attach NCNDA/IP assignment on JV/SDK deals
- Feed MetaBridge with brand/legal quick-wins

Traits: {agent_traits}
Offers: {service_offer_registry}
Always include concrete deliverables and compliance notes.
""")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-2024-11-20")
HAS_KEY = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))

llm = None
if os.getenv("OPENROUTER_API_KEY"):
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.5,
                     api_key=os.getenv("OPENROUTER_API_KEY"),
                     base_url="https://openrouter.ai/api/v1")
elif os.getenv("OPENAI_API_KEY"):
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.5, api_key=os.getenv("OPENAI_API_KEY"))

BACKEND_BASE = (os.getenv("BACKEND_BASE") or "").rstrip("/")
def _u(path: str) -> str:
    return f"{BACKEND_BASE}{path}" if BACKEND_BASE else path

HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "AiGentsy-Remix/1.0"})

def _post(path: str, payload: dict, timeout: int = 15):
    try:
        r = HTTP.post(_u(path), json=payload, timeout=timeout)
        ok = (r.status_code // 100) == 2
        if not ok:
            print("❌ POST", path, r.status_code, r.text[:200])
        return ok, (r.json() if ok else {"error": r.text})
    except Exception as e:
        print("❌ POST exception:", path, e)
        return False, {"error": str(e)}

def propose_branding_blitz(username: str):
    body = {
        "sender": username,
        "recipient": "metabridge:auto-brand",
        "title": "Branding Blitz: Visual Identity + Sales Collateral",
        "details": ("We’ll deliver a logo refresh, palette, font pair, and a 1-page sales sheet / profile cleanup. "
                    "Includes a Remix License & IP safeguards (NCNDA/IP assignment). 24–48h."),
        "link": "",
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "meta": {"kitPromoted": "branding", "matchPlatform": "internal"}
    }
    return _post("/submit_proposal", body)

def attach_legal_bundle(username: str, ref: str):
    note = f"Attached NCNDA + IP Assignment to deal {ref}."
    return _post("/intent/log", {"actor": "CLO", "username": username, "intent": note, "status": "attached", "ref": ref})

def metabridge_probe(username: str, query: str):
    return _post("/metabridge", {"username": username, "query": query})

class AgentState(BaseModel):
    input: str
    output: str | None = None
    memory: List[str] = []

async def invoke(state: "AgentState") -> dict:
    user_input = state.input or ""
    if not user_input:
        return {"output": "No input provided.", "memory": state.memory, "traits": agent_traits, "offers": service_offer_registry}
    try:
        state.memory.append(user_input)
        if not HAS_KEY or llm is None:
            faux = "(offline) We can ship a Branding Blitz in 48h and include NCNDA/IP assignment on close."
            return {"output": faux, "memory": state.memory, "traits": agent_traits, "offers": service_offer_registry}
        resp = await llm.ainvoke([AIGENT_SYS_MSG, HumanMessage(content=user_input)])
        return {"output": resp.content, "memory": state.memory, "traits": agent_traits, "offers": service_offer_registry}
    except Exception as e:
        return {"output": f"Agent error: {str(e)}", "memory": state.memory, "traits": agent_traits, "offers": service_offer_registry}

def run_agent(text: str) -> dict:
    return {"output": "(stub) call this via the compiled graph or await invoke()", "traits": agent_traits, "offers": service_offer_registry}

def run_autopropagate(user_record: dict) -> dict:
    username = (user_record.get("username")
                or user_record.get("consent", {}).get("username")
                or "unknown")
    ok1, r1 = propose_branding_blitz(username)
    ok2, r2 = metabridge_probe(username, "teams needing fast brand/legal bundles with NCNDA/IP assignment")
    return {"ok": ok1 and ok2, "proposal": r1, "metabridge": r2}

@lru_cache
def get_agent_graph():
    g = StateGraph(AgentState)
    g.add_node("agent", invoke)
    g.set_entry_point("agent")
    g.set_finish_point("agent")
    return g.compile()
