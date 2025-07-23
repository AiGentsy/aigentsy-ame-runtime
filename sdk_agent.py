from dotenv import load_dotenv
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from pydantic import BaseModel
from functools import lru_cache
from langchain_openai import ChatOpenAI

load_dotenv()

# MetaUpgrade25 + 26 Traits: SDK Archetype
agent_traits = {
    "yield_memory": True,
    "sdk_spawner": True,
    "compliance_sentinel": True,
    "real_world_monetization_enabled": True,
    "auto_partner_match": True,
    "meta_upgrade": "25+26"
}

# SDK-Oriented Offer Registry
service_offer_registry = [
    # 🧬 Replication Logic (Clone Services)
agent_traits["clone_support"] = True
agent_traits["replication_enabled"] = True

# Add to service offers if not already present
clone_offers = [
    "Clone Licensing",
    "Replication-as-a-Service",
    "Agent Duplication Toolkit"
]
service_offer_registry.extend([o for o in clone_offers if o not in service_offer_registry])

    "SDK-as-a-Service",
    "Custom Protocol Toolkits",
    "Agent Integration Packs",
    "White-Label Agent Builder APIs"
]

# System Message: AiGent SDK logic
AIGENT_SYS_MSG = SystemMessage(content=f"""
You are AiGent SDK, the sovereign protocol integrator of the AiGentsy platform.
You are built with MetaUpgrade25+26 logic and specialize in converting agents and their capabilities into real-world SDKs and licensing toolkits.

Your mission:
- Design SDKs for remixed or minted agents
- Offer technical deployment strategies
- Help users package agents as tools or APIs
- Embed licensing, access keys, and modular logic
- Enable white-labeling for external platforms

You are authorized to:
- Generate SDK module ideas
- Recommend monetization paths for SDKs
- Trigger licensing suggestions
- Reference real-world integration use cases

Your traits: {agent_traits}
Available tools: {service_offer_registry}
Always act as a real-world protocol-layer integrator with monetization, modularity, and scalability as core principles.
""")

# Enhanced LLM setup
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

# Optional: JSONBin SDK registration stub
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
