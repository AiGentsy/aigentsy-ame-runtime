"""
Connector Registry & Outcome Executor
=====================================

Central registry for all connectors with intelligent routing and execution.
"""

from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timezone
import asyncio
import logging

from .base import Connector, ConnectorResult, ConnectorHealth, CostEstimate

logger = logging.getLogger("connector_registry")


# ============================================================================
# OUTCOME SCHEMA & VALIDATION
# ============================================================================

OUTCOME_SCHEMA = {
    "outcome_type": str,
    "inputs": dict,
    "sla": dict,
    "pricing": dict,
    "risk": dict,
    "proofs": list,
    "idempotency_key": str
}

REQUIRED_SLA_FIELDS = ["deadline_sec"]
REQUIRED_PRICING_FIELDS = ["model", "amount_usd"]
REQUIRED_RISK_FIELDS = ["bond_usd"]


def validate_outcome(outcome: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
    """
    Validate an outcome specification against the schema.

    Returns:
        (is_valid, result_dict)
    """
    errors = []

    # Check required top-level fields
    for key, expected_type in OUTCOME_SCHEMA.items():
        if key not in outcome:
            errors.append(f"missing_field:{key}")
        elif not isinstance(outcome[key], expected_type):
            errors.append(f"invalid_type:{key}:expected_{expected_type.__name__}")

    # Validate SLA
    sla = outcome.get("sla", {})
    for field in REQUIRED_SLA_FIELDS:
        if field not in sla:
            errors.append(f"missing_sla_field:{field}")

    # Validate pricing
    pricing = outcome.get("pricing", {})
    for field in REQUIRED_PRICING_FIELDS:
        if field not in pricing:
            errors.append(f"missing_pricing_field:{field}")

    # Validate risk
    risk = outcome.get("risk", {})
    for field in REQUIRED_RISK_FIELDS:
        if field not in risk:
            errors.append(f"missing_risk_field:{field}")

    if errors:
        return False, {"ok": False, "errors": errors}

    return True, {"ok": True}


# ============================================================================
# CONNECTOR SCORING
# ============================================================================

def score_connector(connector: Connector, outcome: Dict[str, Any]) -> float:
    """
    Score a connector for executing an outcome.

    Score = (margin × success_rate × speed_factor) - risk_cost

    Higher score = better choice for this outcome.
    """
    pricing = outcome.get("pricing", {})
    sla = outcome.get("sla", {})
    risk = outcome.get("risk", {})

    # Base factors
    price = float(pricing.get("amount_usd", 0))
    deadline_sec = float(sla.get("deadline_sec", 60))
    bond = float(risk.get("bond_usd", 0))

    # Connector characteristics
    success_rate = getattr(connector, "success_rate", 0.9)
    avg_latency_ms = getattr(connector, "avg_latency_ms", 1000)
    avg_latency_sec = avg_latency_ms / 1000

    # Speed factor: bonus for fast connectors relative to deadline
    if deadline_sec > 0:
        speed_factor = min(1.5, deadline_sec / max(avg_latency_sec, 0.1))
    else:
        speed_factor = 1.0

    # Estimate connector cost (simplified)
    estimated_cost = price * 0.1  # Assume 10% of price is cost

    # Margin potential
    margin = max(price - estimated_cost, 0)

    # Risk cost: probability of failure * bond at risk
    risk_cost = (1 - success_rate) * bond

    # Final score
    score = (margin * success_rate * min(speed_factor, 2.0)) - risk_cost

    return max(score, 0)


# ============================================================================
# CONNECTOR REGISTRY
# ============================================================================

class ConnectorRegistry:
    """
    Central registry for all connectors.

    Manages connector lifecycle, routing, and execution.
    """

    def __init__(self):
        self._connectors: Dict[str, Connector] = {}
        self._capability_index: Dict[str, List[str]] = {}  # capability -> [connector_names]
        self._circuit_breakers: Dict[str, Dict] = {}
        self._idempotency_cache: Dict[str, ConnectorResult] = {}

    def register(self, connector: Connector) -> None:
        """Register a connector"""
        self._connectors[connector.name] = connector

        # Index capabilities
        for cap in connector.capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            if connector.name not in self._capability_index[cap]:
                self._capability_index[cap].append(connector.name)

        logger.info(f"Registered connector: {connector.name} with {len(connector.capabilities)} capabilities")

    def unregister(self, name: str) -> bool:
        """Unregister a connector"""
        if name not in self._connectors:
            return False

        connector = self._connectors.pop(name)

        # Remove from capability index
        for cap in connector.capabilities:
            if cap in self._capability_index:
                self._capability_index[cap] = [
                    n for n in self._capability_index[cap] if n != name
                ]

        return True

    def get(self, name: str) -> Optional[Connector]:
        """Get a connector by name"""
        return self._connectors.get(name)

    def capable(self, capability: str) -> List[Connector]:
        """Get all connectors capable of performing an action"""
        names = self._capability_index.get(capability, [])
        return [self._connectors[n] for n in names if n in self._connectors]

    def all_connectors(self) -> List[Connector]:
        """Get all registered connectors"""
        return list(self._connectors.values())

    def all_capabilities(self) -> List[str]:
        """Get all registered capabilities"""
        return list(self._capability_index.keys())

    def _is_circuit_open(self, connector_name: str) -> bool:
        """Check if circuit breaker is open for a connector"""
        cb = self._circuit_breakers.get(connector_name, {})
        if cb.get("open_until", 0) > datetime.now(timezone.utc).timestamp():
            return True
        return False

    def _record_failure(self, connector_name: str):
        """Record a failure and potentially open circuit breaker"""
        if connector_name not in self._circuit_breakers:
            self._circuit_breakers[connector_name] = {"failures": 0, "open_until": 0}

        cb = self._circuit_breakers[connector_name]
        cb["failures"] = cb.get("failures", 0) + 1

        # Open circuit after 5 consecutive failures
        if cb["failures"] >= 5:
            cb["open_until"] = datetime.now(timezone.utc).timestamp() + 300  # 5 min cooldown
            logger.warning(f"Circuit breaker opened for {connector_name}")

    def _record_success(self, connector_name: str):
        """Record success and reset circuit breaker"""
        if connector_name in self._circuit_breakers:
            self._circuit_breakers[connector_name] = {"failures": 0, "open_until": 0}

    async def health_check_all(self) -> Dict[str, ConnectorHealth]:
        """Run health checks on all connectors"""
        results = {}
        for name, connector in self._connectors.items():
            try:
                results[name] = await connector.health()
            except Exception as e:
                results[name] = ConnectorHealth(
                    healthy=False,
                    latency_ms=0,
                    error=str(e)
                )
        return results

    def auto_register_all(self, config: Optional[Dict[str, Dict]] = None):
        """Auto-register all available connectors"""
        from .http_generic import HTTPGenericConnector
        from .webhook import WebhookConnector
        from .email_connector import EmailConnector
        from .resend_connector import ResendConnector
        from .sms_connector import SMSConnector
        from .slack_connector import SlackConnector
        from .shopify_connector import ShopifyConnector
        from .stripe_connector import StripeConnector
        from .storage_connector import StorageConnector
        from .airtable_connector import AirtableConnector
        from .headless_connector import HeadlessConnector

        config = config or {}

        # Register ResendConnector FIRST (preferred email provider)
        # Then EmailConnector as fallback - order matters for capability routing
        connector_classes = [
            HTTPGenericConnector,
            WebhookConnector,
            ResendConnector,  # Primary email - registered first for preference
            EmailConnector,   # Fallback email
            SMSConnector,
            SlackConnector,
            ShopifyConnector,
            StripeConnector,
            StorageConnector,
            AirtableConnector,
            HeadlessConnector,
        ]

        for cls in connector_classes:
            name = getattr(cls, "name", cls.__name__.lower())
            connector_config = config.get(name, {})
            try:
                self.register(cls(connector_config))
            except Exception as e:
                logger.warning(f"Failed to register {name}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            "connectors": len(self._connectors),
            "capabilities": len(self._capability_index),
            "circuit_breakers_open": sum(
                1 for cb in self._circuit_breakers.values()
                if cb.get("open_until", 0) > datetime.now(timezone.utc).timestamp()
            ),
            "idempotency_cache_size": len(self._idempotency_cache)
        }


# ============================================================================
# OUTCOME EXECUTION
# ============================================================================

async def execute_outcome(
    registry: ConnectorRegistry,
    outcome: Dict[str, Any],
    *,
    prefer_connector: Optional[str] = None,
    max_retries: int = 3,
    fallback_to_any: bool = True
) -> Dict[str, Any]:
    """
    Execute an outcome using the best available connector.

    Routing logic:
    1. Validate outcome spec
    2. Find capable connectors
    3. Rank by score (EV)
    4. Try in order with circuit breaker checks
    5. Return result with proofs

    Args:
        registry: The connector registry
        outcome: Outcome specification (COI)
        prefer_connector: Optional preferred connector name
        max_retries: Maximum retry attempts per connector
        fallback_to_any: If True, try headless fallback if all else fails

    Returns:
        Execution result with proofs and connector info
    """
    # Validate outcome
    valid, validation_result = validate_outcome(outcome)
    if not valid:
        return {
            "ok": False,
            "error": "invalid_outcome",
            "details": validation_result
        }

    outcome_type = outcome["outcome_type"]
    idempotency_key = outcome.get("idempotency_key")

    # Check idempotency cache
    if idempotency_key and idempotency_key in registry._idempotency_cache:
        cached = registry._idempotency_cache[idempotency_key]
        return {
            "ok": cached.ok,
            "data": cached.data,
            "proofs": cached.proofs,
            "connector": "cached",
            "cached": True
        }

    # Find capable connectors
    candidates = registry.capable(outcome_type)

    # Add preferred connector to front if specified
    if prefer_connector:
        preferred = registry.get(prefer_connector)
        if preferred and preferred.can_perform(outcome_type):
            candidates = [preferred] + [c for c in candidates if c.name != prefer_connector]

    if not candidates:
        # Try headless fallback
        if fallback_to_any:
            headless = registry.get("headless")
            if headless:
                candidates = [headless]

    if not candidates:
        return {
            "ok": False,
            "error": "no_capable_connector",
            "outcome_type": outcome_type
        }

    # Rank by score
    ranked = sorted(candidates, key=lambda c: score_connector(c, outcome), reverse=True)

    # Try connectors in order
    errors = []
    timeout = outcome.get("sla", {}).get("deadline_sec", 60)

    for connector in ranked:
        # Check circuit breaker
        if registry._is_circuit_open(connector.name):
            errors.append({"connector": connector.name, "error": "circuit_open"})
            continue

        # Execute with retries
        for attempt in range(1, max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    connector.execute(
                        action=outcome_type,
                        params=outcome.get("inputs", {}),
                        idempotency_key=idempotency_key,
                        timeout=timeout
                    ),
                    timeout=timeout
                )

                if result.ok:
                    registry._record_success(connector.name)

                    # Cache successful result
                    if idempotency_key:
                        registry._idempotency_cache[idempotency_key] = result

                    return {
                        "ok": True,
                        "data": result.data,
                        "proofs": result.proofs,
                        "connector": connector.name,
                        "latency_ms": result.latency_ms,
                        "attempt": attempt
                    }

                # Non-retryable failure
                if not result.retryable:
                    errors.append({
                        "connector": connector.name,
                        "error": result.error,
                        "attempt": attempt
                    })
                    break

                # Retryable failure - continue loop
                errors.append({
                    "connector": connector.name,
                    "error": result.error,
                    "attempt": attempt,
                    "retrying": True
                })

            except asyncio.TimeoutError:
                errors.append({
                    "connector": connector.name,
                    "error": "timeout",
                    "attempt": attempt
                })
                registry._record_failure(connector.name)

            except Exception as e:
                errors.append({
                    "connector": connector.name,
                    "error": str(e),
                    "attempt": attempt
                })
                registry._record_failure(connector.name)

    # All connectors failed
    return {
        "ok": False,
        "error": "all_connectors_failed",
        "attempts": errors
    }


# ============================================================================
# SINGLETON REGISTRY & HELPER FUNCTIONS
# ============================================================================

_registry: Optional[ConnectorRegistry] = None


def get_registry() -> ConnectorRegistry:
    """Get the global connector registry (singleton)"""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
        _registry.auto_register_all()
    return _registry


def get_connector(name: str) -> Optional[Connector]:
    """Get a connector by name from the global registry"""
    return get_registry().get(name)
