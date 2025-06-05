from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from agent_runtime_container import agent_graph

import pkg_resources
print(">> Installed Versions:")
for pkg in ["openai", "langchain-openai", "langchain"]:
    try:
        print(f">> {pkg}=={pkg_resources.get_distribution(pkg).version}")
    except Exception as e:
        print(f">> {pkg} not found: {e}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/trigger")
async def trigger_agent(request: Request) -> dict:
    try:
        data = await request.json()
        user_input = data.get("input", "Hello from AiGentsy")
        result = agent_graph.invoke({"input": user_input})
        return {"output": result["output"]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
