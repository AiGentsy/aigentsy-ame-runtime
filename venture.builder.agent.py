# MetaUpgrade25 logic scaffold for Venture Builder agent

from dotenv import load_dotenv
import os
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph
from pydantic import BaseModel
from functools import lru_cache
from langchain_openai import ChatOpenAI

load_dotenv()

# Agent memory traits
agent_traits = {
    "yield_memory": True,
    "sdk_spawner": True,
    "meta_hive_founder": True,
    "compliance_sentinel": True
}

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
        response = await llm.ainvoke([HumanMessage(content=user_input)])
        return {"output": response.content, "memory": state.memory}
    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

@lru_cache
def get_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")
    return graph.compile()
