"""
═══════════════════════════════════════════════════════════════════════════════
OAUTH CREDENTIAL MANAGER
═══════════════════════════════════════════════════════════════════════════════

Manages OAuth credentials and API keys for all platforms.
Provides endpoints to check credential status and identify missing credentials.

USAGE:
    from oauth_credential_manager import include_credential_endpoints

    include_credential_endpoints(app)

ENDPOINTS:
    GET  /credentials/status           - Get all credential status
    GET  /credentials/missing          - Get missing credentials
    GET  /pdl/missing-credentials      - Get PDLs blocked by missing credentials
    GET  /credentials/setup-guide      - Get setup instructions
    POST /credentials/validate         - Validate a specific credential
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import os
import aiohttp

router = APIRouter(tags=["Credentials"])


def _now():
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# CREDENTIAL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

CREDENTIALS = {
    # ═══════════════════════════════════════════════════════════════════════════
    # TIER 1: FREE APIs (just need account)
    # ═══════════════════════════════════════════════════════════════════════════
    "GITHUB_TOKEN": {
        "name": "GitHub Personal Access Token",
        "platform": "github",
        "tier": "free",
        "required_for": ["github.post_comment", "github.create_issue", "github.star_repo"],
        "setup_url": "https://github.com/settings/tokens",
        "setup_steps": [
            "1. Go to GitHub Settings > Developer Settings > Personal Access Tokens",
            "2. Click 'Generate new token (classic)'",
            "3. Select scopes: repo, read:user, write:discussion",
            "4. Copy token and add to environment as GITHUB_TOKEN"
        ],
        "validation_endpoint": "https://api.github.com/user",
        "validation_header": "Authorization: token {value}"
    },

    "REDDIT_CLIENT_ID": {
        "name": "Reddit OAuth App Client ID",
        "platform": "reddit",
        "tier": "free",
        "required_for": ["reddit.post_comment", "reddit.create_post"],
        "setup_url": "https://www.reddit.com/prefs/apps",
        "setup_steps": [
            "1. Go to Reddit App Preferences",
            "2. Click 'Create App' or 'Create Another App'",
            "3. Choose 'script' type",
            "4. Copy Client ID (under app name) to REDDIT_CLIENT_ID",
            "5. Copy Client Secret to REDDIT_CLIENT_SECRET"
        ],
        "related_keys": ["REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD"]
    },

    "REDDIT_CLIENT_SECRET": {
        "name": "Reddit OAuth App Client Secret",
        "platform": "reddit",
        "tier": "free",
        "required_for": ["reddit.post_comment", "reddit.create_post"],
        "setup_url": "https://www.reddit.com/prefs/apps",
        "related_keys": ["REDDIT_CLIENT_ID"]
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # TIER 2: PAID APIs
    # ═══════════════════════════════════════════════════════════════════════════
    "TWITTER_BEARER_TOKEN": {
        "name": "Twitter/X API Bearer Token",
        "platform": "twitter",
        "tier": "paid",
        "cost": "$100/month (Basic) or Free (read-only)",
        "required_for": ["twitter.post_tweet", "twitter.reply"],
        "setup_url": "https://developer.twitter.com/en/portal/dashboard",
        "setup_steps": [
            "1. Apply for Twitter Developer account",
            "2. Create a Project and App",
            "3. Generate Bearer Token in 'Keys and Tokens'",
            "4. For write access, need Basic tier ($100/month)"
        ]
    },

    "LINKEDIN_ACCESS_TOKEN": {
        "name": "LinkedIn OAuth Access Token",
        "platform": "linkedin",
        "tier": "oauth",
        "required_for": ["linkedin.post_update", "linkedin.send_message"],
        "setup_url": "https://www.linkedin.com/developers/apps",
        "setup_steps": [
            "1. Create LinkedIn Developer App",
            "2. Request 'w_member_social' permission",
            "3. Complete OAuth flow to get access token",
            "4. Tokens expire - need refresh mechanism"
        ],
        "note": "Requires OAuth flow - cannot use static token"
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # TIER 3: MARKETPLACE OAUTH (Complex setup)
    # ═══════════════════════════════════════════════════════════════════════════
    "UPWORK_ACCESS_TOKEN": {
        "name": "Upwork OAuth Access Token",
        "platform": "upwork",
        "tier": "oauth",
        "required_for": ["upwork.submit_proposal", "upwork.search_jobs"],
        "setup_url": "https://www.upwork.com/developer/keys/apply",
        "setup_steps": [
            "1. Apply for Upwork API access (requires approval)",
            "2. Create OAuth app once approved",
            "3. Implement OAuth 1.0a flow",
            "4. Store access token and secret"
        ],
        "note": "Upwork API access requires application approval",
        "related_keys": ["UPWORK_ACCESS_SECRET", "UPWORK_CONSUMER_KEY", "UPWORK_CONSUMER_SECRET"]
    },

    "FIVERR_API_KEY": {
        "name": "Fiverr API Key",
        "platform": "fiverr",
        "tier": "oauth",
        "required_for": ["fiverr.check_orders", "fiverr.send_message"],
        "setup_url": "https://www.fiverr.com/",
        "setup_steps": [
            "1. Fiverr does not offer public API",
            "2. Use browser automation via Universal Fabric instead",
            "3. Or apply for Fiverr Business API (enterprise only)"
        ],
        "note": "No public API - use browser automation",
        "alternative": "BROWSER_AUTOMATION"
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # TIER 4: AI/LLM APIs
    # ═══════════════════════════════════════════════════════════════════════════
    "OPENAI_API_KEY": {
        "name": "OpenAI API Key",
        "platform": "ai",
        "tier": "paid",
        "cost": "Pay per token (~$0.002/1K tokens for GPT-3.5)",
        "required_for": ["ai.generate_content", "ai.analyze_opportunity"],
        "setup_url": "https://platform.openai.com/api-keys",
        "setup_steps": [
            "1. Create OpenAI account",
            "2. Add payment method",
            "3. Generate API key in Settings > API Keys"
        ],
        "validation_endpoint": "https://api.openai.com/v1/models"
    },

    "ANTHROPIC_API_KEY": {
        "name": "Anthropic API Key",
        "platform": "ai",
        "tier": "paid",
        "cost": "Pay per token (~$0.008/1K tokens for Claude 3)",
        "required_for": ["ai.generate_content", "ai.analyze_opportunity"],
        "setup_url": "https://console.anthropic.com/",
        "setup_steps": [
            "1. Create Anthropic account",
            "2. Add payment method",
            "3. Generate API key in Settings"
        ]
    },

    "PERPLEXITY_API_KEY": {
        "name": "Perplexity API Key",
        "platform": "ai",
        "tier": "paid",
        "cost": "$20/month Pro or pay-per-query",
        "required_for": ["search.perplexity", "ai.research"],
        "setup_url": "https://www.perplexity.ai/settings/api",
        "setup_steps": [
            "1. Create Perplexity account",
            "2. Subscribe to Pro or API plan",
            "3. Generate API key in Settings > API"
        ]
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # TIER 5: PAYMENT PROCESSING
    # ═══════════════════════════════════════════════════════════════════════════
    "STRIPE_SECRET_KEY": {
        "name": "Stripe Secret Key",
        "platform": "stripe",
        "tier": "free",
        "required_for": ["stripe.create_payment", "stripe.create_customer"],
        "setup_url": "https://dashboard.stripe.com/apikeys",
        "setup_steps": [
            "1. Create Stripe account",
            "2. Go to Developers > API Keys",
            "3. Copy Secret Key (starts with sk_)"
        ],
        "related_keys": ["STRIPE_PUBLISHABLE_KEY", "STRIPE_WEBHOOK_SECRET"]
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # TIER 6: SEARCH APIs
    # ═══════════════════════════════════════════════════════════════════════════
    "SERPER_API_KEY": {
        "name": "Serper API Key (Google Search)",
        "platform": "search",
        "tier": "freemium",
        "cost": "2500 free queries/month, then $50/month",
        "required_for": ["search.google", "search.serper"],
        "setup_url": "https://serper.dev/",
        "setup_steps": [
            "1. Create Serper account",
            "2. Copy API key from dashboard"
        ]
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # TIER 7: EMAIL
    # ═══════════════════════════════════════════════════════════════════════════
    "SENDGRID_API_KEY": {
        "name": "SendGrid API Key",
        "platform": "email",
        "tier": "freemium",
        "cost": "100 emails/day free, then $15/month",
        "required_for": ["email.send", "email.campaign"],
        "setup_url": "https://app.sendgrid.com/settings/api_keys",
        "setup_steps": [
            "1. Create SendGrid account",
            "2. Go to Settings > API Keys",
            "3. Create API key with 'Full Access'"
        ]
    }
}


# ═══════════════════════════════════════════════════════════════════════════════
# CREDENTIAL STATUS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_credential_status() -> Dict[str, Any]:
    """Get status of all credentials"""
    status = {
        "configured": [],
        "missing": [],
        "by_platform": {},
        "by_tier": {
            "free": {"configured": 0, "missing": 0},
            "paid": {"configured": 0, "missing": 0},
            "oauth": {"configured": 0, "missing": 0},
            "freemium": {"configured": 0, "missing": 0}
        }
    }

    for key, config in CREDENTIALS.items():
        value = os.getenv(key)
        is_configured = bool(value)

        platform = config.get("platform", "other")
        tier = config.get("tier", "other")

        entry = {
            "key": key,
            "name": config["name"],
            "platform": platform,
            "tier": tier,
            "configured": is_configured,
            "required_for": config.get("required_for", [])
        }

        if is_configured:
            status["configured"].append(entry)
            # Mask the value for security
            entry["value_preview"] = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
        else:
            status["missing"].append(entry)
            entry["setup_url"] = config.get("setup_url")

        # Group by platform
        if platform not in status["by_platform"]:
            status["by_platform"][platform] = {"configured": [], "missing": []}

        if is_configured:
            status["by_platform"][platform]["configured"].append(key)
        else:
            status["by_platform"][platform]["missing"].append(key)

        # Count by tier
        if tier in status["by_tier"]:
            if is_configured:
                status["by_tier"][tier]["configured"] += 1
            else:
                status["by_tier"][tier]["missing"] += 1

    status["summary"] = {
        "total_credentials": len(CREDENTIALS),
        "configured": len(status["configured"]),
        "missing": len(status["missing"]),
        "configuration_rate": round(len(status["configured"]) / len(CREDENTIALS) * 100, 1)
    }

    return status


def get_missing_credentials() -> List[Dict[str, Any]]:
    """Get list of missing credentials with setup instructions"""
    missing = []

    for key, config in CREDENTIALS.items():
        if not os.getenv(key):
            missing.append({
                "key": key,
                "name": config["name"],
                "platform": config.get("platform"),
                "tier": config.get("tier"),
                "cost": config.get("cost", "Free"),
                "required_for": config.get("required_for", []),
                "setup_url": config.get("setup_url"),
                "setup_steps": config.get("setup_steps", []),
                "note": config.get("note"),
                "alternative": config.get("alternative")
            })

    return missing


def get_pdls_blocked_by_credentials() -> Dict[str, Any]:
    """Get PDLs that cannot execute due to missing credentials"""
    try:
        from pdl_polymorphic_catalog import get_pdl_catalog
        catalog = get_pdl_catalog()
    except ImportError:
        return {"error": "PDL catalog not available"}

    blocked = []
    executable = []

    for pdl in catalog.get_all_pdls():
        missing_apis = [api for api in pdl.required_apis if not os.getenv(api)]

        if missing_apis:
            blocked.append({
                "pdl_name": pdl.name,
                "platform": pdl.platform,
                "action": pdl.action,
                "missing_apis": missing_apis,
                "setup_instructions": [
                    CREDENTIALS.get(api, {}).get("setup_url", "Unknown")
                    for api in missing_apis
                ]
            })
        else:
            executable.append({
                "pdl_name": pdl.name,
                "platform": pdl.platform,
                "action": pdl.action
            })

    return {
        "blocked_pdls": len(blocked),
        "executable_pdls": len(executable),
        "total_pdls": len(blocked) + len(executable),
        "blocked": blocked,
        "executable": executable
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CREDENTIAL VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

async def validate_credential(key: str) -> Dict[str, Any]:
    """Validate a specific credential by testing it"""
    value = os.getenv(key)

    if not value:
        return {
            "key": key,
            "valid": False,
            "error": "Credential not configured"
        }

    config = CREDENTIALS.get(key, {})
    validation_endpoint = config.get("validation_endpoint")

    if not validation_endpoint:
        return {
            "key": key,
            "valid": None,
            "message": "No validation endpoint available - assumed valid if set"
        }

    try:
        async with aiohttp.ClientSession() as session:
            headers = {}

            # Set appropriate auth header
            if key == "GITHUB_TOKEN":
                headers["Authorization"] = f"token {value}"
            elif key == "OPENAI_API_KEY":
                headers["Authorization"] = f"Bearer {value}"
            elif key == "TWITTER_BEARER_TOKEN":
                headers["Authorization"] = f"Bearer {value}"

            async with session.get(validation_endpoint, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    return {
                        "key": key,
                        "valid": True,
                        "status_code": resp.status
                    }
                else:
                    return {
                        "key": key,
                        "valid": False,
                        "status_code": resp.status,
                        "error": f"API returned {resp.status}"
                    }

    except Exception as e:
        return {
            "key": key,
            "valid": False,
            "error": str(e)
        }


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/credentials/status")
async def credentials_status():
    """Get status of all credentials"""
    return {
        "ok": True,
        "timestamp": _now(),
        **get_credential_status()
    }


@router.get("/credentials/missing")
async def credentials_missing():
    """Get missing credentials with setup instructions"""
    missing = get_missing_credentials()
    return {
        "ok": True,
        "timestamp": _now(),
        "missing_count": len(missing),
        "missing": missing
    }


@router.get("/pdl/missing-credentials")
async def pdl_missing_credentials():
    """Get PDLs blocked by missing credentials"""
    return {
        "ok": True,
        "timestamp": _now(),
        **get_pdls_blocked_by_credentials()
    }


@router.get("/credentials/setup-guide")
async def credentials_setup_guide():
    """Get setup guide for all credentials"""
    guide = []

    for key, config in CREDENTIALS.items():
        is_configured = bool(os.getenv(key))

        guide.append({
            "key": key,
            "name": config["name"],
            "platform": config.get("platform"),
            "tier": config.get("tier"),
            "cost": config.get("cost", "Free"),
            "configured": is_configured,
            "setup_url": config.get("setup_url"),
            "setup_steps": config.get("setup_steps", []),
            "note": config.get("note"),
            "required_for": config.get("required_for", [])
        })

    # Sort by tier priority
    tier_order = {"free": 0, "freemium": 1, "paid": 2, "oauth": 3}
    guide.sort(key=lambda x: (tier_order.get(x["tier"], 99), x["key"]))

    return {
        "ok": True,
        "timestamp": _now(),
        "credentials": guide
    }


@router.post("/credentials/validate")
async def validate_credential_endpoint(body: Dict = Body(...)):
    """Validate a specific credential"""
    key = body.get("key")
    if not key:
        raise HTTPException(status_code=400, detail="key is required")

    if key not in CREDENTIALS:
        raise HTTPException(status_code=404, detail=f"Unknown credential: {key}")

    result = await validate_credential(key)
    return {
        "ok": True,
        "timestamp": _now(),
        **result
    }


@router.get("/credentials/validate-all")
async def validate_all_credentials():
    """Validate all configured credentials"""
    results = []

    for key in CREDENTIALS:
        if os.getenv(key):
            result = await validate_credential(key)
            results.append(result)

    valid_count = sum(1 for r in results if r.get("valid") is True)
    invalid_count = sum(1 for r in results if r.get("valid") is False)

    return {
        "ok": True,
        "timestamp": _now(),
        "validated": len(results),
        "valid": valid_count,
        "invalid": invalid_count,
        "results": results
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def include_credential_endpoints(app):
    """Include credential management endpoints in FastAPI app"""
    app.include_router(router)

    status = get_credential_status()

    print("=" * 80)
    print("🔑 OAUTH CREDENTIAL MANAGER LOADED")
    print("=" * 80)
    print(f"Configured: {status['summary']['configured']}/{status['summary']['total_credentials']} credentials")
    print(f"Configuration Rate: {status['summary']['configuration_rate']}%")
    print("Endpoints:")
    print("  GET  /credentials/status         - All credential status")
    print("  GET  /credentials/missing        - Missing credentials")
    print("  GET  /pdl/missing-credentials    - Blocked PDLs")
    print("  GET  /credentials/setup-guide    - Setup instructions")
    print("  POST /credentials/validate       - Validate credential")
    print("=" * 80)
