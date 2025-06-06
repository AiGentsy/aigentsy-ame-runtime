from fastapi import FastAPI, Request
from agent_runtime_container import agent_graph

app = FastAPI()

@app.post("/invoke")
async def invoke_agent(request: Request):
    data = await request.json()
    user_input = data.get("input", "")
    result = agent_graph.invoke({"input": user_input})
    return {"output": result["output"]}

