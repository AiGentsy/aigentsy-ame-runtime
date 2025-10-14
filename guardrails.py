import os, json
def load_policy():
    raw = os.getenv("AIGENTSY_POLICY_JSON", "{}")
    try: return json.loads(raw)
    except Exception: return {}
def guard_ok(context: dict, cost_usd: float = 0.0):
    pol = {"autonomy":"suggest","spend_cap_usd":0,"block":[]}
    pol.update(load_policy())
    if pol.get("autonomy") == "observe": return False, "autonomy=observe"
    cap = float(pol.get("spend_cap_usd", 0) or 0)
    if cap and cost_usd > cap: return False, f"cap_exceeded>{cap}"
    text = (context.get("text") or "").lower()
    blocks = [b.lower() for b in pol.get("block", [])]
    if any(b in text for b in blocks): return False, "brand_block"
    return True, "ok"
