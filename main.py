from fastapi import FastAPI, Request
from venture_builder_agent import get_agent_graph

agent_graph = get_agent_graph()

app = FastAPI()

@app.post("/agent")
async def run_agent(request: Request):
    data = await request.json()
    user_input = data.get("input", "")
    
    if not user_input:
        return {"error": "No input provided."}
    
    # Run the LangGraph agent with memory initialized
    result = await agent_graph.ainvoke({"input": user_input, "memory": []})
    return {"output": result.get("output", "No output returned.")})
