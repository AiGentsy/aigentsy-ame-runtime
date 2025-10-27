from __future__ import annotations
from typing import Callable, Any, Dict, Optional, List
import inspect, uuid, datetime as dt
from fastapi import APIRouter
try:
    from .event_bus import publish
except Exception:
    def publish(*a, **k): pass

def _now() -> str: return dt.datetime.utcnow().isoformat() + "Z"
def _uuid() -> str: return str(uuid.uuid4())

class AAMQueue:
    def __init__(self, executor: Optional[Callable[[Dict], Any]] = None, max_retries: int = 0,
                 before_hook: Optional[Callable[[Dict], None]] = None, after_hook: Optional[Callable[[Dict, Dict], None]] = None) -> None:
        self.executor = executor; self.max_retries = int(max_retries or 0)
        self.before_hook = before_hook; self.after_hook = after_hook
        self.dead_letter: List[Dict] = []; self.queue: List[Dict] = []

    def set_executor(self, executor: Callable[[Dict], Any]) -> None: self.executor = executor
    def submit_many(self, jobs: List[Dict]) -> List[Dict]: return [self.submit(j) for j in jobs]

    def _run_executor(self, job: Dict) -> Dict:
        if not self.executor: return {"ok": True, "queued": True, "note": "no executor set"}
        try:
            if inspect.iscoroutinefunction(self.executor):
                import asyncio; result = asyncio.get_event_loop().run_until_complete(self.executor(job))
            else:
                result = self.executor(job)
            return {"ok": True, "executed": True, "results": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def submit(self, job: Dict) -> Dict:
        env = {"job_id": job.get("job_id") or _uuid(), "submitted_at": _now(), "mesh_session_id": job.get("mesh_session_id"),
               "bundle_id": job.get("bundle_id"), "intent_id": job.get("intent_id"), "attempt": 0, "max_retries": self.max_retries, "status": "queued"}
        if self.before_hook:
            try: self.before_hook({"job": job, "meta": env})
            except Exception: pass
        attempts = 0; last_result: Dict[str, Any] = {}
        while attempts <= self.max_retries:
            env["attempt"] = attempts + 1; env["started_at"] = _now()
            res = self._run_executor(job); env["finished_at"] = _now(); last_result = res
            if res.get("ok"): env["status"] = "executed" if res.get("executed") else "ok"; break
            attempts += 1
        if not last_result.get("ok"):
            env["status"] = "dead_letter"; self.dead_letter.append({"job": job, "meta": env, "result": last_result})
        envelope = {"ok": last_result.get("ok", False), "job": job, "meta": env, "result": last_result}
        if self.after_hook:
            try: self.after_hook({"job": job, "meta": env, "result": last_result})
            except Exception: pass
        # publish queue event
        publish("AAM_ENQUEUED", envelope)
        self.queue.append(envelope)
        return envelope

Q = AAMQueue()

# FastAPI wrapper
from pydantic import BaseModel
router = APIRouter()

class AAMJob(BaseModel):
    user_id: str
    action: str
    payload: Dict[str, Any]

@router.post("/enqueue")
def enqueue(job: AAMJob):
    # Risk check pass-through
    risk = (job.payload or {}).get("risk",{}).get("score",0)
    if risk and risk > 80:
        return {"ok": False, "skipped": "high_risk"}
    env = {"app":"mesh","action_id":job.action,"payload":job.payload}
    return Q.submit(env)

@router.get("/queue")
def get_queue():
    return {"size": len(Q.queue), "items": Q.queue[-100:]}
