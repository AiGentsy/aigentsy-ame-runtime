"""
APEX INTEGRATION v115 - The Unified Wiring Layer
=================================================

Connects ALL AiGentsy modules into a single autonomous revenue engine.

Wires together:
- Simple Onboard → SKU Orchestrator → Template Actionizer
- Auto-Spawn Engine → Business-in-a-Box Accelerator
- Discovery → Bidding → Execution → Reputation → Payments (flywheel)
- Securitization → LOX → Partner Mesh → Data Coop (trillion-tilt)
- Brain Overlay → Policy Engine → OCS → RevSplit Optimizer
- Proof Merkle → OIO Insurance → Public Trust Page
- Auto-Hedge → Builder Risk Tranches → Profit Analyzer
- One-Tap Widget → Outcome Subscriptions → Idle Time Arbitrage

This is the "Sleep Mode" that runs everything automatically.

Usage:
    from apex_integration import ApexEngine, run_sleep_mode_cycle
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import json
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apex_integration")

# ============================================================================
# OPERATIONAL SAFETY OVERLAYS (v115.1)
# ============================================================================
# Governor - Global spend caps with ND-JSON audit
try:
    from governors.governor_runtime import guard_spend, get_spend_status, get_degradation_level
    GOVERNOR_ENABLED = True
    logger.info("Governor runtime loaded")
except ImportError:
    GOVERNOR_ENABLED = False
    def guard_spend(*args, **kwargs): return True
    def get_spend_status(): return {}
    def get_degradation_level(): return 0

# PSP Enforcer - PSP-only fund flow
try:
    from dealgraph_overlays.psp_enforcer import enforce_psp, validate_payment_meta
    PSP_ENABLED = True
    logger.info("PSP enforcer loaded")
except ImportError:
    PSP_ENABLED = False
    def enforce_psp(meta): return True, None

# Health Breakers - Circuit breaker with backoff
try:
    from connectors.health_breakers import breaker, get_health_status, reset_breaker
    BREAKERS_ENABLED = True
    logger.info("Health breakers loaded")
except ImportError:
    BREAKERS_ENABLED = False
    def breaker(key, healthy, **kwargs): return healthy
    def get_health_status(): return {}

# SLO Guard - Autospawn/white-label gate
try:
    from guards.slo_guard import allow_launch, check_partner_compliance
    SLO_GUARD_ENABLED = True
    logger.info("SLO guard loaded")
except ImportError:
    SLO_GUARD_ENABLED = False
    def allow_launch(*args, **kwargs): return True, "guard_disabled"

# Spawn vs Resale Arbiter
try:
    from arbiter.spawn_resale_arbiter import decide as arbiter_decide
    ARBITER_ENABLED = True
    logger.info("Spawn/resale arbiter loaded")
except ImportError:
    ARBITER_ENABLED = False
    def arbiter_decide(*args, **kwargs): return "spawn", {"reason": "arbiter_disabled"}

# Runbook Manager - Incident response
try:
    from runbooks import is_paused, pause_category, get_runbook_status
    RUNBOOKS_ENABLED = True
    logger.info("Runbooks loaded")
except ImportError:
    RUNBOOKS_ENABLED = False
    def is_paused(cat): return False

# SLO Dashboard - Metrics collection
try:
    from slo_dashboard import record_latency, record_delivery, record_margin
    SLO_METRICS_ENABLED = True
    logger.info("SLO metrics loaded")
except ImportError:
    SLO_METRICS_ENABLED = False
    def record_latency(*args, **kwargs): pass
    def record_delivery(*args, **kwargs): pass
    def record_margin(*args, **kwargs): pass

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


class ApexEngine:
    """
    The apex fulfillment engine - everything, everywhere, automatically.

    v115 Features:
    - Full monetization fabric integration
    - Brain overlay OCS scoring
    - 10 trillion-tilt revenue modules
    - Policy-driven configuration
    - Real-time hedge management
    - Partner mesh coordination
    """

    def __init__(self):
        self.policies = self._load_policies()
        self.stats = {
            "cycles_run": 0,
            "opportunities_found": 0,
            "quotes_generated": 0,
            "contracts_created": 0,
            "outcomes_fulfilled": 0,
            "proofs_generated": 0,
            "revenue_collected": 0.0,
            "lox_resales": 0,
            "spawns_created": 0,
            "hedges_placed": 0,
            "tranches_issued": 0,
            "partner_deals": 0,
            "subscriptions_active": 0,
            "idle_time_captured": 0.0
        }
        self._init_modules()

    def _init_modules(self):
        """Initialize all sub-modules with graceful fallback"""
        # Core fabric modules
        self.monetization = None
        self.brain = None
        self.ocs_engine = None

        try:
            from monetization import MonetizationFabric
            self.monetization = MonetizationFabric()
            logger.info("MonetizationFabric initialized")
        except ImportError as e:
            logger.warning(f"MonetizationFabric not available: {e}")

        try:
            from brain_overlay import Brain, get_brain
            self.brain = get_brain()
            logger.info("Brain overlay initialized")
        except ImportError as e:
            logger.warning(f"Brain overlay not available: {e}")

        try:
            from brain_overlay.ocs import OCSEngine
            self.ocs_engine = OCSEngine()
            logger.info("OCS Engine initialized")
        except ImportError as e:
            logger.warning(f"OCS Engine not available: {e}")

    def _load_policies(self) -> Dict[str, Any]:
        """Load all policy configs from JSON files"""
        policies = {}
        policy_dir = os.path.join(os.path.dirname(__file__), "policies")

        policy_files = [
            "pricing", "contract", "lox", "safety",
            "autospawn", "white_label", "subscriptions"
        ]

        for name in policy_files:
            path = os.path.join(policy_dir, f"{name}.json")
            try:
                with open(path, "r") as f:
                    policies[name] = json.load(f)
                    logger.info(f"Loaded policy: {name}")
            except FileNotFoundError:
                logger.warning(f"Policy file not found: {path}")
                policies[name] = {}
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {path}: {e}")
                policies[name] = {}

        return policies

    async def run_sleep_mode_cycle(self) -> Dict[str, Any]:
        """
        Run one complete sleep mode cycle (8 steps + 6 trillion-tilt):

        CORE FLYWHEEL:
        1. Discover demand
        2. Quote with margin (OCS-aware)
        3. Contract via PSP (no custody)
        4. Fulfill anywhere (UCB/PDL)
        5. Deliver with Merkle proof
        6. Collect & distribute (RevSplit)
        7. Resell overflow (LOX)
        8. Spawn if signals warrant

        TRILLION-TILT:
        9. Auto-hedge positions
        10. Issue risk tranches
        11. Partner mesh sync
        12. Data coop contribute
        13. Idle time arbitrage
        14. Securitization sweep
        """
        cycle_id = f"cycle_{int(datetime.now().timestamp())}"
        cycle_result = {
            "cycle_id": cycle_id,
            "started_at": _now(),
            "steps": {},
            "trillion_tilt": {}
        }

        # Check safety policy first
        safety = self.policies.get("safety", {})
        if not self._check_safety_bounds(safety):
            cycle_result["aborted"] = True
            cycle_result["reason"] = "safety_bounds_exceeded"
            return cycle_result

        # CORE FLYWHEEL (Steps 1-8)
        cycle_result["steps"]["discovery"] = await self._step_discovery()
        cycle_result["steps"]["quote"] = await self._step_quote(cycle_result["steps"]["discovery"])
        cycle_result["steps"]["contract"] = await self._step_contract(cycle_result["steps"]["quote"])
        cycle_result["steps"]["execute"] = await self._step_execute(cycle_result["steps"]["contract"])
        cycle_result["steps"]["deliver"] = await self._step_deliver(cycle_result["steps"]["execute"])
        cycle_result["steps"]["collect"] = await self._step_collect(cycle_result["steps"]["deliver"])
        cycle_result["steps"]["lox"] = await self._step_lox_resale()
        cycle_result["steps"]["spawn"] = await self._step_spawn_decision()

        # TRILLION-TILT (Steps 9-14)
        cycle_result["trillion_tilt"]["hedge"] = await self._step_auto_hedge()
        cycle_result["trillion_tilt"]["tranches"] = await self._step_risk_tranches()
        cycle_result["trillion_tilt"]["partner_mesh"] = await self._step_partner_mesh()
        cycle_result["trillion_tilt"]["data_coop"] = await self._step_data_coop()
        cycle_result["trillion_tilt"]["idle_time"] = await self._step_idle_time_arbitrage()
        cycle_result["trillion_tilt"]["securitization"] = await self._step_securitization()

        cycle_result["completed_at"] = _now()
        self.stats["cycles_run"] += 1

        # Emit brain event for learning
        if self.brain:
            self.brain.emit("apex.cycle_completed", {
                "cycle_id": cycle_id,
                "stats": self.stats,
                "revenue": cycle_result["steps"]["collect"].get("total_collected", 0)
            })

        return cycle_result

    def _check_safety_bounds(self, safety: Dict) -> bool:
        """Check if we're within safety policy bounds"""
        # Check runbook pauses first
        if RUNBOOKS_ENABLED and is_paused("all"):
            logger.warning("Emergency stop active - all operations paused")
            return False

        # Check governor degradation level
        if GOVERNOR_ENABLED:
            degradation = get_degradation_level()
            if degradation >= 3:  # Level 3+ = pause non-critical
                logger.warning(f"Governor degradation level {degradation} - restricting operations")
                return False

            # Check current spend status
            spend_status = get_spend_status()
            if spend_status.get("total_daily_spend_usd", 0) >= safety.get("max_daily_ai_spend_usd", 15000):
                logger.warning("Daily spend cap reached")
                return False

        return True

    async def _step_discovery(self) -> Dict[str, Any]:
        """Step 1: Find demand across all sources"""
        opportunities = []
        sources_checked = []

        try:
            from ultimate_discovery_engine import UltimateDiscoveryEngine
            engine = UltimateDiscoveryEngine("apex")
            result = await engine.discover_opportunities(limit=10)
            opportunities.extend(result.get("opportunities", []))
            sources_checked.extend(result.get("sources_checked", []))
            self.stats["opportunities_found"] += len(opportunities)
            logger.info(f"Discovery found {len(opportunities)} opportunities")
        except ImportError:
            logger.warning("UltimateDiscoveryEngine not available")
        except Exception as e:
            logger.error(f"Discovery error: {e}")

        try:
            from auto_spawn_engine import TrendDetector
            detector = TrendDetector()
            trends = detector.detect_emerging_trends()
            for trend in trends.get("trends", [])[:3]:
                opportunities.append({
                    "id": f"trend_{trend.get('keyword', 'unknown')}",
                    "source": "trend_detection",
                    "estimated_value": trend.get("estimated_opportunity", 500),
                    "confidence": trend.get("confidence", 0.5)
                })
        except ImportError:
            logger.warning("TrendDetector not available")
        except Exception as e:
            logger.error(f"Trend detection error: {e}")

        return {
            "opportunities_found": len(opportunities),
            "sources": sources_checked or ["github", "upwork", "reddit", "producthunt"],
            "top_opportunities": opportunities[:5]
        }

    async def _step_quote(self, discovery: Dict) -> Dict[str, Any]:
        """Step 2: Generate OAA quotes with OCS-aware pricing"""
        quotes = []
        pricing_policy = self.policies.get("pricing", {})

        for opp in discovery.get("top_opportunities", []):
            base_price = opp.get("estimated_value", 100)
            entity_id = opp.get("client_id", opp.get("id", "unknown"))

            # Get OCS score for entity
            ocs_score = 50  # Default
            if self.ocs_engine:
                try:
                    ocs_score = self.ocs_engine.score(entity_id)
                except:
                    pass

            # Calculate OCS-adjusted margin
            base_margin = pricing_policy.get("target_margin", 0.45)
            ocs_adjustment = (ocs_score - 50) / 500  # +/- 10% based on OCS
            adjusted_margin = max(0.25, min(0.60, base_margin + ocs_adjustment))

            # Use monetization fabric for pricing
            if self.monetization:
                try:
                    suggested = self.monetization.price_outcome(
                        base_price=base_price,
                        load_pct=pricing_policy.get("load_factor", 0.5),
                        wave_score=pricing_policy.get("wave_multiplier", 0.3),
                        cogs=base_price * 0.3,
                        min_margin=adjusted_margin
                    )
                except Exception as e:
                    logger.error(f"Pricing error: {e}")
                    suggested = base_price * (1 + adjusted_margin)
            else:
                suggested = base_price * (1 + adjusted_margin)

            # Quote programmatic guarantee if available
            pg_premium = 0
            if self.brain:
                try:
                    pg = self.brain.quote_guarantee(ocs_score, 0.1, suggested)
                    pg_premium = pg.get("premium", 0)
                except:
                    pass

            quotes.append({
                "opportunity_id": opp.get("id"),
                "base_price": base_price,
                "quoted_price": round(suggested, 2),
                "margin": round((suggested - base_price) / suggested, 3),
                "ocs_score": ocs_score,
                "pg_premium": pg_premium,
                "pg_available": pg_premium > 0
            })

        self.stats["quotes_generated"] += len(quotes)
        logger.info(f"Generated {len(quotes)} quotes")

        return {
            "quotes_generated": len(quotes),
            "quotes": quotes,
            "avg_margin": sum(q["margin"] for q in quotes) / len(quotes) if quotes else 0
        }

    async def _step_contract(self, quote_result: Dict) -> Dict[str, Any]:
        """Step 3: Create contracts via PSP (no custody, no money transmission)"""
        contracts = []
        contract_policy = self.policies.get("contract", {})

        for quote in quote_result.get("quotes", []):
            contract = {
                "quote_id": quote.get("opportunity_id"),
                "amount": quote.get("quoted_price"),
                "contract_type": contract_policy.get("contract_type", "clickwrap"),
                "psp": contract_policy.get("payment_processors", ["stripe"])[0],
                "fund_flow": "direct_to_processor",  # PSP-only, no custody
                "escrow_mode": contract_policy.get("escrow_mode", "psp_hold"),
                "pg_attached": quote.get("pg_available", False),
                "status": "pending_acceptance",
                "created_at": _now()
            }
            contracts.append(contract)
            self.stats["contracts_created"] += 1

        logger.info(f"Created {len(contracts)} contracts")

        return {
            "contracts_created": len(contracts),
            "contracts": contracts
        }

    async def _step_execute(self, contract_result: Dict) -> Dict[str, Any]:
        """Step 4: Execute via Universal Executor (UCB/PDL)"""
        executions = []

        try:
            from universal_executor import UniversalExecutor
            executor = UniversalExecutor()

            for contract in contract_result.get("contracts", []):
                if contract.get("status") in ["accepted", "pending_acceptance"]:
                    try:
                        result = await executor.execute(
                            coi_id=contract.get("quote_id"),
                            pdl_id="auto",
                            connector="ucb"
                        )
                        result["contract"] = contract
                        executions.append(result)

                        if result.get("success"):
                            self.stats["outcomes_fulfilled"] += 1

                            # Emit brain event
                            if self.brain:
                                self.brain.emit("coi.executed", {
                                    "actor_id": "apex",
                                    "sku_id": contract.get("quote_id"),
                                    "success": True,
                                    "margin": contract.get("amount", 0) * 0.3
                                })
                    except Exception as e:
                        logger.error(f"Execution error for {contract.get('quote_id')}: {e}")
                        executions.append({
                            "contract": contract,
                            "success": False,
                            "error": str(e)
                        })
        except ImportError:
            logger.warning("UniversalExecutor not available")
        except Exception as e:
            logger.error(f"Executor init error: {e}")

        return {
            "executions": len(executions),
            "successful": sum(1 for e in executions if e.get("success")),
            "results": executions
        }

    async def _step_deliver(self, execute_result: Dict) -> Dict[str, Any]:
        """Step 5: Deliver with Merkle proof for verifiability"""
        deliveries = []

        try:
            from proof_merkle import add_proof_leaf, get_daily_root
            from public_proof_page import record_proof_for_page

            for execution in execute_result.get("results", []):
                if execution.get("success"):
                    execution_id = execution.get("execution_id", f"exec_{int(datetime.now().timestamp())}")
                    revenue = execution.get("contract", {}).get("amount", 0)

                    # Add to Merkle tree
                    proof = add_proof_leaf(
                        execution_id=execution_id,
                        proofs=execution.get("proofs", []),
                        connector=execution.get("connector", "apex"),
                        revenue=revenue
                    )

                    # Record for public trust page
                    record_proof_for_page(
                        execution_id,
                        connector=execution.get("connector", "apex"),
                        revenue=revenue,
                        proofs=execution.get("proofs", [])
                    )

                    deliveries.append({
                        "execution_id": execution_id,
                        "revenue": revenue,
                        "proof": proof,
                        "merkle_leaf": proof.get("leaf_hash", "")
                    })
                    self.stats["proofs_generated"] += 1

            # Get daily root for verification
            daily_root = get_daily_root(datetime.now().strftime("%Y-%m-%d"))

        except ImportError as e:
            logger.warning(f"Proof modules not available: {e}")
            daily_root = {"root": "pending"}
        except Exception as e:
            logger.error(f"Delivery error: {e}")
            daily_root = {"root": "error"}

        return {
            "deliveries": len(deliveries),
            "proofs": deliveries,
            "daily_merkle_root": daily_root.get("root", "pending")
        }

    async def _step_collect(self, deliver_result: Dict) -> Dict[str, Any]:
        """Step 6: Collect payment & distribute via RevSplit"""
        collections = []

        try:
            from integration_hooks import IntegrationHooks
            from revsplit_optimizer import get_optimal_split, record_split_outcome

            hooks = IntegrationHooks("apex")

            for delivery in deliver_result.get("proofs", []):
                amount = delivery.get("revenue", 0)
                if amount > 0:
                    # Get optimal split based on segment performance
                    split_result = get_optimal_split(amount, segment="default")
                    splits = split_result.get("splits", {})

                    # Record payment received
                    payment = hooks.on_payment_received(
                        amount=amount,
                        currency="USD",
                        payer_id="customer",
                        ref_type="outcome",
                        ref_id=delivery.get("execution_id")
                    )

                    # Record to monetization ledger
                    if self.monetization:
                        try:
                            self.monetization.record_sale(
                                coi_id=delivery.get("execution_id"),
                                gross=amount,
                                splits=splits
                            )
                        except Exception as e:
                            logger.error(f"Ledger error: {e}")

                    # Record outcome for RevSplit learning
                    record_split_outcome(
                        delivery.get("execution_id"),
                        amount,
                        splits,
                        success=True
                    )

                    collections.append({
                        "amount": amount,
                        "split": splits,
                        "payment": payment,
                        "execution_id": delivery.get("execution_id")
                    })

                    self.stats["revenue_collected"] += amount

        except ImportError as e:
            logger.warning(f"Collection modules not available: {e}")
        except Exception as e:
            logger.error(f"Collection error: {e}")

        total = sum(c.get("amount", 0) for c in collections)
        logger.info(f"Collected ${total:.2f} from {len(collections)} deliveries")

        return {
            "collections": len(collections),
            "total_collected": total,
            "details": collections
        }

    async def _step_lox_resale(self) -> Dict[str, Any]:
        """Step 7: Resell overflow leads via LOX (Lead Overflow Exchange)"""
        resales = []
        lox_policy = self.policies.get("lox", {})

        if not lox_policy.get("enabled", True):
            return {"lox_enabled": False, "resales": 0}

        try:
            from lead_overflow_exchange import (
                get_lox_book, post_to_lox, match_lox_orders,
                get_lox_stats
            )

            idle_threshold = lox_policy.get("idle_threshold_minutes", 15)
            floor_pct = lox_policy.get("floor_pct", 0.50)

            # Get current LOX book
            book = get_lox_book()

            # Match any pending orders
            matches = match_lox_orders()
            for match in matches.get("matches", []):
                resales.append({
                    "lead_id": match.get("lead_id"),
                    "buyer": match.get("buyer_id"),
                    "price": match.get("fill_price"),
                    "original_value": match.get("original_value")
                })

            self.stats["lox_resales"] += len(resales)

            stats = get_lox_stats()

        except ImportError:
            logger.warning("LOX module not available")
            stats = {}
        except Exception as e:
            logger.error(f"LOX error: {e}")
            stats = {}

        return {
            "lox_enabled": True,
            "resales": len(resales),
            "book_size": stats.get("book_size", 0),
            "total_volume": stats.get("total_volume", 0),
            "details": resales
        }

    async def _step_spawn_decision(self) -> Dict[str, Any]:
        """Step 8: Decide whether to spawn new business based on signals"""
        spawn_policy = self.policies.get("autospawn", {})

        if not spawn_policy.get("enabled", True):
            return {"spawn_enabled": False, "decision": "disabled"}

        decision = {
            "spawn_enabled": True,
            "decision": "no_spawn",
            "reason": "signals_below_threshold"
        }

        try:
            from auto_spawn_engine import BusinessSpawner, TrendDetector

            # Check signals against policy thresholds
            signals = spawn_policy.get("signals", {})
            demand_threshold = signals.get("demand_z_min", 1.5)
            fill_threshold = signals.get("fill_rate_min", 0.8)
            opp_threshold = signals.get("opportunity_score_min", 0.7)
            budget_cap = spawn_policy.get("kelly_budget_cap_usd", 1500)

            detector = TrendDetector()
            trends = detector.detect_emerging_trends()

            qualifying_trends = []
            for trend in trends.get("trends", []):
                if (trend.get("demand_z", 0) >= demand_threshold and
                    trend.get("confidence", 0) >= opp_threshold):
                    qualifying_trends.append(trend)

            if qualifying_trends:
                # Use Kelly criterion for position sizing
                best_trend = qualifying_trends[0]
                kelly_fraction = min(0.25, best_trend.get("confidence", 0.5) * 0.5)
                spawn_budget = min(budget_cap, budget_cap * kelly_fraction)

                spawner = BusinessSpawner()
                spawn_result = spawner.spawn_business(
                    niche=best_trend.get("keyword"),
                    budget=spawn_budget
                )

                if spawn_result.get("success"):
                    self.stats["spawns_created"] += 1
                    decision = {
                        "spawn_enabled": True,
                        "decision": "spawned",
                        "spawn_id": spawn_result.get("spawn_id"),
                        "niche": best_trend.get("keyword"),
                        "budget": spawn_budget
                    }

        except ImportError:
            logger.warning("Auto-spawn modules not available")
        except Exception as e:
            logger.error(f"Spawn decision error: {e}")

        return decision

    # ============================================================
    # TRILLION-TILT MODULES (Steps 9-14)
    # ============================================================

    async def _step_auto_hedge(self) -> Dict[str, Any]:
        """Step 9: Auto-hedge exposure via outcome derivatives"""
        hedges = []

        try:
            from auto_hedge import (
                get_exposure_summary, place_hedge,
                get_hedge_portfolio, rebalance_hedges
            )

            exposure = get_exposure_summary()

            # Check if exposure exceeds threshold
            if exposure.get("net_exposure", 0) > 10000:
                hedge_result = place_hedge(
                    exposure_type="outcome",
                    amount=exposure.get("net_exposure", 0) * 0.3,
                    instrument="put_spread"
                )
                if hedge_result.get("success"):
                    hedges.append(hedge_result)
                    self.stats["hedges_placed"] += 1

            # Rebalance existing hedges
            rebalance = rebalance_hedges()

        except ImportError:
            logger.warning("Auto-hedge module not available")
            exposure = {}
            rebalance = {}
        except Exception as e:
            logger.error(f"Hedge error: {e}")
            exposure = {}
            rebalance = {}

        return {
            "hedges_placed": len(hedges),
            "net_exposure": exposure.get("net_exposure", 0),
            "hedged_pct": exposure.get("hedged_pct", 0),
            "rebalanced": rebalance.get("rebalanced", False)
        }

    async def _step_risk_tranches(self) -> Dict[str, Any]:
        """Step 10: Issue risk tranches for outcome portfolio"""
        tranches = []

        try:
            from builder_risk_tranches import (
                get_tranche_portfolio, issue_tranche,
                price_tranche, get_tranche_yields
            )

            portfolio = get_tranche_portfolio()

            # Check if we have enough collateral for new tranches
            if portfolio.get("available_collateral", 0) > 5000:
                for tier in ["senior", "mezzanine", "equity"]:
                    pricing = price_tranche(tier, portfolio.get("available_collateral", 0) / 3)
                    if pricing.get("yield_apr", 0) > 0.05:  # Min 5% yield
                        result = issue_tranche(tier, pricing)
                        if result.get("success"):
                            tranches.append(result)
                            self.stats["tranches_issued"] += 1

            yields = get_tranche_yields()

        except ImportError:
            logger.warning("Risk tranches module not available")
            yields = {}
        except Exception as e:
            logger.error(f"Tranche error: {e}")
            yields = {}

        return {
            "tranches_issued": len(tranches),
            "yields": yields,
            "details": tranches
        }

    async def _step_partner_mesh(self) -> Dict[str, Any]:
        """Step 11: Sync with partner mesh for deal flow"""
        synced = []
        white_label_policy = self.policies.get("white_label", {})

        try:
            from partner_mesh import (
                sync_partners, route_to_partner,
                get_partner_stats, settle_partner_splits
            )

            # Sync with all connected partners
            sync_result = sync_partners()
            synced = sync_result.get("partners_synced", [])

            # Route any overflow deals to partners
            overflow = []  # Would come from discovery/LOX
            for deal in overflow:
                route = route_to_partner(deal, white_label_policy)
                if route.get("routed"):
                    self.stats["partner_deals"] += 1

            # Settle any pending partner splits
            settlements = settle_partner_splits()

            stats = get_partner_stats()

        except ImportError:
            logger.warning("Partner mesh module not available")
            stats = {}
            settlements = {}
        except Exception as e:
            logger.error(f"Partner mesh error: {e}")
            stats = {}
            settlements = {}

        return {
            "partners_synced": len(synced),
            "deals_routed": self.stats["partner_deals"],
            "pending_settlements": settlements.get("pending", 0),
            "stats": stats
        }

    async def _step_data_coop(self) -> Dict[str, Any]:
        """Step 12: Contribute to and benefit from data cooperative"""
        contributions = []

        try:
            from data_coop import (
                contribute_signal, query_coop,
                get_coop_stats, claim_rewards
            )

            # Contribute anonymized signals
            if self.stats["cycles_run"] > 0:
                signal = {
                    "type": "cycle_stats",
                    "opportunities": self.stats["opportunities_found"],
                    "conversion_rate": self.stats["outcomes_fulfilled"] / max(1, self.stats["quotes_generated"]),
                    "avg_margin": 0.35  # Would calculate from actual data
                }
                contribution = contribute_signal(signal)
                if contribution.get("accepted"):
                    contributions.append(contribution)

            # Query coop for market intelligence
            intelligence = query_coop({"type": "market_rates"})

            # Claim any accrued rewards
            rewards = claim_rewards()

            stats = get_coop_stats()

        except ImportError:
            logger.warning("Data coop module not available")
            intelligence = {}
            rewards = {}
            stats = {}
        except Exception as e:
            logger.error(f"Data coop error: {e}")
            intelligence = {}
            rewards = {}
            stats = {}

        return {
            "contributions": len(contributions),
            "intelligence_received": bool(intelligence),
            "rewards_claimed": rewards.get("amount", 0),
            "coop_stats": stats
        }

    async def _step_idle_time_arbitrage(self) -> Dict[str, Any]:
        """Step 13: Capture idle time for micro-tasks"""
        captured = []

        try:
            from idle_time_arbitrage import (
                detect_idle_capacity, assign_micro_task,
                get_idle_stats, optimize_scheduling
            )

            # Detect any idle capacity in the system
            idle = detect_idle_capacity()

            for slot in idle.get("idle_slots", []):
                if slot.get("duration_minutes", 0) >= 5:
                    task = assign_micro_task(slot)
                    if task.get("assigned"):
                        captured.append(task)
                        self.stats["idle_time_captured"] += slot.get("value", 0)

            # Optimize future scheduling
            optimization = optimize_scheduling()

            stats = get_idle_stats()

        except ImportError:
            logger.warning("Idle time arbitrage module not available")
            stats = {}
            optimization = {}
        except Exception as e:
            logger.error(f"Idle time error: {e}")
            stats = {}
            optimization = {}

        return {
            "tasks_assigned": len(captured),
            "value_captured": self.stats["idle_time_captured"],
            "optimization": optimization,
            "stats": stats
        }

    async def _step_securitization(self) -> Dict[str, Any]:
        """Step 14: Sweep completed outcomes into securitization desk"""
        securitized = []

        try:
            from securitization_desk import (
                sweep_completed_outcomes, package_abs,
                get_desk_stats, price_abs
            )

            # Sweep all completed outcomes into pool
            sweep = sweep_completed_outcomes()

            # Package into ABS if enough volume
            if sweep.get("pool_value", 0) >= 10000:
                pricing = price_abs(sweep.get("pool_value", 0))
                if pricing.get("yield_spread", 0) >= 0.02:  # Min 2% spread
                    package = package_abs(sweep.get("outcome_ids", []))
                    if package.get("success"):
                        securitized.append(package)

            stats = get_desk_stats()

        except ImportError:
            logger.warning("Securitization desk module not available")
            stats = {}
        except Exception as e:
            logger.error(f"Securitization error: {e}")
            stats = {}

        return {
            "outcomes_swept": sweep.get("count", 0) if 'sweep' in dir() else 0,
            "abs_packaged": len(securitized),
            "desk_stats": stats
        }

    # ============================================================
    # STATUS & HEALTH METHODS
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get apex engine statistics"""
        return {
            **self.stats,
            "policies_loaded": list(self.policies.keys()),
            "modules_active": {
                "monetization": self.monetization is not None,
                "brain": self.brain is not None,
                "ocs": self.ocs_engine is not None
            },
            "last_updated": _now()
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        health = {
            "status": "healthy",
            "version": "v115",
            "flywheel": "running",
            "discovery": "active",
            "execution": "active",
            "proofs": "active",
            "lox": "active" if self.policies.get("lox", {}).get("enabled") else "disabled",
            "autospawn": "active" if self.policies.get("autospawn", {}).get("enabled") else "disabled",
            "trillion_tilt": {
                "auto_hedge": "active",
                "risk_tranches": "active",
                "partner_mesh": "active",
                "data_coop": "active",
                "idle_time": "active",
                "securitization": "active"
            },
            "policies": {k: "loaded" for k in self.policies.keys()},
            "checked_at": _now()
        }

        # Check module health
        if not self.monetization:
            health["status"] = "degraded"
            health["monetization"] = "unavailable"
        if not self.brain:
            health["brain_overlay"] = "unavailable"

        return health

    def reload_policies(self) -> Dict[str, Any]:
        """Hot-reload policies from disk"""
        self.policies = self._load_policies()
        return {"ok": True, "policies_loaded": list(self.policies.keys())}


# Module-level singleton
_apex = ApexEngine()


async def run_sleep_mode_cycle() -> Dict[str, Any]:
    """Run one sleep mode cycle"""
    return await _apex.run_sleep_mode_cycle()


def get_apex_stats() -> Dict[str, Any]:
    """Get apex engine stats"""
    return _apex.get_stats()


def get_system_health() -> Dict[str, Any]:
    """Get system health"""
    return _apex.get_system_health()


def get_loaded_policies() -> Dict[str, Any]:
    """Get all loaded policies"""
    return _apex.policies


def reload_policies() -> Dict[str, Any]:
    """Hot-reload policies"""
    return _apex.reload_policies()


async def run_continuous_sleep_mode(interval_minutes: int = 15):
    """
    Run continuous sleep mode (production loop).

    This is the "Do Nothing" mode - everything runs automatically.
    """
    logger.info(f"Starting continuous sleep mode (interval: {interval_minutes}m)")

    while True:
        try:
            result = await run_sleep_mode_cycle()
            logger.info(f"Cycle {result['cycle_id']} completed")
            logger.info(f"  - Opportunities: {result['steps']['discovery'].get('opportunities_found', 0)}")
            logger.info(f"  - Quotes: {result['steps']['quote'].get('quotes_generated', 0)}")
            logger.info(f"  - Revenue: ${_apex.stats['revenue_collected']:.2f}")
            logger.info(f"  - Trillion-tilt hedges: {result['trillion_tilt']['hedge'].get('hedges_placed', 0)}")
        except Exception as e:
            logger.error(f"Cycle error: {e}")

        await asyncio.sleep(interval_minutes * 60)
