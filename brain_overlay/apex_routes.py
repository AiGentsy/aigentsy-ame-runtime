"""
APEX ROUTES
===========

Cross-agent knowledge distribution.
Top-decile policies promoted as "Apex Routes" - compact JSON policies signed + versioned.

Each agent subscribes to hive/routes/apex/* and hot-loads if lift persists for N runs.
Maintains shadow evaluation (A/B) to avoid policy collapse.

Schema:
{
  "route_id": "oaa_pricing_v12",
  "scope": {"segment": "B2B-SaaS", "geo": "US"},
  "policy": {"price_slope": 0.23, "pg_attach_logit": 1.8, "kelly_cap": 0.35},
  "guardrails": {"min_margin": 0.28, "sla_p95_ms": 180000},
  "proven_on": 4127,
  "sig": "ed25519:..."
}
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from collections import defaultdict
import hashlib
import json
import base64

# Try to import MetaHive for network distribution
try:
    from metahive_brain import contribute_to_hive, query_hive
    METAHIVE_AVAILABLE = True
except ImportError:
    METAHIVE_AVAILABLE = False
    async def contribute_to_hive(*args, **kwargs): return {"ok": False}
    async def query_hive(*args, **kwargs): return {"ok": True, "patterns": []}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _sign_route(route: dict) -> str:
    """Generate signature for route (simplified - use proper signing in prod)"""
    payload = json.dumps(route, sort_keys=True, default=str)
    return f"sha256:{hashlib.sha256(payload.encode()).hexdigest()[:32]}"


class ApexRoutes:
    """
    Apex route manager for cross-agent knowledge distribution.

    Responsibilities:
    - Find top-performing policies
    - Sign and version routes
    - Publish to MetaHive
    - Subscribe and hot-load routes
    - Shadow A/B evaluation
    """

    def __init__(self):
        self._routes: Dict[str, Dict[str, Any]] = {}
        self._subscriptions: List[str] = []
        self._shadow_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._min_proven_samples = 100
        self._min_lift_threshold = 0.08
        self._min_confidence = 0.9

    def find_top(
        self,
        top_k: int = 20,
        min_lift: float = None,
        min_conf: float = None
    ) -> List[Dict[str, Any]]:
        """
        Find top-performing policies to promote as apex routes.

        Requires access to policy metrics - integrates with PolicyEngine.
        """
        min_lift = min_lift or self._min_lift_threshold
        min_conf = min_conf or self._min_confidence

        # Get policy metrics from policy engine
        try:
            from .policy import _policy_engine
            metrics = _policy_engine.get_all_metrics()
        except:
            metrics = {}

        candidates = []
        for name, data in metrics.items():
            if data.get("history_size", 0) < self._min_proven_samples:
                continue

            avg_reward = data.get("avg_reward", 0)
            best_reward = data.get("best_reward", 0)

            # Calculate lift vs baseline (assume baseline avg_reward = 0)
            lift = avg_reward  # Simplified - should compare to baseline

            if lift >= min_lift:
                candidates.append({
                    "route_id": name.replace(".", "_"),
                    "policy_name": name,
                    "params": data.get("params", {}),
                    "lift": round(lift, 4),
                    "proven_on": data.get("history_size", 0),
                    "avg_reward": round(avg_reward, 4)
                })

        # Sort by lift and take top_k
        candidates.sort(key=lambda x: x["lift"], reverse=True)
        return candidates[:top_k]

    def create_route(
        self,
        route_id: str,
        scope: Dict[str, str],
        policy: Dict[str, float],
        guardrails: Dict[str, float],
        proven_on: int
    ) -> Dict[str, Any]:
        """Create a signed apex route"""
        route = {
            "route_id": route_id,
            "scope": scope,
            "policy": policy,
            "guardrails": guardrails,
            "proven_on": proven_on,
            "version": 1,
            "created_at": _now_iso()
        }

        # Sign route
        route["sig"] = _sign_route(route)

        # Store locally
        self._routes[route_id] = route

        return route

    def publish(self, routes: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Publish apex routes to MetaHive for network distribution.

        Args:
            routes: Routes to publish (or use find_top if None)
        """
        if routes is None:
            routes = self.find_top()

        published = []
        for r in routes:
            # Create full route spec
            route = self.create_route(
                route_id=r.get("route_id", r.get("policy_name", "unknown").replace(".", "_")),
                scope=r.get("scope", {"segment": "all", "geo": "all"}),
                policy=r.get("params", {}),
                guardrails=r.get("guardrails", {"min_margin": 0.25}),
                proven_on=r.get("proven_on", 0)
            )

            # Publish to MetaHive
            if METAHIVE_AVAILABLE:
                import asyncio
                try:
                    asyncio.create_task(contribute_to_hive(
                        username="apex_routes",
                        pattern_type="ai_routing",
                        context={"route_id": route["route_id"], "scope": route["scope"]},
                        action={"type": "apex_route", "policy": route["policy"]},
                        outcome={
                            "roas": 1 + r.get("lift", 0),
                            "quality_score": 0.95,
                            "proven_on": route["proven_on"]
                        },
                        anonymize=False
                    ))
                except:
                    pass

            published.append(route)

        return {
            "ok": True,
            "published": len(published),
            "routes": published
        }

    def subscribe(self, route_patterns: List[str] = None) -> Dict[str, Any]:
        """Subscribe to apex route updates"""
        patterns = route_patterns or ["hive/routes/apex/*"]
        self._subscriptions.extend(patterns)
        return {"ok": True, "subscriptions": self._subscriptions}

    async def fetch_updates(self) -> List[Dict[str, Any]]:
        """Fetch latest apex routes from MetaHive"""
        if not METAHIVE_AVAILABLE:
            return []

        try:
            result = await query_hive(
                pattern_type="ai_routing",
                limit=50,
                min_quality=0.9
            )
            return result.get("patterns", [])
        except:
            return []

    def hot_load(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hot-load an apex route into the policy engine.

        Only loads if lift persists (via shadow A/B).
        """
        route_id = route.get("route_id")
        if not route_id:
            return {"ok": False, "error": "missing_route_id"}

        # Verify signature
        stored_sig = route.get("sig")
        route_copy = {k: v for k, v in route.items() if k != "sig"}
        expected_sig = _sign_route(route_copy)

        if stored_sig != expected_sig:
            return {"ok": False, "error": "signature_mismatch"}

        # Check if we have shadow results
        shadow = self._shadow_results.get(route_id, [])
        if len(shadow) < 10:
            # Start shadow evaluation
            return self._start_shadow(route)

        # Check shadow lift
        shadow_avg = sum(s.get("reward", 0) for s in shadow) / len(shadow)
        baseline_avg = sum(s.get("baseline_reward", 0) for s in shadow) / len(shadow)

        lift = (shadow_avg - baseline_avg) / baseline_avg if baseline_avg != 0 else 0

        if lift < self._min_lift_threshold:
            return {
                "ok": False,
                "error": "shadow_lift_insufficient",
                "lift": round(lift, 4),
                "required": self._min_lift_threshold
            }

        # Load into policy engine
        try:
            from .policy import _policy_engine
            policy_name = route_id.replace("_", ".")
            policy = _policy_engine.get(policy_name)
            policy.load_apex(route)

            self._routes[route_id] = route

            return {
                "ok": True,
                "route_id": route_id,
                "loaded": True,
                "lift": round(lift, 4)
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _start_shadow(self, route: Dict[str, Any]) -> Dict[str, Any]:
        """Start shadow A/B evaluation for route"""
        route_id = route.get("route_id")
        self._routes[f"shadow:{route_id}"] = route

        return {
            "ok": True,
            "route_id": route_id,
            "status": "shadow_evaluation_started",
            "samples_needed": 10 - len(self._shadow_results.get(route_id, []))
        }

    def record_shadow_result(
        self,
        route_id: str,
        reward: float,
        baseline_reward: float
    ):
        """Record shadow evaluation result"""
        self._shadow_results[route_id].append({
            "ts": _now_iso(),
            "reward": reward,
            "baseline_reward": baseline_reward
        })

        # Trim old results
        if len(self._shadow_results[route_id]) > 100:
            self._shadow_results[route_id] = self._shadow_results[route_id][-100:]

    def get_route(self, route_id: str) -> Optional[Dict[str, Any]]:
        """Get route by ID"""
        return self._routes.get(route_id)

    def list_routes(self) -> List[Dict[str, Any]]:
        """List all loaded routes"""
        return [
            {
                "route_id": r["route_id"],
                "scope": r.get("scope"),
                "proven_on": r.get("proven_on"),
                "version": r.get("version")
            }
            for r in self._routes.values()
            if not r.get("route_id", "").startswith("shadow:")
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get apex routes statistics"""
        return {
            "total_routes": len([r for r in self._routes if not r.startswith("shadow:")]),
            "shadow_evaluations": len([r for r in self._routes if r.startswith("shadow:")]),
            "subscriptions": len(self._subscriptions)
        }


# Module-level singleton
_apex_routes = ApexRoutes()


def publish_apex(routes: List[Dict] = None) -> Dict[str, Any]:
    """Publish apex routes"""
    return _apex_routes.publish(routes)


def subscribe_apex(patterns: List[str] = None) -> Dict[str, Any]:
    """Subscribe to apex routes"""
    return _apex_routes.subscribe(patterns)


def hot_load_route(route: Dict[str, Any]) -> Dict[str, Any]:
    """Hot-load an apex route"""
    return _apex_routes.hot_load(route)


def find_apex_routes(top_k: int = 20, **kwargs) -> List[Dict[str, Any]]:
    """Find top apex routes"""
    return _apex_routes.find_top(top_k, **kwargs)
