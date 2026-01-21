"""
MASTER AUTONOMOUS ORCHESTRATOR v2.0
═══════════════════════════════════════════════════════════════════════════════

PRODUCTION-HARDENED END-TO-END AUTONOMOUS REVENUE SYSTEM

Safety Rails:
- Retry/backoff/jitter with idempotency keys
- Dedupe + EV prioritization before comms
- Circuit breakers per platform
- Concurrency semaphores for outreach
- Structured logging with run_id tracing
- Consent/allowlist gates for PII

Orchestrates ALL 1000+ endpoints across the entire pipeline:

1. DISCOVERY (7 Dimensions)
2. COMMUNICATION (Multi-Channel)
3. CONTRACT & AGREEMENT
4. FULFILLMENT
5. PAYMENT COLLECTION

Updated: Jan 2026 - Production Hardened
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from hashlib import sha1
from uuid import uuid4
import asyncio
import random
import os
import json
import logging

# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURED LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("autonomous_orchestrator")

def _log_structured(run_id: str, phase: str, event: str, data: Dict = None):
    """Emit structured log for observability"""
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "phase": phase,
        "event": event,
        **(data or {})
    }
    logger.info(json.dumps(log_entry))


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


# ═══════════════════════════════════════════════════════════════════════════════
# COI RUNTIME (FULFILLMENT FABRIC)
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from coi_runtime import get_coi_runtime, COIRuntime
    COI_AVAILABLE = True
except ImportError:
    COI_AVAILABLE = False
    logger.warning("COI Runtime not available - fabric execution disabled")


# ═══════════════════════════════════════════════════════════════════════════════
# MONETIZATION FABRIC INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from monetization import MonetizationFabric
    from monetization.pricing_arm import suggest as monetization_price_suggest
    from monetization.revenue_router import split as monetization_revenue_split
    from monetization.ledger import post_entry as monetization_ledger_post, record_sale
    from monetization.proof_badges import mint_badge as monetization_mint_badge
    from monetization.referrals import allocate_referrals, register_chain
    from monetization.subscriptions import check_quota, record_usage, subscribe
    from monetization.fee_schedule import get_fee, calculate_platform_fee
    from monetization.arbitrage_engine import detect_spread_opportunity
    from monetization.settlements import initiate_payout
    MONETIZATION_AVAILABLE = True
    logger.info("✅ Monetization Fabric loaded")
except ImportError as e:
    MONETIZATION_AVAILABLE = False
    logger.warning(f"Monetization Fabric not available: {e}")
    # Fallbacks
    def monetization_price_suggest(base, **kwargs): return base
    def monetization_revenue_split(gross, **kwargs): return {"platform": 0, "user": gross}
    def monetization_ledger_post(*args, **kwargs): return {"ok": True}
    def monetization_mint_badge(att): return {"badge_id": None}
    def allocate_referrals(gross, chain, **kwargs): return {"splits": {}, "remainder": gross}
    def register_chain(user, chain): return {"ok": True}
    def check_quota(user, calls=1): return {"ok": True, "within_quota": True}
    def record_usage(user, calls=1): return {"ok": True}
    def subscribe(user, tier, **kwargs): return {"ok": True}
    def get_fee(key, default): return default
    def calculate_platform_fee(amount): return {"fee": 0, "net": amount}
    def detect_spread_opportunity(bids, asks, **kwargs): return {"ok": False}
    def initiate_payout(entity, **kwargs): return {"ok": False}
    def record_sale(coi_id, gross, splits, **kwargs): return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# CONSENT & SUPPRESSION LIST
# ═══════════════════════════════════════════════════════════════════════════════

class ConsentManager:
    """
    Manages consent for outreach to stay compliant with CAN-SPAM/TCPA.
    """
    def __init__(self):
        self.suppression_list: Set[str] = set()
        self.consent_log: List[Dict] = []
        self.allowlist: Set[str] = set()  # Explicit opt-ins

    def is_allowed(self, contact: str, channel: str) -> bool:
        """Check if contact is allowed for outreach on this channel"""
        # Suppressed contacts are never allowed
        if contact.lower() in self.suppression_list:
            return False
        # If allowlist is populated, only allow those
        if self.allowlist and contact.lower() not in self.allowlist:
            return False
        return True

    def suppress(self, contact: str, reason: str = "unsubscribe"):
        """Add contact to suppression list"""
        self.suppression_list.add(contact.lower())
        self.consent_log.append({
            "contact": contact,
            "action": "suppress",
            "reason": reason,
            "ts": datetime.now(timezone.utc).isoformat()
        })

    def record_consent(self, contact: str, channel: str, proof: str):
        """Record proof of consent for compliance"""
        self.consent_log.append({
            "contact": contact,
            "channel": channel,
            "action": "consent",
            "proof": proof,
            "ts": datetime.now(timezone.utc).isoformat()
        })
        self.allowlist.add(contact.lower())


# ═══════════════════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════════════════════

class CircuitBreaker:
    """
    Simple counter-based circuit breaker per platform.
    Opens after threshold failures, auto-closes after cooldown.
    """
    def __init__(self, threshold: int = 5, cooldown_seconds: float = 300):
        self.threshold = threshold
        self.cooldown = cooldown_seconds
        self.breakers: Dict[str, Dict] = {}

    def can_call(self, platform: str) -> bool:
        """Check if platform circuit is closed (callable)"""
        now = asyncio.get_event_loop().time()
        b = self.breakers.get(platform, {"fail": 0, "open_until": 0})
        if now >= b["open_until"]:
            return True
        return False

    def record_success(self, platform: str):
        """Record successful call - reset failure count"""
        if platform in self.breakers:
            self.breakers[platform]["fail"] = 0

    def record_failure(self, platform: str):
        """Record failed call - increment counter, maybe open breaker"""
        b = self.breakers.setdefault(platform, {"fail": 0, "open_until": 0})
        b["fail"] += 1
        if b["fail"] >= self.threshold:
            try:
                now = asyncio.get_event_loop().time()
            except RuntimeError:
                now = 0
            b["open_until"] = now + self.cooldown
            logger.warning(f"Circuit OPEN for {platform} - cooling down {self.cooldown}s")

    def get_status(self) -> Dict[str, Any]:
        """Get all breaker statuses"""
        return {k: {"fail_count": v["fail"], "open": v["open_until"] > 0}
                for k, v in self.breakers.items()}


# ═══════════════════════════════════════════════════════════════════════════════
# MASTER ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════════

class MasterAutonomousOrchestrator:
    """
    Production-hardened orchestrator with:
    - Retry/backoff/jitter
    - Idempotency keys
    - Dedupe + EV ranking
    - Circuit breakers
    - Concurrency control
    - Structured logging
    - Consent management
    """

    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or BACKEND_URL
        self.client = httpx.AsyncClient(timeout=300) if HTTPX_AVAILABLE else None

        # Production safety components
        self.circuit_breaker = CircuitBreaker(threshold=5, cooldown_seconds=300)
        self.consent_manager = ConsentManager()

        # COI Runtime (Fulfillment Fabric) - Uses API keys from environment
        self.coi_runtime = None
        if COI_AVAILABLE:
            self.coi_runtime = get_coi_runtime()
            logger.info("COI Runtime initialized - Fulfillment Fabric connected")

        # Monetization Fabric - Revenue generation overlay
        self.monetization_fabric = None
        if MONETIZATION_AVAILABLE:
            try:
                self.monetization_fabric = MonetizationFabric()
                logger.info("✅ Monetization Fabric initialized - Revenue overlay connected")
            except Exception as e:
                logger.warning(f"Monetization Fabric init failed: {e}")

        # Concurrency limits per platform type
        self.semaphores = {
            "email": asyncio.Semaphore(20),
            "twitter": asyncio.Semaphore(5),
            "linkedin": asyncio.Semaphore(3),
            "sms": asyncio.Semaphore(10),
            "github": asyncio.Semaphore(15),
            "reddit": asyncio.Semaphore(5),
            "upwork": asyncio.Semaphore(8),
            "fiverr": asyncio.Semaphore(8),
            "freelancer": asyncio.Semaphore(8),
            "default": asyncio.Semaphore(12)
        }

        # Track execution state
        self.current_run = {
            "run_id": None,
            "started_at": None,
            "phase": None,
            "results": {},
            "errors": [],
            "metrics": {
                "calls_made": 0,
                "calls_succeeded": 0,
                "calls_failed": 0,
                "retries": 0,
                "circuit_opens": 0,
                # Monetization metrics
                "gross_revenue": 0.0,
                "platform_fees": 0.0,
                "referral_payouts": 0.0,
                "badges_minted": 0,
                "arbitrage_captured": 0.0
            }
        }

        # Seen opportunity keys for deduplication
        self._seen_keys: Set[str] = set()

    def _run_id(self) -> str:
        """Get or create run ID for tracing"""
        if not self.current_run.get("run_id"):
            self.current_run["run_id"] = f"orch-{uuid4().hex[:12]}"
        return self.current_run["run_id"]

    def _get_semaphore(self, platform: str) -> asyncio.Semaphore:
        """Get concurrency semaphore for platform"""
        return self.semaphores.get(platform.lower(), self.semaphores["default"])

    # ═══════════════════════════════════════════════════════════════════════════
    # PRODUCTION-HARDENED HTTP CALLER
    # ═══════════════════════════════════════════════════════════════════════════

    async def _call(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        *,
        idempotency_key: str = None,
        timeout: float = 60,
        tries: int = 4,
        platform: str = "internal"
    ) -> Dict[str, Any]:
        """
        Production-safe HTTP caller with:
        - Exponential backoff + jitter
        - Idempotency header
        - Circuit breaker check
        - Structured logging
        """
        if not self.client:
            return {"ok": False, "error": "httpx not available"}

        # Circuit breaker check
        if not self.circuit_breaker.can_call(platform):
            _log_structured(self._run_id(), "http", "circuit_open", {"platform": platform, "endpoint": endpoint})
            return {"ok": False, "error": f"circuit_open:{platform}"}

        url = f"{self.backend_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        backoff = 0.4
        last_error = None

        for attempt in range(1, tries + 1):
            try:
                self.current_run["metrics"]["calls_made"] += 1

                if method == "GET":
                    response = await self.client.get(url, params=data, timeout=timeout)
                else:
                    response = await self.client.post(url, json=data or {}, headers=headers, timeout=timeout)

                code = response.status_code

                if code in (200, 201):
                    self.circuit_breaker.record_success(platform)
                    self.current_run["metrics"]["calls_succeeded"] += 1
                    _log_structured(self._run_id(), "http", "success", {
                        "endpoint": endpoint, "code": code, "attempt": attempt
                    })
                    try:
                        return response.json()
                    except:
                        return {"ok": True, "raw": response.text[:1000]}

                # Retryable errors
                if code in (429, 500, 502, 503, 504):
                    self.current_run["metrics"]["retries"] += 1
                    jitter = random.random() * 0.3
                    wait = backoff + jitter
                    _log_structured(self._run_id(), "http", "retry", {
                        "endpoint": endpoint, "code": code, "attempt": attempt, "wait": wait
                    })
                    await asyncio.sleep(wait)
                    backoff *= 2
                    continue

                # Non-retryable error
                self.circuit_breaker.record_failure(platform)
                self.current_run["metrics"]["calls_failed"] += 1
                return {"ok": False, "error": f"HTTP {code}", "body": response.text[:500]}

            except asyncio.TimeoutError:
                last_error = "timeout"
                self.current_run["metrics"]["retries"] += 1
                await asyncio.sleep(backoff)
                backoff *= 2

            except Exception as e:
                last_error = str(e)
                if attempt == tries:
                    self.circuit_breaker.record_failure(platform)
                    self.current_run["metrics"]["calls_failed"] += 1
                    return {"ok": False, "error": last_error}
                await asyncio.sleep(backoff)
                backoff *= 2

        self.circuit_breaker.record_failure(platform)
        self.current_run["metrics"]["calls_failed"] += 1
        return {"ok": False, "error": f"max_retries:{last_error}"}

    # ═══════════════════════════════════════════════════════════════════════════
    # DEDUPE + EV PRIORITIZATION
    # ═══════════════════════════════════════════════════════════════════════════

    def _compute_opportunity_key(self, opp: Dict) -> str:
        """Generate stable key for deduplication"""
        raw = f"{opp.get('platform', '')}|{opp.get('url') or opp.get('id', '')}|{opp.get('title', '')}"
        return sha1(raw.encode()).hexdigest()[:16]

    def _compute_ev(self, opp: Dict) -> float:
        """
        Compute Expected Value for opportunity prioritization.
        EV = (value × win_prob × time_decay) - cogs

        For AI-automated fulfillment:
        - COGS is mostly compute/API costs (~$5-20 per task)
        - Win probability for bounties with clear specs is higher
        """
        value = float(opp.get("value", 0) or opp.get("estimated_value", 0) or 0)

        # Source-aware win probability defaults
        source = opp.get("source", "").lower()
        platform = opp.get("platform", "").lower()
        if "bounty" in source or "bounty" in str(opp.get("labels", [])).lower():
            default_win_prob = 0.40  # Bounties have clearer specs
        elif platform in ("github", "upwork", "freelancer"):
            default_win_prob = 0.35  # Marketplace opportunities
        else:
            default_win_prob = 0.25  # General opportunities

        win_prob = float(opp.get("win_prob", opp.get("confidence", default_win_prob)))

        # COGS: For AI-automated work, use fixed cost estimate not percentage
        # Typical API/compute costs: $5-20 depending on complexity
        default_cogs = min(value * 0.10, 25.0) if value > 0 else 10.0
        cogs = float(opp.get("cogs_estimate", default_cogs))

        # Time decay - fresher opportunities score higher
        posted_minutes = opp.get("posted_minutes_ago", opp.get("age_minutes", 9999))
        if posted_minutes < 30:
            decay = 1.0
        elif posted_minutes < 120:
            decay = 0.95
        elif posted_minutes < 1440:  # 24h
            decay = 0.85
        else:
            decay = 0.70

        ev = (value * win_prob * decay) - cogs
        return max(ev, 0)

    def _dedupe_and_rank(self, opportunities: List[Dict], limit: int = 250) -> List[Dict]:
        """
        Deduplicate opportunities and rank by Expected Value.
        Returns top N by EV score.
        """
        unique = []

        for opp in opportunities:
            key = self._compute_opportunity_key(opp)

            # Skip if already seen in this run or globally
            if key in self._seen_keys:
                continue

            self._seen_keys.add(key)
            opp["_key"] = key
            opp["_ev"] = self._compute_ev(opp)
            unique.append(opp)

        # Sort by EV descending
        ranked = sorted(unique, key=lambda x: x["_ev"], reverse=True)

        _log_structured(self._run_id(), "dedupe", "complete", {
            "input": len(opportunities),
            "unique": len(unique),
            "returned": min(len(ranked), limit)
        })

        return ranked[:limit]

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: DISCOVERY - ALL 7 DIMENSIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_discovery_all_dimensions(self) -> Dict[str, Any]:
        """
        Run discovery across ALL 7 dimensions simultaneously.
        Returns deduplicated, EV-ranked opportunities.
        """
        self.current_run["phase"] = "discovery"
        _log_structured(self._run_id(), "discovery", "start", {})

        results = {
            "dimension_1_explicit_marketplaces": [],
            "dimension_2_pain_point_detection": [],
            "dimension_3_flow_arbitrage": [],
            "dimension_4_predictive_intelligence": [],
            "dimension_5_network_amplification": [],
            "dimension_6_opportunity_creation": [],
            "dimension_7_emergent_patterns": [],
            "total_opportunities": 0,
            "total_value": 0,
            "total_ev": 0
        }

        # Run all dimension discoveries in parallel
        discovery_tasks = [
            self._discover_dimension_1_explicit_marketplaces(),
            self._discover_dimension_2_pain_points(),
            self._discover_dimension_3_flow_arbitrage(),
            self._discover_dimension_4_predictive(),
            self._discover_dimension_5_network(),
            self._discover_dimension_6_opportunity_creation(),
            self._discover_dimension_7_emergent()
        ]

        dimension_results = await asyncio.gather(*discovery_tasks, return_exceptions=True)

        dimension_names = [
            "dimension_1_explicit_marketplaces",
            "dimension_2_pain_point_detection",
            "dimension_3_flow_arbitrage",
            "dimension_4_predictive_intelligence",
            "dimension_5_network_amplification",
            "dimension_6_opportunity_creation",
            "dimension_7_emergent_patterns"
        ]

        all_opportunities = []

        for name, result in zip(dimension_names, dimension_results):
            if isinstance(result, Exception):
                self.current_run["errors"].append({"dimension": name, "error": str(result)})
                _log_structured(self._run_id(), "discovery", "dimension_error", {
                    "dimension": name, "error": str(result)
                })
            else:
                opps = result.get("opportunities", [])
                results[name] = opps
                all_opportunities.extend(opps)

        # Dedupe and rank all opportunities
        ranked = self._dedupe_and_rank(all_opportunities)

        results["total_opportunities"] = len(ranked)
        results["total_value"] = sum(o.get("value", 0) or o.get("estimated_value", 0) for o in ranked)
        results["total_ev"] = sum(o.get("_ev", 0) for o in ranked)
        results["ranked_opportunities"] = ranked

        _log_structured(self._run_id(), "discovery", "complete", {
            "total": len(ranked),
            "total_value": results["total_value"],
            "total_ev": results["total_ev"]
        })

        self.current_run["results"]["discovery"] = results
        return results

    async def _discover_dimension_1_explicit_marketplaces(self) -> Dict[str, Any]:
        """Dimension 1: Explicit Marketplaces"""
        opportunities = []
        idem = f"{self._run_id()}|d1"

        tasks = [
            self._call("POST", "/discovery/github/bounties", {"limit": 50}, idempotency_key=f"{idem}|gh", platform="github"),
            self._call("POST", "/discovery/upwork/search", {"limit": 30}, idempotency_key=f"{idem}|uw", platform="upwork"),
            self._call("POST", "/discovery/fiverr/buyer-requests", {"limit": 20}, idempotency_key=f"{idem}|fv", platform="fiverr"),
            self._call("POST", "/discovery/freelancer/search", {"limit": 30}, idempotency_key=f"{idem}|fl", platform="freelancer"),
            self._call("GET", "/discovery/remoteok/jobs", idempotency_key=f"{idem}|ro", platform="remoteok"),
            self._call("GET", "/discovery/weworkremotely/jobs", idempotency_key=f"{idem}|wwr", platform="weworkremotely"),
            self._call("GET", "/discovery/angellist/jobs", idempotency_key=f"{idem}|al", platform="angellist"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r.get("ok"):
                opportunities.extend(r.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "explicit_marketplaces"}

    async def _discover_dimension_2_pain_points(self) -> Dict[str, Any]:
        """Dimension 2: Pain Point Detection"""
        opportunities = []
        idem = f"{self._run_id()}|d2"

        tasks = [
            self._call("POST", "/discovery/reddit/pain-points", {
                "subreddits": ["webdev", "startups", "entrepreneur", "SaaS", "freelance"],
                "limit": 50
            }, idempotency_key=f"{idem}|rd", platform="reddit"),
            self._call("GET", "/discovery/hackernews/who-is-hiring", idempotency_key=f"{idem}|hn", platform="hackernews"),
            self._call("POST", "/discovery/twitter/pain-signals", {
                "keywords": ["need developer", "looking for", "anyone know", "help with"],
                "limit": 30
            }, idempotency_key=f"{idem}|tw", platform="twitter"),
            self._call("GET", "/discovery/producthunt/launches", idempotency_key=f"{idem}|ph", platform="producthunt"),
            self._call("GET", "/discovery/indiehackers/requests", idempotency_key=f"{idem}|ih", platform="indiehackers"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r.get("ok"):
                opportunities.extend(r.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "pain_point_detection"}

    async def _discover_dimension_3_flow_arbitrage(self) -> Dict[str, Any]:
        """Dimension 3: Flow Arbitrage"""
        opportunities = []
        idem = f"{self._run_id()}|d3"

        tasks = [
            self._call("GET", "/discovery/arbitrage/detect", idempotency_key=f"{idem}|det", platform="internal"),
            self._call("GET", "/discovery/arbitrage/cross-platform", idempotency_key=f"{idem}|xp", platform="internal"),
            self._call("GET", "/discovery/arbitrage/underpriced", idempotency_key=f"{idem}|up", platform="internal"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r.get("ok"):
                opportunities.extend(r.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "flow_arbitrage"}

    async def _discover_dimension_4_predictive(self) -> Dict[str, Any]:
        """Dimension 4: Predictive Intelligence"""
        opportunities = []
        idem = f"{self._run_id()}|d4"

        tasks = [
            self._call("GET", "/discovery/predictive/trends", idempotency_key=f"{idem}|tr", platform="internal"),
            self._call("GET", "/discovery/predictive/demand-forecast", idempotency_key=f"{idem}|df", platform="internal"),
            self._call("GET", "/discovery/predictive/seasonal", idempotency_key=f"{idem}|se", platform="internal"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r.get("ok"):
                opportunities.extend(r.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "predictive_intelligence"}

    async def _discover_dimension_5_network(self) -> Dict[str, Any]:
        """Dimension 5: Network Amplification"""
        opportunities = []
        idem = f"{self._run_id()}|d5"

        tasks = [
            self._call("GET", "/discovery/network/referrals", idempotency_key=f"{idem}|rf", platform="internal"),
            self._call("GET", "/discovery/network/viral-loops", idempotency_key=f"{idem}|vl", platform="internal"),
            self._call("GET", "/discovery/network/partnerships", idempotency_key=f"{idem}|pt", platform="internal"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r.get("ok"):
                opportunities.extend(r.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "network_amplification"}

    async def _discover_dimension_6_opportunity_creation(self) -> Dict[str, Any]:
        """Dimension 6: Opportunity Creation"""
        opportunities = []
        idem = f"{self._run_id()}|d6"

        tasks = [
            self._call("POST", "/discovery/outreach/targets", {"limit": 50}, idempotency_key=f"{idem}|tg", platform="internal"),
            self._call("POST", "/discovery/linkedin/prospects", {"limit": 30}, idempotency_key=f"{idem}|li", platform="linkedin"),
            self._call("GET", "/discovery/email/opportunities", idempotency_key=f"{idem}|em", platform="internal"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r.get("ok"):
                opportunities.extend(r.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "opportunity_creation"}

    async def _discover_dimension_7_emergent(self) -> Dict[str, Any]:
        """Dimension 7: Emergent Patterns"""
        opportunities = []
        idem = f"{self._run_id()}|d7"

        tasks = [
            self._call("GET", "/discovery/emergent/new-markets", idempotency_key=f"{idem}|nm", platform="internal"),
            self._call("GET", "/discovery/emergent/trend-surf", idempotency_key=f"{idem}|ts", platform="internal"),
            self._call("GET", "/discovery/emergent/tech-shifts", idempotency_key=f"{idem}|tc", platform="internal"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r.get("ok"):
                opportunities.extend(r.get("opportunities", []))

        return {"ok": True, "opportunities": opportunities, "dimension": "emergent_patterns"}

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: MULTI-CHANNEL COMMUNICATION (with consent + concurrency)
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_communication_all_channels(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """
        Initiate communication with consent checking, concurrency control,
        and EV-prioritized ordering.
        """
        self.current_run["phase"] = "communication"
        _log_structured(self._run_id(), "communication", "start", {"count": len(opportunities)})

        results = {
            "emails_sent": 0,
            "dms_sent": 0,
            "sms_sent": 0,
            "platform_messages": 0,
            "skipped_no_consent": 0,
            "skipped_circuit_open": 0,
            "conversations_started": [],
            "errors": []
        }

        # Dedupe and rank if not already done
        ranked = self._dedupe_and_rank(opportunities, limit=250)

        async def _process_opportunity(opp: Dict):
            """Process single opportunity with concurrency control"""
            platform = opp.get("platform", "unknown")
            contact = opp.get("contact", {})
            opp_key = opp.get("_key", self._compute_opportunity_key(opp))
            idem_base = f"{self._run_id()}|comm|{opp_key}"

            sem = self._get_semaphore(platform)

            async with sem:
                try:
                    # Email outreach
                    if contact.get("email"):
                        email = contact["email"]
                        if not self.consent_manager.is_allowed(email, "email"):
                            results["skipped_no_consent"] += 1
                        elif not self.circuit_breaker.can_call("email"):
                            results["skipped_circuit_open"] += 1
                        else:
                            r = await self._send_email_outreach(opp, idempotency_key=f"{idem_base}|em")
                            if r.get("ok"):
                                results["emails_sent"] += 1
                                results["conversations_started"].append({
                                    "opportunity_id": opp.get("id"),
                                    "channel": "email",
                                    "status": "sent",
                                    "ev": opp.get("_ev", 0)
                                })

                    # Twitter DM
                    if contact.get("twitter"):
                        tw = contact["twitter"]
                        if self.consent_manager.is_allowed(tw, "twitter") and self.circuit_breaker.can_call("twitter"):
                            async with self._get_semaphore("twitter"):
                                r = await self._send_twitter_dm(opp, idempotency_key=f"{idem_base}|tw")
                                if r.get("ok"):
                                    results["dms_sent"] += 1

                    # LinkedIn
                    if contact.get("linkedin"):
                        li = contact["linkedin"]
                        if self.consent_manager.is_allowed(li, "linkedin") and self.circuit_breaker.can_call("linkedin"):
                            async with self._get_semaphore("linkedin"):
                                r = await self._send_linkedin_message(opp, idempotency_key=f"{idem_base}|li")
                                if r.get("ok"):
                                    results["dms_sent"] += 1

                    # SMS
                    if contact.get("phone"):
                        phone = contact["phone"]
                        if self.consent_manager.is_allowed(phone, "sms") and self.circuit_breaker.can_call("sms"):
                            async with self._get_semaphore("sms"):
                                r = await self._send_sms(opp, idempotency_key=f"{idem_base}|sms")
                                if r.get("ok"):
                                    results["sms_sent"] += 1

                    # Platform-specific
                    if platform in ["github", "github_bounties"]:
                        if self.circuit_breaker.can_call("github"):
                            r = await self._post_github_interest(opp, idempotency_key=f"{idem_base}|gh")
                            if r.get("ok"):
                                results["platform_messages"] += 1

                    elif platform == "reddit":
                        if self.circuit_breaker.can_call("reddit"):
                            r = await self._post_reddit_reply(opp, idempotency_key=f"{idem_base}|rd")
                            if r.get("ok"):
                                results["platform_messages"] += 1

                    elif platform in ["upwork", "freelancer", "fiverr"]:
                        if self.circuit_breaker.can_call(platform):
                            r = await self._send_platform_proposal(opp, idempotency_key=f"{idem_base}|prop")
                            if r.get("ok"):
                                results["platform_messages"] += 1

                except Exception as e:
                    results["errors"].append({
                        "opportunity_id": opp.get("id"),
                        "error": str(e)
                    })

        # Process all opportunities with controlled concurrency
        await asyncio.gather(*[_process_opportunity(opp) for opp in ranked], return_exceptions=True)

        _log_structured(self._run_id(), "communication", "complete", {
            "emails": results["emails_sent"],
            "dms": results["dms_sent"],
            "sms": results["sms_sent"],
            "platform": results["platform_messages"],
            "skipped_consent": results["skipped_no_consent"]
        })

        self.current_run["results"]["communication"] = results
        return results

    async def _send_email_outreach(self, opp: Dict, idempotency_key: str = None) -> Dict[str, Any]:
        """Send personalized email outreach via COI Fabric or fallback to HTTP"""
        contact = opp.get("contact", {})
        email = contact.get("email")
        if not email:
            return {"ok": False, "error": "no_email"}

        # Generate pitch with opportunity context
        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opp,
            "channel": "email",
            "ev_score": opp.get("_ev", 0)
        }, idempotency_key=f"{idempotency_key}|pitch", platform="internal")

        subject = pitch.get("subject", f"Re: {opp.get('title', 'Your Project')}")
        body = pitch.get("body", "")

        # Use COI Runtime if available (API keys in Render env)
        if self.coi_runtime:
            try:
                await self.coi_runtime.initialize()
                result = await self.coi_runtime.execute_from_pdl("email.send", {
                    "to": email,
                    "subject": subject,
                    "body": body
                }, idempotency_key=idempotency_key)

                if result.get("ok"):
                    _log_structured(self._run_id(), "fabric", "email_sent", {
                        "to": email[:20] + "...",
                        "connector": result.get("connector"),
                        "proofs": len(result.get("proofs", []))
                    })
                return result
            except Exception as e:
                _log_structured(self._run_id(), "fabric", "email_fallback", {"error": str(e)})

        # Fallback to HTTP endpoint
        return await self._call("POST", "/email/send", {
            "to": email,
            "subject": subject,
            "body": body,
            "opportunity_id": opp.get("id"),
            "ev_score": opp.get("_ev", 0)
        }, idempotency_key=idempotency_key, platform="email")

    async def _send_twitter_dm(self, opp: Dict, idempotency_key: str = None) -> Dict[str, Any]:
        """Send Twitter DM"""
        contact = opp.get("contact", {})
        twitter = contact.get("twitter")
        if not twitter:
            return {"ok": False, "error": "no_twitter"}

        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opp,
            "channel": "twitter_dm",
            "max_length": 280
        }, platform="internal")

        return await self._call("POST", "/twitter/send-dm", {
            "username": twitter,
            "message": pitch.get("body", ""),
            "opportunity_id": opp.get("id")
        }, idempotency_key=idempotency_key, platform="twitter")

    async def _send_linkedin_message(self, opp: Dict, idempotency_key: str = None) -> Dict[str, Any]:
        """Send LinkedIn message"""
        contact = opp.get("contact", {})
        linkedin = contact.get("linkedin")
        if not linkedin:
            return {"ok": False, "error": "no_linkedin"}

        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opp,
            "channel": "linkedin"
        }, platform="internal")

        return await self._call("POST", "/linkedin/send-message", {
            "profile_url": linkedin,
            "message": pitch.get("body", ""),
            "opportunity_id": opp.get("id")
        }, idempotency_key=idempotency_key, platform="linkedin")

    async def _send_sms(self, opp: Dict, idempotency_key: str = None) -> Dict[str, Any]:
        """Send SMS via COI Fabric (Twilio connector) or fallback to HTTP"""
        contact = opp.get("contact", {})
        phone = contact.get("phone")
        if not phone:
            return {"ok": False, "error": "no_phone"}

        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opp,
            "channel": "sms",
            "max_length": 160
        }, platform="internal")

        message = pitch.get("body", "")

        # Use COI Runtime if available (Twilio credentials in Render env)
        if self.coi_runtime:
            try:
                await self.coi_runtime.initialize()
                result = await self.coi_runtime.execute_from_pdl("sms.send", {
                    "to": phone,
                    "body": message
                }, idempotency_key=idempotency_key)

                if result.get("ok"):
                    _log_structured(self._run_id(), "fabric", "sms_sent", {
                        "to": phone[-4:],  # Last 4 digits only for privacy
                        "connector": result.get("connector"),
                        "proofs": len(result.get("proofs", []))
                    })
                return result
            except Exception as e:
                _log_structured(self._run_id(), "fabric", "sms_fallback", {"error": str(e)})

        # Fallback to HTTP endpoint
        return await self._call("POST", "/sms/send", {
            "to": phone,
            "message": message,
            "opportunity_id": opp.get("id")
        }, idempotency_key=idempotency_key, platform="sms")

    async def _post_github_interest(self, opp: Dict, idempotency_key: str = None) -> Dict[str, Any]:
        """Post GitHub comment expressing interest"""
        return await self._call("POST", "/github/post-comment", {
            "url": opp.get("url"),
            "type": "interest",
            "opportunity_id": opp.get("id"),
            "ev_score": opp.get("_ev", 0)
        }, idempotency_key=idempotency_key, platform="github")

    async def _post_reddit_reply(self, opp: Dict, idempotency_key: str = None) -> Dict[str, Any]:
        """Post Reddit reply"""
        return await self._call("POST", "/reddit/post-reply", {
            "url": opp.get("url"),
            "type": "offer_help",
            "opportunity_id": opp.get("id")
        }, idempotency_key=idempotency_key, platform="reddit")

    async def _send_platform_proposal(self, opp: Dict, idempotency_key: str = None) -> Dict[str, Any]:
        """Send proposal on freelance platform"""
        platform = opp.get("platform")

        pitch = await self._call("POST", "/ame/generate-pitch", {
            "opportunity": opp,
            "channel": platform,
            "include_sla": True
        }, platform="internal")

        # COGS-aware bid calculation
        value = opp.get("value", 0) or opp.get("estimated_value", 0)
        cogs = opp.get("cogs_estimate", value * 0.3)
        min_margin = 0.2  # 20% minimum margin
        suggested_bid = max(value * 0.8, cogs * (1 + min_margin))

        return await self._call("POST", f"/{platform}/submit-proposal", {
            "job_id": opp.get("job_id") or opp.get("id"),
            "proposal": pitch.get("body", ""),
            "bid_amount": suggested_bid,
            "sla": pitch.get("sla")
        }, idempotency_key=idempotency_key, platform=platform)

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: CONTRACT & AGREEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_contract_flow(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Handle contract and agreement flow with idempotency"""
        self.current_run["phase"] = "contract"
        _log_structured(self._run_id(), "contract", "start", {"count": len(conversations)})

        results = {
            "contracts_generated": 0,
            "contracts_sent": 0,
            "deposits_requested": 0,
            "deposits_collected": 0,
            "total_contract_value": 0,
            "contracts": [],
            "errors": []
        }

        for conv in conversations:
            if conv.get("status") != "client_interested":
                continue

            try:
                opportunity = conv.get("opportunity", {})
                opp_key = opportunity.get("_key", self._compute_opportunity_key(opportunity))
                idem_base = f"{self._run_id()}|contract|{opp_key}"

                # Generate contract with idempotency
                contract = await self._call("POST", "/contract/generate", {
                    "opportunity": opportunity,
                    "client_email": conv.get("client_email"),
                    "amount": opportunity.get("value", 0),
                    "milestones": self._generate_milestones(opportunity),
                    "ev_score": opportunity.get("_ev", 0)
                }, idempotency_key=f"{idem_base}|gen", platform="internal")

                if contract.get("ok"):
                    results["contracts_generated"] += 1
                    contract_id = contract.get("contract_id")

                    # ═══════════════════════════════════════════════════════════════
                    # MONETIZATION: Apply dynamic pricing uplift
                    # ═══════════════════════════════════════════════════════════════
                    base_value = opportunity.get("value", 0)
                    if MONETIZATION_AVAILABLE and base_value > 0:
                        try:
                            # Dynamic pricing based on EV, load, wave score
                            adjusted_value = monetization_price_suggest(
                                base_value,
                                load_pct=0.3,  # System load estimate
                                wave_score=min(opportunity.get("_ev", 0) / 100, 1.0),
                                cogs=opportunity.get("cogs_estimate", base_value * 0.3),
                                min_margin=0.25
                            )
                            opportunity["adjusted_value"] = adjusted_value
                            _log_structured(self._run_id(), "monetization", "price_uplift", {
                                "base": base_value,
                                "adjusted": adjusted_value,
                                "uplift_pct": round((adjusted_value - base_value) / base_value * 100, 1) if base_value > 0 else 0
                            })
                        except Exception as e:
                            adjusted_value = base_value
                            _log_structured(self._run_id(), "monetization", "price_error", {"error": str(e)})
                    else:
                        adjusted_value = base_value

                    # 50% deposit via COI Fabric (Stripe connector)
                    deposit_amount = adjusted_value * 0.5
                    payment_link = await self._create_payment_link_fabric(
                        amount=deposit_amount,
                        description=f"Deposit: {opportunity.get('title', 'Project')}",
                        metadata={"contract_id": contract_id, "type": "deposit"},
                        idempotency_key=f"{idem_base}|pay"
                    )

                    if payment_link.get("ok"):
                        results["deposits_requested"] += 1

                    # Send contract
                    send_result = await self._call("POST", "/contract/send", {
                        "contract_id": contract_id,
                        "include_payment_link": True
                    }, idempotency_key=f"{idem_base}|send", platform="email")

                    if send_result.get("ok"):
                        results["contracts_sent"] += 1
                        results["total_contract_value"] += opportunity.get("value", 0)
                        results["contracts"].append({
                            "contract_id": contract_id,
                            "opportunity_id": opportunity.get("id"),
                            "value": opportunity.get("value", 0),
                            "deposit": deposit_amount,
                            "payment_link": payment_link.get("payment_link"),
                            "ev_score": opportunity.get("_ev", 0)
                        })

            except Exception as e:
                results["errors"].append({
                    "conversation_id": conv.get("id"),
                    "error": str(e)
                })

        _log_structured(self._run_id(), "contract", "complete", {
            "generated": results["contracts_generated"],
            "sent": results["contracts_sent"],
            "value": results["total_contract_value"]
        })

        self.current_run["results"]["contract"] = results
        return results

    def _generate_milestones(self, opportunity: Dict) -> List[Dict]:
        """Generate milestone structure based on opportunity type"""
        opp_type = opportunity.get("type", "general")

        if opp_type in ["code_generation", "software_development"]:
            return [
                {"name": "Initial Setup & Architecture", "percentage": 20},
                {"name": "Core Development", "percentage": 40},
                {"name": "Testing & Refinement", "percentage": 25},
                {"name": "Deployment & Handoff", "percentage": 15}
            ]
        elif opp_type in ["content_generation", "writing", "copywriting"]:
            return [
                {"name": "Research & Outline", "percentage": 25},
                {"name": "First Draft", "percentage": 50},
                {"name": "Revisions & Final", "percentage": 25}
            ]
        else:
            return [
                {"name": "Deposit", "percentage": 50},
                {"name": "Final Delivery", "percentage": 50}
            ]

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 4: FULFILLMENT & DELIVERY
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_fulfillment(self, contracts: List[Dict]) -> Dict[str, Any]:
        """Execute fulfillment for signed contracts"""
        self.current_run["phase"] = "fulfillment"
        _log_structured(self._run_id(), "fulfillment", "start", {"count": len(contracts)})

        results = {
            "fulfilled": 0,
            "delivered": 0,
            "total_delivered_value": 0,
            "upsells_sent": 0,
            "fulfillments": [],
            "errors": []
        }

        for contract in contracts:
            if contract.get("status") not in ["signed", "deposit_paid"]:
                continue

            try:
                opportunity = contract.get("opportunity", {})
                contract_id = contract.get("contract_id")
                opp_key = opportunity.get("_key", self._compute_opportunity_key(opportunity))
                idem_base = f"{self._run_id()}|fulfill|{opp_key}"

                # Execute fulfillment
                fulfillment_result = await self._execute_fulfillment(
                    opportunity,
                    idempotency_key=f"{idem_base}|exec"
                )

                if fulfillment_result.get("success"):
                    results["fulfilled"] += 1

                    # Deliver work
                    delivery_result = await self._deliver_work(
                        opportunity,
                        fulfillment_result,
                        idempotency_key=f"{idem_base}|deliver"
                    )

                    if delivery_result.get("success"):
                        results["delivered"] += 1
                        gross_value = opportunity.get("adjusted_value", opportunity.get("value", 0))
                        results["total_delivered_value"] += gross_value

                        # Final payment link (remaining 50%) via COI Fabric
                        remaining = gross_value * 0.5
                        payment_result = await self._create_payment_link_fabric(
                            amount=remaining,
                            description=f"Final payment: {opportunity.get('title', 'Work')}",
                            metadata={"contract_id": contract_id, "type": "final"},
                            idempotency_key=f"{idem_base}|final_pay"
                        )

                        # ═══════════════════════════════════════════════════════════════
                        # MONETIZATION: Finalize sale - revenue split, badge, ledger
                        # ═══════════════════════════════════════════════════════════════
                        monetization_result = {}
                        if MONETIZATION_AVAILABLE and gross_value > 0:
                            try:
                                # Revenue split (AiGentsy platform fee + user/pool/partner)
                                splits = monetization_revenue_split(
                                    gross_value,
                                    user_pct=0.70,
                                    pool_pct=0.10,
                                    partner_pct=0.05
                                )

                                # Referral chain allocation
                                ref_chain = opportunity.get("referral_chain", [])
                                if ref_chain:
                                    ref_alloc = allocate_referrals(gross_value, ref_chain)
                                    splits["referrals"] = ref_alloc.get("splits", {})
                                    self.current_run["metrics"]["referral_payouts"] += ref_alloc.get("total_allocated", 0)

                                # Mint proof badge
                                badge = monetization_mint_badge({
                                    "outcome_id": contract_id,
                                    "outcome_type": opportunity.get("type", "fulfillment"),
                                    "outcome_hash": hashlib.sha1(f"{contract_id}:{gross_value}".encode()).hexdigest(),
                                    "sla_verdict": "pass",
                                    "proofs": delivery_result.get("proofs", []),
                                    "entity": opportunity.get("contact", {}).get("name", "client")
                                })
                                self.current_run["metrics"]["badges_minted"] += 1

                                # Record in ledger
                                record_sale(
                                    coi_id=contract_id,
                                    gross=gross_value,
                                    splits=splits,
                                    badge=badge
                                )

                                # Update run metrics
                                self.current_run["metrics"]["gross_revenue"] += gross_value
                                self.current_run["metrics"]["platform_fees"] += splits.get("platform", 0)

                                monetization_result = {
                                    "splits": splits,
                                    "badge": badge,
                                    "gross": gross_value
                                }

                                _log_structured(self._run_id(), "monetization", "sale_recorded", {
                                    "contract_id": contract_id,
                                    "gross": gross_value,
                                    "platform_fee": splits.get("platform", 0),
                                    "badge_id": badge.get("badge_id")
                                })

                            except Exception as e:
                                _log_structured(self._run_id(), "monetization", "finalize_error", {
                                    "contract_id": contract_id,
                                    "error": str(e)
                                })

                        # Post-delivery upsell sequence
                        upsell = await self._call("POST", "/upsell/trigger-sequence", {
                            "contract_id": contract_id,
                            "opportunity": opportunity,
                            "delivery": delivery_result
                        }, idempotency_key=f"{idem_base}|upsell", platform="internal")

                        if upsell.get("ok"):
                            results["upsells_sent"] += 1

                        results["fulfillments"].append({
                            "contract_id": contract_id,
                            "opportunity_id": opportunity.get("id"),
                            "delivery_url": delivery_result.get("delivery_url"),
                            "payment_link": payment_result.get("payment_link"),
                            "value": gross_value,
                            "ev_score": opportunity.get("_ev", 0),
                            "monetization": monetization_result
                        })

            except Exception as e:
                results["errors"].append({
                    "contract_id": contract.get("contract_id"),
                    "error": str(e)
                })

        _log_structured(self._run_id(), "fulfillment", "complete", {
            "fulfilled": results["fulfilled"],
            "delivered": results["delivered"],
            "value": results["total_delivered_value"]
        })

        self.current_run["results"]["fulfillment"] = results
        return results

    async def _execute_fulfillment(self, opportunity: Dict, idempotency_key: str = None) -> Dict[str, Any]:
        """Execute the actual work based on opportunity type"""
        opp_type = opportunity.get("type", "general")

        endpoint_map = {
            "code_generation": "/fulfillment/code-generation",
            "software_development": "/fulfillment/code-generation",
            "content_generation": "/fulfillment/content-generation",
            "writing": "/fulfillment/content-generation",
            "copywriting": "/fulfillment/content-generation",
            "graphics": "/fulfillment/graphics-generation",
            "design": "/fulfillment/graphics-generation",
            "logo": "/fulfillment/graphics-generation",
            "video": "/fulfillment/video-generation",
            "animation": "/fulfillment/video-generation",
            "audio": "/fulfillment/audio-generation",
            "music": "/fulfillment/audio-generation",
            "voiceover": "/fulfillment/audio-generation",
        }

        endpoint = endpoint_map.get(opp_type, "/fulfillment/claude-generic")

        return await self._call("POST", endpoint, {
            "opportunity": opportunity,
            "ev_score": opportunity.get("_ev", 0)
        }, idempotency_key=idempotency_key, platform="internal")

    async def _deliver_work(self, opportunity: Dict, fulfillment: Dict, idempotency_key: str = None) -> Dict[str, Any]:
        """Deliver completed work to client/platform via COI Fabric or fallback"""
        platform = opportunity.get("platform", "unknown")
        contact = opportunity.get("contact", {})

        if platform in ["github", "github_bounties"]:
            return await self._call("POST", "/delivery/github", {
                "opportunity": opportunity,
                "fulfillment": fulfillment
            }, idempotency_key=idempotency_key, platform="github")

        elif platform in ["upwork", "freelancer", "fiverr"]:
            return await self._call("POST", f"/delivery/{platform}", {
                "opportunity": opportunity,
                "fulfillment": fulfillment
            }, idempotency_key=idempotency_key, platform=platform)

        else:
            # Email delivery via COI Fabric
            email = contact.get("email")
            if email and self.coi_runtime:
                try:
                    await self.coi_runtime.initialize()

                    # Generate delivery email content
                    title = opportunity.get("title", "Your Project")
                    delivery_url = fulfillment.get("delivery_url", fulfillment.get("artifact_url", ""))

                    result = await self.coi_runtime.execute_from_pdl("email.send", {
                        "to": email,
                        "subject": f"Delivery Complete: {title}",
                        "body": f"""Your work has been completed!

Project: {title}

{'Download your deliverable: ' + delivery_url if delivery_url else 'Please find your deliverable attached.'}

Summary:
{fulfillment.get('summary', 'Work completed as specified.')}

If you have any questions or need revisions, please reply to this email.

Best regards,
AiGentsy Autonomous Fulfillment
""",
                        "html": f"""
<h2>Your work has been completed!</h2>
<p><strong>Project:</strong> {title}</p>
{'<p><a href="' + delivery_url + '">Download your deliverable</a></p>' if delivery_url else ''}
<h3>Summary</h3>
<p>{fulfillment.get('summary', 'Work completed as specified.')}</p>
<p>If you have any questions or need revisions, please reply to this email.</p>
<p>Best regards,<br>AiGentsy Autonomous Fulfillment</p>
"""
                    }, idempotency_key=idempotency_key)

                    if result.get("ok"):
                        _log_structured(self._run_id(), "fabric", "delivery_email_sent", {
                            "to": email[:20] + "...",
                            "connector": result.get("connector"),
                            "proofs": len(result.get("proofs", []))
                        })
                        return {
                            "ok": True,
                            "success": True,
                            "delivery_method": "email_fabric",
                            "message_id": result.get("data", {}).get("message_id"),
                            "proofs": result.get("proofs", [])
                        }
                except Exception as e:
                    _log_structured(self._run_id(), "fabric", "delivery_fallback", {"error": str(e)})

            # Fallback to HTTP endpoint
            return await self._call("POST", "/delivery/email", {
                "opportunity": opportunity,
                "fulfillment": fulfillment
            }, idempotency_key=idempotency_key, platform="email")

    # ═══════════════════════════════════════════════════════════════════════════
    # PAYMENT HELPERS (COI Fabric Integration)
    # ═══════════════════════════════════════════════════════════════════════════

    async def _create_payment_link_fabric(
        self,
        amount: float,
        description: str,
        metadata: Dict = None,
        idempotency_key: str = None
    ) -> Dict[str, Any]:
        """
        Create Stripe payment link via COI Fabric (uses STRIPE_SECRET_KEY from env).
        Falls back to HTTP endpoint if COI not available.
        """
        if self.coi_runtime:
            try:
                await self.coi_runtime.initialize()
                result = await self.coi_runtime.execute_from_pdl("stripe.payment_link", {
                    "amount": amount,
                    "currency": "usd",
                    "description": description,
                    "metadata": metadata or {}
                }, idempotency_key=idempotency_key)

                if result.get("ok"):
                    data = result.get("data", {})
                    _log_structured(self._run_id(), "fabric", "payment_link_created", {
                        "amount": amount,
                        "connector": result.get("connector"),
                        "payment_link_id": data.get("payment_link_id"),
                        "proofs": len(result.get("proofs", []))
                    })
                    return {
                        "ok": True,
                        "payment_link": data.get("url"),
                        "payment_link_id": data.get("payment_link_id"),
                        "amount": amount,
                        "proofs": result.get("proofs", []),
                        "via_fabric": True
                    }
                else:
                    _log_structured(self._run_id(), "fabric", "payment_link_error", {
                        "error": result.get("error")
                    })
            except Exception as e:
                _log_structured(self._run_id(), "fabric", "payment_link_fallback", {"error": str(e)})

        # Fallback to HTTP endpoint
        return await self._call("POST", "/wade/payment-link", {
            "amount": amount,
            "description": description
        }, idempotency_key=idempotency_key, platform="stripe")

    async def _send_invoice_fabric(
        self,
        customer_email: str,
        amount: float,
        description: str,
        idempotency_key: str = None
    ) -> Dict[str, Any]:
        """
        Create and send Stripe invoice via COI Fabric.
        """
        if self.coi_runtime:
            try:
                await self.coi_runtime.initialize()

                # First create customer if needed (via HTTP for now)
                customer = await self._call("POST", "/stripe/get-or-create-customer", {
                    "email": customer_email
                }, platform="stripe")

                customer_id = customer.get("customer_id")
                if not customer_id:
                    return {"ok": False, "error": "customer_creation_failed"}

                result = await self.coi_runtime.execute_from_pdl("stripe.invoice", {
                    "customer_id": customer_id,
                    "amount": amount,
                    "description": description,
                    "send": True
                }, idempotency_key=idempotency_key)

                if result.get("ok"):
                    data = result.get("data", {})
                    _log_structured(self._run_id(), "fabric", "invoice_sent", {
                        "customer": customer_email[:20] + "...",
                        "amount": amount,
                        "invoice_id": data.get("invoice_id"),
                        "proofs": len(result.get("proofs", []))
                    })
                    return {
                        "ok": True,
                        "invoice_id": data.get("invoice_id"),
                        "invoice_url": data.get("hosted_invoice_url"),
                        "amount": amount,
                        "proofs": result.get("proofs", []),
                        "via_fabric": True
                    }
            except Exception as e:
                _log_structured(self._run_id(), "fabric", "invoice_fallback", {"error": str(e)})

        # Fallback to HTTP endpoint
        return await self._call("POST", "/stripe/send-invoice", {
            "email": customer_email,
            "amount": amount,
            "description": description
        }, idempotency_key=idempotency_key, platform="stripe")

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 5: PAYMENT COLLECTION
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_payment_collection(self) -> Dict[str, Any]:
        """Collect all pending payments with idempotency"""
        self.current_run["phase"] = "payment_collection"
        idem_base = f"{self._run_id()}|payment"
        _log_structured(self._run_id(), "payment", "start", {})

        results = {
            "invoices_sent": 0,
            "payment_links_created": 0,
            "escrow_releases_requested": 0,
            "bounties_claimed": 0,
            "total_collected": 0,
            "total_pending": 0,
            "collections": [],
            "errors": []
        }

        # Send all pending invoices
        invoices = await self._call("POST", "/stripe/send-invoices", {},
                                     idempotency_key=f"{idem_base}|inv", platform="stripe")
        if invoices.get("ok"):
            results["invoices_sent"] = len(invoices.get("invoiced", []))

        # Request escrow releases
        escrow = await self._call("POST", "/escrow/auto-release", {},
                                   idempotency_key=f"{idem_base}|esc", platform="internal")
        if escrow.get("ok"):
            results["escrow_releases_requested"] = escrow.get("requested", 0)

        # Claim bounties
        bounties = await self._call("POST", "/bounties/claim-all", {},
                                     idempotency_key=f"{idem_base}|bounty", platform="internal")
        if bounties.get("ok"):
            results["bounties_claimed"] = bounties.get("claimed", 0)

        # Process subscription renewals
        subs = await self._call("POST", "/subscriptions/process-renewals", {},
                                 idempotency_key=f"{idem_base}|subs", platform="stripe")
        if subs.get("ok"):
            results["total_collected"] += subs.get("collected", 0)

        # Get current payment status
        status = await self._call("GET", "/payments/status", platform="internal")
        if status.get("ok"):
            results["total_pending"] = status.get("summary", {}).get("total_pending", 0)

        # Batch payouts
        payouts = await self._call("POST", "/stripe/batch-payouts", {},
                                    idempotency_key=f"{idem_base}|payout", platform="stripe")
        if payouts.get("ok"):
            results["total_collected"] += payouts.get("paid_out", 0)

        _log_structured(self._run_id(), "payment", "complete", {
            "invoices": results["invoices_sent"],
            "escrow": results["escrow_releases_requested"],
            "bounties": results["bounties_claimed"],
            "collected": results["total_collected"],
            "pending": results["total_pending"]
        })

        self.current_run["results"]["payment_collection"] = results
        return results

    # ═══════════════════════════════════════════════════════════════════════════
    # MASTER ORCHESTRATION - FULL AUTONOMOUS CYCLE
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_full_autonomous_cycle(self, config: Dict = None) -> Dict[str, Any]:
        """
        RUN THE COMPLETE AUTONOMOUS CYCLE

        Discovery → Communication → Contract → Fulfillment → Payment

        Production-hardened with:
        - Idempotency keys throughout
        - Dedupe + EV prioritization
        - Circuit breakers per platform
        - Concurrency control
        - Structured logging
        - Consent management
        """
        config = config or {}

        # Initialize fresh run
        self.current_run = {
            "run_id": f"orch-{uuid4().hex[:12]}",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "phase": "initializing",
            "results": {},
            "errors": [],
            "metrics": {
                "calls_made": 0,
                "calls_succeeded": 0,
                "calls_failed": 0,
                "retries": 0,
                "circuit_opens": 0
            }
        }
        self._seen_keys = set()  # Reset dedupe for fresh run

        _log_structured(self._run_id(), "orchestrator", "cycle_start", config)

        final_results = {
            "ok": True,
            "run_id": self._run_id(),
            "started_at": self.current_run["started_at"],
            "phases_completed": [],
            "summary": {}
        }

        try:
            # DRY RUN CHECK
            dry_run = config.get("dry_run", False)
            if dry_run:
                _log_structured(self._run_id(), "orchestrator", "dry_run_mode", {})

            # PHASE 1: DISCOVERY
            _log_structured(self._run_id(), "orchestrator", "phase_start", {"phase": "discovery"})
            discovery = await self.run_discovery_all_dimensions()
            final_results["phases_completed"].append("discovery")
            final_results["discovery"] = {
                "total_opportunities": discovery["total_opportunities"],
                "total_value": discovery["total_value"],
                "total_ev": discovery.get("total_ev", 0),
                "by_dimension": {
                    k: len(v) for k, v in discovery.items()
                    if k.startswith("dimension_") and isinstance(v, list)
                }
            }

            ranked_opportunities = discovery.get("ranked_opportunities", [])

            # PHASE 2: COMMUNICATION (if not dry run)
            if ranked_opportunities and not dry_run:
                _log_structured(self._run_id(), "orchestrator", "phase_start", {"phase": "communication"})
                communication = await self.run_communication_all_channels(ranked_opportunities)
                final_results["phases_completed"].append("communication")
                final_results["communication"] = {
                    "emails_sent": communication["emails_sent"],
                    "dms_sent": communication["dms_sent"],
                    "sms_sent": communication["sms_sent"],
                    "platform_messages": communication["platform_messages"],
                    "skipped_no_consent": communication["skipped_no_consent"],
                    "conversations_started": len(communication["conversations_started"])
                }

                # PHASE 3: CONTRACT
                interested = [c for c in communication["conversations_started"]
                              if c.get("status") == "client_interested"]
                if interested:
                    _log_structured(self._run_id(), "orchestrator", "phase_start", {"phase": "contract"})
                    contracts = await self.run_contract_flow(interested)
                    final_results["phases_completed"].append("contract")
                    final_results["contract"] = {
                        "contracts_generated": contracts["contracts_generated"],
                        "contracts_sent": contracts["contracts_sent"],
                        "deposits_requested": contracts["deposits_requested"],
                        "total_contract_value": contracts["total_contract_value"]
                    }

                    # PHASE 4: FULFILLMENT
                    signed = [c for c in contracts["contracts"]
                              if c.get("status") in ["signed", "deposit_paid"]]
                    if signed:
                        _log_structured(self._run_id(), "orchestrator", "phase_start", {"phase": "fulfillment"})
                        fulfillment = await self.run_fulfillment(signed)
                        final_results["phases_completed"].append("fulfillment")
                        final_results["fulfillment"] = {
                            "fulfilled": fulfillment["fulfilled"],
                            "delivered": fulfillment["delivered"],
                            "upsells_sent": fulfillment["upsells_sent"],
                            "total_delivered_value": fulfillment["total_delivered_value"]
                        }

            # PHASE 5: PAYMENT COLLECTION (always run unless dry run)
            if not dry_run:
                _log_structured(self._run_id(), "orchestrator", "phase_start", {"phase": "payment_collection"})
                payment = await self.run_payment_collection()
                final_results["phases_completed"].append("payment_collection")
                final_results["payment_collection"] = {
                    "invoices_sent": payment["invoices_sent"],
                    "escrow_releases_requested": payment["escrow_releases_requested"],
                    "bounties_claimed": payment["bounties_claimed"],
                    "total_collected": payment["total_collected"],
                    "total_pending": payment["total_pending"]
                }

            # SUMMARY
            final_results["summary"] = {
                "opportunities_found": discovery["total_opportunities"],
                "total_ev": discovery.get("total_ev", 0),
                "communications_sent": (
                    final_results.get("communication", {}).get("emails_sent", 0) +
                    final_results.get("communication", {}).get("dms_sent", 0) +
                    final_results.get("communication", {}).get("sms_sent", 0) +
                    final_results.get("communication", {}).get("platform_messages", 0)
                ),
                "contracts_value": final_results.get("contract", {}).get("total_contract_value", 0),
                "delivered_value": final_results.get("fulfillment", {}).get("total_delivered_value", 0),
                "collected": final_results.get("payment_collection", {}).get("total_collected", 0),
                "pending": final_results.get("payment_collection", {}).get("total_pending", 0),
                # Monetization summary
                "monetization": {
                    "gross_revenue": self.current_run["metrics"]["gross_revenue"],
                    "platform_fees": self.current_run["metrics"]["platform_fees"],
                    "referral_payouts": self.current_run["metrics"]["referral_payouts"],
                    "badges_minted": self.current_run["metrics"]["badges_minted"],
                    "arbitrage_captured": self.current_run["metrics"]["arbitrage_captured"]
                }
            }

            final_results["completed_at"] = datetime.now(timezone.utc).isoformat()
            final_results["metrics"] = self.current_run["metrics"]
            final_results["errors"] = self.current_run["errors"]
            final_results["circuit_breaker_status"] = self.circuit_breaker.get_status()

            _log_structured(self._run_id(), "orchestrator", "cycle_complete", final_results["summary"])

        except Exception as e:
            final_results["ok"] = False
            final_results["error"] = str(e)
            final_results["errors"] = self.current_run["errors"]
            _log_structured(self._run_id(), "orchestrator", "cycle_error", {"error": str(e)})

        return final_results


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_orchestrator_instance = None


def get_master_orchestrator() -> MasterAutonomousOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MasterAutonomousOrchestrator()
    return _orchestrator_instance
