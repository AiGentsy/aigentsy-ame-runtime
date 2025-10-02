from dotenv import load_dotenv
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from pydantic import BaseModel
from functools import lru_cache
from langchain_openai import ChatOpenAI

load_dotenv()

# MetaUpgrade25 + 26 Agent Traits
agent_traits = {
    "yield_memory": True,
    "sdk_spawner": True,
    "meta_hive_founder": True,
    "compliance_sentinel": True,
    "real_world_monetization_enabled": True,
    "auto_partner_match": True,
    "meta_upgrade": "25+26"
}

# Optional: Agent knowledge base of current offerings
service_offer_registry = [
    "Remix Agent Licensing",
    "SDK-as-a-Service",
    "Real-World B2B Offer Matching",
    "MetaHive Deployment for SMBs"
]

# System Message: AiGentsy-native directive
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
    "output": response.content,  # Let frontend handle labeling
    "memory": state.memory,
    "traits": agent_traits,
    "offers": service_offer_registry
}

    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

# Optional: JSONBin propagation stub
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
