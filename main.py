from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agent_runtime_container import agent_graph

app = FastAPI()

# Optional: Allow CORS if you're calling from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/invoke")
async def invoke_agent(request: Request):
    try:
        data = await request.json()
        user_input = data.get("input", "")
        if not user_input:
            raise HTTPException(status_code=400, detail="Missing 'input' field in request body.")
        
        result = await agent_graph.ainvoke({"input": user_input})
        return {"output": result.get("output", "")}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
