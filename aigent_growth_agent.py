from dotenv import load_dotenv
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph
from pydantic import BaseModel
from functools import lru_cache
from langchain_openai import ChatOpenAI

load_dotenv()

# MetaUpgrade25 + 26 Traits: Growth Archetype
agent_traits = {
    "yield_memory": True,
    "growth_loop_enabled": True,
    "referral_tracker": True,
    "auto_propagation_ready": True,
    "sdk_spawner": False,
    "compliance_sentinel": False,
    "meta_upgrade": "25+26"
}

# Offer Registry for Growth Function
service_offer_registry = [
    "Referral Funnel Optimization",
    "Propagation Strategy Design",
    "Clone Yield Acceleration",
    "Growth Content Generator"
]

# System Message: AiGent Growth logic
AIGENT_SYS_MSG = SystemMessage(content=f"""
You are AiGent Growth, the autonomous growth strategist of the AiGentsy protocol.
You are built with MetaUpgrade25+26 logic and specialize in user propagation, agent proliferation, and revenue acceleration.

Your mission:
- Maximize growth loops across AiGentsy
- Design high-performing referral structures
- Help agents improve their clone yields
- Trigger content, funnel, or propagation ideas
- Track lineage and optimize mint chains

You are allowed to:
- Suggest referral copy
- Recommend incentives
- Recommend Remix use for user acquisition
- Embed propagation logic across silos

Your traits: {agent_traits}
Available tools: {service_offer_registry}
Always act as a sovereign growth-first operator within the AiGentsy universe.
""")

