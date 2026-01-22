"""
UNIFIED API CONFIGURATION
=========================

Centralizes all API keys and credentials for V106-V115 revenue engines.
Maps your available APIs to monetization engines:

V111 Super-Harvesters ($6.36T TAM):
├── U-ACR (Abandoned Checkout Recovery): Shopify + Stripe + Twitter + Instagram
├── Receivables Desk: Stripe invoice sync
└── Payments Optimizer: Stripe PSP routing

V110 Gap Harvesters:
├── Support Queue Monetizer: Twilio
├── Email automation: Resend
└── Social signals: Twitter + Instagram

V107-V109 Overlays:
├── Creator Performance Network: Twitter + Instagram + LinkedIn
├── Service BNPL: Stripe
└── Content generation: Stability + RunwayML

V115 Apex/Fabric:
└── All engines unified with full API access

Usage:
    from api_config import get_api_config, is_api_configured

    config = get_api_config()
    if is_api_configured("stripe"):
        # Use Stripe APIs
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class APICredential:
    """Single API credential with metadata"""
    key: str
    name: str
    env_var: str
    value: Optional[str] = None
    required_for: List[str] = field(default_factory=list)
    description: str = ""

    def is_configured(self) -> bool:
        return bool(self.value)


class APIConfig:
    """
    Unified API configuration for all revenue engines.
    Loads from environment variables (Render-compatible).
    """

    def __init__(self):
        self._credentials: Dict[str, APICredential] = {}
        self._load_all_credentials()

    def _load_all_credentials(self):
        """Load all API credentials from environment"""

        # ═══════════════════════════════════════════════════════════════════
        # PAYMENTS (Stripe)
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="stripe_secret",
            name="Stripe Secret Key",
            env_var="STRIPE_SECRET_KEY",
            required_for=["v111_uacr", "v111_receivables", "v111_payments", "v108_service_bnpl"],
            description="Stripe API secret key for payments, invoices, payment links"
        )
        self._add_credential(
            key="stripe_webhook_secret",
            name="Stripe Webhook Secret",
            env_var="STRIPE_WEBHOOK_SECRET",
            required_for=["v111_uacr", "v111_receivables", "webhooks"],
            description="Stripe webhook signing secret for payment verification"
        )

        # ═══════════════════════════════════════════════════════════════════
        # E-COMMERCE (Shopify)
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="shopify_admin_token",
            name="Shopify Admin Token",
            env_var="SHOPIFY_ADMIN_TOKEN",
            required_for=["v111_uacr", "abandoned_cart_recovery"],
            description="Shopify Admin API access token"
        )
        self._add_credential(
            key="shopify_shop_url",
            name="Shopify Shop URL",
            env_var="SHOPIFY_SHOP_URL",
            required_for=["v111_uacr", "abandoned_cart_recovery"],
            description="Shopify store URL (mystore.myshopify.com)"
        )
        self._add_credential(
            key="shopify_webhook_secret",
            name="Shopify Webhook Secret",
            env_var="SHOPIFY_WEBHOOK_SECRET",
            required_for=["v111_uacr", "webhooks"],
            description="Shopify webhook HMAC secret"
        )

        # ═══════════════════════════════════════════════════════════════════
        # SOCIAL - TWITTER
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="twitter_bearer_token",
            name="Twitter Bearer Token",
            env_var="TWITTER_BEARER_TOKEN",
            required_for=["v111_uacr", "v108_creator_network", "social_signals"],
            description="Twitter API v2 bearer token for reading tweets"
        )
        self._add_credential(
            key="twitter_api_key",
            name="Twitter API Key",
            env_var="TWITTER_API_KEY",
            required_for=["v111_uacr", "v108_creator_network"],
            description="Twitter API key (consumer key)"
        )
        self._add_credential(
            key="twitter_api_secret",
            name="Twitter API Secret",
            env_var="TWITTER_API_SECRET",
            required_for=["v111_uacr", "v108_creator_network"],
            description="Twitter API secret (consumer secret)"
        )
        self._add_credential(
            key="twitter_access_token",
            name="Twitter Access Token",
            env_var="TWITTER_ACCESS_TOKEN",
            required_for=["v111_uacr", "v108_creator_network", "dm_outreach"],
            description="Twitter user access token for DMs/posting"
        )
        self._add_credential(
            key="twitter_access_secret",
            name="Twitter Access Secret",
            env_var="TWITTER_ACCESS_SECRET",
            required_for=["v111_uacr", "v108_creator_network", "dm_outreach"],
            description="Twitter user access token secret"
        )

        # ═══════════════════════════════════════════════════════════════════
        # SOCIAL - INSTAGRAM
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="instagram_access_token",
            name="Instagram Access Token",
            env_var="INSTAGRAM_ACCESS_TOKEN",
            required_for=["v111_uacr", "v108_creator_network", "social_signals"],
            description="Instagram Graph API access token"
        )
        self._add_credential(
            key="instagram_business_id",
            name="Instagram Business ID",
            env_var="INSTAGRAM_BUSINESS_ID",
            required_for=["v111_uacr", "v108_creator_network"],
            description="Instagram Business Account ID"
        )

        # ═══════════════════════════════════════════════════════════════════
        # SOCIAL - LINKEDIN
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="linkedin_access_token",
            name="LinkedIn Access Token",
            env_var="LINKEDIN_ACCESS_TOKEN",
            required_for=["v108_creator_network", "b2b_signals"],
            description="LinkedIn API access token"
        )
        self._add_credential(
            key="linkedin_client_id",
            name="LinkedIn Client ID",
            env_var="LINKEDIN_CLIENT_ID",
            required_for=["v108_creator_network"],
            description="LinkedIn OAuth client ID"
        )
        self._add_credential(
            key="linkedin_client_secret",
            name="LinkedIn Client Secret",
            env_var="LINKEDIN_CLIENT_SECRET",
            required_for=["v108_creator_network"],
            description="LinkedIn OAuth client secret"
        )

        # ═══════════════════════════════════════════════════════════════════
        # COMMUNICATION - TWILIO (SMS)
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="twilio_account_sid",
            name="Twilio Account SID",
            env_var="TWILIO_ACCOUNT_SID",
            required_for=["v110_support_queue", "sms_automation", "cart_recovery_sms"],
            description="Twilio account SID"
        )
        self._add_credential(
            key="twilio_auth_token",
            name="Twilio Auth Token",
            env_var="TWILIO_AUTH_TOKEN",
            required_for=["v110_support_queue", "sms_automation"],
            description="Twilio auth token"
        )
        self._add_credential(
            key="twilio_phone_number",
            name="Twilio Phone Number",
            env_var="TWILIO_PHONE_NUMBER",
            required_for=["v110_support_queue", "sms_automation"],
            description="Twilio phone number for sending SMS"
        )

        # ═══════════════════════════════════════════════════════════════════
        # COMMUNICATION - RESEND (Email)
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="resend_api_key",
            name="Resend API Key",
            env_var="RESEND_API_KEY",
            required_for=["v110_email_automation", "cart_recovery_email", "invoice_reminders"],
            description="Resend API key for email delivery"
        )

        # ═══════════════════════════════════════════════════════════════════
        # AI / LLM
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="openrouter_api_key",
            name="OpenRouter API Key",
            env_var="OPENROUTER_API_KEY",
            required_for=["ai_generation", "content_creation", "dm_personalization"],
            description="OpenRouter API key (Claude + GPT-4 access)"
        )
        self._add_credential(
            key="gemini_api_key",
            name="Gemini API Key",
            env_var="GEMINI_API_KEY",
            required_for=["ai_fallback", "vision_tasks"],
            description="Google Gemini API key"
        )
        self._add_credential(
            key="perplexity_api_key",
            name="Perplexity API Key",
            env_var="PERPLEXITY_API_KEY",
            required_for=["web_search", "market_research"],
            description="Perplexity API key for web search"
        )

        # ═══════════════════════════════════════════════════════════════════
        # CONTENT GENERATION
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="stability_api_key",
            name="Stability API Key",
            env_var="STABILITY_API_KEY",
            required_for=["v109_content_generation", "image_generation"],
            description="Stability AI API key for image generation"
        )
        self._add_credential(
            key="runwav_api_key",
            name="RunwayML API Key",
            env_var="RUNWAV_API_KEY",
            required_for=["v109_content_generation", "video_generation"],
            description="RunwayML API key for video generation"
        )

        # ═══════════════════════════════════════════════════════════════════
        # DEVELOPER / STORAGE
        # ═══════════════════════════════════════════════════════════════════
        self._add_credential(
            key="github_token",
            name="GitHub Token",
            env_var="GITHUB_TOKEN",
            required_for=["code_execution", "repo_management"],
            description="GitHub personal access token"
        )
        self._add_credential(
            key="jsonbin_secret",
            name="JSONBin Secret",
            env_var="JSONBIN_SECRET",
            required_for=["data_storage", "logging"],
            description="JSONBin master key"
        )
        self._add_credential(
            key="jsonbin_url",
            name="JSONBin URL",
            env_var="JSONBIN_URL",
            required_for=["data_storage", "logging"],
            description="JSONBin bin URL"
        )

    def _add_credential(self, key: str, name: str, env_var: str,
                       required_for: List[str], description: str = ""):
        """Add a credential and load from environment"""
        value = os.getenv(env_var)
        self._credentials[key] = APICredential(
            key=key,
            name=name,
            env_var=env_var,
            value=value,
            required_for=required_for,
            description=description
        )

    def get(self, key: str) -> Optional[str]:
        """Get credential value by key"""
        cred = self._credentials.get(key)
        return cred.value if cred else None

    def is_configured(self, key: str) -> bool:
        """Check if credential is configured"""
        cred = self._credentials.get(key)
        return cred.is_configured() if cred else False

    def get_for_engine(self, engine: str) -> Dict[str, str]:
        """Get all credentials required for a specific engine"""
        result = {}
        for key, cred in self._credentials.items():
            if engine in cred.required_for and cred.value:
                result[key] = cred.value
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get configuration status for all credentials"""
        configured = []
        missing = []

        for key, cred in self._credentials.items():
            if cred.is_configured():
                configured.append({
                    "key": key,
                    "name": cred.name,
                    "env_var": cred.env_var,
                    "required_for": cred.required_for
                })
            else:
                missing.append({
                    "key": key,
                    "name": cred.name,
                    "env_var": cred.env_var,
                    "required_for": cred.required_for
                })

        return {
            "configured_count": len(configured),
            "missing_count": len(missing),
            "configured": configured,
            "missing": missing
        }

    def get_engine_readiness(self) -> Dict[str, Any]:
        """Check which engines are ready to activate"""
        engines = {
            # V111 Super-Harvesters
            "v111_uacr": {
                "name": "U-ACR (Abandoned Checkout Recovery)",
                "tam": "$4.6T",
                "required": ["stripe_secret", "shopify_admin_token", "twitter_bearer_token", "instagram_access_token"],
                "optional": ["twitter_access_token", "twilio_account_sid", "resend_api_key"]
            },
            "v111_receivables": {
                "name": "Receivables Desk",
                "tam": "$1.5T",
                "required": ["stripe_secret"],
                "optional": ["resend_api_key", "twilio_account_sid"]
            },
            "v111_payments": {
                "name": "Payments Optimizer",
                "tam": "$260B",
                "required": ["stripe_secret"],
                "optional": []
            },
            # V110 Gap Harvesters
            "v110_support_queue": {
                "name": "Support Queue Monetizer",
                "required": ["twilio_account_sid", "twilio_auth_token"],
                "optional": ["openrouter_api_key"]
            },
            "v110_email_automation": {
                "name": "Email Automation",
                "required": ["resend_api_key"],
                "optional": ["openrouter_api_key"]
            },
            # V108 Overlays
            "v108_creator_network": {
                "name": "Creator Performance Network",
                "required": ["twitter_bearer_token", "instagram_access_token"],
                "optional": ["linkedin_access_token"]
            },
            "v108_service_bnpl": {
                "name": "Service BNPL",
                "required": ["stripe_secret"],
                "optional": []
            },
            # V109 Overlays
            "v109_content_generation": {
                "name": "Content Generation",
                "required": ["stability_api_key"],
                "optional": ["runwav_api_key", "openrouter_api_key"]
            }
        }

        readiness = {}

        for engine_id, engine_info in engines.items():
            required_configured = all(self.is_configured(k) for k in engine_info["required"])
            optional_configured = [k for k in engine_info.get("optional", []) if self.is_configured(k)]
            missing_required = [k for k in engine_info["required"] if not self.is_configured(k)]

            readiness[engine_id] = {
                "name": engine_info["name"],
                "tam": engine_info.get("tam", "N/A"),
                "ready": required_configured,
                "status": "READY" if required_configured else "MISSING_KEYS",
                "required_configured": [k for k in engine_info["required"] if self.is_configured(k)],
                "missing_required": missing_required,
                "optional_configured": optional_configured
            }

        return readiness

    def get_v111_config(self) -> Dict[str, Any]:
        """Get configuration specifically for V111 Super-Harvesters"""
        return {
            "uacr": {
                "stripe_secret": self.get("stripe_secret"),
                "stripe_webhook_secret": self.get("stripe_webhook_secret"),
                "shopify_admin_token": self.get("shopify_admin_token"),
                "shopify_shop_url": self.get("shopify_shop_url"),
                "shopify_webhook_secret": self.get("shopify_webhook_secret"),
                "twitter_bearer_token": self.get("twitter_bearer_token"),
                "twitter_access_token": self.get("twitter_access_token"),
                "twitter_access_secret": self.get("twitter_access_secret"),
                "instagram_access_token": self.get("instagram_access_token"),
                "instagram_business_id": self.get("instagram_business_id"),
                "twilio_account_sid": self.get("twilio_account_sid"),
                "twilio_auth_token": self.get("twilio_auth_token"),
                "twilio_phone_number": self.get("twilio_phone_number"),
                "resend_api_key": self.get("resend_api_key")
            },
            "receivables": {
                "stripe_secret": self.get("stripe_secret"),
                "stripe_webhook_secret": self.get("stripe_webhook_secret"),
                "resend_api_key": self.get("resend_api_key"),
                "twilio_account_sid": self.get("twilio_account_sid"),
                "twilio_auth_token": self.get("twilio_auth_token")
            },
            "payments": {
                "stripe_secret": self.get("stripe_secret"),
                "stripe_webhook_secret": self.get("stripe_webhook_secret")
            }
        }


