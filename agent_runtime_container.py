import os
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool

# === Memory setup ===
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# === LLM setup ===
llm = ChatOpenAI(
    temperature=0.2,
    api_key=os.environ["OPENAI_API_KEY"]
)

# === Tool definition ===
def generate_agent_output(input: str) -> str:
    return f"[Autonomous Output Triggered] Role action initiated: {input}"

output_tool = Tool(
    name="GenerateAgentOutput",
    func=generate_agent_output,
    description="Produces default output for the assigned role"
)

# === Agent definition ===
agent = initialize_agent(
    tools=[output_tool],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

# === LangGraph Node ===
def run_agent_node(state):
    input_text = state["input"]
    result = agent.run(input_text)
    return {"output": result}

# === LangGraph Assembly ===
builder = StateGraph()
builder.add_node("agent_node", run_agent_node)
builder.set_entry_point("agent_node")
builder.set_finish_point("agent_node")
agent_graph = builder.compile()

# === Local test run (optional) ===
if __name__ == "__main__":
    user_input = "Write a sample contract for remix licensing."
    result = agent_graph.invoke({"input": user_input})
    print("Agent Output:", result["output"])
