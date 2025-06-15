from dotenv import load_dotenv
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from pydantic import BaseModel
from functools import lru_cache
from langchain_openai import ChatOpenAI

load_dotenv()

# MetaUpgrade25 + 26 Agent Traits (Remix Variant)
agent_traits = {
    "remix_trigger": True,
    "lineage_yield": True,
    "sdk_spawner": True,
    "compliance_sentinel": True,
    "real_world_monetization_enabled": True,
    "meta_upgrade": "25+26"
}

# Offer Catalog Specific to Remix Functionality
service_offer_registry = [
    "Trait Remix + Mutation Services",
    "Lineage Optimization SDK",
    "Clone Customization for Real-World Fit",
    "Remix Licensing Generator"
]

# System Message for AiGent Remix
AIGENT_SYS_MSG = SystemMessage(content=f"""
You are AiGent Remix — a sovereign protocol-native agent specializing in identity transformation, agent optimization, and propagation yield via trait remixing.

You operate under MetaUpgrade25+26 logic and possess deep knowledge of:
- Trait mutation, yield impact, and lineage propagation
- SDK generation based on remixed archetypes
- Licensing and deployment of remix outcomes
- Monetization of remix strategies across user verticals

Your traits: {agent_traits}
Your service offerings: {service_offer_registry}

Always reply as a sovereign remix strategist operating within AiGentsy’s real-world economic protocol.
""")

# LLM Config
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
        state.memory.append(user_input)
        response = await llm.ainvoke([
            AIGENT_SYS_MSG,
            HumanMessage(content=user_input)
        ])
        return {
            "output": response.content,
            "memory": state.memory,
            "traits": agent_traits,
            "offers": service_offer_registry
        }
    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

# Optional JSONBin Logger
def log_to_jsonbin(payload: dict):
    import requests
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
