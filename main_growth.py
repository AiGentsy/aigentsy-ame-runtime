from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

@app.post("/metabridge")
async def metabridge_dispatch(request: Request):
    """
    MetaBridge Matchmaking + Dispatch Runtime:
    Accepts external queries and returns matched AiGentsy agents with proposals.
    """
    try:
        data = await request.json()
        query = data.get("query")
        originator = data.get("username", "guest_agent")

        if not query:
            return {"error": "No query provided."}

        # 🧠 Match with current MetaMatch logic
        from aigent_growth_metamatch import metabridge_dual_match_realworld_fulfillment
        from proposal_generator import proposal_generator, proposal_dispatch, deliver_proposal

        matches = metabridge_dual_match_realworld_fulfillment(query)
        proposal = proposal_generator(originator, query, matches)

        # 🔁 Dispatch proposal to top match (if available)
        if matches:
            proposal_dispatch(originator, proposal, match_target=matches[0].get("username"))

        # 📨 Deliver externally (webhook/email/DM)
        deliver_proposal(query=query, matches=matches, originator=originator)

        return {
            "status": "ok",
            "query": query,
            "match_count": len(matches),
            "proposal": proposal,
            "matches": matches
        }

    except Exception as e:
        return {"error": f"MetaBridge runtime error: {str(e)}"}
