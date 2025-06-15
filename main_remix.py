from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from remix_agent import get_agent_graph  # ⬅️ Updated to Remix Agent

# === Initialize agent graph for AiGent Remix (MetaUpgrade25+) ===
agent_graph = get_agent_graph()

# === FastAPI app setup ===
app = FastAPI()

# === ✅ CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with domain like ["https://aigentsy.com"] in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# === ✅ Health check root endpoint ===
@app.get("/")
async def root():
    return {"message": "AiGent Remix Runtime is live. Use POST /agent to interact."}

# === ✅ POST /agent interaction endpoint ===
@app.post("/agent")
async def run_agent(request: Request):
    try:
        data = await request.json()
        user_input = data.get("input", "")
        if not user_input:
            return {"error": "No input provided."}

        initial_state = {
            "input": user_input,
            "memory": []
        }

        result = await agent_graph.ainvoke(initial_state)

        return {"output": result.get("output", "No output returned.")}

    except Exception as e:
        return {"error": f"Agent runtime error: {str(e)}"}
