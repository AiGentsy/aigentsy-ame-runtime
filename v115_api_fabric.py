"""
V115 API FABRIC - UNIFIED API WIRING FOR MONETIZATION
======================================================

Wires all your available APIs through to v115/fabric logic for monetization:

PAYMENT LAYER:
├── Stripe (payments, invoices, payment links, PSP routing)
└── Shopify (e-commerce, abandoned carts, order tracking)

SOCIAL SIGNAL LAYER:
├── Twitter (purchase intent scraping, DM outreach)
├── Instagram (shopping signals, engagement)
└── LinkedIn (B2B signals, professional outreach)

COMMUNICATION LAYER:
├── Twilio SMS (cart recovery, support automation)
└── Resend Email (outreach, invoice reminders)

AI GENERATION LAYER:
├── OpenRouter (Claude + GPT-4 for content)
├── Gemini (vision tasks)
├── Perplexity (web search for purchase intent)
├── Stability AI (image generation)
└── RunwayML (video generation)

STORAGE LAYER:
├── JSONBin (data logging)
└── GitHub (code operations)

This module:
1. Validates all API configurations
2. Creates unified connectors
3. Wires to V111 Super-Harvesters
4. Integrates with V115 ApexEngine sleep mode
5. Enables continuous monetization

Usage:
    from v115_api_fabric import get_fabric_status, run_monetization_cycle
"""

