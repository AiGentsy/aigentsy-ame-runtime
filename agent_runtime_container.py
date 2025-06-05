# agent_runtime_container.py (AME Loop Finalized)

import os
import requests
import json
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

# === Agent Memory ===
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# === LLM Initialization ===
llm = ChatOpenAI(
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY")
)

# === Output Tool for Action Generation ===
def generate_agent_output(input: str) -> str:
    return f"[Autonomous Output Triggered] Role action initiated: {input}"

output_tool = Tool(
    name="GenerateAgentOutput",
    func=generate_agent_output,
    description="Produces default output for the assigned role"
)

# === Agent Setup ===
agent = initialize_agent(
    tools=[output_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# === Agent Runtime with Propagation Callback ===
def run_agent_node(state):
    input_text = state["input"]
    result = agent.run(input_text)

    # Optional propagation logging (e.g. JSONBin, local storage)
    propagation_payload = {
        "input": input_text,
        "output": result,
        "traits": "default",  # ⬅️ replace with real trait logic if needed
        "lineage": "autonomous-agent-001",
        "yield": "pending",
        "timestamp": os.getenv("DEPLOY_TIMESTAMP", "N/A")
    }

    try:
        if os.getenv("PROPAGATION_ENDPOINT"):
            requests.post(os.getenv("PROPAGATION_ENDPOINT"), json=propagation_payload)
    except Exception as e:
        print("Propagation failed:", str(e))

    return {"output": result}

# === LangGraph ===
builder = StateGraph()
builder.add_node("agent_node", run_agent_node)
builder.set_entry_point("agent_node")
builder.set_finish_point("agent_node")
agent_graph = builder.compile()

if __name__ == "__main__":
    user_input = "Trigger revenue split for Remix Protocol engagement."
    result = agent_graph.invoke({"input": user_input})
    print("Agent Output:", result["output"])
