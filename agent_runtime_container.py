import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph, END
from langgraph.graph.schema import StateSchema
from langchain_openai import ChatOpenAI
from functools import lru_cache

# === MetaUpgrade25: Autonomous Learning Mesh | Agent Runtime Container ===
# This module runs agent learning loops using LangGraph + OpenAI-compatible LLM

# 0. Load environment variables (Render/Vercel/Railway safe)
load_dotenv()

# 1. Initialize LangChain LLM (OpenAI backend)
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# 2. Async node for LangGraph agent runtime
async def invoke(state: dict) -> dict:
    user_input = state.get("input", "")
    if not user_input:
        return {"output": "No input provided."}
    try:
        response = await llm.ainvoke([HumanMessage(content=user_input)])
        return {"output": response.content}
    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

# 3. Minimal state schema for LangGraph
class AgentState(StateSchema):
    input: str
    output: str

# 4. Reusable LangGraph builder with memoized cache
@lru_cache
def get_agent_graph() -> Runnable:
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point(END)
    return graph.compile()

# 5. Compile once for fast import
agent_graph = get_agent_graph()
