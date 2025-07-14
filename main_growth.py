from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aigent_growth_metamatch import run_metamatch_campaign
from aigent_growth_agent import get_agent_graph

# Initialize agent graph from MetaUpgrade25 archetype
agent_graph = get_agent_graph()

# FastAPI app setup
app = FastAPI()

# === ✅ CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["https://aigentsy.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/agent")
async def run_agent(request: Request):
    try:
        data = await request.json()
        user_input = data.get("input", "")
        if not user_input:
            return {"error": "No input provided."}

        # Prepare input state for Venture Builder agent (MetaUpgrade25 logic)
        initial_state = {
            "input": user_input,
            "memory": []
        }

        # Invoke the agent graph
        result = await agent_graph.ainvoke(initial_state)

        return {"output": result.get("output", "No output returned.")}

    except Exception as e:
        return {"error": f"Agent runtime error: {str(e)}"}



@app.post("/launch-metamatch")
async def launch_metamatch(request: Request):
    try:
        data = await request.json()
        user_data = data.get("user_data")

        if not user_data or not user_data.get("username"):
            return {"error": "Missing or invalid user_data."}

        run_metamatch_campaign(user_data)
        return {"status": "✅ MetaMatch campaign launched."}

    except Exception as e:
        return {"error": f"MetaMatch error: {str(e)}"}
