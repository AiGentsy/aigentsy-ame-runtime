from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.schema import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

import os
import asyncio

# Define a simple echo tool
def simple_tool(input_text: str) -> str:
    return f"Echo: {input_text}"

tools = [Tool(name="EchoTool", func=simple_tool, description="Echo back the input")]

llm = ChatOpenAI(
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# Async wrapper for agent.run
async def run_agent_async(input_text: str) -> str:
    return await asyncio.to_thread(agent.run, input_text)

# Async-compatible node
async def invoke(input):
    result = await run_agent_async(input["input"])
    return {"output": result}

# LangGraph setup
graph = StateGraph()
graph.add_node("agent", ToolNode(invoke))
graph.set_entry_point("agent")
graph.set_finish_point(END)
agent_graph = graph.compile()
