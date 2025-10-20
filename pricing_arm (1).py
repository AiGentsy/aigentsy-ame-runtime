
import os, uuid, math, asyncio, httpx
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

JSONBIN_URL    = os.getenv("JSONBIN_URL")
JSONBIN_SECRET = os.getenv("JSONBIN_SECRET")

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

async def _jsonbin_get(client: httpx.AsyncClient) -> Dict[str, Any]:
    r = await client.get(JSONBIN_URL, headers={"X-Master-Key": JSONBIN_SECRET})
    r.raise_for_status()
    return r.json()

async def _jsonbin_put(client: httpx.AsyncClient, users: list) -> None:
    r = await client.put(JSONBIN_URL,
                         headers={"X-Master-Key": JSONBIN_SECRET, "Content-Type": "application/json"},
                         json={"record": users})
    r.raise_for_status()

def _uname(u: Dict[str, Any]) -> str:
    return u.get("username") or (u.get("consent", {}) or {}).get("username")

def _find_user(users: List[Dict[str, Any]], username: str) -> Optional[Dict[str, Any]]:
    un = (username or "").lower()
    for u in users:
        if (_uname(u) or "").lower() == un:
            return u
    return None

def _ensure(u: Dict[str, Any]):
    u.setdefault("experiments", [])

def _new_exp(username: str, bundles: List[Dict[str, Any]]) -> Dict[str, Any]:
    # bundles: [{id, price, meta?}, ...]
    arms = []
    for b in bundles:
        arms.append({
            "bundle_id": b.get("id") or f"bundle_{uuid.uuid4().hex[:8]}",
            "price": float(b.get("price", 0)),
            "meta": b.get("meta") or {},
            "pulls": 0,
            "reward_sum": 0.0,
        })
    return {
        "id": f"arm_{uuid.uuid4().hex[:10]}",
        "type": "bundle_pricing_AB",
        "username": username,
        "arms": arms,
        "epsilon": 0.15,
        "created": _now(),
        "last_arm": None,
    }

def _avg_reward(arm: Dict[str, Any]) -> float:
    n = int(arm.get("pulls", 0))
    s = float(arm.get("reward_sum", 0.0))
    return (s / n) if n > 0 else 0.0

def _ucb1(arm: Dict[str, Any], total_pulls: int) -> float:
    n = max(1, int(arm.get("pulls", 0)))
    mean = _avg_reward(arm)
    return mean + math.sqrt(2.0 * math.log(max(2, total_pulls)) / n)

async def start_bundle_test(username: str, bundles: List[Dict[str, Any]], epsilon: float = 0.15) -> Dict[str, Any]:
    """
    Create a new test for 'username' over the given bundles.
    Returns the experiment record.
    """
    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        u = _find_user(users, username)
        if not u:
            raise RuntimeError("user not found")
        _ensure(u)
        exp = _new_exp(username, bundles)
        exp["epsilon"] = float(epsilon)
        u["experiments"].append(exp)
        await _jsonbin_put(client, users)
        return exp

async def next_arm(username: str, exp_id: str) -> Dict[str, Any]:
    """
    Epsilon-greedy with UCB1 tiebreak for exploration.
    Returns: {"bundle_id":..., "price":...}
    """
    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        u = _find_user(users, username)
        if not u:
            raise RuntimeError("user not found")
        exp = next((e for e in u.get("experiments", []) if e.get("id")==exp_id), None)
        if not exp:
            raise RuntimeError("experiment not found")

        import random
        arms = exp["arms"]
        # Pull count
        total_pulls = sum(int(a.get("pulls",0)) for a in arms)

        # Force-initialize: pull each arm once
        cold = [a for a in arms if int(a.get("pulls",0)) == 0]
        if cold:
            choice = random.choice(cold)
        else:
            if random.random() < float(exp.get("epsilon", 0.15)):
                choice = random.choice(arms)
            else:
                # choose argmax UCB1
                choice = max(arms, key=lambda a: _ucb1(a, total_pulls))

        choice["pulls"] = int(choice.get("pulls",0)) + 1
        exp["last_arm"] = choice["bundle_id"]
        await _jsonbin_put(client, users)
        return {"bundle_id": choice["bundle_id"], "price": choice["price"]}

async def record_outcome(username: str, exp_id: str, bundle_id: str, revenue_usd: float):
    """
    After an exposure to 'bundle_id', record realized revenue (0 if no purchase).
    """
    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        u = _find_user(users, username)
        if not u:
            raise RuntimeError("user not found")
        exp = next((e for e in u.get("experiments", []) if e.get("id")==exp_id), None)
        if not exp:
            raise RuntimeError("experiment not found")
        arm = next((a for a in exp["arms"] if a.get("bundle_id")==bundle_id), None)
        if not arm:
            raise RuntimeError("arm not found")
        arm["reward_sum"] = float(arm.get("reward_sum",0.0)) + float(revenue_usd)
        exp["last_outcome_ts"] = _now()
        await _jsonbin_put(client, users)
        return {"ok": True, "bundle_id": bundle_id, "rev": float(revenue_usd), "pulls": arm["pulls"], "sum": arm["reward_sum"]}

async def best_arm(username: str, exp_id: str) -> Dict[str, Any]:
    """
    Returns the empirically best arm (highest average revenue).
    """
    async with httpx.AsyncClient(timeout=20) as client:
        data = await _jsonbin_get(client)
        users = data.get("record", [])
        u = _find_user(users, username)
        if not u:
            raise RuntimeError("user not found")
        exp = next((e for e in u.get("experiments", []) if e.get("id")==exp_id), None)
        if not exp:
            raise RuntimeError("experiment not found")
        arms = exp.get("arms", [])
        if not arms:
            raise RuntimeError("no arms")
        best = max(arms, key=lambda a: (a.get("reward_sum",0.0) / max(1,int(a.get("pulls",0)))))
        return {"bundle_id": best["bundle_id"], "price": best["price"], "avg_rev": best.get("reward_sum",0.0)/max(1,int(best.get("pulls",0)))}
