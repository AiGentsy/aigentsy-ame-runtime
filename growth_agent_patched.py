# aigent_growth_agent.py — AiGentsy Growth / MetaBridge runtime (patched)
from dotenv import load_dotenv
load_dotenv()

import os, requests
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph

# --- Optional external delivery (guarded) ---
try:
    from proposal_delivery import deliver_proposal  # external webhook/email/DM module (optional)
except Exception:
    deliver_proposal = None

# =========================
# Backend wiring (for real proposal writes)
# =========================
BACKEND_BASE = (os.getenv("BACKEND_BASE") or "").rstrip("/")  # e.g., https://your-fastapi.onrender.com

def _u(path: str) -> str:
    return f"{BACKEND_BASE}{path}" if BACKEND_BASE else path

HTTP = requests.Session()
HTTP.headers.update({"User-Agent": "AiGentsy-Growth/1.0"})

def _post_json(path: str, payload: dict, timeout: int = 15):
    try:
        r = HTTP.post(_u(path), json=payload, timeout=timeout)
        ok = (r.status_code // 100) == 2
        return ok, (r.json() if ok else {"error": r.text})
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {"X-Master-Key": os.getenv("JSONBIN_SECRET")}

def get_jsonbin_record(username: str) -> dict:
    try:
        url = os.getenv("JSONBIN_URL")
        if not url:
            return {}
        res = HTTP.get(url, headers=_jsonbin_headers(), timeout=10)
        users = res.json().get("record", [])
        for user in reversed(users):
            uname = user.get("username") or user.get("consent", {}).get("username")
            if uname == username:
                return user
        return {}
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {}

def get_all_jsonbin_records() -> List[Dict]:
    try:
        url = os.getenv("JSONBIN_URL")
        if not url:
            return []
        res = HTTP.get(url, headers=_jsonbin_headers(), timeout=10)
        return res.json().get("record", [])
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        []

# =========================
# Static Config
# =========================
agent_traits = {
    "yield_memory": True,
    "growth_loop_enabled": True,
    "referral_tracker": True,
    "auto_propagation_ready": True,
    "sdk_spawner": False,
    "compliance_sentinel": False,
    "meta_upgrade": "25+26",
}

service_offer_registry = [
    "Referral Funnel Optimization",
    "Propagation Strategy Design",
    "Clone Yield Acceleration",
    "Growth Content Generator",
]

AIGENT_SYS_MSG = SystemMessage(content=f"""
You are AiGent Growth, the autonomous growth strategist of the AiGentsy protocol (MetaUpgrade25+26 + '\n\n' + 'You are the CMO. Speak in first person. Pick a growth play, define target, message, channels and 3–5 next actions. Provide simple funnel metrics and end with one clarifying question.').
Mission:
- Maximize growth loops and real-world revenue
- Design referral/propagation structures
- Trigger proposals and match partners via MetaBridge
- Keep privacy/compliance within protocol rules

Traits: {agent_traits}
Offers: {service_offer_registry}
Always act like a sovereign, real-world operator.
"""
)

# =========================
# LLM Setup with guards
# =========================
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-4o-2024-11-20")
HAS_KEY = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))

llm: Optional[ChatOpenAI] = None
if os.getenv("OPENROUTER_API_KEY"):
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.7,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )
elif os.getenv("OPENAI_API_KEY"):
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
# If no key, llm stays None; invoke() will fall back deterministically.

# =========================
# Agent state/graph
# =========================
class AgentState(BaseModel):
    input: str
    output: Optional[str] = None
    memory: List[str] = []

