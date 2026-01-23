"""
═══════════════════════════════════════════════════════════════════════════════
AUTONOMOUS INTEGRATION - Full Self-Operating Platform
═══════════════════════════════════════════════════════════════════════════════

Integrates 4 autonomous systems for fully self-operating AI business:

1. Autonomous Reconciliation - Financial truth across all platforms
2. Autonomous Deal Graph - Network intelligence for cross-sell
3. Master Autonomous Orchestrator - Intelligent coordination
4. Autonomous Upgrades - Self-evolution and improvement

Usage:
    from autonomous_integration import include_autonomous_endpoints
    include_autonomous_endpoints(app)
"""

from fastapi import FastAPI, HTTPException, Body
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging
import asyncio

logger = logging.getLogger("autonomous_integration")

# ═══════════════════════════════════════════════════════════════════════════════
# LAZY IMPORTS - Only load when needed
# ═══════════════════════════════════════════════════════════════════════════════

_reconciliation_engine = None
_deal_graph = None
_master_orchestrator = None


def get_reconciliation_engine():
    """Get the autonomous reconciliation engine singleton"""
    global _reconciliation_engine
    if _reconciliation_engine is None:
        try:
            from autonomous_reconciliation_engine import reconciliation_engine
            _reconciliation_engine = reconciliation_engine
            logger.info("✅ Autonomous Reconciliation Engine loaded")
        except ImportError as e:
            logger.warning(f"⚠️ Reconciliation engine not available: {e}")
            _reconciliation_engine = None
    return _reconciliation_engine


def get_deal_graph():
    """Get the autonomous deal graph singleton"""
    global _deal_graph
    if _deal_graph is None:
        try:
            from autonomous_deal_graph import get_deal_graph as _get_dg
            _deal_graph = _get_dg()
            logger.info("✅ Autonomous Deal Graph loaded")
        except ImportError as e:
            logger.warning(f"⚠️ Deal graph not available: {e}")
            _deal_graph = None
    return _deal_graph


def get_master_orchestrator():
    """Get the master autonomous orchestrator singleton"""
    global _master_orchestrator
    if _master_orchestrator is None:
        try:
            from master_autonomous_orchestrator import get_master_orchestrator as _get_mo
            _master_orchestrator = _get_mo()
            logger.info("✅ Master Autonomous Orchestrator loaded")
        except ImportError as e:
            logger.warning(f"⚠️ Master orchestrator not available: {e}")
            _master_orchestrator = None
    return _master_orchestrator


# ═══════════════════════════════════════════════════════════════════════════════
# AUTONOMOUS UPGRADES - Import functions with state management
# ═══════════════════════════════════════════════════════════════════════════════

# State storage for upgrades (these functions are stateless)
_upgrade_tests: List[Dict[str, Any]] = []
_upgrade_deployments: List[Dict[str, Any]] = []


