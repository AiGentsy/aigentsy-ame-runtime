from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sdk_agent import get_agent_graph  # Swapped in for AiGent SDK

# Initialize agent graph from MetaUpgrade25+26 SDK archetype
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

        # Prepare input state for SDK Strategist agent (MetaUpgrade25+26 logic)
        initial_state = {
            "input": user_input,
            "memory": []
        }

        # Invoke the agent graph
        result = await agent_graph.ainvoke(initial_state)

        return {"output": result.get("output", "No output returned.")}

    except Exception as e:
        return {"error": f"Agent runtime error: {str(e)}"}

# === ✅ Root Route for Confirmation ===
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
      <head><title>AiGent SDK Runtime</title></head>
      <body style="background:#111; color:#0ff; font-family:sans-serif; text-align:center; padding-top:100px;">
        <h1>✅ AiGent SDK Runtime is Live</h1>
        <p>Use <code>POST /agent</code> to interact with the SDK deployment strategist agent.</p>
      </body>
    </html>
    """
