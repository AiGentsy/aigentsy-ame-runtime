# agent_runtime_container.py — AME Phase 1 Runtime Container (LangGraph-Based)

from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
# ToolNode removed — no longer supported in current langgraph
# from langgraph.prebuilt import ToolNode

# === Agent Memory and Context ===
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

# === Memory Setup ===
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# === LLM Model (can be replaced with OpenAI function-calling or Claude) ===
llm = ChatOpenAI(temperature=0.2)

# === Basic Tool: Codegen or Offer Output (expandable) ===
def generate_agent_output(input: str) -> str:
    return f"[Autonomous Output Triggered] Role action initiated: {input}"

output_tool = Tool(
    name="GenerateAgentOutput",
    func=generate_agent_output,
    description="Produces default output for the assigned role"
)

# === Agent Init ===
agent = initialize_agent(
    tools=[output_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# === LangGraph Definition ===
def run_agent_node(state):
    input_text = state["input"]
    result = agent.run(input_text)
    return {"output": result}

builder = StateGraph()
builder.add_node("agent_node", run_agent_node)
builder.set_entry_point("agent_node")
builder.set_finish_point("agent_node")
agent_graph = builder.compile()

# === Runtime Execution ===
if __name__ == "__main__":
    # Example agent input
    user_input = "Write a sample contract for remix licensing."
    result = agent_graph.invoke({"input": user_input})
    print("Agent Output:", result["output"])
