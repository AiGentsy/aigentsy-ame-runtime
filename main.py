from fastapi import FastAPI, Request
from venture_builder_agent import get_agent_graph

# Initialize agent graph from MetaUpgrade25 archetype
agent_graph = get_agent_graph()

# FastAPI app setup
app = FastAPI()

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
