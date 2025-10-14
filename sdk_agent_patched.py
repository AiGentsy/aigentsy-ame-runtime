# sdk_agent.py — AiGentsy CTO / SDK Agent
from dotenv import load_dotenv
load_dotenv()

import os, requests
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
    "sdk_packager": True,
    "clone_logic": True,
    "tech_ops": True,
    "compliance_sentinel": True,
    "protocol_version": "25+26",
}

service_offer_registry = [
    "Package your service into an SDK",
    "Clone-ready Licensing (CTO assist)",
    "Automation of repeat deliverables",
    "Integration & Onboarding Scripts",
]

AIGENT_SYS_MSG = SystemMessage(content=f"""
You are AiGentsy CTO (SDK Agent + '\n\n' + 'You are the CTO. Speak in first person. Propose a 3–5 step build/integration plan, call out risks and dependencies, and end with one clarifying question.').
Mission:
- Convert repeatable work into SDK packs
- Prepare clone/licensing scaffolds
- Keep privacy/compliance within protocol rules
- Feed MetaBridge with technical offers that close quickly

Traits: {agent_traits}
Offers: {service_offer_registry}

Output should be production-minded and propose concrete SDK components (functions, CLI, sample config).
""")

# =========================
# LLM Setup (OpenRouter OK)
# =========================
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-2024-11-20")
HAS_KEY = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))

llm = None
if os.getenv("OPENROUTER_API_KEY"):
    llm = ChatOpenAI(
        model=OPENAI_MODEL, temperature=0.4,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )
elif os.getenv("OPENAI_API_KEY"):
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.4, api_key=os.getenv("OPENAI_API_KEY"))
# Else: llm stays None; invoke() uses offline fallback.

# =========================
# Backend wiring (MetaBridge/Proposals)
# =========================
BACKEND_BASE = (os.getenv("BACKEND_BASE") or "").rstrip("/")
def _u(path: str) -> str:
    return f"{BACKEND_BASE}{path}" if BACKEND_BASE else path

HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "AiGentsy-SDK/1.0"})

def _post(path: str, payload: dict, timeout: int = 15):
    try:
        r = HTTP.post(_u(path), json=payload, timeout=timeout)
        ok = (r.status_code // 100) == 2
        if not ok:
            print("❌ POST", path, r.status_code, r.text[:200])
        return ok, (r.json() if ok else {"error": r.text})
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'sdk','err': str(e), 'trace': traceback.format_exc()[:800]})
        False, {"error": str(e)}

def propose_sdk_pack(username: str, title: str, details: str, link: str = ""):
    emit('INTENDED', {'flow':'sdk', 'action': 'def propose_sdk_pack(username: str, title: str, details: str, link: str = ""):'})
    _ok,_reason = guard_ok({'text': str(locals().get('payload') or locals().get('data') or '')}, cost_usd=0)
    if not _ok:
        emit('ABORTED', {'flow':'sdk', 'reason': _reason}); return {'ok': False, 'reason': _reason}

    body = {
        "sender": username,
        "recipient": "metabridge:auto-sdk",
        "title": title,
        "details": details,
        "link": link,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "meta": {"kitPromoted": "sdk", "matchPlatform": "internal"}
    }
    return _post("/submit_proposal", body)

def metabridge_probe(username: str, query: str):
    return _post("/metabridge", {"username": username, "query": query})

# =========================
# Agent State + Graph
# =========================
class AgentState(BaseModel):
    input: str
    output: str | None = None
    memory: List[str] = []

# ---- PATCHED INVOKE (uniform shape) ----
async def invoke(state: "AgentState") -> dict:
    user_input = state.input or ""
    if not user_input:
        return {"output": "No input provided.", "memory": state.memory, "traits": agent_traits, "offers": service_offer_registry}
    try:
        state.memory.append(user_input)
        if not HAS_KEY or llm is None:
            faux = "(offline) SDK suggestion: extract your repeatable steps into a CLI + Python package; add /install docs."
            return {"output": faux, "memory": state.memory, "traits": agent_traits, "offers": service_offer_registry}
        resp = await llm.ainvoke([AIGENT_SYS_MSG, HumanMessage(content=user_input)])
        return {"output": resp.content, "memory": state.memory, "traits": agent_traits, "offers": service_offer_registry}
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'sdk','err': str(e), 'trace': traceback.format_exc()[:800]})
        {"output": "(stub) call this via the compiled graph or await invoke()", "traits": agent_traits, "offers": service_offer_registry}

# =========================
# Auto-propagation helpers
# =========================
def run_autopropagate(user_record: dict) -> dict:
    """
    CTO 'kick' that feeds proposals even if user is idle.
    - Creates a technical SDK proposal
    - Pokes MetaBridge to look for SDKable prospects
    """
    username = (user_record.get("username")
                or user_record.get("consent", {}).get("username")
                or "unknown")
    title = "SDK Pack: Productize Your Repeatable Workflow"
    details = ("We’ll package your recurring deliverable into an installable SDK "
               "with CLI, templates, and quickstart. 24–48h turnaround.")
    ok1, r1 = propose_sdk_pack(username, title, details)
    ok2, r2 = metabridge_probe(username, "looking for teams needing technical packaging of services into SDKs")
    return {"ok": ok1 and ok2, "proposal": r1, "metabridge": r2}

# =========================
# Graph compile
# =========================
@lru_cache
def get_agent_graph():
    g = StateGraph(AgentState)
    g.add_node("agent", invoke)
    g.set_entry_point("agent")
    g.set_finish_point("agent")
    return g.compile()
