"""
FULFILLMENT FABRIC API ROUTES
=============================

API endpoints for the Universal Connector Bus, COI Runtime, and FCG.

This module exposes the fulfillment fabric to the REST API, enabling:
- Outcome execution via COI
- PDL-based operations
- Connector health monitoring
- Capability discovery
- SLA monitoring
"""

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any, Optional
import logging

from coi_runtime import get_coi_runtime, COIRuntime, FulfillmentCapabilityGraph
from pdl_catalog import PDLCatalog
from connectors import ConnectorRegistry

logger = logging.getLogger("fulfillment_fabric")

router = APIRouter(prefix="/fabric", tags=["fulfillment-fabric"])


# ============================================================================
# OUTCOME EXECUTION
# ============================================================================

@router.post("/execute")
async def execute_outcome(body: Dict[str, Any] = Body(...)):
    """
    Execute a Contractable Outcome Interface (COI) specification.

    Request body should contain:
    - outcome_type: The type of outcome (e.g., "send_email", "create_product")
    - inputs: Input parameters for the outcome
    - sla: SLA requirements (deadline_sec, success_criteria)
    - pricing: Pricing model (model, amount_usd)
    - risk: Risk parameters (bond_usd, insurance_pct)
    - proofs: List of required proof types
    - idempotency_key: Unique key for idempotent execution

    Optional:
    - quote_only: If true, return quote without executing
    - dry_run: If true, simulate execution
    """
    runtime = get_coi_runtime()

    quote_only = body.pop("quote_only", False)
    dry_run = body.pop("dry_run", False)

    result = await runtime.execute_outcome(
        body,
        quote_only=quote_only,
        dry_run=dry_run
    )

    return result


@router.post("/execute-pdl/{pdl_name}")
async def execute_from_pdl(pdl_name: str, body: Dict[str, Any] = Body(default={})):
    """
    Execute an outcome using a Protocol Descriptor Language (PDL) specification.

    Args:
        pdl_name: Name of the PDL (e.g., "shopify.create_product", "email.send")
        body: Input parameters for the PDL

    Optional body params:
    - idempotency_key: Unique key for idempotent execution
    - quote_only: If true, return quote without executing
    - dry_run: If true, simulate execution
    """
    runtime = get_coi_runtime()

    idempotency_key = body.pop("idempotency_key", None)
    quote_only = body.pop("quote_only", False)
    dry_run = body.pop("dry_run", False)

    result = await runtime.execute_from_pdl(
        pdl_name,
        body,
        idempotency_key=idempotency_key,
        quote_only=quote_only,
        dry_run=dry_run
    )

    return result


@router.post("/quote")
async def quote_outcome(body: Dict[str, Any] = Body(...)):
    """
    Get a price quote for an outcome without executing it.
    """
    runtime = get_coi_runtime()
    result = await runtime.execute_outcome(body, quote_only=True)
    return result


@router.post("/batch-execute")
async def batch_execute(body: Dict[str, Any] = Body(...)):
    """
    Execute multiple outcomes in batch.

    Request body:
    - outcomes: List of COI specifications
    - parallel: If true, execute in parallel (default: true)
    """
    runtime = get_coi_runtime()

    outcomes = body.get("outcomes", [])
    parallel = body.get("parallel", True)

    if not outcomes:
        return {"ok": False, "error": "no_outcomes_provided"}

    import asyncio

    if parallel:
        tasks = [runtime.execute_outcome(o) for o in outcomes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            "ok": True,
            "results": [
                r if isinstance(r, dict) else {"ok": False, "error": str(r)}
                for r in results
            ],
            "total": len(outcomes),
            "successful": sum(1 for r in results if isinstance(r, dict) and r.get("ok"))
        }
    else:
        results = []
        for o in outcomes:
            result = await runtime.execute_outcome(o)
            results.append(result)
        return {
            "ok": True,
            "results": results,
            "total": len(outcomes),
            "successful": sum(1 for r in results if r.get("ok"))
        }


# ============================================================================
# CAPABILITY & PDL DISCOVERY
# ============================================================================