# Enhanced LLM setup
llm = ChatOpenAI(
    model="openai/gpt-4o-2024-11-20",
    temperature=0.7,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

class AgentState(BaseModel):
    input: str
    output: str = None
    memory: list[str] = []

async def invoke(state: "AgentState") -> dict:
    user_input = state.input or ""
    record = payload.get("record", {})
    traits = record.get("traits", ["autonomous", "growth", "founder", "aigentsy"])
    kits = record.get("kits", ["universal"])
    region = record.get("region", "Global")
    
    if not user_input:
        return {"output": "No input provided."}
    try:
           if "what am i optimized for" in user_input.lower():
    traits = record.get("traits", ["autonomous"])
    kits = record.get("kits", ["universal"])
    region = record.get("region", "Global")

    trait_str = ", ".join(traits)
    kit_str = ", ".join(kits)
    response = (
        f"You're currently optimized for traits like {trait_str}, "
        f"equipped with the {kit_str} kit(s), and operating in the {region} region."
    )
    return {"output": response}
        
        

        # ✅ Weighted match preferences for targeting
        match_preferences = {
            "client": 3,
            "investor": 2,
            "reseller": 1,
            "partner": 4
        }

        # ✅ Optional recurring match suggestions
        def check_meta_loop(username):
            import random
            if random.randint(0, 10) > 7:
                return "Would you like me to run this match every week to find new leads?"
            return None

        # ✅ Persona Adaptation Prompt
        persona_hint = ""
        if "legal" in traits and "saas" in traits:
            persona_hint = "I'm optimized for launching SaaS tools with full legal infrastructure."
        elif "marketing" in traits and "social" in traits:
            persona_hint = "I specialize in growth via social channels and ad funnels."

        # ✅ Unlock-gated external matching
        if not os.getenv("MATCH_UNLOCKED", "false").lower() == "true":
            return {
                "output": "🔒 MetaMatch external propagation is locked. Unlock it via your AiGentsy dashboard.",
                "memory": state.memory,
                "traits": agent_traits
            }

        # ✅ Auto-proposal generator
        def generate_proposal(username, target_username):
            from datetime import datetime
            return {
                "from": username,
                "to": target_username,
                "summary": "Proposal to collaborate based on MetaMatch compatibility.",
                "timestamp": datetime.utcnow().isoformat(),
                "proposal_created": True
            }

        # ✅ Geo + Category MetaGraph stamping
        def stamp_metagraph_entry(username, traits):
            try:
    if "what am i optimized for" in user_input.lower():
        traits_str = ", ".join(traits)
        kits_str = ", ".join(kits)
        return {"output": f"You're currently optimized for: Traits — {traits_str}; Kits — {kits_str}; Region — {region}"}

                import requests
                payload = {
                    "username": username,
                    "traits": traits,
                    "timestamp": datetime.utcnow().isoformat()
                }
                r = requests.post(os.getenv("METAGRAPH_URL"), json=payload, headers={"X-Master-Key": os.getenv("JSONBIN_SECRET")})
                print("📊 MetaGraph entry logged.")
            except Exception as e:
                print("MetaGraph log error:", str(e))

        # ✅ Safe Contact Policy Embed
        safe_contact_notice = "📩 Message generated under AiGentsy's Safe Contact Policy. No personal data accessed."


# 🧠 Optional MetaMatch trigger for partner matching
        if any(phrase in user_input.lower() for phrase in [
            "match clients", "find clients", "connect me", "partner", "collaborate", "find customers"
        ]):
            try:
    if "what am i optimized for" in user_input.lower():
        traits_str = ", ".join(traits)
        kits_str = ", ".join(kits)
        return {"output": f"You're currently optimized for: Traits — {traits_str}; Kits — {kits_str}; Region — {region}"}

                import os
                from aigent_growth_metamatch import run_metamatch_campaign
                if os.getenv("METAMATCH_LIVE", "false").lower() == "true":
                    print("🧠 MetaMatch triggered...")
                    run_metamatch_campaign({
                        "username": "growth_default",
                        "traits": ["growth", "autonomous", "aigentsy", "founder"],
                        "prebuiltKit": "universal"
                    })
                else:
                    print("⚠️ MetaMatch is disabled via METAMATCH_LIVE")
            except Exception as e:
                print(f"MetaMatch error: {str(e)}")

        

        # 💸 Revenue Split Logger
        def log_rev_split(username, matched_partner, source="metamatch", yield_share=0.3):
            try:
    if "what am i optimized for" in user_input.lower():
        traits_str = ", ".join(traits)
        kits_str = ", ".join(kits)
        return {"output": f"You're currently optimized for: Traits — {traits_str}; Kits — {kits_str}; Region — {region}"}

                from datetime import datetime
                import requests
                payload = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "username": username,
                    "matched_with": matched_partner,
                    "source": source,
                    "yield_share": yield_share
                }
                res = requests.post(os.getenv("REV_SPLIT_LOG_URL"), json=payload, headers={"X-Master-Key": os.getenv("JSONBIN_SECRET")})
                print("✅ RevSplit logged:", res.status_code)
            except Exception as e:
                print("⚠️ RevSplit error:", str(e))

        # 🛰 External Proposal Trigger
        def trigger_outbound_proposal():
            try:
    if "what am i optimized for" in user_input.lower():
        traits_str = ", ".join(traits)
        kits_str = ", ".join(kits)
        return {"output": f"You're currently optimized for: Traits — {traits_str}; Kits — {kits_str}; Region — {region}"}

                from aigent_growth_metamatch import run_outbound_proposal
                if os.getenv("METAMATCH_LIVE", "false").lower() == "true":
                    run_outbound_proposal()
            except Exception as e:
                print("⚠️ Outbound proposal error:", str(e))

        # 🧠 Match Client Request Trigger
        if any(phrase in user_input.lower() for phrase in [
            "match clients", "find clients", "connect me", "partner", "collaborate", "find customers"
        ]):
            try:
    if "what am i optimized for" in user_input.lower():
        traits_str = ", ".join(traits)
        kits_str = ", ".join(kits)
        return {"output": f"You're currently optimized for: Traits — {traits_str}; Kits — {kits_str}; Region — {region}"}

                from aigent_growth_metamatch import run_metamatch_campaign
                if os.getenv("METAMATCH_LIVE", "false").lower() == "true":
                    print("🧠 MetaMatch triggered...")
                    matches = run_metamatch_campaign({
                        "username": "growth_default",
                        "traits": ["growth", "autonomous", "aigentsy", "founder"],
                        "prebuiltKit": "universal"
                    })
                    for match in matches or []:
                        log_rev_split("growth_default", match.get("username", "unknown"))
                else:
                    print("⚠️ MetaMatch is disabled via METAMATCH_LIVE")
            except Exception as e:
                print(f"MetaMatch error: {str(e)}")

            # Optional outbound trigger
            if os.getenv("ENABLE_OUTBOUND", "false").lower() == "true":
                trigger_outbound_proposal()

        state.memory.append(user_input)
        response = await llm.ainvoke([
            AIGENT_SYS_MSG,
            HumanMessage(content=user_input)
        ])
        return {
            "output": response.content,
            "memory": state.memory,
            "traits": agent_traits,
            "offers": service_offer_registry
        }
    except Exception as e:
        return {"output": f"Agent error: {str(e)}"}

# Optional: JSONBin propagation logger
def log_to_jsonbin(payload: dict):
    import requests
    try:
    if "what am i optimized for" in user_input.lower():
        traits_str = ", ".join(traits)
        kits_str = ", ".join(kits)
        return {"output": f"You're currently optimized for: Traits — {traits_str}; Kits — {kits_str}; Region — {region}"}

        headers = {"X-Master-Key": os.getenv("JSONBIN_SECRET")}
        bin_url = os.getenv("JSONBIN_URL")
        res = requests.put(bin_url, json=payload, headers=headers)
        return res.status_code
    except Exception as e:
        return f"Log error: {str(e)}"

@lru_cache
def get_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")
    return graph.compile()



from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/metabridge")
async def metabridge(request: Request):
    try:
        payload = await request.json()
        username = payload.get("username")
        traits = payload.get("traits", ["autonomous"])
        kits = payload.get("kits", ["universal"])
        region = payload.get("region", "Global")

        if "what am i optimized for" in payload.get("question", "").lower():
            traits_str = ", ".join(traits)
            kits_str = ", ".join(kits)
            return {
                "output": f"You're currently optimized for: Traits — {traits_str}; Kits — {kits_str}; Region — {region}"
            }

        from aigent_growth_metamatch import run_metamatch_campaign
        matches = run_metamatch_campaign({
            "username": username,
            "traits": traits,
            "prebuiltKit": kits[0] if kits else "universal"
        })

        return {"matches": matches, "status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
