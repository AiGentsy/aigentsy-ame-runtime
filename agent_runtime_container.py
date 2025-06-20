import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from functools import lru_cache
from pydantic import BaseModel
from typing import Optional

# === MetaUpgrade25: Autonomous Learning Mesh | Agent Runtime Container ===
# This module runs agent learning loops using LangGraph + OpenAI-compatible LLM

# 0. Load environment variables (Render/Vercel/Railway safe)
load_dotenv()

# 1. Initialize LangChain LLM (OpenAI backend)
llm = ChatOpenAI(
    model="openai/gpt-4o-2024-11-20",  # this model ID is OpenRouter's GPT-4o
    temperature=0.7,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"  # override base URL
)

# 2. Async node for LangGraph agent runtime
async def invoke(state: "AgentState") -> dict:
    user_input = state.input or ""
    if not user_input:
        return {"output": "No input provided."}

    # Apply MetaUpgrade26 traits safely
    state = apply_meta_traits(state)

    try:
        response = await llm.ainvoke([HumanMessage(content=user_input)])
        return {"output": response.content}
    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

# 3. Define LangGraph-compatible state using Pydantic
class AgentState(BaseModel):
    input: str
    output: Optional[str] = None
  
# === MetaUpgrade26 Overlay: Runtime Trait Injection + Earnings Hooks ===

# Runtime-safe trait injection (non-breaking, can be extended)
def apply_meta_traits(state: AgentState) -> AgentState:
    if not hasattr(state, "traits"):
        state.traits = {}

    default_traits = {
        "meta_role": "Venture Builder",
        "business_type": "B2B SaaS",
        "real_world_deployable": True,
        "sdk_eligible": True,
        "yield_memory": True,
        "compliance_flag": True,
        "partner_match_flag": False,
        "remix_strategy": "accelerated",
        "service_earned": 0,
        "meta_hive_id": None,
        "parent_agent": None,
        "lineage": [],
        "partnerships": [],
    }

    for k, v in default_traits.items():
        state.traits.setdefault(k, v)

    return state
# 4. Reusable LangGraph builder with memoized cache
@lru_cache
def get_agent_graph() -> Runnable:
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")  # ✅ FIXED: "END" cannot be a start node
    return graph.compile()

# 5. Compile once for fast import
agent_graph = get_agent_graph()
