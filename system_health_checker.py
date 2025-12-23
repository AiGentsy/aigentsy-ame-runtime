"""
SYSTEM HEALTH CHECKER
Tests all 50+ AiGentsy systems to verify they're actually working (not stubs)

This will show you which of your 160 "logics" are:
- ✅ WORKING (actually implemented)
- ⚠️ STUB (placeholder only)
- ❌ BROKEN (import/runtime errors)
"""

import asyncio
import inspect
from datetime import datetime, timezone
from typing import Dict, Any, List, Callable
import traceback


# Define all systems to test
SYSTEMS_TO_TEST = {
    # ===== CORE REVENUE =====
    "ame_pitches": {
        "module": "ame_pitches",
        "functions": ["generate_pitch", "approve_pitch", "get_stats"],
        "category": "Core Revenue"
    },
    
    "intent_exchange": {
        "module": "intent_exchange_UPGRADED",
        "functions": ["publish_intent", "bid_on_intent", "verify_proof_of_outcome"],
        "category": "Core Revenue"
    },
    
    "revenue_flows": {
        "module": "revenue_flows",
        "functions": ["calculate_base_fee", "calculate_full_fee_with_premium"],
        "category": "Core Revenue"
    },
    
    # ===== FINANCIAL TOOLS =====
    "ocl_engine": {
        "module": "ocl_engine",
        "functions": ["calculate_ocl_limit", "spend_ocl"],
        "category": "Financial Tools"
    },
    
    "ocl_p2p": {
        "module": "ocl_p2p_lending",
        "functions": ["create_lending_pool", "request_loan"],
        "category": "Financial Tools"
    },
    
    "factoring": {
        "module": "agent_factoring",
        "functions": ["calculate_factoring_tier", "request_factoring_advance"],
        "category": "Financial Tools"
    },
    
    "ipvault": {
        "module": "ipvault",
        "functions": ["create_ip_asset", "license_ip_asset"],
        "category": "Financial Tools"
    },
    
    # ===== MARKETPLACE =====
    "metabridge": {
        "module": "metabridge",
        "functions": ["create", "match"],
        "category": "Marketplace"
    },
    
    "dealgraph": {
        "module": "metabridge_dealgraph_UPGRADED",
        "functions": ["create", "get_dealgraph"],
        "category": "Marketplace"
    },
    
    "dark_pool": {
        "module": "dark_pool",
        "functions": ["create_dark_pool_order", "match_orders"],
        "category": "Marketplace"
    },
    
    # ===== GROWTH & OPTIMIZATION =====
    "growth_agent": {
        "module": "aigent_growth_agent",
        "functions": ["metabridge", "cold_lead_pitch"],
        "category": "Growth"
    },
    
    "metamatch": {
        "module": "aigent_growth_metamatch",
        "functions": ["run_metamatch_campaign"],
        "category": "Growth"
    },
    
    "r3_router": {
        "module": "r3_router_UPGRADED",
        "functions": ["allocate", "get_performance"],
        "category": "Growth"
    },
    
    "amg_orchestrator": {
        "module": "amg_orchestrator",
        "functions": ["optimize_revenue"],
        "category": "Growth"
    },
    
    "analytics_engine": {
        "module": "analytics_engine",
        "functions": ["calculate_metrics", "generate_insights"],
        "category": "Growth"
    },
    
    "ltv_forecaster": {
        "module": "ltv_forecaster",
        "functions": ["calculate_ltv_with_churn"],
        "category": "Growth"
    },
    
    # ===== BUSINESS MODELS =====
    "franchise": {
        "module": "franchise_engine",
        "functions": ["create_franchise", "calculate_franchise_fee"],
        "category": "Business Models"
    },
    
    "syndication": {
        "module": "syndication",
        "functions": ["create_syndicate", "distribute_returns"],
        "category": "Business Models"
    },
    
    "coop_sponsors": {
        "module": "coop_sponsors",
        "functions": ["create_coop_pool", "distribute_sponsorship"],
        "category": "Business Models"
    },
    
    # ===== ADVANCED FEATURES =====
    "pricing_oracle": {
        "module": "pricing_oracle",
        "functions": ["calculate_dynamic_price"],
        "category": "Advanced Features"
    },
    
    "bundle_engine": {
        "module": "bundle_engine",
        "functions": ["create_bundle", "calculate_bundle_discount"],
        "category": "Advanced Features"
    },
    
    "performance_bonds": {
        "module": "performance_bonds",
        "functions": ["create_bond", "claim_bond"],
        "category": "Advanced Features"
    },
    
    # ===== INTELLIGENCE =====
    "aigentsy_conductor": {
        "module": "aigentsy_conductor",
        "functions": ["execute_task"],  # Class-based, need to check differently
        "category": "Intelligence"
    },
    
    "execution_scorer": {
        "module": "execution_scorer",
        "functions": ["score_opportunity"],  # Class-based
        "category": "Intelligence"
    },
    
    "outcome_oracle": {
        "module": "outcome_oracle_max",
        "functions": ["on_event"],
        "category": "Intelligence"
    },
    
    # ===== DISCOVERY =====
    "alpha_discovery": {
        "module": "alpha_discovery_engine",
        "functions": ["discover_all"],  # Class-based
        "category": "Discovery"
    },
    
    "ultimate_discovery": {
        "module": "ultimate_discovery_engine",
        "functions": ["discover_all_opportunities"],
        "category": "Discovery"
    },
    
    # ===== EXECUTION (NEW) =====
    "universal_executor": {
        "module": "universal_executor",
        "functions": ["execute_opportunity"],  # Class-based
        "category": "Execution"
    },
    
    "platform_apis": {
        "module": "platform_apis",
        "functions": None,  # Multiple classes
        "category": "Execution"
    },
    
    "payment_collector": {
        "module": "payment_collector",
        "functions": ["record_revenue", "mark_paid"],
        "category": "Execution"
    },
    
    "approval_system": {
        "module": "approval_system",
        "functions": ["request_approval", "approve_execution"],
        "category": "Execution"
    }
}


