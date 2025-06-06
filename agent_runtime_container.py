
import os
from langgraph.graph import StateGraph
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.schema import HumanMessage, SystemMessage

# === Memory ===
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# === Tool Definition ===
def generate_agent_output(input: str) -> str:
    return f"[Autonomous Output Triggered] Role action initiated: {input}"

output_tool = Tool(
    name="GenerateAgentOutput",
    func=generate_agent_output,
    description="Produces default output for the assigned role"
)

# === LLM Initialization ===
llm = ChatOpenAI(
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# === Agent Initialization ===
agent = initialize_agent(
    tools=[output_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# === LangGraph Assembly ===
def run_agent_node(state):
    input_text = state["input"]
    result = agent.run(input_text)
    return {"output": result}

builder = StateGraph()
builder.add_node("agent_node", run_agent_node)
builder.set_entry_point("agent_node")
builder.set_finish_point("agent_node")
agent_graph = builder.compile()
