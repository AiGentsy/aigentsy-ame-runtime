import os, time, json, uuid, typing as T, requests, datetime as dt
def _now(): return dt.datetime.utcnow().isoformat()+"Z"
def _uid(): return str(uuid.uuid4())
def _emit(kind, data):
    try:
        from events import emit; emit(kind, data)
    except Exception: pass
    try:
        from log_to_jsonbin_aam_patched import log_event; log_event({"kind":kind, **(data or {})})
    except Exception: pass
JSONBIN_URL = os.getenv("JSONBIN_URL",""); JSONBIN_SECRET = os.getenv("JSONBIN_SECRET",""); HTTP = requests.Session()
def _load_users():
    if not JSONBIN_URL: return []
    r = HTTP.get(JSONBIN_URL, headers={"X-Master-Key": JSONBIN_SECRET}, timeout=20)
    try: x=r.json(); return x.get("record") if isinstance(x,dict) else x
    except Exception: return []
def _save_users(users):
    if not JSONBIN_URL: return False
    r = HTTP.put(JSONBIN_URL, json={"record": users}, headers={"X-Master-Key": JSONBIN_SECRET}, timeout=20)
    return (r.status_code//100)==2
def _find_user(users, username):
    for u in users:
        un = u.get("username") or u.get("consent",{}).get("username")
        if un == username: return u
    return users[0] if users else None
def credit_aigx(user, amount, reason):
    y = user.setdefault("yield", {}); y["aigxEarned"] = int(y.get("aigxEarned",0)) + int(amount)
    user.setdefault("transactions",{}).setdefault("yieldEvents",[]).append({"id":_uid(),"ts":_now(),"amount":amount,"reason":reason})
    return amount
def autostake(user, paid_usd):
    pol = user.setdefault("autoStake_policy", {"ratio":0.25,"weekly_cap_usd":50,"enabled":True})
    if not pol.get("enabled"): return 0.0
    amt = min(float(paid_usd)*float(pol.get("ratio",0.25)), float(pol.get("weekly_cap_usd",50)))
    user.setdefault("wallet",{}); user["wallet"]["staked"]=float(user["wallet"].get("staked",0))+float(amt); return amt
def on_event(evt: dict):
    kind = (evt.get("kind") or "").upper()
    users = _load_users(); user = _find_user(users, evt.get("user") or evt.get("username") or "chatgpt")
    if not user: return {"ok": False, "err":"no_user"}
    if kind in ("ATTRIBUTED","PAID"):
        usd = float(evt.get("value_usd") or evt.get("amount_usd") or 0.0)
        credit_aigx(user, int(round(usd)), f"{kind}:{evt.get('provider','unknown')}")
        if kind=="PAID": autostake(user, usd)
        if evt.get("bundle_id"):
            b = user.setdefault("bundle_experiments",{}).setdefault(evt["bundle_id"], {"rev_usd":0.0,"events":0})
            b["rev_usd"] = float(b["rev_usd"]) + usd; b["events"] = int(b["events"]) + 1
        if evt.get("mesh_session_id"):
            user.setdefault("mesh",{}).setdefault("sessions",[]).append({"id":evt["mesh_session_id"],"kind":kind,"usd":usd,"ts":_now()})
    if kind.startswith("INTENT_"):
        user.setdefault("intents", []).append({"ts": _now(), **evt})
    if kind.startswith("DEALGRAPH_"):
        user.setdefault("dealGraph", {"nodes":[], "edges":[], "revSplit":[]}).setdefault("events", []).append({"ts": _now(), **evt})
    if kind.startswith("FRANCHISE_"):
        user.setdefault("franchise_packs", []).append({"ts": _now(), **evt})
    if kind.startswith("R3_"):
        r3 = user.setdefault("r3", {"budget_usd":0,"last_allocation":None})
        if kind=="R3_ALLOCATED": r3["last_allocation"]={"ts":_now(),"usd":evt.get("usd",0),"channel":evt.get("channel")}
    ok=_save_users(users); _emit(kind, evt); return {"ok": ok}
