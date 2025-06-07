from fastapi import FastAPI, Request
from agent_runtime_container import agent_graph

app = FastAPI()

@app.post("/invoke")
async def invoke_agent(request: Request):
    data = await request.json()
    user_input = data.get("input", "")
    result = await agent_graph.ainvoke({"input": user_input})
    return {"output": result["output"]}
