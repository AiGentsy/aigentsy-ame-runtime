import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

# 0. Load environment variables (safe for Render/Vercel/Railway)
load_dotenv()

# 1. Initialize OpenAI-compatible LLM via LangChain
llm = ChatOpenAI(
    temperature=0.2,
    model="gpt-3.5-turbo",  # or gpt-4 if desired and available
    api_key=os.getenv("OPENAI_API_KEY")  # ✅ securely loaded
)

# 2. Define an async handler node
async def invoke(state: dict) -> dict:
    user_input = state.get("input", "")
    if not user_input:
        return {"output": "No input provided."}
    try:
        response = await llm.ainvoke([HumanMessage(content=user_input)])
        return {"output": response.content}
    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

# 3. Create LangGraph runtime with single node
graph = StateGraph()
graph.add_node("agent", invoke)
graph.set_entry_point("agent")
graph.set_finish_point(END)

# 4. Compile graph to runnable
agent_graph = graph.compile()
