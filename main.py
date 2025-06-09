import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent_runtime_container import agent_graph

# Load .env variables for local/dev and cloud
load_dotenv()

# Create FastAPI app
app = FastAPI()

# Optional: Allow cross-origin for frontend/dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route
@app.get("/")
async def read_root():
    return {"message": "AiGentsy agent runtime is online."}

# POST endpoint to interact with the agent
@app.post("/invoke")
async def invoke_agent(request: Request):
    try:
        body = await request.json()
        input_text = body.get("input", "")
        state = {"input": input_text}
        result = await agent_graph.ainvoke(state)
        return {"output": result.get("output", "No response")}
    except Exception as e:
        return {"error": str(e)}

# Debug version check route
@app.get("/debug-version")
def debug_version():
    import openai
    import langchain_openai
    return {
        "openai_version": openai.__version__,
        "langchain_openai_version": langchain_openai.__version__,
    }