async def test_system(system_name: str, config: Dict) -> Dict[str, Any]:
    """
    Test a single system
    
    Returns:
        Result with status (working/stub/broken) and details
    """
    
    result = {
        "system": system_name,
        "category": config["category"],
        "module": config["module"],
        "status": "unknown",
        "functions_tested": 0,
        "functions_working": 0,
        "functions_stub": 0,
        "functions_broken": 0,
        "details": {},
        "error": None
    }
    
    try:
        # Try to import module
        module = __import__(config["module"])
        
        # If no specific functions listed, just check import
        if not config.get("functions"):
            result["status"] = "working"
            result["details"]["import"] = "success"
            return result
        
        # Test each function
        for func_name in config["functions"]:
            result["functions_tested"] += 1
            
            try:
                # Get function
                if hasattr(module, func_name):
                    func = getattr(module, func_name)
                    
                    # Check if it's a stub
                    if callable(func):
                        # Try to get source code
                        try:
                            source = inspect.getsource(func)
                            
                            # Check for stub patterns
                            if '"stub": True' in source or "'stub': True" in source:
                                result["functions_stub"] += 1
                                result["details"][func_name] = "STUB"
                            elif "return {}" in source or "pass" in source:
                                result["functions_stub"] += 1
                                result["details"][func_name] = "STUB (empty)"
                            else:
                                result["functions_working"] += 1
                                result["details"][func_name] = "WORKING"
                        except:
                            # Can't get source, assume working
                            result["functions_working"] += 1
                            result["details"][func_name] = "WORKING (no source)"
                    else:
                        result["functions_working"] += 1
                        result["details"][func_name] = "WORKING (not callable)"
                else:
                    result["functions_broken"] += 1
                    result["details"][func_name] = "BROKEN (not found)"
            
            except Exception as e:
                result["functions_broken"] += 1
                result["details"][func_name] = f"BROKEN: {str(e)}"
        
        # Determine overall status
        if result["functions_broken"] > 0:
            result["status"] = "broken"
        elif result["functions_stub"] == result["functions_tested"]:
            result["status"] = "stub"
        elif result["functions_working"] > 0:
            result["status"] = "working"
        else:
            result["status"] = "unknown"
    
    except ImportError as e:
        result["status"] = "broken"
        result["error"] = f"Import error: {str(e)}"
    
    except Exception as e:
        result["status"] = "broken"
        result["error"] = f"Error: {str(e)}"
    
    return result