@router.get("/capabilities")
async def list_capabilities():
    """List all available capabilities in the fulfillment fabric"""
    runtime = get_coi_runtime()
    await runtime.initialize()

    capabilities = runtime.list_capabilities()
    return {
        "ok": True,
        "capabilities": capabilities,
        "count": len(capabilities)
    }


@router.get("/pdls")
async def list_pdls(tag: Optional[str] = None, connector: Optional[str] = None):
    """
    List all available Protocol Descriptors (PDLs).

    Query params:
    - tag: Filter by tag (e.g., "payment", "email")
    - connector: Filter by connector (e.g., "stripe", "shopify")
    """
    runtime = get_coi_runtime()
    await runtime.initialize()

    pdls = runtime.pdl_catalog.all()

    if tag:
        pdls = [p for p in pdls if tag in p.tags]
    if connector:
        pdls = [p for p in pdls if p.connector == connector]

    return {
        "ok": True,
        "pdls": [
            {
                "name": pdl.name,
                "connector": pdl.connector,
                "action": pdl.action,
                "description": pdl.description,
                "inputs": pdl.inputs,
                "sla": pdl.sla,
                "cost_model": pdl.cost_model,
                "tags": pdl.tags
            }
            for pdl in pdls
        ],
        "count": len(pdls)
    }


@router.get("/pdl/{pdl_name}")
async def get_pdl(pdl_name: str):
    """Get details of a specific PDL"""
    runtime = get_coi_runtime()
    await runtime.initialize()

    pdl = runtime.pdl_catalog.get(pdl_name)
    if not pdl:
        raise HTTPException(status_code=404, detail=f"PDL not found: {pdl_name}")

    return {
        "ok": True,
        "pdl": pdl.to_dict()
    }


# ============================================================================
# CONNECTORS
# ============================================================================

@router.get("/connectors")
async def list_connectors():
    """List all registered connectors"""
    runtime = get_coi_runtime()
    await runtime.initialize()

    connectors = runtime.connector_registry.all_connectors()
    return {
        "ok": True,
        "connectors": [
            {
                "name": c.name,
                "capabilities": c.capabilities,
                "auth_schemes": [s.value for s in c.auth_schemes],
                "avg_latency_ms": c.avg_latency_ms,
                "success_rate": c.success_rate,
                "metrics": c.get_metrics()
            }
            for c in connectors
        ],
        "count": len(connectors)
    }


