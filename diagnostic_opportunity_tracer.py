"""
═══════════════════════════════════════════════════════════════════════════════
DIAGNOSTIC OPPORTUNITY TRACER
═══════════════════════════════════════════════════════════════════════════════

Traces the full lifecycle of opportunity discovery → execution to identify
bottlenecks, failures, and optimization opportunities.

USAGE:
    from diagnostic_opportunity_tracer import include_diagnostic_endpoints
    include_diagnostic_endpoints(app)

ENDPOINTS:
    GET  /diagnostic/trace-cycle     - Run a traced unified cycle
    GET  /diagnostic/bottlenecks     - Show identified bottlenecks
    GET  /diagnostic/phase-timing    - Show timing for each phase
    GET  /diagnostic/failure-analysis - Show failure breakdown
    GET  /diagnostic/opportunity-funnel - Show conversion funnel
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
import asyncio
import time
import traceback
import os

router = APIRouter(prefix="/diagnostic", tags=["Diagnostic Tracer"])


# ═══════════════════════════════════════════════════════════════════════════════
# TRACE STATE
# ═══════════════════════════════════════════════════════════════════════════════

TRACE_RESULTS = {}
PHASE_TIMINGS = {}
BOTTLENECKS = []
FAILURES = []


def _now():
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# TRACE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

class PhaseTracer:
    """Context manager for tracing phase execution"""

    def __init__(self, phase_name: str, trace_id: str):
        self.phase_name = phase_name
        self.trace_id = trace_id
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error = None
        self.sub_traces = []

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        trace_entry = {
            "phase": self.phase_name,
            "trace_id": self.trace_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": round(duration, 3),
            "success": exc_type is None,
            "error": str(exc_val) if exc_val else None,
            "sub_traces": self.sub_traces
        }

        if self.trace_id not in PHASE_TIMINGS:
            PHASE_TIMINGS[self.trace_id] = []
        PHASE_TIMINGS[self.trace_id].append(trace_entry)

        # Identify bottlenecks (phases > 5 seconds)
        if duration > 5.0:
            BOTTLENECKS.append({
                "trace_id": self.trace_id,
                "phase": self.phase_name,
                "duration": round(duration, 3),
                "timestamp": _now()
            })

        # Track failures
        if exc_type:
            FAILURES.append({
                "trace_id": self.trace_id,
                "phase": self.phase_name,
                "error": str(exc_val),
                "traceback": traceback.format_exc(),
                "timestamp": _now()
            })

        return False  # Don't suppress exceptions

    def add_sub_trace(self, name: str, data: Dict):
        self.sub_traces.append({
            "name": name,
            "timestamp": _now(),
            "data": data
        })


async def trace_async_phase(phase_name: str, trace_id: str, coro):
    """Trace an async phase execution"""
    start = time.time()
    error = None
    result = None

    try:
        result = await coro
    except Exception as e:
        error = str(e)
        FAILURES.append({
            "trace_id": trace_id,
            "phase": phase_name,
            "error": error,
            "traceback": traceback.format_exc(),
            "timestamp": _now()
        })
        raise
    finally:
        duration = time.time() - start

        trace_entry = {
            "phase": phase_name,
            "trace_id": trace_id,
            "duration_seconds": round(duration, 3),
            "success": error is None,
            "error": error,
            "result_summary": _summarize_result(result) if result else None
        }

        if trace_id not in PHASE_TIMINGS:
            PHASE_TIMINGS[trace_id] = []
        PHASE_TIMINGS[trace_id].append(trace_entry)

        if duration > 5.0:
            BOTTLENECKS.append({
                "trace_id": trace_id,
                "phase": phase_name,
                "duration": round(duration, 3),
                "timestamp": _now()
            })

    return result


def _summarize_result(result: Any) -> Dict:
    """Create a summary of a result for tracing"""
    if isinstance(result, dict):
        summary = {"type": "dict", "keys": list(result.keys())[:10]}

        # Extract key metrics
        if "total" in result:
            summary["total"] = result["total"]
        if "count" in result:
            summary["count"] = result["count"]
        if "opportunities" in result:
            summary["opportunities_count"] = len(result.get("opportunities", []))
        if "signals" in result:
            summary["signals"] = result["signals"]
        if "spawned" in result:
            summary["spawned"] = result["spawned"]

        return summary
    elif isinstance(result, list):
        return {"type": "list", "length": len(result)}
    else:
        return {"type": type(result).__name__}


# ═══════════════════════════════════════════════════════════════════════════════
# TRACED UNIFIED CYCLE
# ═══════════════════════════════════════════════════════════════════════════════

async def run_traced_cycle() -> Dict[str, Any]:
    """
    Run a full unified cycle with detailed tracing.

    Traces:
    1. Spawn phase
    2. Discovery phase
    3. Polymorphic execution phase
    4. Social phase
    5. Fiverr phase
    6. Cart recovery phase
    7. Subscriptions phase
    8. Arbitrage phase
    """
    trace_id = f"trace_{uuid4().hex[:12]}"
    cycle_start = time.time()

    results = {
        "trace_id": trace_id,
        "started_at": _now(),
        "phases": {},
        "funnel": {
            "signals_detected": 0,
            "opportunities_discovered": 0,
            "opportunities_qualified": 0,
            "opportunities_executed": 0,
            "opportunities_succeeded": 0
        },
        "bottlenecks": [],
        "failures": []
    }

    # Import orchestrators
    try:
        from universal_revenue_orchestrator import UniversalRevenueOrchestrator
        orchestrator = UniversalRevenueOrchestrator()
    except ImportError as e:
        return {
            "trace_id": trace_id,
            "error": f"Failed to import orchestrator: {e}",
            "timestamp": _now()
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: SPAWN
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        spawn_start = time.time()
        spawn_result = await orchestrator.spawn_engine.run_spawn_cycle() if orchestrator.spawn_engine else {"signals": 0, "spawned": 0}
        spawn_duration = time.time() - spawn_start

        results["phases"]["spawn"] = {
            "duration_seconds": round(spawn_duration, 3),
            "signals": spawn_result.get("signals", 0),
            "spawned": spawn_result.get("spawned", 0),
            "success": True
        }
        results["funnel"]["signals_detected"] = spawn_result.get("signals", 0)

        if spawn_duration > 5.0:
            results["bottlenecks"].append({"phase": "spawn", "duration": spawn_duration})
    except Exception as e:
        results["phases"]["spawn"] = {"error": str(e), "success": False}
        results["failures"].append({"phase": "spawn", "error": str(e)})

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: DISCOVERY
    # ═══════════════════════════════════════════════════════════════════════════
    discovered_opportunities = []
    try:
        discovery_start = time.time()

        if orchestrator.polymorphic_orchestrator:
            discovery_result = await orchestrator.polymorphic_orchestrator.run_discovery_all_dimensions()
            discovered_opportunities = discovery_result.get("ranked_opportunities", [])
        else:
            discovery_result = {"total": 0, "opportunities": []}

        discovery_duration = time.time() - discovery_start

        results["phases"]["discovery"] = {
            "duration_seconds": round(discovery_duration, 3),
            "total_opportunities": len(discovered_opportunities),
            "total_ev": sum(o.get("ev", 0) for o in discovered_opportunities),
            "by_platform": _count_by_key(discovered_opportunities, "platform"),
            "by_type": _count_by_key(discovered_opportunities, "type"),
            "success": True
        }
        results["funnel"]["opportunities_discovered"] = len(discovered_opportunities)

        if discovery_duration > 10.0:
            results["bottlenecks"].append({"phase": "discovery", "duration": discovery_duration})
    except Exception as e:
        results["phases"]["discovery"] = {"error": str(e), "success": False}
        results["failures"].append({"phase": "discovery", "error": str(e)})

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: POLYMORPHIC EXECUTION
    # ═══════════════════════════════════════════════════════════════════════════
    try:
        poly_start = time.time()

        if orchestrator.polymorphic_orchestrator and discovered_opportunities:
            poly_result = await orchestrator.polymorphic_orchestrator.run_polymorphic_execution(discovered_opportunities)
        else:
            poly_result = {"total_processed": 0}

        poly_duration = time.time() - poly_start

        results["phases"]["polymorphic_execution"] = {
            "duration_seconds": round(poly_duration, 3),
            "total_processed": poly_result.get("total_processed", 0),
            "immediate_executed": poly_result.get("immediate_executed", 0),
            "conversational_started": poly_result.get("conversational_started", 0),
            "proposals_submitted": poly_result.get("proposals_submitted", 0),
            "queued_for_review": poly_result.get("queued_for_review", 0),
            "success": True
        }
        results["funnel"]["opportunities_executed"] = poly_result.get("total_processed", 0)
        results["funnel"]["opportunities_succeeded"] = poly_result.get("immediate_executed", 0) + poly_result.get("conversational_started", 0)

        if poly_duration > 15.0:
            results["bottlenecks"].append({"phase": "polymorphic_execution", "duration": poly_duration})
    except Exception as e:
        results["phases"]["polymorphic_execution"] = {"error": str(e), "success": False}
        results["failures"].append({"phase": "polymorphic_execution", "error": str(e)})

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 4-8: OTHER PHASES (traced but abbreviated)
    # ═══════════════════════════════════════════════════════════════════════════
    other_phases = ["social", "fiverr", "cart_recovery", "subscriptions", "arbitrage"]

    for phase_name in other_phases:
        try:
            phase_start = time.time()

            if phase_name == "social":
                phase_result = await orchestrator.run_social_posting() if hasattr(orchestrator, 'run_social_posting') else {"posts": 0}
            elif phase_name == "fiverr":
                phase_result = await orchestrator.check_fiverr_orders() if hasattr(orchestrator, 'check_fiverr_orders') else {"pending": 0}
            elif phase_name == "cart_recovery":
                phase_result = await orchestrator.run_recovery_cycle() if hasattr(orchestrator, 'run_recovery_cycle') else {"recovered": 0}
            elif phase_name == "subscriptions":
                phase_result = await orchestrator.check_subscription_renewals() if hasattr(orchestrator, 'check_subscription_renewals') else {"renewals": 0}
            elif phase_name == "arbitrage":
                phase_result = await orchestrator.run_arbitrage_scan() if hasattr(orchestrator, 'run_arbitrage_scan') else {"opportunities": 0}
            else:
                phase_result = {}

            phase_duration = time.time() - phase_start

            results["phases"][phase_name] = {
                "duration_seconds": round(phase_duration, 3),
                "result": _summarize_result(phase_result),
                "success": True
            }

            if phase_duration > 5.0:
                results["bottlenecks"].append({"phase": phase_name, "duration": phase_duration})
        except Exception as e:
            results["phases"][phase_name] = {"error": str(e), "success": False}
            results["failures"].append({"phase": phase_name, "error": str(e)})

    # ═══════════════════════════════════════════════════════════════════════════
    # FINALIZE
    # ═══════════════════════════════════════════════════════════════════════════
    total_duration = time.time() - cycle_start

    results["completed_at"] = _now()
    results["total_duration_seconds"] = round(total_duration, 3)

    # Calculate conversion rates
    funnel = results["funnel"]
    if funnel["signals_detected"] > 0:
        funnel["signal_to_opportunity_rate"] = round(funnel["opportunities_discovered"] / funnel["signals_detected"], 3)
    if funnel["opportunities_discovered"] > 0:
        funnel["opportunity_to_execution_rate"] = round(funnel["opportunities_executed"] / funnel["opportunities_discovered"], 3)
    if funnel["opportunities_executed"] > 0:
        funnel["execution_success_rate"] = round(funnel["opportunities_succeeded"] / funnel["opportunities_executed"], 3)

    # Store trace results
    TRACE_RESULTS[trace_id] = results

    return results


def _count_by_key(items: List[Dict], key: str) -> Dict[str, int]:
    """Count items by a key value"""
    counts = {}
    for item in items:
        val = item.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/trace-cycle")
async def trace_cycle_endpoint():
    """
    Run a full unified cycle with detailed tracing.

    Returns timing, bottlenecks, failures, and conversion funnel.
    """
    return await run_traced_cycle()


@router.get("/bottlenecks")
async def get_bottlenecks():
    """Get identified bottlenecks from recent traces"""
    return {
        "ok": True,
        "bottlenecks": BOTTLENECKS[-50:],  # Last 50
        "total": len(BOTTLENECKS)
    }


@router.get("/phase-timing")
async def get_phase_timing():
    """Get detailed phase timing from recent traces"""
    return {
        "ok": True,
        "traces": dict(list(PHASE_TIMINGS.items())[-10:]),  # Last 10 traces
        "total_traces": len(PHASE_TIMINGS)
    }


@router.get("/failure-analysis")
async def get_failure_analysis():
    """Get failure breakdown from recent traces"""
    # Count failures by phase
    by_phase = {}
    for failure in FAILURES:
        phase = failure.get("phase", "unknown")
        by_phase[phase] = by_phase.get(phase, 0) + 1

    return {
        "ok": True,
        "total_failures": len(FAILURES),
        "by_phase": by_phase,
        "recent_failures": FAILURES[-20:]  # Last 20
    }


@router.get("/opportunity-funnel")
async def get_opportunity_funnel():
    """Get opportunity conversion funnel from recent traces"""
    funnels = []
    for trace_id, result in list(TRACE_RESULTS.items())[-10:]:
        if "funnel" in result:
            funnels.append({
                "trace_id": trace_id,
                "timestamp": result.get("started_at"),
                "funnel": result["funnel"]
            })

    # Calculate averages
    if funnels:
        avg_funnel = {
            "signals_detected": sum(f["funnel"].get("signals_detected", 0) for f in funnels) / len(funnels),
            "opportunities_discovered": sum(f["funnel"].get("opportunities_discovered", 0) for f in funnels) / len(funnels),
            "opportunities_executed": sum(f["funnel"].get("opportunities_executed", 0) for f in funnels) / len(funnels),
            "opportunities_succeeded": sum(f["funnel"].get("opportunities_succeeded", 0) for f in funnels) / len(funnels)
        }
    else:
        avg_funnel = {}

    return {
        "ok": True,
        "recent_funnels": funnels,
        "average_funnel": avg_funnel
    }


@router.get("/trace/{trace_id}")
async def get_trace(trace_id: str):
    """Get a specific trace by ID"""
    if trace_id in TRACE_RESULTS:
        return {"ok": True, "trace": TRACE_RESULTS[trace_id]}
    raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")


@router.get("/system-check")
async def system_check():
    """Quick system health check for diagnostic purposes"""
    checks = {}

    # Check orchestrator imports
    try:
        from universal_revenue_orchestrator import UniversalRevenueOrchestrator
        checks["unified_orchestrator"] = "✓"
    except Exception as e:
        checks["unified_orchestrator"] = f"✗ {e}"

    try:
        from master_autonomous_orchestrator import MasterAutonomousOrchestrator
        checks["master_orchestrator"] = "✓"
    except Exception as e:
        checks["master_orchestrator"] = f"✗ {e}"

    try:
        from auto_spawn_engine import AutoSpawnEngine
        checks["spawn_engine"] = "✓"
    except Exception as e:
        checks["spawn_engine"] = f"✗ {e}"

    try:
        from universal_fulfillment_fabric import fabric_execute
        checks["universal_fabric"] = "✓"
    except Exception as e:
        checks["universal_fabric"] = f"✗ {e}"

    # Check Playwright
    try:
        from playwright.async_api import async_playwright
        checks["playwright"] = "✓"
    except:
        checks["playwright"] = "✗ Not installed"

    # Check API keys
    api_keys = [
        "GITHUB_TOKEN", "REDDIT_CLIENT_ID", "TWITTER_BEARER_TOKEN",
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "SERPER_API_KEY",
        "PERPLEXITY_API_KEY", "STRIPE_SECRET_KEY"
    ]
    checks["api_keys"] = {}
    for key in api_keys:
        checks["api_keys"][key] = "✓" if os.getenv(key) else "✗"

    return {
        "ok": True,
        "timestamp": _now(),
        "checks": checks
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_diagnostic_endpoints(app):
    """Include diagnostic tracer endpoints in FastAPI app"""
    app.include_router(router)

    print("=" * 80)
    print("🔍 DIAGNOSTIC OPPORTUNITY TRACER LOADED")
    print("=" * 80)
    print("Endpoints:")
    print("  GET  /diagnostic/trace-cycle       - Run traced unified cycle")
    print("  GET  /diagnostic/bottlenecks       - View bottlenecks")
    print("  GET  /diagnostic/phase-timing      - View phase timing")
    print("  GET  /diagnostic/failure-analysis  - View failures")
    print("  GET  /diagnostic/opportunity-funnel - View conversion funnel")
    print("  GET  /diagnostic/system-check      - Quick system check")
    print("=" * 80)
