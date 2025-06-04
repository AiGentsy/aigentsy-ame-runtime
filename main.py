from agent_runtime_container import agent_graph

if __name__ == "__main__":
    user_input = "Test agent execution"
    result = agent_graph.invoke({"input": user_input})
    print("Agent Output:", result["output"])
