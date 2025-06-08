import os
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langgraph.graph import END, StateGraph
from langchain_openai import ChatOpenAI

# 1. Define the LLM
llm = ChatOpenAI(
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY")  # ✅ correct
)

# 2. Define a runnable node
async def invoke(state: dict) -> dict:
    user_input = state.get("input", "")
    response = await llm.ainvoke([HumanMessage(content=user_input)])
    return {"output": response.content}

# 3. Build LangGraph with the async invoke node
graph = StateGraph()
graph.add_node("agent", invoke)
graph.set_entry_point("agent")
graph.set_finish_point(END)

# 4. Compile the graph
agent_graph = graph.compile()