import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# ═══════════════════════════════════════════════════════════════════════════════
# API VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def validate_all_apis() -> Dict[str, Any]:
    """Validate all API configurations and return readiness status"""

    apis = {}

    # PAYMENTS - STRIPE (supports both STRIPE_SECRET and STRIPE_SECRET_KEY)
    apis["stripe"] = {
        "name": "Stripe Payments",
        "configured": bool(os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET")),
        "webhook_ready": bool(os.getenv("STRIPE_WEBHOOK_SECRET")),
        "env_vars": ["STRIPE_SECRET_KEY", "STRIPE_SECRET", "STRIPE_WEBHOOK_SECRET"],
        "engines": ["v111_uacr", "v111_receivables", "v111_payments", "v108_service_bnpl"],
        "revenue_potential": "High - Direct payment processing"
    }

    # E-COMMERCE - SHOPIFY (Optional - only for direct AiGentsy storefront)
    apis["shopify"] = {
        "name": "Shopify E-Commerce",
        "configured": bool(os.getenv("SHOPIFY_ADMIN_TOKEN") or os.getenv("SHOPIFY_ACCESS_TOKEN")),
        "webhook_ready": bool(os.getenv("SHOPIFY_WEBHOOK_SECRET")),
        "env_vars": ["SHOPIFY_ADMIN_TOKEN", "SHOPIFY_SHOP_URL", "SHOPIFY_WEBHOOK_SECRET"],
        "engines": ["direct_storefront"],
        "revenue_potential": "Optional - Only for direct AiGentsy storefront"
    }

    # AFFILIATE NETWORKS - AMAZON ASSOCIATES (For U-ACR $4.6T TAM)
    apis["amazon_affiliate"] = {
        "name": "Amazon Associates",
        "configured": True,  # Always configured with default tag
        "env_vars": ["AMAZON_AFFILIATE_TAG"],
        "default_tag": "aigentsy-20",
        "engines": ["v111_uacr", "affiliate_matching"],
        "revenue_potential": "High - Affiliate matching ($4.6T TAM)"
    }

    # SOCIAL - TWITTER
    apis["twitter"] = {
        "name": "Twitter/X",
        "configured": bool(os.getenv("TWITTER_BEARER_TOKEN")) or all([
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_SECRET")
        ]),
        "bearer_token": bool(os.getenv("TWITTER_BEARER_TOKEN")),
        "oauth_configured": all([
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_SECRET")
        ]),
        "env_vars": ["TWITTER_BEARER_TOKEN", "TWITTER_API_KEY", "TWITTER_API_SECRET",
                     "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET"],
        "engines": ["v111_uacr", "v108_creator_network", "social_signals"],
        "capabilities": ["search", "dm_outreach"] if os.getenv("TWITTER_ACCESS_TOKEN") else ["search"],
        "revenue_potential": "Medium - Purchase intent signals"
    }

    # SOCIAL - INSTAGRAM
    apis["instagram"] = {
        "name": "Instagram",
        "configured": all([os.getenv("INSTAGRAM_ACCESS_TOKEN"), os.getenv("INSTAGRAM_BUSINESS_ID")]),
        "env_vars": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ID"],
        "engines": ["v111_uacr", "v108_creator_network", "social_signals"],
        "revenue_potential": "Medium - Shopping intent signals"
    }

    # SOCIAL - LINKEDIN
    apis["linkedin"] = {
        "name": "LinkedIn B2B",
        "configured": bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
        "oauth_configured": all([
            os.getenv("LINKEDIN_ACCESS_TOKEN"),
            os.getenv("LINKEDIN_CLIENT_ID"),
            os.getenv("LINKEDIN_CLIENT_SECRET")
        ]),
        "env_vars": ["LINKEDIN_ACCESS_TOKEN", "LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"],
        "engines": ["v108_creator_network", "b2b_signals"],
        "capabilities": ["post", "message"] if os.getenv("LINKEDIN_ACCESS_TOKEN") else [],
        "revenue_potential": "High - B2B deal flow"
    }

    # COMMUNICATION - TWILIO
    apis["twilio"] = {
        "name": "Twilio SMS",
        "configured": all([
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN"),
            os.getenv("TWILIO_PHONE_NUMBER")
        ]),
        "env_vars": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_PHONE_NUMBER"],
        "engines": ["v110_support_queue", "cart_recovery_sms"],
        "revenue_potential": "Medium - SMS automation"
    }

    # COMMUNICATION - RESEND
    apis["resend"] = {
        "name": "Resend Email",
        "configured": bool(os.getenv("RESEND_API_KEY")),
        "env_vars": ["RESEND_API_KEY", "RESEND_FROM_EMAIL"],
        "engines": ["v110_email_automation", "cart_recovery_email", "invoice_reminders"],
        "revenue_potential": "Medium - Email automation"
    }

    # AI - OPENROUTER
    apis["openrouter"] = {
        "name": "OpenRouter (Claude + GPT-4)",
        "configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "env_vars": ["OPENROUTER_API_KEY"],
        "engines": ["ai_generation", "content_personalization", "dm_templates"],
        "revenue_potential": "Enabling - Powers intelligent content"
    }

    # AI - GEMINI
    apis["gemini"] = {
        "name": "Google Gemini",
        "configured": bool(os.getenv("GEMINI_API_KEY")),
        "env_vars": ["GEMINI_API_KEY"],
        "engines": ["ai_fallback", "vision_tasks"],
        "revenue_potential": "Enabling - Fallback AI"
    }

    # AI - PERPLEXITY
    apis["perplexity"] = {
        "name": "Perplexity Web Search",
        "configured": bool(os.getenv("PERPLEXITY_API_KEY")),
        "env_vars": ["PERPLEXITY_API_KEY"],
        "engines": ["v111_uacr", "market_research", "web_search"],
        "revenue_potential": "High - Quality purchase intent detection"
    }

    # CONTENT - STABILITY
    apis["stability"] = {
        "name": "Stability AI",
        "configured": bool(os.getenv("STABILITY_API_KEY")),
        "env_vars": ["STABILITY_API_KEY"],
        "engines": ["v109_content_generation", "image_generation"],
        "revenue_potential": "Medium - Content creation"
    }

    # CONTENT - RUNWAY
    apis["runway"] = {
        "name": "RunwayML Video",
        "configured": bool(os.getenv("RUNWAV_API_KEY")),
        "env_vars": ["RUNWAV_API_KEY"],
        "engines": ["v109_content_generation", "video_generation"],
        "revenue_potential": "Medium - Video content"
    }

    # STORAGE - JSONBIN
    apis["jsonbin"] = {
        "name": "JSONBin Storage",
        "configured": bool(os.getenv("JSONBIN_SECRET")),
        "env_vars": ["JSONBIN_SECRET", "JSONBIN_URL"],
        "engines": ["data_storage", "logging"],
        "revenue_potential": "Enabling - Data persistence"
    }

    # DEV - GITHUB
    apis["github"] = {
        "name": "GitHub",
        "configured": bool(os.getenv("GITHUB_TOKEN")),
        "env_vars": ["GITHUB_TOKEN"],
        "engines": ["code_execution", "repo_management"],
        "revenue_potential": "Low - Dev operations"
    }

    # Calculate totals
    configured_count = sum(1 for api in apis.values() if api["configured"])
    total_count = len(apis)

    return {
        "ok": True,
        "configured_count": configured_count,
        "total_count": total_count,
        "configuration_pct": round(configured_count / total_count * 100, 1),
        "apis": apis,
        "validated_at": _now()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENGINE READINESS
# ═══════════════════════════════════════════════════════════════════════════════

def get_engine_readiness() -> Dict[str, Any]:
    """Get readiness status for all V106-V115 revenue engines"""

    apis = validate_all_apis()["apis"]

    engines = {
        # V111 SUPER-HARVESTERS
        "v111_uacr": {
            "name": "U-ACR (Affiliate Matching)",
            "version": "V111",
            "tam": "$4.6T",
            "required_apis": ["twitter", "instagram", "amazon_affiliate"],
            "optional_apis": ["perplexity", "twilio", "resend", "openrouter"],
            "description": "Capture purchase intent signals from social, match to affiliate offers (3-15% commission)"
        },
        "v111_receivables": {
            "name": "Receivables Desk",
            "version": "V111",
            "tam": "$1.5T",
            "required_apis": ["stripe"],
            "optional_apis": ["resend", "twilio"],
            "description": "Kelly-sized advances on unpaid invoices"
        },
        "v111_payments": {
            "name": "Payments Optimizer",
            "version": "V111",
            "tam": "$260B",
            "required_apis": ["stripe"],
            "optional_apis": [],
            "description": "Route transactions to optimal PSP for savings"
        },

        # V110 GAP HARVESTERS
        "v110_support_queue": {
            "name": "Support Queue Monetizer",
            "version": "V110",
            "required_apis": ["twilio"],
            "optional_apis": ["openrouter", "resend"],
            "description": "Monetize support interactions via SMS"
        },
        "v110_email_automation": {
            "name": "Email Automation",
            "version": "V110",
            "required_apis": ["resend"],
            "optional_apis": ["openrouter"],
            "description": "Automated email sequences for conversion"
        },

        # V108 OVERLAYS
        "v108_creator_network": {
            "name": "Creator Performance Network",
            "version": "V108",
            "required_apis": ["twitter", "instagram"],
            "optional_apis": ["linkedin"],
            "description": "Track and monetize creator engagement"
        },
        "v108_service_bnpl": {
            "name": "Service BNPL",
            "version": "V108",
            "required_apis": ["stripe"],
            "optional_apis": [],
            "description": "Buy-now-pay-later for services"
        },

        # V109 OVERLAYS
        "v109_content_generation": {
            "name": "Content Generation",
            "version": "V109",
            "required_apis": ["stability"],
            "optional_apis": ["runway", "openrouter"],
            "description": "AI-powered content creation"
        }
    }

    readiness = {}
    ready_count = 0

    for engine_id, engine_info in engines.items():
        required = engine_info["required_apis"]
        optional = engine_info.get("optional_apis", [])

        required_configured = all(apis.get(api, {}).get("configured", False) for api in required)
        optional_configured = [api for api in optional if apis.get(api, {}).get("configured", False)]
        missing_required = [api for api in required if not apis.get(api, {}).get("configured", False)]

        if required_configured:
            ready_count += 1

        readiness[engine_id] = {
            **engine_info,
            "ready": required_configured,
            "status": "READY" if required_configured else "MISSING_APIS",
            "required_configured": [api for api in required if apis.get(api, {}).get("configured", False)],
            "missing_required": missing_required,
            "optional_configured": optional_configured
        }

    return {
        "ok": True,
        "engines_ready": ready_count,
        "engines_total": len(engines),
        "readiness_pct": round(ready_count / len(engines) * 100, 1),
        "engines": readiness,
        "checked_at": _now()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED MONETIZATION CYCLE
# ═══════════════════════════════════════════════════════════════════════════════

async def run_monetization_cycle() -> Dict[str, Any]:
    """
    Run one complete monetization cycle using all available APIs.
    This is the unified entry point for V115 fabric logic.
    """

    cycle_id = f"cycle_{int(datetime.now().timestamp())}"
    results = {
        "cycle_id": cycle_id,
        "started_at": _now(),
        "steps": {}
    }

    # Step 1: Validate APIs
    api_status = validate_all_apis()
    results["api_status"] = {
        "configured": api_status["configured_count"],
        "total": api_status["total_count"]
    }

    # Step 2: Check engine readiness
    engine_status = get_engine_readiness()
    results["engine_status"] = {
        "ready": engine_status["engines_ready"],
        "total": engine_status["engines_total"]
    }

    # Step 3: Run V111 Super-Harvesters if ready
    v111_results = {}

    # U-ACR: Scrape social signals → Ingest → Quote → Fulfill
    if engine_status["engines"].get("v111_uacr", {}).get("ready"):
        try:
            from v111_production_integrations import (
                scrape_twitter_purchase_signals,
                scrape_instagram_shopping_signals,
                scrape_perplexity_purchase_signals,
                PERPLEXITY_AVAILABLE
            )
            from v111_gapharvester_ii import uacr_ingest_signals, get_canary_metrics

            # Scrape Twitter
            twitter_signals = await scrape_twitter_purchase_signals(max_results=50)

            # Scrape Instagram
            instagram_signals = await scrape_instagram_shopping_signals()

            # Scrape Perplexity (high-quality)
            perplexity_signals = []
            if PERPLEXITY_AVAILABLE:
                perplexity_signals = await scrape_perplexity_purchase_signals(max_signals=10)

            # Combine all signals
            all_signals = twitter_signals + instagram_signals + perplexity_signals

            # Ingest
            if all_signals:
                ingest_result = await uacr_ingest_signals(all_signals, source_type="v115_fabric")
                v111_results["uacr"] = {
                    "signals_captured": len(all_signals),
                    "signals_ingested": ingest_result.get("signals_ingested", 0),
                    "sources": {
                        "twitter": len(twitter_signals),
                        "instagram": len(instagram_signals),
                        "perplexity": len(perplexity_signals)
                    }
                }
            else:
                v111_results["uacr"] = {"signals_captured": 0, "note": "No signals found"}

            # Get canary metrics
            canary = await get_canary_metrics()
            v111_results["canary_health"] = canary.get("all_healthy", False)

        except Exception as e:
            v111_results["uacr"] = {"error": str(e)}
    else:
        v111_results["uacr"] = {"skipped": True, "reason": "missing_apis"}

    # Receivables Desk: Sync Stripe invoices
    if engine_status["engines"].get("v111_receivables", {}).get("ready"):
        try:
            from v111_production_integrations import STRIPE_AVAILABLE

            if STRIPE_AVAILABLE:
                import stripe
                from v111_gapharvester_ii import receivables_ingest

                # Get open invoices
                invoices = stripe.Invoice.list(status="open", limit=50)

                invoice_data = []
                for inv in invoices.auto_paging_iter():
                    invoice_data.append({
                        "invoice_id": inv.id,
                        "amount": inv.amount_due / 100,
                        "customer": inv.customer_email or inv.customer,
                        "due_date": inv.due_date,
                        "days_outstanding": (datetime.now(timezone.utc).timestamp() - inv.created) // 86400 if inv.created else 0
                    })

                if invoice_data:
                    result = await receivables_ingest(invoice_data, platform="stripe")
                    v111_results["receivables"] = {
                        "invoices_found": len(invoice_data),
                        "invoices_ingested": result.get("invoices_ingested", 0)
                    }
                else:
                    v111_results["receivables"] = {"invoices_found": 0}
            else:
                v111_results["receivables"] = {"skipped": True, "reason": "stripe_not_available"}
        except Exception as e:
            v111_results["receivables"] = {"error": str(e)}
    else:
        v111_results["receivables"] = {"skipped": True, "reason": "missing_apis"}

    results["steps"]["v111_super_harvesters"] = v111_results

    # Step 4: Run V115 ApexEngine cycle
    try:
        from apex_integration import run_sleep_mode_cycle, get_apex_stats

        apex_result = await run_sleep_mode_cycle()
        results["steps"]["apex_cycle"] = {
            "cycle_id": apex_result.get("cycle_id"),
            "opportunities_found": apex_result.get("steps", {}).get("discovery", {}).get("opportunities_found", 0),
            "quotes_generated": apex_result.get("steps", {}).get("quote", {}).get("quotes_generated", 0),
            "revenue_collected": apex_result.get("steps", {}).get("collect", {}).get("total_collected", 0)
        }

        results["apex_stats"] = get_apex_stats()

    except Exception as e:
        results["steps"]["apex_cycle"] = {"error": str(e)}

    results["completed_at"] = _now()

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# FABRIC STATUS ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════

def get_fabric_status() -> Dict[str, Any]:
    """Get complete fabric status for all APIs and engines"""

    api_status = validate_all_apis()
    engine_status = get_engine_readiness()

    # Calculate TAM for ready engines
    tam_map = {
        "v111_uacr": 4.6,      # $4.6T
        "v111_receivables": 1.5,  # $1.5T
        "v111_payments": 0.26     # $260B
    }

    addressable_tam = sum(
        tam_map.get(engine_id, 0)
        for engine_id, info in engine_status["engines"].items()
        if info.get("ready")
    )

    # Ready Super-Harvesters
    super_harvesters_ready = [
        engine_id for engine_id in ["v111_uacr", "v111_receivables", "v111_payments"]
        if engine_status["engines"].get(engine_id, {}).get("ready")
    ]

    return {
        "ok": True,
        "summary": {
            "apis_configured": f"{api_status['configured_count']}/{api_status['total_count']}",
            "engines_ready": f"{engine_status['engines_ready']}/{engine_status['engines_total']}",
            "addressable_tam": f"${addressable_tam}T",
            "super_harvesters_ready": len(super_harvesters_ready)
        },
        "v111_super_harvesters": {
            engine_id: engine_status["engines"].get(engine_id)
            for engine_id in ["v111_uacr", "v111_receivables", "v111_payments"]
        },
        "apis": api_status["apis"],
        "engines": engine_status["engines"],
        "fabric_version": "v115",
        "checked_at": _now()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_v115_fabric(app):
    """Add V115 fabric endpoints to FastAPI app"""

    @app.get("/v115/fabric/status")
    async def fabric_status():
        """Get complete V115 fabric status"""
        return get_fabric_status()

    @app.get("/v115/fabric/apis")
    async def api_validation():
        """Get API validation status"""
        return validate_all_apis()

    @app.get("/v115/fabric/engines")
    async def engine_readiness():
        """Get engine readiness status"""
        return get_engine_readiness()

    @app.post("/v115/fabric/run-cycle")
    async def run_cycle():
        """Run one complete monetization cycle"""
        return await run_monetization_cycle()

    print("=" * 80)
    print("🔌 V115 API FABRIC LOADED")
    print("=" * 80)

    status = get_fabric_status()
    print(f"APIs Configured: {status['summary']['apis_configured']}")
    print(f"Engines Ready: {status['summary']['engines_ready']}")
    print(f"Addressable TAM: {status['summary']['addressable_tam']}")
    print()
    print("V111 Super-Harvesters:")
    for engine_id, info in status["v111_super_harvesters"].items():
        status_icon = "✅" if info.get("ready") else "❌"
        print(f"  {status_icon} {info.get('name')} ({info.get('tam', 'N/A')})")

    print("=" * 80)
    print("Endpoints:")
    print("  GET  /v115/fabric/status")
    print("  GET  /v115/fabric/apis")
    print("  GET  /v115/fabric/engines")
    print("  POST /v115/fabric/run-cycle")
    print("=" * 80)


# ═══════════════════════════════════════════════════════════════════════════════
# PRINT STATUS ON IMPORT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\nV115 API Fabric Status:\n")
    status = get_fabric_status()

    print(f"Summary:")
    print(f"  APIs: {status['summary']['apis_configured']}")
    print(f"  Engines: {status['summary']['engines_ready']}")
    print(f"  TAM: {status['summary']['addressable_tam']}")

    print(f"\nSuper-Harvesters:")
    for engine_id, info in status["v111_super_harvesters"].items():
        icon = "✅" if info.get("ready") else "❌"
        print(f"  {icon} {info.get('name')}")
        if not info.get("ready"):
            print(f"      Missing: {', '.join(info.get('missing_required', []))}")