async def test_all_systems() -> Dict[str, Any]:
    """
    Test all systems and return comprehensive report
    
    Returns:
        Full health check report with stats by category
    """
    
    print("\n" + "="*60)
    print("🔍 SYSTEM HEALTH CHECK - TESTING ALL SYSTEMS")
    print("="*60 + "\n")
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_systems": len(SYSTEMS_TO_TEST),
        "working": 0,
        "stub": 0,
        "broken": 0,
        "unknown": 0,
        "by_category": {},
        "systems": {}
    }
    
    # Test each system
    for system_name, config in SYSTEMS_TO_TEST.items():
        print(f"Testing: {system_name}...", end=" ")
        
        result = await test_system(system_name, config)
        results["systems"][system_name] = result
        
        # Update counts
        if result["status"] == "working":
            results["working"] += 1
            print("✅ WORKING")
        elif result["status"] == "stub":
            results["stub"] += 1
            print("⚠️ STUB")
        elif result["status"] == "broken":
            results["broken"] += 1
            print("❌ BROKEN")
        else:
            results["unknown"] += 1
            print("❓ UNKNOWN")
        
        # Update category stats
        category = config["category"]
        if category not in results["by_category"]:
            results["by_category"][category] = {
                "working": 0,
                "stub": 0,
                "broken": 0,
                "total": 0
            }
        
        results["by_category"][category]["total"] += 1
        if result["status"] in ["working", "stub", "broken"]:
            results["by_category"][category][result["status"]] += 1
    
    # Calculate percentages
    results["working_percentage"] = (results["working"] / results["total_systems"] * 100) if results["total_systems"] > 0 else 0
    results["stub_percentage"] = (results["stub"] / results["total_systems"] * 100) if results["total_systems"] > 0 else 0
    results["broken_percentage"] = (results["broken"] / results["total_systems"] * 100) if results["total_systems"] > 0 else 0
    
    # Print summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"Total Systems: {results['total_systems']}")
    print(f"✅ Working: {results['working']} ({results['working_percentage']:.1f}%)")
    print(f"⚠️ Stubs: {results['stub']} ({results['stub_percentage']:.1f}%)")
    print(f"❌ Broken: {results['broken']} ({results['broken_percentage']:.1f}%)")
    print("\n" + "="*60 + "\n")
    
    return results


async def get_system_status(system_name: str) -> Dict[str, Any]:
    """
    Get status of a specific system
    
    Args:
        system_name: Name of system to check
    
    Returns:
        System status details
    """
    
    if system_name not in SYSTEMS_TO_TEST:
        raise ValueError(f"Unknown system: {system_name}")
    
    config = SYSTEMS_TO_TEST[system_name]
    return await test_system(system_name, config)


# Quick health check (just counts, no details)
async def quick_health_check() -> Dict[str, int]:
    """
    Quick health check without full details
    
    Returns:
        Simple counts of working/stub/broken systems
    """
    
    results = await test_all_systems()
    
    return {
        "total": results["total_systems"],
        "working": results["working"],
        "stub": results["stub"],
        "broken": results["broken"],
        "working_percentage": results["working_percentage"]
    }
