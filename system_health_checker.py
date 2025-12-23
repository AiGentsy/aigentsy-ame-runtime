"""
ULTIMATE SYSTEM HEALTH CHECKER
Tests ALL 143+ AiGentsy systems

Wade's complete arsenal - every single file tested
"""

import asyncio
import inspect
from datetime import datetime, timezone
from typing import Dict, Any, List
import traceback


# COMPLETE SYSTEM MAP - ALL 143 SYSTEMS
ULTIMATE_SYSTEMS = {
    # ===== CORE REVENUE (7 systems) =====
    "ame_pitches": {"module": "ame_pitches", "functions": ["generate_pitch"], "category": "Core Revenue"},
    "ame_routes": {"module": "ame_routes", "functions": None, "category": "Core Revenue"},
    "intent_exchange": {"module": "intent_exchange_UPGRADED", "functions": ["publish_intent"], "category": "Core Revenue"},
    "revenue_flows": {"module": "revenue_flows", "functions": ["calculate_base_fee"], "category": "Core Revenue"},
    "batch_payments": {"module": "batch_payments", "functions": None, "category": "Core Revenue"},
    "aigx_engine": {"module": "aigx_engine", "functions": ["credit_aigx"], "category": "Core Revenue"},
    "aigx_config": {"module": "aigx_config", "functions": None, "category": "Core Revenue"},
    
    # ===== FINANCIAL TOOLS (15 systems) =====
    "ocl_engine": {"module": "ocl_engine", "functions": ["calculate_ocl_limit"], "category": "Financial"},
    "ocl_expansion": {"module": "ocl_expansion", "functions": None, "category": "Financial"},
    "ocl_p2p": {"module": "ocl_p2p_lending", "functions": None, "category": "Financial"},
    "agent_factoring": {"module": "agent_factoring", "functions": None, "category": "Financial"},
    "agent_spending": {"module": "agent_spending", "functions": None, "category": "Financial"},
    "ipvault": {"module": "ipvault", "functions": None, "category": "Financial"},
    "escrow_lite": {"module": "escrow_lite", "functions": None, "category": "Financial"},
    "performance_bonds": {"module": "performance_bonds", "functions": None, "category": "Financial"},
    "subscription_engine": {"module": "subscription_engine", "functions": None, "category": "Financial"},
    "currency_engine": {"module": "currency_engine", "functions": None, "category": "Financial"},
    "state_money": {"module": "state_money", "functions": None, "category": "Financial"},
    "budget_manager": {"module": "budget_manager", "functions": None, "category": "Financial"},
    "pricing_arm": {"module": "pricing_arm", "functions": None, "category": "Financial"},
    "tax_reporting": {"module": "tax_reporting", "functions": None, "category": "Financial"},
    "warranty_engine": {"module": "warranty_engine", "functions": None, "category": "Financial"},
    
    # ===== MARKETPLACE (12 systems) =====
    "metabridge": {"module": "metabridge", "functions": ["create"], "category": "Marketplace"},
    "dealgraph": {"module": "metabridge_dealgraph_UPGRADED", "functions": ["create"], "category": "Marketplace"},
    "metabridge_runtime": {"module": "metabridge_runtime", "functions": None, "category": "Marketplace"},
    "dark_pool": {"module": "dark_pool", "functions": None, "category": "Marketplace"},
    "sponsor_pools": {"module": "sponsor_pools", "functions": None, "category": "Marketplace"},
    "coop_sponsors": {"module": "coop_sponsors", "functions": None, "category": "Marketplace"},
    "proof_pipe": {"module": "proof_pipe", "functions": None, "category": "Marketplace"},
    "jv_mesh": {"module": "jv_mesh", "functions": None, "category": "Marketplace"},
    "disputes": {"module": "disputes", "functions": None, "category": "Marketplace"},
    "dispute_resolution": {"module": "dispute_resolution", "functions": None, "category": "Marketplace"},
    "event_bus": {"module": "event_bus", "functions": None, "category": "Marketplace"},
    "events": {"module": "events", "functions": None, "category": "Marketplace"},
    
    # ===== GROWTH & OPTIMIZATION (16 systems) =====
    "growth_agent": {"module": "aigent_growth_agent", "functions": None, "category": "Growth"},
    "metamatch": {"module": "aigent_growth_metamatch", "functions": None, "category": "Growth"},
    "r3_router": {"module": "r3_router_UPGRADED", "functions": ["allocate"], "category": "Growth"},
    "r3_autopilot": {"module": "r3_autopilot", "functions": None, "category": "Growth"},
    "amg_orchestrator": {"module": "amg_orchestrator", "functions": None, "category": "Growth"},
    "analytics_engine": {"module": "analytics_engine", "functions": None, "category": "Growth"},
    "ltv_forecaster": {"module": "ltv_forecaster", "functions": None, "category": "Growth"},
    "autonomous_upgrades": {"module": "autonomous_upgrades", "functions": None, "category": "Growth"},
    "badge_engine": {"module": "badge_engine", "functions": None, "category": "Growth"},
    "booster_engine": {"module": "booster_engine", "functions": None, "category": "Growth"},
    "reputation_pricing": {"module": "reputation_pricing", "functions": None, "category": "Growth"},
    "reputation_knobs": {"module": "reputation_knobs", "functions": None, "category": "Growth"},
    "proposal_autoclose": {"module": "proposal_autoclose", "functions": None, "category": "Growth"},
    "proposal_delivery": {"module": "proposal_delivery", "functions": None, "category": "Growth"},
    "flow_arbitrage": {"module": "flow_arbitrage_detector", "functions": None, "category": "Growth"},
    "pain_point_detector": {"module": "pain_point_detector", "functions": None, "category": "Growth"},
    
    # ===== BUSINESS MODELS (5 systems) =====
    "franchise": {"module": "franchise_engine", "functions": None, "category": "Business Models"},
    "syndication": {"module": "syndication", "functions": None, "category": "Business Models"},
    "pwp_engine": {"module": "pwp_engine", "functions": None, "category": "Business Models"},
    "slo_engine": {"module": "slo_engine", "functions": None, "category": "Business Models"},
    "slo_tiers": {"module": "slo_tiers", "functions": None, "category": "Business Models"},
    
    # ===== ADVANCED FEATURES (10 systems) =====
    "pricing_oracle": {"module": "pricing_oracle", "functions": ["calculate_dynamic_price"], "category": "Advanced"},
    "bundle_engine": {"module": "bundle_engine", "functions": None, "category": "Advanced"},
    "template_integration": {"module": "template_integration_coordinator", "functions": None, "category": "Advanced"},
    "value_chain": {"module": "value_chain_engine", "functions": None, "category": "Advanced"},
    "yield_memory": {"module": "yield_memory", "functions": None, "category": "Advanced"},
    "mint_generator": {"module": "mint_generator", "functions": None, "category": "Advanced"},
    "device_oauth": {"module": "device_oauth_connector", "functions": None, "category": "Advanced"},
    "template_actionizer": {"module": "template_actionizer", "functions": None, "category": "Advanced"},
    "template_library": {"module": "template_library", "functions": None, "category": "Advanced"},
    "template_variations": {"module": "template_variations", "functions": None, "category": "Advanced"},
    
    # ===== INTELLIGENCE & AI (9 systems) =====
    "aigentsy_conductor": {"module": "aigentsy_conductor", "functions": None, "category": "Intelligence"},
    "execution_scorer": {"module": "execution_scorer", "functions": None, "category": "Intelligence"},
    "outcome_oracle": {"module": "outcome_oracle_max", "functions": ["on_event"], "category": "Intelligence"},
    "csuite_orchestrator": {"module": "csuite_orchestrator", "functions": None, "category": "Intelligence"},
    "csuite_base": {"module": "csuite_base", "functions": None, "category": "Intelligence"},
    "sdk_aam_executor": {"module": "sdk_aam_executor_UPGRADED", "functions": None, "category": "Intelligence"},
    "sdk_agent": {"module": "sdk_agent", "functions": None, "category": "Intelligence"},
    "venture_builder": {"module": "venture_builder_agent", "functions": None, "category": "Intelligence"},
    "remix_agent": {"module": "remix_agent", "functions": None, "category": "Intelligence"},
    
    # ===== DISCOVERY (5 systems) =====
    "alpha_discovery": {"module": "alpha_discovery_engine", "functions": None, "category": "Discovery"},
    "ultimate_discovery": {"module": "ultimate_discovery_engine", "functions": None, "category": "Discovery"},
    "advanced_discovery": {"module": "advanced_discovery_dimensions", "functions": None, "category": "Discovery"},
    "opportunity_approval": {"module": "opportunity_approval", "functions": None, "category": "Discovery"},
    "opportunity_engagement": {"module": "opportunity_engagement", "functions": None, "category": "Discovery"},
    "explicit_scrapers": {"module": "explicit_marketplace_scrapers", "functions": None, "category": "Discovery"},
    
    # ===== EXECUTION (8 systems) =====
    "execution_orchestrator": {"module": "execution_orchestrator", "functions": None, "category": "Execution"},
    "execution_routes": {"module": "execution_routes", "functions": None, "category": "Execution"},
    "autonomous_routes": {"module": "autonomous_routes", "functions": None, "category": "Execution"},
    "universal_executor": {"module": "universal_executor", "functions": None, "category": "Execution"},
    "platform_apis": {"module": "platform_apis", "functions": None, "category": "Execution"},
    "payment_collector": {"module": "payment_collector", "functions": None, "category": "Execution"},
    "approval_system": {"module": "approval_system", "functions": None, "category": "Execution"},
    "week1_api": {"module": "week1_api", "functions": None, "category": "Execution"},
    
    # ===== META SYSTEMS (3 systems) =====
    "metahive_brain": {"module": "metahive_brain", "functions": None, "category": "Meta"},
    "metahive_rewards": {"module": "metahive_rewards", "functions": None, "category": "Meta"},
    "agent_runtime": {"module": "agent_runtime_container", "functions": None, "category": "Meta"},
    
    # ===== INTEGRATIONS (20 systems) =====
    "aam_queue": {"module": "aam_queue_MERGED", "functions": None, "category": "Integrations"},
    "aam_stripe": {"module": "aam_stripe", "functions": None, "category": "Integrations"},
    "shopify_webhook": {"module": "shopify_webhook", "functions": None, "category": "Integrations"},
    "shopify_inventory": {"module": "shopify_inventory_proxy", "functions": None, "category": "Integrations"},
    "stripe_webhook": {"module": "stripe_webhook_handler", "functions": None, "category": "Integrations"},
    "dashboard_api": {"module": "dashboard_api", "functions": None, "category": "Integrations"},
    "dashboard_connector": {"module": "dashboard_connector", "functions": None, "category": "Integrations"},
    "storefront_deployer": {"module": "storefront_deployer", "functions": None, "category": "Integrations"},
    "vercel_deployer": {"module": "vercel_deployer", "functions": None, "category": "Integrations"},
    "supabase_provisioner": {"module": "supabase_provisioner", "functions": None, "category": "Integrations"},
    "resend_automator": {"module": "resend_automator", "functions": None, "category": "Integrations"},
    "messaging_adapters": {"module": "messaging_adapters", "functions": None, "category": "Integrations"},
    "openai_deployer": {"module": "openai_agent_deployer", "functions": None, "category": "Integrations"},
    "openrouter_helper": {"module": "openrouter_agent_helper", "functions": None, "category": "Integrations"},
    "jsonbin_client": {"module": "jsonbin_client", "functions": None, "category": "Integrations"},
    "log_to_jsonbin": {"module": "log_to_jsonbin", "functions": None, "category": "Integrations"},
    "sku_config": {"module": "sku_config_loader", "functions": None, "category": "Integrations"},
    "sku_orchestrator": {"module": "sku_orchestrator", "functions": None, "category": "Integrations"},
    "templates_catalog": {"module": "templates_catalog", "functions": None, "category": "Integrations"},
    "register_manifests": {"module": "register_manifests", "functions": None, "category": "Integrations"},
    
    # ===== RISK & COMPLIANCE (6 systems) =====
    "fraud_detector": {"module": "fraud_detector", "functions": None, "category": "Risk"},
    "compliance_oracle": {"module": "compliance_oracle", "functions": None, "category": "Risk"},
    "guardrails": {"module": "guardrails", "functions": None, "category": "Risk"},
    "risk_policies": {"module": "risk_policies", "functions": None, "category": "Risk"},
    "insurance_pool": {"module": "insurance_pool", "functions": None, "category": "Risk"},
    "helpers_net": {"module": "helpers_net", "functions": None, "category": "Risk"},
    
    # ===== KNOWLEDGE & DATA (4 systems) =====
    "industry_knowledge": {"module": "industry_knowledge", "functions": None, "category": "Knowledge"},
    "business_ingestion": {"module": "business_ingestion", "functions": None, "category": "Knowledge"},
    "actionization_routes": {"module": "actionization_routes", "functions": None, "category": "Knowledge"},
    "alpha_discovery_main": {"module": "alpha_discovery_main_integration", "functions": None, "category": "Knowledge"},
    
    # ===== APEX ULTRA (1 mega-system) =====
    "apex_ultra": {"module": "aigentsy_apex_ultra", "functions": ["activate_apex_ultra"], "category": "Apex"},
    
    # ===== UTILITIES (9 systems) =====
    "wade_dashboard": {"module": "wade_approval_dashboard", "functions": None, "category": "Utilities"},
    "system_health": {"module": "system_health_checker", "functions": None, "category": "Utilities"},
    "migrate_jsonbin": {"module": "migrate_jsonbin_records", "functions": None, "category": "Utilities"},
    "normalize_jsonbin": {"module": "normalize_jsonbin", "functions": None, "category": "Utilities"},
    "validate_jsonbin": {"module": "validate_jsonbin", "functions": None, "category": "Utilities"},
    "test_discovery": {"module": "test_alpha_discovery", "functions": None, "category": "Utilities"},
    "test_phase1": {"module": "test_phase1_integration", "functions": None, "category": "Utilities"},
    "run_smoketest": {"module": "run_aam_smoketest", "functions": None, "category": "Utilities"},
    "run_outcome_sim": {"module": "run_outcome_sim", "functions": None, "category": "Utilities"},
}


