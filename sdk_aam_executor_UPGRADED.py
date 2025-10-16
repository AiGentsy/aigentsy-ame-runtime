import os, requests
HTTP = requests.Session(); BASE=(os.getenv("BACKEND_BASE") or "").rstrip("/")
def _u(p): return f"{BASE}{p}" if BASE else p
def execute(job: dict):
    actions = job.get("actions") or []; results=[]
    for a in actions:
        t = a.get("type"); p = a.get("params",{})
        try:
            if t=="mesh.start": results.append({"ok": True, "mesh_session_id": p.get("session_id")}); continue
            ep = None
            if t=="price.arm": ep="/pricing/arm"
            elif t=="r3.allocate": ep="/r3/allocate"
            elif t=="proposal.nudge": ep="/proposal/nudge"
            elif t=="proposal.convert": ep="/proposal/convert"
            elif t=="inventory.check": results.append({"ok": True, "note":"defer to /inventory/get from executor caller"}); continue
            elif t=="coop.spend": ep="/coop/sponsor"  # placeholder
            else: results.append({"ok": False,"error": f"unknown_action:{t}"}); continue
            r = HTTP.post(_u(ep), json=p, timeout=20); results.append({"ok": r.ok, "status": r.status_code, "resp": (r.json() if r.ok else r.text)})
        except Exception as e:
            results.append({"ok": False, "error": str(e)})
    return results