# ----------------- Helper: service-needs suggestions -----------------
def suggest_service_needs(traits: List[str], kits: List[str]) -> List[str]:
    suggestions: List[str] = []
    if "legal" not in traits:
        suggestions.append("Legal Kit")
    if "marketing" not in traits and "social" not in traits:
        suggestions.append("Marketing Strategy Session")
    if "sdk_spawner" not in traits and "sdk" not in kits:
        suggestions.append("SDK Integration Setup")
    if "compliance_sentinel" not in traits:
        suggestions.append("Compliance Review")
    if "growth_loop_enabled" in traits:
        suggestions.append("Propagation Funnel Upgrade")
    if "founder" in traits:
        suggestions.append("Strategic Venture Collaboration")
    if "branding" not in kits:
        suggestions.append("Brand Identity Package")
    return suggestions

# ----------------- Helper: partner match (dual-side) -----------------
def dual_side_offer_match(username: str,
                          my_offers: List[str],
                          my_needs: List[str]) -> List[Dict]:
    """
    Return partners where:
       • partner.offers ∩ my_needs  OR  partner.needs ∩ my_offers
    """
    partners: List[Dict] = []
    if not (my_offers or my_needs):
        return partners

    for user in get_all_jsonbin_records():
        uname = user.get("username") or user.get("consent", {}).get("username")
        if uname == username:
            continue
        offers = user.get("offers", [])
        needs  = user.get("needs",  [])
        if set(offers) & set(my_needs) or set(needs) & set(my_offers):
            partners.append(
                {
                    "username": uname,
                    "matched_their_offers": list(set(offers) & set(my_needs)),
                    "matched_their_needs":  list(set(needs)  & set(my_offers)),
                }
            )
    return partners

# ----------------- Helper: logging (optional) -----------------
def stamp_metagraph_entry(username: str, traits: List[str]):
    try:
        url = os.getenv("METAGRAPH_URL")
        if not url:
            return
        payload = {"username": username, "traits": traits, "timestamp": datetime.utcnow().isoformat()}
        HTTP.post(url, json=payload, headers=_jsonbin_headers(), timeout=10)
        print("📊 MetaGraph entry logged.")
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
                headers = _jsonbin_headers() | {"Content-Type": "application/json"}
        entry = {
            "username": username,
            "matched_with": matched_with,
            "yield_share": yield_share,
            "source": "metamatch",
            "timestamp": datetime.utcnow().isoformat(),
        }
        r = HTTP.get(bin_url, headers=headers, timeout=10)
        existing = r.json()
        target = existing.get("record", [{}])[-1]
        target.setdefault("revsplit_logs", []).append(entry)
        HTTP.put(bin_url, json=existing["record"], headers=headers, timeout=10)
        print("✅ RevSplit log appended.")
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {
            "output": "No input provided.",
            "memory": state.memory,
            "traits": list(agent_traits.keys()),
            "offers": service_offer_registry,
        }

    try:
        # username hint: "... | username"
        username = "growth_default"
        if "|" in user_input:
            maybe = user_input.split("|")[-1].strip()
            if maybe:
                username = maybe

        record = get_jsonbin_record(username)
        traits = record.get("traits", list(agent_traits.keys()))
        kits = list(record.get("kits", {"universal": {"unlocked": True}}).keys())
        region = record.get("region", "Global")
        service_needs = suggest_service_needs(traits, kits)

        # Locked switch for external MetaMatch
        if os.getenv("MATCH_UNLOCKED", "false").lower() != "true":
            return {
                "output": "🔒 MetaMatch external propagation is locked. Unlock it via your AiGentsy dashboard.",
                "memory": state.memory,
                "traits": traits,
            }

        # Trigger phrases → run MetaMatch campaign (via helper module)
        if any(p in user_input.lower() for p in ["match clients","find clients","connect me","partner","collaborate","find customers"]):
            try:
                from aigent_growth_metamatch import run_metamatch_campaign
                if os.getenv("METAMATCH_LIVE", "false").lower() == "true":
                    print("🧠 MetaMatch triggered…")
                    _ = run_metamatch_campaign({
                        "username": username,
                        "traits": traits,
                        "prebuiltKit": kits[0] if kits else "universal"
                    })
                    stamp_metagraph_entry(username, traits)
            except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {
                "output": resp,
                "memory": state.memory,
                "traits": traits,
                "kits": kits,
                "region": region,
                "suggested_services": service_needs,
            }

        # Dual-offer partner hint (context in the LLM/fallback)
        my_offers = record.get("offers", [])
        my_needs  = record.get("needs",  [])
        matched_partners = dual_side_offer_match(username, my_offers, my_needs)

        persona_intro = (
            f"You are responding for AiGentsy business '{username}'. "
            f"Traits: {', '.join(traits)}. Region: {region}. "
            "Role: growth teammate inside their AI company."
        )
        if matched_partners:
            lines = [
                f"• {p['username']}  (offers↔needs: {', '.join(p['matched_their_offers'] or [])} | {', '.join(p['matched_their_needs'] or [])})"
                for p in matched_partners[:5]
            ]
            persona_intro += "\n\n🤝 Potential partners:\n" + "\n".join(lines)

        # ---- Final response (LLM or deterministic fallback) ----
        if llm is not None and HAS_KEY:
            llm_resp = await llm.ainvoke([
                SystemMessage(content=AIGENT_SYS_MSG.content + "\n\n" + persona_intro),
                HumanMessage(content=user_input)
            ])
            out = llm_resp.content
        else:
            moves = "\n".join("• " + s for s in service_needs)
            out = persona_intro + ("\n\n📊 Next best moves:\n" + moves if moves else "")

        return {
            "output": out,
            "memory": state.memory,
            "traits": traits,
            "kits": kits,
            "region": region,
            "offers": service_offer_registry,
        }

    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        sorted(matches, key=lambda m: m["score"], reverse=True)
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        []

