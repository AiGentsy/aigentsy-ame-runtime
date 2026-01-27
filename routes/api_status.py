"""
API STATUS ROUTES: Monitor Premium API Credentials & Usage

Endpoints:
- GET /api/status - Overall API credential status
- GET /api/credentials/missing - List missing credentials
- GET /api/packs - List all API packs with status
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["API Status"])


@router.get("/status")
async def get_api_status():
    """
    Get overall API credential status

    Shows which of the 28 premium APIs are configured
    """
    try:
        from integrations.oauth_broker import get_oauth_broker

        broker = get_oauth_broker()
        status = broker.get_status()

        return {
            "ok": True,
            "total_loaded": status["total_loaded"],
            "total_expected": status["total_expected"],
            "coverage_pct": round(status["total_loaded"] / status["total_expected"] * 100, 1),
            "apis": status["apis"]
        }

    except Exception as e:
        logger.error(f"API status error: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@router.get("/credentials/missing")
async def get_missing_credentials():
    """
    List missing API credentials

    Returns list of expected APIs that don't have credentials configured
    """
    try:
        from integrations.oauth_broker import get_oauth_broker

        broker = get_oauth_broker()
        missing = broker.list_missing_apis()

        return {
            "ok": True,
            "total_missing": len(missing),
            "missing": missing,
            "recommendation": "Add these to Render environment variables" if missing else "All credentials loaded!"
        }

    except Exception as e:
        logger.error(f"Missing credentials error: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


@router.get("/packs")
async def get_api_packs():
    """
    List all premium API packs with status

    Shows pack name, priority, and whether credentials are available
    """
    try:
        from platforms.packs import get_api_packs, get_api_pack_count
        from integrations.oauth_broker import get_oauth_broker

        broker = get_oauth_broker()
        packs = get_api_packs()

        pack_status = []
        for pack in packs:
            name = pack.get('name', 'unknown')

            # Determine which credential this pack needs
            api_name = name.replace('_api', '').replace('_discovery', '').replace('_enhanced', '').replace('_marketplace', '').split('_')[0]

            has_creds = broker.has_credentials(api_name)

            pack_status.append({
                "name": name,
                "priority": pack.get('priority', 0),
                "has_api": pack.get('has_api', False),
                "requires_auth": pack.get('requires_auth', False),
                "credentials_loaded": has_creds,
                "status": "ready" if has_creds else "missing_credentials"
            })

        # Sort by priority
        pack_status.sort(key=lambda x: -x['priority'])

        ready_count = sum(1 for p in pack_status if p['credentials_loaded'])

        return {
            "ok": True,
            "total_packs": get_api_pack_count(),
            "ready": ready_count,
            "missing_credentials": len(pack_status) - ready_count,
            "packs": pack_status
        }

    except Exception as e:
        logger.error(f"API packs error: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


def log_api_status_on_startup():
    """
    Log API credential status on startup

    Call this from main.py startup event
    """
    try:
        from integrations.oauth_broker import get_oauth_broker

        broker = get_oauth_broker()

        logger.info("=" * 60)
        logger.info("API CREDENTIALS STATUS")
        logger.info("=" * 60)

        expected_apis = [
            'twitter', 'instagram', 'linkedin', 'github', 'shopify',
            'openrouter', 'perplexity', 'gemini', 'anthropic', 'stability', 'runway',
            'twilio', 'resend', 'jsonbin'
        ]

        loaded = 0
        for api in expected_apis:
            status = "LOADED" if broker.has_credentials(api) else "MISSING"
            if broker.has_credentials(api):
                loaded += 1
            logger.info(f"  {api:20s} {status}")

        logger.info("=" * 60)
        logger.info(f"Total APIs loaded: {loaded}/{len(expected_apis)}")
        logger.info("=" * 60)

    except Exception as e:
        logger.warning(f"Could not log API status: {e}")
