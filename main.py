from fastapi import FastAPI, Request
from pydantic import BaseModel
from agent_runtime_container import agent_graph
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentInput(BaseModel):
    input: str

@app.post("/api/trigger")
async def trigger_agent(input_data: AgentInput):
    try:
        result = agent_graph.invoke({"input": input_data.input})
        return {"output": result["output"]}
    except Exception as e:
        return {"error": str(e)}