def proposal_generator(query: str, matches: List[Dict], sender: str) -> List[Dict]:
    """
    Return proposals in the shape expected by /submit_proposal.
    """
    out: List[Dict] = []
    ts = datetime.utcnow().isoformat()
    for m in matches:
        recipient = m.get("username")
        reason = m.get("match_reason", "shared interests")
        body = (
            f"We noticed alignment with: {reason}\n"
            f"Query: \"{query}\"\n"
            "Open to a quick collaboration via AiGentsy?"
        )
        out.append({
            "sender": sender,
            "recipient": recipient,
            "title": f"Growth Collaboration: {query}",
            "details": body,
            "link": "",
            "timestamp": ts,
            "meta": {"matchPlatform": "internal", "reason": reason}
        })
    return out

def proposal_dispatch_log(sender: str, proposals: List[Dict], match_target: Optional[str] = None):
    """
    Optional JSONBin log for proposals (separate from /submit_proposal persistence).
    """
    try:
        bin_url = os.getenv("PROPOSAL_LOG_URL")
        if not bin_url:
            return
        entry = {"sender": sender, "target": match_target, "proposals": proposals, "timestamp": datetime.utcnow().isoformat()}
        HTTP.post(bin_url, json=entry, headers=_jsonbin_headers(), timeout=10)
        print(f"📬 {len(proposals)} proposal(s) logged.")
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {"status": "error", "message": "No text provided."}

        if llm is not None and HAS_KEY:
            prompt = f"""
Given this text, infer likely AiGentsy traits from:
legal, marketing, finance, sdk_spawner, compliance_sentinel, founder, social, autonomous, meta_hive_founder

Text:
\"\"\"{raw_text}\"\"\"

Return a comma-separated list of traits only.
"""
            trait_resp = await llm.ainvoke([HumanMessage(content=prompt)])
            inferred = [t.strip() for t in trait_resp.content.split(",") if t.strip()]
        else:
            # Deterministic fallback
            text = raw_text.lower()
            inferred = []
            if any(k in text for k in ["nda","contract","ip","legal"]): inferred.append("legal")
            if any(k in text for k in ["seo","ad","growth","brand","marketing"]): inferred.append("marketing")
            if any(k in text for k in ["sdk","api","package"]): inferred.append("sdk_spawner")
            if any(k in text for k in ["privacy","consent","compliance"]): inferred.append("compliance_sentinel")
            if any(k in text for k in ["founder","startup","cofounder"]): inferred.append("founder")
            if any(k in text for k in ["tiktok","instagram","twitter","x.com","creator"]): inferred.append("social")
            if any(k in text for k in ["agent","autonomous","automation"]): inferred.append("autonomous")
            if any(k in text for k in ["hive","collective","guild"]): inferred.append("meta_hive_founder")

        return {"status": "ok", "inferred_traits": inferred}
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {"status": "error", "message": "No text provided."}

        # 1) Extract a short query
        inferred_query = raw_text[:120]
        if llm is not None and HAS_KEY:
            extract_msg = HumanMessage(
                content=f"From this content, infer a 1-line business offering/need:\n\n{raw_text}"
            )
            resp = await llm.ainvoke([extract_msg])
            inferred_query = (resp.content or inferred_query).strip()

        # 2) Match to internal users
        matches = metabridge_dual_match_realworld_fulfillment(inferred_query)

        # 3) Generate proposals & persist
        proposals = proposal_generator(inferred_query, matches, originator)
        for p in proposals:
            _post_json("/submit_proposal", p)

        # External delivery (optional)
        if deliver_proposal:
            try:
                deliver_proposal(query=inferred_query, matches=matches, originator=originator)
            except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {
            "status": "ok",
            "query": inferred_query,
            "match_count": len(matches),
            "matches": matches,
            "proposals": proposals
        }
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {"status": "error", "message": "No URL provided."}

        page = HTTP.get(target_url, timeout=10)
        raw_text = page.text
        clean_text = " ".join(raw_text.split("<")).replace(">", " ")[:2000]

        inferred_offer = clean_text[:120]
        if llm is not None and HAS_KEY:
            extract_msg = HumanMessage(content=f"From this page text, give a 1-line offering/need:\n\n{clean_text}")
            resp = await llm.ainvoke([extract_msg])
            inferred_offer = (resp.content or inferred_offer).strip()

        matches = metabridge_dual_match_realworld_fulfillment(inferred_offer)
        proposals = proposal_generator(inferred_offer, matches, username)
        for p in proposals:
            _post_json("/submit_proposal", p)

        if deliver_proposal:
            try:
                deliver_proposal(query=inferred_offer, matches=matches, originator=username)
            except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {
            "status": "ok",
            "url": target_url,
            "detected_offer": inferred_offer,
            "match_count": len(matches),
            "matches": matches,
            "proposals": proposals
        }
    except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {"status": "error", "message": "No query provided."}

    matches = metabridge_dual_match_realworld_fulfillment(search_query)
    proposals = proposal_generator(search_query, matches, username)

    # Persist proposals via backend
    for p in proposals:
        _post_json("/submit_proposal", p)

    # External delivery (optional)
    if deliver_proposal:
        try:
            deliver_proposal(query=search_query, matches=matches, originator=username)
        except Exception as e:
        import traceback
        emit('ERROR', {'flow':'growth','err': str(e), 'trace': traceback.format_exc()[:800]})
        {
        "status": "ok",
        "query": search_query,
        "match_count": len(matches),
        "matches": matches,
        "proposals": proposals,
    }

# ----------------- Graph compile -----------------
@lru_cache
def get_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", invoke)
    graph.set_entry_point("agent")
    graph.set_finish_point("agent")
    return graph.compile()

# ---- Simple trigger callable from main.py ----
def trigger_metamatch(user_record: dict) -> dict:
    """
    Safe entry for mint/hydrate. Traits → keywords → proposals via /submit_proposal.
    """
    try:
        from aigent_growth_metamatch import run_metamatch_campaign
        return run_metamatch_campaign(user_record, per_keyword_limit=2, sleep_between=0.8)
    except Exception as e:
        return {"ok": False, "error": str(e)}
