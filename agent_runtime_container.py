from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.schema import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

import os

# Basic tool example (you can expand this with your real tools)
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

def run_agent(input_text: str) -> str:
    return agent.run(input_text)

def invoke(input):
    return {"output": run_agent(input["input"])}

# LangGraph wrapper
graph = StateGraph()
graph.add_node("agent", ToolNode(invoke))
graph.set_entry_point("agent")
graph.set_finish_point(END)
agent_graph = graph.compile()