@router.get("/connectors/{connector_name}")
async def get_connector(connector_name: str):
    """Get details of a specific connector"""
    runtime = get_coi_runtime()
    await runtime.initialize()

    connector = runtime.connector_registry.get(connector_name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector not found: {connector_name}")

    return {
        "ok": True,
        "connector": {
            "name": connector.name,
            "capabilities": connector.capabilities,
            "auth_schemes": [s.value for s in connector.auth_schemes],
            "avg_latency_ms": connector.avg_latency_ms,
            "success_rate": connector.success_rate,
            "max_rps": connector.max_rps,
            "metrics": connector.get_metrics()
        }
    }


@router.get("/connectors/{connector_name}/health")
async def connector_health(connector_name: str):
    """Check health of a specific connector"""
    runtime = get_coi_runtime()
    await runtime.initialize()

    connector = runtime.connector_registry.get(connector_name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector not found: {connector_name}")

    health = await connector.health()
    return {
        "ok": health.healthy,
        "connector": connector_name,
        "healthy": health.healthy,
        "latency_ms": health.latency_ms,
        "error": health.error,
        "details": health.details,
        "checked_at": health.checked_at
    }


# ============================================================================
# HEALTH & MONITORING
# ============================================================================

@router.get("/health")
async def fabric_health():
    """Check health of the entire fulfillment fabric"""
    runtime = get_coi_runtime()
    health = await runtime.health_check()
    return health


@router.get("/metrics")
async def fabric_metrics():
    """Get fulfillment fabric metrics"""
    runtime = get_coi_runtime()
    await runtime.initialize()

    metrics = runtime.get_metrics()
    return {
        "ok": True,
        "metrics": metrics
    }


@router.get("/sla-violations")
async def get_sla_violations(limit: int = 100):
    """Get recent SLA violations"""
    runtime = get_coi_runtime()
    violations = runtime.get_sla_violations(limit)
    return {
        "ok": True,
        "violations": violations,
        "count": len(violations)
    }


@router.get("/contract/{outcome_id}")
async def get_contract(outcome_id: str):
    """Get contract details by outcome ID"""
    runtime = get_coi_runtime()
    contract = runtime.get_contract(outcome_id)

    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract not found: {outcome_id}")

    return {
        "ok": True,
        "contract": contract.to_dict()
    }


# ============================================================================
# CONVENIENCE ENDPOINTS (High-level operations)
# ============================================================================

@router.post("/send-email")
async def send_email(body: Dict[str, Any] = Body(...)):
    """
    Convenience endpoint to send an email.

    Required: to, subject, body
    Optional: html, idempotency_key
    """
    runtime = get_coi_runtime()

    return await runtime.execute_from_pdl("email.send", {
        "to": body.get("to"),
        "subject": body.get("subject"),
        "body": body.get("body"),
        "html": body.get("html")
    }, idempotency_key=body.get("idempotency_key"))


@router.post("/send-sms")
async def send_sms(body: Dict[str, Any] = Body(...)):
    """
    Convenience endpoint to send an SMS.

    Required: to, body
    Optional: idempotency_key
    """
    runtime = get_coi_runtime()

    return await runtime.execute_from_pdl("sms.send", {
        "to": body.get("to"),
        "body": body.get("body")
    }, idempotency_key=body.get("idempotency_key"))


@router.post("/create-payment-link")
async def create_payment_link(body: Dict[str, Any] = Body(...)):
    """
    Convenience endpoint to create a Stripe payment link.

    Required: amount
    Optional: currency, description, metadata, idempotency_key
    """
    runtime = get_coi_runtime()

    return await runtime.execute_from_pdl("stripe.payment_link", {
        "amount": body.get("amount"),
        "currency": body.get("currency", "usd"),
        "description": body.get("description", "Payment"),
        "metadata": body.get("metadata", {})
    }, idempotency_key=body.get("idempotency_key"))


@router.post("/create-shopify-product")
async def create_shopify_product(body: Dict[str, Any] = Body(...)):
    """
    Convenience endpoint to create a Shopify product.

    Required: title, price
    Optional: description, images, sku, inventory, idempotency_key
    """
    runtime = get_coi_runtime()

    return await runtime.execute_from_pdl("shopify.create_product", {
        "title": body.get("title"),
        "price": body.get("price"),
        "description": body.get("description", ""),
        "images": body.get("images", []),
        "sku": body.get("sku", ""),
        "inventory": body.get("inventory", 0)
    }, idempotency_key=body.get("idempotency_key"))


@router.post("/webhook-deliver")
async def deliver_webhook(body: Dict[str, Any] = Body(...)):
    """
    Convenience endpoint to deliver a webhook.

    Required: url, payload
    Optional: signing_secret, idempotency_key
    """
    runtime = get_coi_runtime()

    return await runtime.execute_from_pdl("webhook.deliver", {
        "url": body.get("url"),
        "payload": body.get("payload")
    }, idempotency_key=body.get("idempotency_key"))


# ============================================================================
# INCLUDE ROUTER FUNCTION
# ============================================================================

def include_fulfillment_fabric(app):
    """Include fulfillment fabric routes in FastAPI app"""
    app.include_router(router)

    logger.info("Fulfillment Fabric routes registered at /fabric/*")
    logger.info("  - POST /fabric/execute (COI execution)")
    logger.info("  - POST /fabric/execute-pdl/{name} (PDL execution)")
    logger.info("  - GET  /fabric/capabilities (list capabilities)")
    logger.info("  - GET  /fabric/pdls (list PDLs)")
    logger.info("  - GET  /fabric/connectors (list connectors)")
    logger.info("  - GET  /fabric/health (fabric health)")
    logger.info("  - GET  /fabric/metrics (fabric metrics)")
