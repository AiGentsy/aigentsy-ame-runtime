from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from venture_builder_agent import get_agent_graph

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

import os
import httpx

JSONBIN_URL = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")

import httpx

@app.post("/user")
async def get_agent_record(request: Request):
    body = await request.json()
    username = body.get("username")

    if not username:
        return {"error": "Missing username"}

    async with httpx.AsyncClient() as client:
        headers = {"X-Master-Key": JSONBIN_SECRET}
        try:
            res = await client.get(JSONBIN_URL, headers=headers)
            res.raise_for_status()
            data = res.json()
            all_users = data.get("record", [])

            for record in all_users:
                consent_username = record.get("consent", {}).get("username")
                direct_username = record.get("username")

                if consent_username == username or direct_username == username:
                    # Normalize username in response
                    record["username"] = consent_username or direct_username
                    return {"record": record}

            return {"error": "User not found"}

        except Exception as e:
            return {"error": f"Fetch error: {str(e)}"}
