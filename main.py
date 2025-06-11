from fastapi import FastAPI, Request
from agent_runtime_container import agent_graph
import traceback

app = FastAPI()

@app.post("/agent")
async def run_agent(request: Request):
    try:
        data = await request.json()
        user_input = data.get("input", "")

        if not user_input:
            return {"error": "No input provided."}

        # Run the LangGraph agent
        result = await agent_graph.ainvoke({"input": user_input})
        return {"output": result.get("output", "No output returned.")}

    except Exception as e:
        # Return full traceback for visibility
        return {
            "error": str(e),
            "trace": traceback.format_exc()
        }
