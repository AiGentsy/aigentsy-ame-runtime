import os
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 0. Load environment variables (safer for Render/Fly/Railway)
load_dotenv()

# 1. Define the LLM using modern, proxy-safe stack
llm = ChatOpenAI(
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY")  # ✅ required and now isolated
)

# 2. Define a runnable node that takes input and returns output
async def invoke(state: dict) -> dict:
    user_input = state.get("input", "")
    if not user_input:
        return {"output": "No input provided."}
    try:
        response = await llm.ainvoke([HumanMessage(content=user_input)])
        return {"output": response.content}
    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

# 3. Build a LangGraph with the single async node
graph = StateGraph()
graph.add_node("agent", invoke)
graph.set_entry_point("agent")
graph.set_finish_point(END)

# 4. Compile into executable runtime agent graph
agent_graph = graph.compile()
