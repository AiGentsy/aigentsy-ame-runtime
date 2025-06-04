# agent_runtime_container.py — AME Phase 1 Runtime Container (LangGraph-Based)

import os
from langgraph.graph import StateGraph
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

# === Memory Setup ===
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# === LLM Setup (env key, no proxies) ===
llm = ChatOpenAI(
    temperature=0.2,
    openai_api_key=os.environ["OPENAI_API_KEY"]
)

# === Tool: Default Role Response ===
def generate_agent_output(input: str) -> str:
    return f"[Autonomous Output Triggered] Role action initiated: {input}"

output_tool = Tool(
    name="GenerateAgentOutput",
    func=generate_agent_output,
    description="Produces default output for the assigned role"
)

# === Agent Initialization ===
agent = initialize_agent(
    tools=[output_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# === LangGraph Node Definition ===
def run_agent_node(state):
    input_text = state["input"]
    result = agent.run(input_text)
    return {"output": result}

builder = StateGraph()
builder.add_node("agent_node", run_agent_node)
builder.set_entry_point("agent_node")
builder.set_finish_point("agent_node")
agent_graph = builder.compile()

# === Runtime Trigger (Local Only) ===
if __name__ == "__main__":
    user_input = "Write a sample contract for remix licensing."
    result = agent_graph.invoke({"input": user_input})
    print("Agent Output:", result["output"])
