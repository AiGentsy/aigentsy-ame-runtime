"""
COI RUNTIME - Contractable Outcome Interface
============================================

The COI Runtime is the execution fabric that turns any outcome specification
into a fulfilled contract with proofs, SLAs, and reconciliation.

Components:
1. COI Validator: Validates outcome specifications
2. Capability Router: Routes outcomes to best connector chain
3. Proof Collector: Gathers attestations and evidence
4. SLA Monitor: Tracks performance against contracts
5. Risk Manager: Handles bonds, insurance, and escrow

Usage:
    from coi_runtime import COIRuntime

    runtime = COIRuntime()
    await runtime.initialize()

    result = await runtime.execute_outcome({
        "outcome_type": "send_email",
        "inputs": {"to": "user@example.com", "subject": "Hello"},
        "sla": {"deadline_sec": 30},
        "pricing": {"model": "fixed", "amount_usd": 0.01},
        "risk": {"bond_usd": 0},
        "proofs": ["message_id"],
        "idempotency_key": "email-123"
    })
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field
import asyncio
import hashlib
import json
import logging
import time
import os

from connectors import ConnectorRegistry, execute_outcome as connector_execute
from connectors.base import ConnectorResult
from pdl_catalog import PDLCatalog, PDLSpec

# ═══════════════════════════════════════════════════════════════════════════════
# MONETIZATION FABRIC INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from monetization.pricing_arm import suggest as monetization_price_suggest
    from monetization.revenue_router import split as monetization_revenue_split
    from monetization.ledger import post_entry as monetization_ledger_post
    from monetization.proof_badges import mint_badge as monetization_mint_badge
    from monetization.referrals import allocate_referrals as monetization_ref_alloc
    from monetization.subscriptions import check_quota, record_usage
    from monetization.fee_schedule import calculate_platform_fee
    MONETIZATION_AVAILABLE = True
except ImportError as e:
    MONETIZATION_AVAILABLE = False

# MetaHive integration for collective AI learning
try:
    from metahive_brain import contribute_to_hive, query_hive
    METAHIVE_AVAILABLE = True
except ImportError:
    METAHIVE_AVAILABLE = False
    async def contribute_to_hive(*args, **kwargs): return {"ok": False}
    async def query_hive(*args, **kwargs): return {"ok": True, "patterns": []}
    # Fallbacks
    def monetization_price_suggest(base, **kwargs): return base
    def monetization_revenue_split(gross, **kwargs): return {"platform": 0, "user": gross}
    def monetization_ledger_post(*args, **kwargs): return {"ok": True}
    def monetization_mint_badge(att): return {"badge_id": None}
    def monetization_ref_alloc(gross, chain, **kwargs): return {"splits": {}, "remainder": gross}
    def check_quota(user, calls=1): return {"ok": True, "within_quota": True}
    def record_usage(user, calls=1): return {"ok": True}
    def calculate_platform_fee(amount): return {"fee": 0, "net": amount}

logger = logging.getLogger("coi_runtime")


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class COIContract:
    """A contractable outcome with terms and tracking"""
    outcome_id: str
    outcome_type: str
    inputs: Dict[str, Any]
    sla: Dict[str, Any]
    pricing: Dict[str, Any]
    risk: Dict[str, Any]
    proofs_required: List[str]
    idempotency_key: str

    # Execution state
    status: str = "pending"  # pending, executing, completed, failed, disputed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # Results
    result: Optional[Dict[str, Any]] = None
    proofs_collected: List[Dict[str, Any]] = field(default_factory=list)
    connector_used: Optional[str] = None
    latency_ms: float = 0.0

    # Financial
    quoted_price: float = 0.0
    actual_cost: float = 0.0
    margin: float = 0.0
    bond_held: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "outcome_type": self.outcome_type,
            "inputs": self.inputs,
            "sla": self.sla,
            "pricing": self.pricing,
            "risk": self.risk,
            "proofs_required": self.proofs_required,
            "idempotency_key": self.idempotency_key,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "proofs_collected": self.proofs_collected,
            "connector_used": self.connector_used,
            "latency_ms": self.latency_ms,
            "quoted_price": self.quoted_price,
            "actual_cost": self.actual_cost,
            "margin": self.margin,
            "bond_held": self.bond_held
        }


@dataclass
class SLAViolation:
    """Record of an SLA violation"""
    outcome_id: str
    violation_type: str  # timeout, quality, proof_missing
    expected: Any
    actual: Any
    severity: str  # minor, major, critical
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============================================================================
# COI RUNTIME
# ============================================================================

class COIRuntime:
    """
    The Contractable Outcome Interface Runtime.

    Orchestrates outcome execution with full contract lifecycle management.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Core components
        self.connector_registry = ConnectorRegistry()
        self.pdl_catalog = PDLCatalog()

        # State
        self._contracts: Dict[str, COIContract] = {}
        self._sla_violations: List[SLAViolation] = []
        self._idempotency_cache: Dict[str, COIContract] = {}

        # Metrics
        self._metrics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_revenue": 0.0,
            "total_cost": 0.0,
            "sla_violations": 0
        }

        # Callbacks
        self._on_complete_callbacks: List[Callable] = []
        self._on_failure_callbacks: List[Callable] = []

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the runtime with connectors and PDLs"""
        if self._initialized:
            return

        # Register all connectors
        connector_config = self.config.get("connectors", {})
        self.connector_registry.auto_register_all(connector_config)

        # Load PDL catalog
        self.pdl_catalog.load_builtin()

        # Load custom PDLs if configured
        pdl_dir = self.config.get("pdl_directory")
        if pdl_dir and os.path.exists(pdl_dir):
            self.pdl_catalog.load_from_dir(pdl_dir)

        self._initialized = True
        logger.info(f"COI Runtime initialized: {len(self.connector_registry.all_connectors())} connectors, {len(self.pdl_catalog.all())} PDLs")

    # ========================================================================
    # OUTCOME EXECUTION
    # ========================================================================

    async def execute_outcome(
        self,
        outcome: Dict[str, Any],
        *,
        quote_only: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute an outcome specification (COI).

        Args:
            outcome: The outcome specification
            quote_only: If True, just return quote without executing
            dry_run: If True, simulate execution without side effects

        Returns:
            Execution result with proofs and contract details
        """
        if not self._initialized:
            await self.initialize()

        # Generate outcome ID
        outcome_id = self._generate_outcome_id(outcome)
        idempotency_key = outcome.get("idempotency_key", outcome_id)

        # Check idempotency
        if idempotency_key in self._idempotency_cache:
            cached = self._idempotency_cache[idempotency_key]
            return {
                "ok": cached.status == "completed",
                "outcome_id": cached.outcome_id,
                "cached": True,
                "contract": cached.to_dict()
            }

        # Validate outcome
        valid, errors = self._validate_outcome(outcome)
        if not valid:
            return {"ok": False, "error": "invalid_outcome", "details": errors}

        # Create contract
        contract = COIContract(
            outcome_id=outcome_id,
            outcome_type=outcome["outcome_type"],
            inputs=outcome["inputs"],
            sla=outcome["sla"],
            pricing=outcome["pricing"],
            risk=outcome["risk"],
            proofs_required=outcome.get("proofs", []),
            idempotency_key=idempotency_key
        )

        # Quote pricing
        quote = await self._quote_outcome(contract)
        contract.quoted_price = quote["price"]
        contract.bond_held = quote.get("bond", 0)

        if quote_only:
            return {
                "ok": True,
                "outcome_id": outcome_id,
                "quote": quote,
                "contract": contract.to_dict()
            }

        if dry_run:
            contract.status = "dry_run"
            return {
                "ok": True,
                "outcome_id": outcome_id,
                "dry_run": True,
                "quote": quote,
                "contract": contract.to_dict()
            }

        # Execute
        contract.status = "executing"
        contract.started_at = datetime.now(timezone.utc).isoformat()
        self._contracts[outcome_id] = contract

        try:
            result = await self._execute_with_sla_monitoring(contract, outcome)

            contract.status = "completed" if result["ok"] else "failed"
            contract.completed_at = datetime.now(timezone.utc).isoformat()
            contract.result = result.get("data")
            contract.proofs_collected = result.get("proofs", [])
            contract.connector_used = result.get("connector")
            contract.latency_ms = result.get("latency_ms", 0)

            # Calculate actual cost and margin
            contract.actual_cost = await self._calculate_actual_cost(contract)
            contract.margin = contract.quoted_price - contract.actual_cost

            # Update metrics
            self._metrics["total_executions"] += 1
            if result["ok"]:
                self._metrics["successful_executions"] += 1
                self._metrics["total_revenue"] += contract.quoted_price
                self._metrics["total_cost"] += contract.actual_cost
            else:
                self._metrics["failed_executions"] += 1

            # Cache for idempotency
            self._idempotency_cache[idempotency_key] = contract

            # Invoke callbacks
            await self._invoke_callbacks(contract)

            return {
                "ok": result["ok"],
                "outcome_id": outcome_id,
                "data": result.get("data"),
                "proofs": result.get("proofs", []),
                "connector": result.get("connector"),
                "latency_ms": result.get("latency_ms"),
                "contract": contract.to_dict()
            }

        except Exception as e:
            contract.status = "failed"
            contract.completed_at = datetime.now(timezone.utc).isoformat()
            self._metrics["failed_executions"] += 1

            logger.error(f"Outcome execution failed: {outcome_id} - {e}")

            return {
                "ok": False,
                "outcome_id": outcome_id,
                "error": str(e),
                "contract": contract.to_dict()
            }

    async def execute_from_pdl(
        self,
        pdl_name: str,
        params: Dict[str, Any],
        *,
        idempotency_key: Optional[str] = None,
        quote_only: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute an outcome using a PDL specification.

        Args:
            pdl_name: Name of the PDL (e.g., "shopify.create_product")
            params: Input parameters for the PDL
            idempotency_key: Optional idempotency key
            quote_only: If True, just return quote
            dry_run: If True, simulate execution

        Returns:
            Execution result
        """
        if not self._initialized:
            await self.initialize()

        pdl = self.pdl_catalog.get(pdl_name)
        if not pdl:
            return {"ok": False, "error": f"pdl_not_found:{pdl_name}"}

        try:
            outcome = pdl.to_outcome(params, idempotency_key=idempotency_key)
        except ValueError as e:
            return {"ok": False, "error": str(e)}

        return await self.execute_outcome(outcome, quote_only=quote_only, dry_run=dry_run)

    # ========================================================================
    # INTERNAL METHODS
    # ========================================================================

    def _generate_outcome_id(self, outcome: Dict[str, Any]) -> str:
        """Generate unique outcome ID"""
        raw = json.dumps(outcome, sort_keys=True, default=str)
        hash_val = hashlib.sha256(raw.encode()).hexdigest()[:16]
        ts = int(time.time() * 1000)
        return f"coi-{ts}-{hash_val}"

    def _validate_outcome(self, outcome: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate outcome specification"""
        errors = []

        required_fields = ["outcome_type", "inputs", "sla", "pricing", "risk", "proofs", "idempotency_key"]
        for field in required_fields:
            if field not in outcome:
                errors.append(f"missing_field:{field}")

        if "sla" in outcome:
            if "deadline_sec" not in outcome["sla"]:
                errors.append("missing_sla_deadline")

        if "pricing" in outcome:
            if "model" not in outcome["pricing"] or "amount_usd" not in outcome["pricing"]:
                errors.append("incomplete_pricing")

        if "risk" in outcome:
            if "bond_usd" not in outcome["risk"]:
                errors.append("missing_risk_bond")

        return len(errors) == 0, errors

    async def _quote_outcome(self, contract: COIContract) -> Dict[str, Any]:
        """Generate price quote for outcome with monetization fabric integration"""
        base_price = contract.pricing.get("amount_usd", 0)

        # Find capable connectors and get cost estimates
        candidates = self.connector_registry.capable(contract.outcome_type)

        min_cost = float("inf")
        for connector in candidates:
            try:
                estimate = await connector.cost_estimate(contract.outcome_type, contract.inputs)
                min_cost = min(min_cost, estimate.estimated_usd)
            except:
                pass

        if min_cost == float("inf"):
            min_cost = base_price * 0.3  # Default 30% cost

        # Calculate quote with margin
        margin_pct = self.config.get("default_margin_pct", 0.30)
        quoted_price = max(base_price, min_cost * (1 + margin_pct))

        # ═══════════════════════════════════════════════════════════════════════
        # MONETIZATION: Dynamic price uplift via Pricing ARM
        # ═══════════════════════════════════════════════════════════════════════
        if MONETIZATION_AVAILABLE:
            try:
                # Get pricing context from config/inputs
                fx_rate = contract.inputs.get("fx_rate", 1.0)
                load_pct = self.config.get("system_load_pct", 0.3)
                wave_score = contract.inputs.get("wave_score", 0.2)

                # Apply monetization pricing uplift
                quoted_price = monetization_price_suggest(
                    quoted_price,
                    fx_rate=fx_rate,
                    load_pct=load_pct,
                    wave_score=wave_score,
                    cogs=min_cost,
                    min_margin=margin_pct
                )
            except Exception as e:
                logger.warning(f"Monetization pricing uplift failed: {e}")

        # Calculate bond
        bond = contract.risk.get("bond_usd", quoted_price * 0.2)

        return {
            "price": round(quoted_price, 4),
            "estimated_cost": round(min_cost, 4),
            "margin": round(quoted_price - min_cost, 4),
            "bond": round(bond, 4),
            "currency": "USD"
        }

    async def _execute_with_sla_monitoring(
        self,
        contract: COIContract,
        outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute outcome with SLA monitoring"""
        deadline_sec = contract.sla.get("deadline_sec", 60)

        start_time = time.time()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                connector_execute(
                    self.connector_registry,
                    outcome,
                    max_retries=3
                ),
                timeout=deadline_sec
            )

            elapsed_ms = (time.time() - start_time) * 1000

            # Check for SLA violations
            if elapsed_ms > deadline_sec * 1000:
                self._record_sla_violation(
                    contract.outcome_id,
                    "timeout",
                    deadline_sec * 1000,
                    elapsed_ms,
                    "major"
                )

            # Check proof requirements
            if result.get("ok"):
                proofs_collected = set(p.get("type") for p in result.get("proofs", []))
                proofs_required = set(contract.proofs_required)
                missing = proofs_required - proofs_collected

                if missing:
                    self._record_sla_violation(
                        contract.outcome_id,
                        "proof_missing",
                        list(proofs_required),
                        list(proofs_collected),
                        "minor"
                    )

            result["latency_ms"] = elapsed_ms
            return result

        except asyncio.TimeoutError:
            elapsed_ms = (time.time() - start_time) * 1000

            self._record_sla_violation(
                contract.outcome_id,
                "timeout",
                deadline_sec * 1000,
                elapsed_ms,
                "critical"
            )

            return {
                "ok": False,
                "error": "timeout",
                "latency_ms": elapsed_ms
            }

    def _record_sla_violation(
        self,
        outcome_id: str,
        violation_type: str,
        expected: Any,
        actual: Any,
        severity: str
    ):
        """Record an SLA violation"""
        violation = SLAViolation(
            outcome_id=outcome_id,
            violation_type=violation_type,
            expected=expected,
            actual=actual,
            severity=severity
        )
        self._sla_violations.append(violation)
        self._metrics["sla_violations"] += 1

        logger.warning(f"SLA Violation: {outcome_id} - {violation_type} ({severity})")

    async def _calculate_actual_cost(self, contract: COIContract) -> float:
        """Calculate actual cost of execution"""
        connector = self.connector_registry.get(contract.connector_used or "")
        if connector:
            try:
                estimate = await connector.cost_estimate(contract.outcome_type, contract.inputs)
                return estimate.estimated_usd
            except:
                pass

        # Fallback to estimated cost
        return contract.quoted_price * 0.3

    async def _invoke_callbacks(self, contract: COIContract):
        """Invoke registered callbacks"""
        callbacks = (
            self._on_complete_callbacks if contract.status == "completed"
            else self._on_failure_callbacks
        )

        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(contract)
                else:
                    callback(contract)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        # ═══════════════════════════════════════════════════════════════════════
        # MONETIZATION: Finalize sale on successful completion
        # ═══════════════════════════════════════════════════════════════════════
        if contract.status == "completed" and MONETIZATION_AVAILABLE:
            await self._monetization_finalize(contract)

    async def _monetization_finalize(self, contract: COIContract):
        """
        Monetization Fabric finalization:
        1. Mint proof badge from attestation
        2. Split revenue (platform/user/pool/partner)
        3. Process referral chain allocation
        4. Post to double-entry ledger
        5. Record API usage
        """
        try:
            gross = contract.quoted_price
            outcome_id = contract.outcome_id

            # 1. Mint proof badge from collected proofs
            attestation = {
                "outcome_id": outcome_id,
                "outcome_type": contract.outcome_type,
                "outcome_hash": hashlib.sha256(json.dumps(contract.to_dict(), default=str).encode()).hexdigest(),
                "sla_verdict": "pass" if not any(
                    v.outcome_id == outcome_id for v in self._sla_violations
                ) else "fail",
                "proofs": contract.proofs_collected,
                "entity": contract.inputs.get("entity", "system")
            }
            badge = monetization_mint_badge(attestation)

            # 2. Revenue split (platform gets 6%, remainder split user/pool/partner)
            entity = contract.inputs.get("entity", "system")
            referral_chain = contract.inputs.get("referral_chain", [])

            splits = monetization_revenue_split(
                gross,
                user_pct=0.70,
                pool_pct=0.10,
                partner_pct=0.05
            )

            # 3. Referral chain allocation
            ref_alloc = {"splits": {}, "total_allocated": 0}
            if referral_chain:
                ref_alloc = monetization_ref_alloc(gross, referral_chain)
                splits["referrals"] = ref_alloc.get("splits", {})

            # 4. Post to double-entry ledger
            # Gross sale entry
            monetization_ledger_post(
                "coi_sale",
                f"coi:{contract.idempotency_key}",
                debit=0,
                credit=gross,
                meta={
                    "outcome_type": contract.outcome_type,
                    "entity": entity,
                    "connector": contract.connector_used,
                    "latency_ms": contract.latency_ms,
                    "badge_id": badge.get("badge_id")
                }
            )

            # Platform fee entry
            platform_fee = splits.get("platform", 0)
            if platform_fee > 0:
                monetization_ledger_post(
                    "platform_fee",
                    "entity:aigentsy_platform",
                    debit=0,
                    credit=platform_fee,
                    meta={"source_coi": outcome_id}
                )

            # User payout entry
            user_payout = splits.get("user", 0)
            if user_payout > 0:
                monetization_ledger_post(
                    "user_payout",
                    f"entity:{entity}",
                    debit=0,
                    credit=user_payout,
                    meta={"source_coi": outcome_id}
                )

            # Referral payouts
            for referrer, amount in ref_alloc.get("splits", {}).items():
                monetization_ledger_post(
                    "referral_payout",
                    f"entity:{referrer}",
                    debit=0,
                    credit=amount,
                    meta={"source_coi": outcome_id, "source_user": entity}
                )

            # 5. Record API usage
            record_usage(entity, calls=1)

            # Store monetization result on contract
            contract.result = contract.result or {}
            contract.result["monetization"] = {
                "badge": badge,
                "splits": splits,
                "referral_allocation": ref_alloc,
                "gross": gross,
                "platform_fee": platform_fee
            }

            logger.info(f"Monetization finalized: {outcome_id} - gross=${gross:.2f}, platform=${platform_fee:.2f}")

            # ═══════════════════════════════════════════════════════════════════
            # METAHIVE: Contribute successful pattern for collective AI learning
            # ═══════════════════════════════════════════════════════════════════
            if METAHIVE_AVAILABLE:
                try:
                    margin_pct = (gross - contract.actual_cost) / gross if gross > 0 else 0
                    await contribute_to_hive(
                        username=entity,
                        pattern_type="pricing_insight",
                        context={
                            "outcome_type": contract.outcome_type,
                            "base_price": contract.pricing.get("amount_usd", 0),
                            "quoted_price": gross,
                            "actual_cost": contract.actual_cost,
                            "connector": contract.connector_used
                        },
                        action={
                            "pricing_model": contract.pricing.get("model", "dynamic"),
                            "sla_met": attestation["sla_verdict"] == "pass",
                            "proof_count": len(contract.proofs_collected),
                            "latency_ms": contract.latency_ms
                        },
                        outcome={
                            "roas": 1 + margin_pct,
                            "quality_score": 0.9 if attestation["sla_verdict"] == "pass" else 0.5,
                            "revenue": gross,
                            "margin": contract.margin
                        },
                        anonymize=True
                    )
                except Exception as hive_err:
                    logger.debug(f"MetaHive contribution failed: {hive_err}")

        except Exception as e:
            logger.error(f"Monetization finalization failed for {contract.outcome_id}: {e}")

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def on_complete(self, callback: Callable) -> None:
        """Register callback for successful completions"""
        self._on_complete_callbacks.append(callback)

    def on_failure(self, callback: Callable) -> None:
        """Register callback for failures"""
        self._on_failure_callbacks.append(callback)

    def get_contract(self, outcome_id: str) -> Optional[COIContract]:
        """Get contract by outcome ID"""
        return self._contracts.get(outcome_id)

    def get_metrics(self) -> Dict[str, Any]:
        """Get runtime metrics"""
        return {
            **self._metrics,
            "connectors": len(self.connector_registry.all_connectors()),
            "pdls": len(self.pdl_catalog.all()),
            "active_contracts": len([c for c in self._contracts.values() if c.status == "executing"]),
            "cached_results": len(self._idempotency_cache)
        }

    def get_sla_violations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent SLA violations"""
        violations = self._sla_violations[-limit:]
        return [
            {
                "outcome_id": v.outcome_id,
                "type": v.violation_type,
                "expected": v.expected,
                "actual": v.actual,
                "severity": v.severity,
                "timestamp": v.timestamp
            }
            for v in violations
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Run health check on all connectors"""
        if not self._initialized:
            await self.initialize()

        results = await self.connector_registry.health_check_all()

        healthy_count = sum(1 for r in results.values() if r.healthy)
        total_count = len(results)

        return {
            "ok": healthy_count > 0,
            "healthy_connectors": healthy_count,
            "total_connectors": total_count,
            "details": {
                name: {"healthy": r.healthy, "latency_ms": r.latency_ms, "error": r.error}
                for name, r in results.items()
            }
        }

    def list_capabilities(self) -> List[str]:
        """List all available capabilities"""
        return self.connector_registry.all_capabilities()

    def list_pdls(self) -> List[Dict[str, Any]]:
        """List all available PDLs"""
        return [
            {"name": pdl.name, "connector": pdl.connector, "action": pdl.action, "tags": pdl.tags}
            for pdl in self.pdl_catalog.all()
        ]


# ============================================================================
# FULFILLMENT CAPABILITY GRAPH (FCG)
# ============================================================================

class FulfillmentCapabilityGraph:
    """
    Routes outcomes to the best doer (internal, SaaS, or partner agent).

    Maintains a capability index with embeddings and scores candidates by:
    EV = margin × win_prob × reliability × speed - risk_cost
    """

    def __init__(self, coi_runtime: COIRuntime):
        self.runtime = coi_runtime
        self._capability_registry: Dict[str, List[Dict[str, Any]]] = {}
        self._partner_capabilities: Dict[str, Dict[str, Any]] = {}

    def register_capability(
        self,
        capability: str,
        provider: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Register a capability provider"""
        if capability not in self._capability_registry:
            self._capability_registry[capability] = []

        self._capability_registry[capability].append({
            "provider": provider,
            "success_rate": metadata.get("success_rate", 0.9),
            "avg_latency_ms": metadata.get("avg_latency_ms", 1000),
            "cost_per_call": metadata.get("cost_per_call", 0.01),
            "tags": metadata.get("tags", [])
        })

    def register_partner(
        self,
        partner_id: str,
        capabilities: List[str],
        metadata: Dict[str, Any]
    ) -> None:
        """Register an external partner with capabilities"""
        self._partner_capabilities[partner_id] = {
            "capabilities": capabilities,
            "endpoint": metadata.get("endpoint"),
            "success_rate": metadata.get("success_rate", 0.85),
            "revenue_share": metadata.get("revenue_share", 0.2)
        }

    def find_best_provider(
        self,
        capability: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Find best provider for a capability"""
        candidates = self._capability_registry.get(capability, [])

        # Add partner candidates
        for partner_id, info in self._partner_capabilities.items():
            if capability in info["capabilities"]:
                candidates.append({
                    "provider": f"partner:{partner_id}",
                    "success_rate": info["success_rate"],
                    "avg_latency_ms": 2000,  # Assume partner latency
                    "cost_per_call": 0.05,
                    "is_partner": True
                })

        if not candidates:
            return None

        # Score candidates
        constraints = constraints or {}
        max_latency = constraints.get("max_latency_ms", float("inf"))
        min_success_rate = constraints.get("min_success_rate", 0)

        scored = []
        for c in candidates:
            if c["avg_latency_ms"] > max_latency:
                continue
            if c["success_rate"] < min_success_rate:
                continue

            # EV = margin × win_prob × reliability × speed_factor
            speed_factor = 1.0 / (c["avg_latency_ms"] / 1000)
            ev = (1 - c["cost_per_call"]) * c["success_rate"] * speed_factor
            scored.append((ev, c))

        if not scored:
            return None

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1]

    def can_fulfill(self, capability: str) -> bool:
        """Check if capability can be fulfilled"""
        return capability in self._capability_registry or any(
            capability in info["capabilities"]
            for info in self._partner_capabilities.values()
        )

    def get_capability_map(self) -> Dict[str, Any]:
        """Get full capability map"""
        return {
            "internal": self._capability_registry,
            "partners": self._partner_capabilities,
            "total_capabilities": len(self._capability_registry) + sum(
                len(p["capabilities"]) for p in self._partner_capabilities.values()
            )
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_runtime_instance: Optional[COIRuntime] = None


def get_coi_runtime() -> COIRuntime:
    """Get or create the singleton COI runtime instance"""
    global _runtime_instance
    if _runtime_instance is None:
        _runtime_instance = COIRuntime()
    return _runtime_instance