async def test_system(system_name: str, config: Dict) -> Dict[str, Any]:
    """Test a single system"""
    
    result = {
        "system": system_name,
        "category": config["category"],
        "module": config["module"],
        "status": "unknown",
        "error": None
    }
    
    try:
        module = __import__(config["module"])
        result["status"] = "working"
        result["details"] = "import_success"
        
        # If functions specified, test them
        if config.get("functions"):
            for func_name in config["functions"]:
                if not hasattr(module, func_name):
                    result["status"] = "stub"
                    result["details"] = f"missing_{func_name}"
                    break
    
    except ImportError as e:
        result["status"] = "broken"
        result["error"] = f"Import failed: {str(e)[:80]}"
    except Exception as e:
        result["status"] = "broken"
        result["error"] = f"Error: {str(e)[:80]}"
    
    return result


async def test_all_systems() -> Dict[str, Any]:
    """Test ALL systems"""
    
    print("\n" + "="*70)
    print("🔍 ULTIMATE SYSTEM HEALTH CHECK")
    print(f"Testing {len(ULTIMATE_SYSTEMS)} systems...")
    print("="*70 + "\n")
    
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_systems": len(ULTIMATE_SYSTEMS),
        "working": 0,
        "stub": 0,
        "broken": 0,
        "by_category": {},
        "systems": {}
    }
    
    # Test each system
    for system_name, config in ULTIMATE_SYSTEMS.items():
        result = await test_system(system_name, config)
        results["systems"][system_name] = result
        
        # Update counts
        status = result["status"]
        if status == "working":
            results["working"] += 1
            icon = "✅"
        elif status == "stub":
            results["stub"] += 1
            icon = "⚠️"
        else:
            results["broken"] += 1
            icon = "❌"
        
        print(f"{icon} {system_name:35s} [{config['category']}]")
        
        # Update category stats
        category = config["category"]
        if category not in results["by_category"]:
            results["by_category"][category] = {"working": 0, "stub": 0, "broken": 0, "total": 0}
        
        results["by_category"][category]["total"] += 1
        results["by_category"][category][status] += 1
    
    # Calculate percentages
    total = results["total_systems"]
    results["working_percentage"] = (results["working"] / total * 100) if total > 0 else 0
    results["stub_percentage"] = (results["stub"] / total * 100) if total > 0 else 0
    results["broken_percentage"] = (results["broken"] / total * 100) if total > 0 else 0
    
    # Print summary
    print("\n" + "="*70)
    print("📊 SUMMARY BY CATEGORY")
    print("="*70)
    
    for category, stats in sorted(results["by_category"].items()):
        print(f"\n{category}:")
        print(f"  Total: {stats['total']}")
        print(f"  ✅ Working: {stats['working']}")
        print(f"  ⚠️ Stubs: {stats['stub']}")
        print(f"  ❌ Broken: {stats['broken']}")
    
    print("\n" + "="*70)
    print("🎯 OVERALL RESULTS")
    print("="*70)
    print(f"Total Systems: {results['total_systems']}")
    print(f"✅ WORKING: {results['working']} ({results['working_percentage']:.1f}%)")
    print(f"⚠️ STUBS: {results['stub']} ({results['stub_percentage']:.1f}%)")
    print(f"❌ BROKEN: {results['broken']} ({results['broken_percentage']:.1f}%)")
    print("="*70 + "\n")
    
    return results


async def quick_health_check() -> Dict[str, int]:
    """Quick health check"""
    results = await test_all_systems()
    
    return {
        "total": results["total_systems"],
        "working": results["working"],
        "stub": results["stub"],
        "broken": results["broken"],
        "working_percentage": results["working_percentage"]
    }