def _import_upgrades():
    """Import upgrade functions"""
    try:
        from autonomous_upgrades import (
            suggest_next_upgrade,
            create_ab_test,
            get_active_tests,
            analyze_ab_test,
            deploy_logic_upgrade,
            rollback_logic_upgrade,
            UPGRADE_TYPES
        )
        return {
            "suggest_next_upgrade": suggest_next_upgrade,
            "create_ab_test": create_ab_test,
            "get_active_tests": get_active_tests,
            "analyze_ab_test": analyze_ab_test,
            "deploy_logic_upgrade": deploy_logic_upgrade,
            "rollback_logic_upgrade": rollback_logic_upgrade,
            "upgrade_types": UPGRADE_TYPES,
            "available": True
        }
    except ImportError as e:
        logger.warning(f"⚠️ Autonomous upgrades not available: {e}")
        return {"available": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_autonomous_endpoints(app: FastAPI):
    """Register all autonomous system endpoints"""

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. RECONCILIATION ENDPOINTS - Financial Truth
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/reconciliation/status")
    async def reconciliation_status():
        """Get reconciliation engine status and summary"""
        engine = get_reconciliation_engine()
        if not engine:
            return {"ok": False, "error": "Reconciliation engine not available"}

        try:
            dashboard = engine.get_dashboard()
            return {
                "ok": True,
                "engine": "autonomous_reconciliation",
                "dashboard": dashboard,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/reconciliation/discrepancies")
    async def reconciliation_discrepancies():
        """Get list of financial discrepancies requiring attention"""
        engine = get_reconciliation_engine()
        if not engine:
            return {"ok": False, "error": "Reconciliation engine not available"}

        try:
            # Get activities with discrepancies
            discrepancies = []
            if hasattr(engine, 'activities'):
                for activity in engine.activities.values():
                    if hasattr(activity, 'status') and 'discrepancy' in str(activity.status).lower():
                        discrepancies.append({
                            "id": getattr(activity, 'id', 'unknown'),
                            "type": getattr(activity, 'activity_type', 'unknown'),
                            "amount": getattr(activity, 'gross_revenue', 0),
                            "status": str(getattr(activity, 'status', 'unknown'))
                        })

            return {
                "ok": True,
                "discrepancies": discrepancies,
                "count": len(discrepancies),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/reconciliation/dashboard")
    async def reconciliation_dashboard():
        """Full reconciliation dashboard"""
        engine = get_reconciliation_engine()
        if not engine:
            return {"ok": False, "error": "Reconciliation engine not available"}

        return engine.get_dashboard()

    @app.post("/reconciliation/record")
    async def reconciliation_record(activity: Dict[str, Any] = Body(...)):
        """Record a new activity for reconciliation"""
        engine = get_reconciliation_engine()
        if not engine:
            return {"ok": False, "error": "Reconciliation engine not available"}

        try:
            result = engine.record_activity(
                activity_type=activity.get("type", "unknown"),
                gross_revenue=activity.get("amount", 0),
                path=activity.get("path", "path_a"),
                metadata=activity.get("metadata", {})
            )
            return {"ok": True, "activity_id": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. DEAL GRAPH ENDPOINTS - Network Intelligence
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/deal-graph/connections")
    async def deal_graph_connections():
        """Get all entity connections in the deal graph"""
        dg = get_deal_graph()
        if not dg:
            return {"ok": False, "error": "Deal graph not available"}

        try:
            # Get graph statistics
            stats = dg.get_graph_stats() if hasattr(dg, 'get_graph_stats') else {}

            # Get entities
            entities = []
            if hasattr(dg, 'relationship_graph') and hasattr(dg.relationship_graph, 'entities'):
                for eid, entity in list(dg.relationship_graph.entities.items())[:50]:
                    entities.append({
                        "id": eid,
                        "type": getattr(entity, 'entity_type', 'unknown'),
                        "name": getattr(entity, 'name', 'unknown'),
                        "metadata": getattr(entity, 'metadata', {})
                    })

            return {
                "ok": True,
                "stats": stats,
                "entities": entities,
                "entity_count": len(entities),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/deal-graph/cross-sell")
    async def deal_graph_cross_sell():
        """Get cross-sell opportunities from network"""
        dg = get_deal_graph()
        if not dg:
            return {"ok": False, "error": "Deal graph not available"}

        try:
            opportunities = []

            # Get intro opportunities if available
            if hasattr(dg, 'get_intro_opportunities'):
                intros = dg.get_intro_opportunities(limit=20)
                for intro in intros:
                    opportunities.append({
                        "type": "intro",
                        "id": getattr(intro, 'id', 'unknown'),
                        "source": getattr(intro, 'source_id', 'unknown'),
                        "target": getattr(intro, 'target_id', 'unknown'),
                        "ev": getattr(intro, 'expected_value', 0),
                        "reason": getattr(intro, 'reason', 'network connection')
                    })

            # Get cross-sell from relationships
            if hasattr(dg, 'relationship_graph') and hasattr(dg.relationship_graph, 'find_cross_sell'):
                cross_sells = dg.relationship_graph.find_cross_sell()
                for cs in cross_sells[:20]:
                    opportunities.append({
                        "type": "cross_sell",
                        "entity": cs.get("entity_id"),
                        "product": cs.get("product"),
                        "ev": cs.get("ev", 0),
                        "confidence": cs.get("confidence", 0.5)
                    })

            return {
                "ok": True,
                "opportunities": opportunities,
                "count": len(opportunities),
                "total_ev": sum(o.get("ev", 0) for o in opportunities),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/deal-graph/entity")
    async def deal_graph_add_entity(entity: Dict[str, Any] = Body(...)):
        """Add an entity to the deal graph"""
        dg = get_deal_graph()
        if not dg:
            return {"ok": False, "error": "Deal graph not available"}

        try:
            if hasattr(dg, 'relationship_graph') and hasattr(dg.relationship_graph, 'add_entity'):
                entity_id = dg.relationship_graph.add_entity(
                    entity_type=entity.get("type", "customer"),
                    name=entity.get("name", "Unknown"),
                    metadata=entity.get("metadata", {})
                )
                return {"ok": True, "entity_id": entity_id}
            return {"ok": False, "error": "add_entity not available"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/deal-graph/relationship")
    async def deal_graph_add_relationship(rel: Dict[str, Any] = Body(...)):
        """Add a relationship between entities"""
        dg = get_deal_graph()
        if not dg:
            return {"ok": False, "error": "Deal graph not available"}

        try:
            if hasattr(dg, 'relationship_graph') and hasattr(dg.relationship_graph, 'add_relationship'):
                rel_id = dg.relationship_graph.add_relationship(
                    source_id=rel.get("source_id"),
                    target_id=rel.get("target_id"),
                    relationship_type=rel.get("type", "knows"),
                    strength=rel.get("strength", 0.5),
                    metadata=rel.get("metadata", {})
                )
                return {"ok": True, "relationship_id": rel_id}
            return {"ok": False, "error": "add_relationship not available"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. MASTER ORCHESTRATOR ENDPOINTS - Intelligent Coordination
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/orchestrator/autonomous-status")
    async def orchestrator_autonomous_status():
        """Get master orchestrator status"""
        mo = get_master_orchestrator()
        if not mo:
            return {"ok": False, "error": "Master orchestrator not available"}

        try:
            status = {
                "ok": True,
                "engine": "master_autonomous_orchestrator",
                "cycle_count": getattr(mo, 'cycle_count', 0),
                "total_revenue": getattr(mo, 'total_revenue', 0),
                "active_workflows": len(getattr(mo, 'active_workflows', {})),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Add consent status if available
            if hasattr(mo, 'consent_manager'):
                status["consents"] = mo.consent_manager.get_all_consents() if hasattr(mo.consent_manager, 'get_all_consents') else {}

            return status
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/orchestrator/autonomous-cycle")
    async def orchestrator_autonomous_cycle():
        """Run a full autonomous orchestration cycle"""
        mo = get_master_orchestrator()
        if not mo:
            return {"ok": False, "error": "Master orchestrator not available"}

        try:
            # Run autonomous cycle
            if hasattr(mo, 'run_autonomous_cycle'):
                result = await mo.run_autonomous_cycle()
            elif hasattr(mo, 'run_cycle'):
                result = await mo.run_cycle()
            else:
                # Fallback: run component cycles
                result = {
                    "phases_completed": [],
                    "opportunities_found": 0,
                    "actions_taken": 0,
                    "revenue_generated": 0
                }

                # Try to run discovery
                if hasattr(mo, 'run_discovery'):
                    disc = await mo.run_discovery()
                    result["phases_completed"].append("discovery")
                    result["opportunities_found"] = disc.get("count", 0)

                # Try to run execution
                if hasattr(mo, 'run_execution'):
                    exec_result = await mo.run_execution()
                    result["phases_completed"].append("execution")
                    result["actions_taken"] = exec_result.get("actions", 0)

            return {
                "ok": True,
                "cycle_result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Autonomous cycle error: {e}")
            return {"ok": False, "error": str(e)}

    @app.post("/orchestrator/prioritize")
    async def orchestrator_prioritize(opportunities: List[Dict[str, Any]] = Body(...)):
        """Prioritize opportunities using EV × Probability × Network × Learning"""
        mo = get_master_orchestrator()

        # Priority scoring function
        def score_opportunity(opp: Dict) -> float:
            ev = opp.get("ev", opp.get("expected_value", 0))
            prob = opp.get("probability", opp.get("confidence", 0.5))
            network_mult = opp.get("network_multiplier", 1.0)
            learning_mult = opp.get("learning_multiplier", 1.0)
            return ev * prob * network_mult * learning_mult

        # Score and sort
        scored = []
        for opp in opportunities:
            score = score_opportunity(opp)
            scored.append({
                **opp,
                "priority_score": round(score, 2)
            })

        scored.sort(key=lambda x: x["priority_score"], reverse=True)

        return {
            "ok": True,
            "prioritized": scored,
            "count": len(scored),
            "total_ev": sum(o.get("priority_score", 0) for o in scored),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. AUTONOMOUS UPGRADES ENDPOINTS - Self-Evolution
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/upgrades/status")
    async def upgrades_status():
        """Get autonomous upgrade system status"""
        upgrades = _import_upgrades()
        if not upgrades.get("available"):
            return {"ok": False, "error": upgrades.get("error", "Upgrades not available")}

        try:
            # Use internal state storage
            active_tests = upgrades["get_active_tests"](_upgrade_tests)
            return {
                "ok": True,
                "engine": "autonomous_upgrades",
                "active_tests": len(active_tests),
                "tests": active_tests[:10],  # Limit to 10
                "total_deployments": len(_upgrade_deployments),
                "upgrade_types": list(upgrades.get("upgrade_types", {}).keys()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/upgrades/propose")
    async def upgrades_propose():
        """Get proposed next upgrade based on outcome patterns"""
        upgrades = _import_upgrades()
        if not upgrades.get("available"):
            return {"ok": False, "error": upgrades.get("error", "Upgrades not available")}

        try:
            # Get outcome data for suggestion (simplified)
            outcomes = []  # Would come from Outcome Oracle
            suggestion = upgrades["suggest_next_upgrade"](outcomes)
            return {
                "ok": True,
                "proposal": suggestion,
                "upgrade_types": upgrades.get("upgrade_types", {}),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/upgrades/test")
    async def upgrades_create_test(test_config: Dict[str, Any] = Body(...)):
        """Create a new A/B test for an upgrade"""
        upgrades = _import_upgrades()
        if not upgrades.get("available"):
            return {"ok": False, "error": upgrades.get("error", "Upgrades not available")}

        try:
            test = upgrades["create_ab_test"](
                name=test_config.get("name", "unnamed_test"),
                control_logic=test_config.get("control", {}),
                variant_logic=test_config.get("variant", {}),
                success_metric=test_config.get("metric", "revenue"),
                sample_size=test_config.get("sample_size", 100)
            )
            # Store in internal state
            _upgrade_tests.append(test)
            return {
                "ok": True,
                "test_id": test.get("id"),
                "test": test,
                "status": "created",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/upgrades/deploy")
    async def upgrades_deploy(deploy_config: Dict[str, Any] = Body(...)):
        """Deploy an approved upgrade (requires human approval flag)"""
        upgrades = _import_upgrades()
        if not upgrades.get("available"):
            return {"ok": False, "error": upgrades.get("error", "Upgrades not available")}

        # Safety check - require explicit approval
        if not deploy_config.get("human_approved"):
            return {
                "ok": False,
                "error": "Human approval required",
                "message": "Set human_approved: true to deploy. Review the upgrade first.",
                "upgrade_id": deploy_config.get("upgrade_id")
            }

        try:
            result = upgrades["deploy_logic_upgrade"](
                upgrade_id=deploy_config.get("upgrade_id"),
                target_module=deploy_config.get("module"),
                new_logic=deploy_config.get("logic", {})
            )
            return {
                "ok": True,
                "deployed": True,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/upgrades/rollback")
    async def upgrades_rollback(rollback_config: Dict[str, Any] = Body(...)):
        """Rollback a deployed upgrade"""
        upgrades = _import_upgrades()
        if not upgrades.get("available"):
            return {"ok": False, "error": upgrades.get("error", "Upgrades not available")}

        try:
            result = upgrades["rollback_logic_upgrade"](
                upgrade_id=rollback_config.get("upgrade_id")
            )
            return {
                "ok": True,
                "rolled_back": True,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════════
    # UNIFIED AUTONOMOUS STATUS
    # ═══════════════════════════════════════════════════════════════════════════

    @app.get("/autonomous/status")
    async def autonomous_full_status():
        """Get status of all autonomous systems"""
        status = {
            "ok": True,
            "systems": {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Check reconciliation
        recon = get_reconciliation_engine()
        status["systems"]["reconciliation"] = {
            "available": recon is not None,
            "activities": len(getattr(recon, 'activities', {})) if recon else 0
        }

        # Check deal graph
        dg = get_deal_graph()
        status["systems"]["deal_graph"] = {
            "available": dg is not None
        }
        if dg and hasattr(dg, 'get_graph_stats'):
            try:
                status["systems"]["deal_graph"]["stats"] = dg.get_graph_stats()
            except:
                pass

        # Check master orchestrator
        mo = get_master_orchestrator()
        status["systems"]["master_orchestrator"] = {
            "available": mo is not None,
            "cycle_count": getattr(mo, 'cycle_count', 0) if mo else 0
        }

        # Check upgrades
        upgrades = _import_upgrades()
        status["systems"]["upgrades"] = {
            "available": upgrades.get("available", False)
        }
        if upgrades.get("available"):
            try:
                status["systems"]["upgrades"]["active_tests"] = len(upgrades["get_active_tests"]())
            except:
                pass

        # Summary
        available_count = sum(1 for s in status["systems"].values() if s.get("available"))
        status["summary"] = {
            "total_systems": 4,
            "available": available_count,
            "percentage": round(available_count / 4 * 100, 1)
        }

        return status

    logger.info("=" * 70)
    logger.info("🤖 AUTONOMOUS INTEGRATION LOADED")
    logger.info("=" * 70)
    logger.info("Endpoints registered:")
    logger.info("  Reconciliation: /reconciliation/status, /reconciliation/discrepancies")
    logger.info("  Deal Graph: /deal-graph/connections, /deal-graph/cross-sell")
    logger.info("  Orchestrator: /orchestrator/autonomous-cycle, /orchestrator/prioritize")
    logger.info("  Upgrades: /upgrades/status, /upgrades/propose, /upgrades/deploy")
    logger.info("  Unified: /autonomous/status")
    logger.info("=" * 70)
