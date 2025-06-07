import os
import asyncio
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# 1. Define tools
def simple_tool(input_text: str) -> str:
    return f"Echo: {input_text}"

tools = [
    Tool(
        name="EchoTool",
        func=simple_tool,
        description="Echoes the input back verbatim"
    )
]

# 2. Define the LLM (OpenAI Functions mode)
llm = ChatOpenAI(
    temperature=0.2,
    api_key=os.getenv("OPENAI_API_KEY")
)

# 3. Initialize the agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    handle_parsing_errors=True
)

# 4. Async wrapper for calling the agent
async def run_agent_async(input_text: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, agent.run, input_text)

# 5. LangGraph-compatible invocation node
async def invoke(state: dict) -> dict:
    user_input = state.get("input", "")
    response = await run_agent_async(user_input)
    return {"output": response}

# 6. Build the LangGraph runtime
graph = StateGraph()
graph.add_node("agent", ToolNode(invoke))
graph.set_entry_point("agent")
graph.set_finish_point(END)

# 7. Compile graph
agent_graph = graph.compile()
