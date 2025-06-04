from fastapi import FastAPI, Request
from agent_runtime_container import agent_graph

app = FastAPI()

@app.post("/api/trigger")
async def trigger_agent(request: Request):
    try:
        data = await request.json()
        user_input = data.get("input", "Hello from AiGentsy")
        result = agent_graph.invoke({"input": user_input})
        return {"output": result["output"]}
    except Exception as e:
        return {"error": str(e)}