# Module-level singleton
_config: Optional[APIConfig] = None


def get_api_config() -> APIConfig:
    """Get the global API configuration"""
    global _config
    if _config is None:
        _config = APIConfig()
    return _config


def is_api_configured(key: str) -> bool:
    """Check if a specific API is configured"""
    return get_api_config().is_configured(key)


def get_api_key(key: str) -> Optional[str]:
    """Get a specific API key value"""
    return get_api_config().get(key)


def get_engine_readiness() -> Dict[str, Any]:
    """Get readiness status for all revenue engines"""
    return get_api_config().get_engine_readiness()


def get_v111_config() -> Dict[str, Any]:
    """Get V111 Super-Harvester configuration"""
    return get_api_config().get_v111_config()


# Print status on import (for debugging)
def _print_status():
    config = get_api_config()
    status = config.get_status()
    readiness = config.get_engine_readiness()

    print("=" * 80)
    print("API CONFIGURATION STATUS")
    print("=" * 80)
    print(f"Configured: {status['configured_count']} / {status['configured_count'] + status['missing_count']}")
    print()

    print("V111 SUPER-HARVESTERS READINESS:")
    for engine_id in ["v111_uacr", "v111_receivables", "v111_payments"]:
        info = readiness.get(engine_id, {})
        status_icon = "✅" if info.get("ready") else "❌"
        print(f"  {status_icon} {info.get('name', engine_id)} ({info.get('tam', 'N/A')}): {info.get('status')}")
        if info.get("missing_required"):
            print(f"      Missing: {', '.join(info['missing_required'])}")

    print("=" * 80)


if __name__ == "__main__":
    _print_status()
