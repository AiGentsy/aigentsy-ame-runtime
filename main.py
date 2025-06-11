from fastapi import FastAPI, Request
from agent_runtime_container import agent_graph

app = FastAPI()

@app.post("/agent")
async def run_agent(request: Request):
    data = await request.json()
    user_input = data.get("input", "")
    if not user_input:
        return {"error": "No input provided."}
    
    # Run the LangGraph agent
    result = await agent_graph.ainvoke({"input": user_input})
    return {"output": result.get("output", "No output returned.")}
