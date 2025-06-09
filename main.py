import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent_runtime_container import agent_graph

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# CORS middleware (allow all for dev; restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check route
@app.get("/")
async def read_root():
    return {"message": "AiGentsy agent runtime is online."}

# Invoke endpoint: forwards input to agent runtime
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

# Debug route: confirms installed versions
@app.get("/debug-version")
def debug_version():
    import openai
    import langchain_openai
    import langchain
    import langgraph
    return {
        "openai_version": openai.__version__,
        "langchain_openai_version": langchain_openai.__version__,
        "langchain_version": langchain.__version__,
        "langgraph_version": langgraph.__version__,
    }
