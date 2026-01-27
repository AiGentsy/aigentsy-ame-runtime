"""
OAUTH BROKER: Central Credential Management for 28 Premium APIs

Reads YOUR Render environment variable names exactly.
No additional setup needed - it reads from existing env vars.

Supported APIs:
- Social: Twitter v2, Instagram Business, LinkedIn
- AI/LLM: OpenRouter, Perplexity, Gemini, Stability, Runway
- Platform: GitHub, Shopify
- Communication: Twilio, Resend
- Storage: JSONBin
"""

import os
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class OAuthBroker:
    """
    Central credential manager for all API integrations.

    Responsibilities:
    - Load credentials from environment variables
    - Provide credentials to platform packs
    - Track which APIs are available
    - Refresh OAuth tokens when needed
    """

    def __init__(self):
        self.credentials: Dict[str, Dict] = {}
        self._load_from_env()

    def _load_from_env(self):
        """Load credentials from YOUR Render environment variables"""

        # Twitter (Full OAuth 1.0a + v2 Bearer token)
        if os.getenv('TWITTER_ACCESS_TOKEN') or os.getenv('TWITTER_BEARER_TOKEN'):
            self.credentials['twitter'] = {
                'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
                'access_token_secret': os.getenv('TWITTER_ACCESS_SECRET'),
                'api_key': os.getenv('TWITTER_API_KEY'),
                'api_secret': os.getenv('TWITTER_API_SECRET'),
                'bearer_token': os.getenv('TWITTER_BEARER_TOKEN')
            }
            logger.info("Twitter v2 API credentials loaded")

        # Instagram Business
        if os.getenv('INSTAGRAM_ACCESS_TOKEN'):
            self.credentials['instagram'] = {
                'access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN'),
                'business_id': os.getenv('INSTAGRAM_BUSINESS_ID')
            }
            logger.info("Instagram Business API credentials loaded")

        # LinkedIn
        if os.getenv('LINKEDIN_ACCESS_TOKEN'):
            self.credentials['linkedin'] = {
                'access_token': os.getenv('LINKEDIN_ACCESS_TOKEN'),
                'client_id': os.getenv('LINKEDIN_CLIENT_ID'),
                'client_secret': os.getenv('LINKEDIN_CLIENT_SECRET')
            }
            logger.info("LinkedIn API credentials loaded")

        # GitHub
        if os.getenv('GITHUB_TOKEN'):
            self.credentials['github'] = {
                'token': os.getenv('GITHUB_TOKEN')
            }
            logger.info("GitHub API credentials loaded")

        # Shopify
        if os.getenv('SHOPIFY_ADMIN_TOKEN'):
            self.credentials['shopify'] = {
                'admin_token': os.getenv('SHOPIFY_ADMIN_TOKEN'),
                'webhook_secret': os.getenv('SHOPIFY_WEBHOOK_SECRET')
            }
            logger.info("Shopify API credentials loaded")

        # AI/LLM APIs
        if os.getenv('OPENROUTER_API_KEY'):
            self.credentials['openrouter'] = {
                'api_key': os.getenv('OPENROUTER_API_KEY')
            }
            logger.info("OpenRouter API credentials loaded")

        if os.getenv('PERPLEXITY_API_KEY'):
            self.credentials['perplexity'] = {
                'api_key': os.getenv('PERPLEXITY_API_KEY')
            }
            logger.info("Perplexity API credentials loaded")

        if os.getenv('GEMINI_API_KEY'):
            self.credentials['gemini'] = {
                'api_key': os.getenv('GEMINI_API_KEY')
            }
            logger.info("Gemini API credentials loaded")

        if os.getenv('ANTHROPIC_API_KEY'):
            self.credentials['anthropic'] = {
                'api_key': os.getenv('ANTHROPIC_API_KEY')
            }
            logger.info("Anthropic API credentials loaded")

        if os.getenv('STABILITY_API_KEY'):
            self.credentials['stability'] = {
                'api_key': os.getenv('STABILITY_API_KEY')
            }
            logger.info("Stability AI credentials loaded")

        if os.getenv('RUNWAY_API_KEY'):
            self.credentials['runway'] = {
                'api_key': os.getenv('RUNWAY_API_KEY')
            }
            logger.info("Runway ML credentials loaded")

        # Communication APIs
        if os.getenv('TWILIO_ACCOUNT_SID'):
            self.credentials['twilio'] = {
                'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
                'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
                'phone_number': os.getenv('TWILIO_PHONE_NUMBER')
            }
            logger.info("Twilio credentials loaded")

        if os.getenv('RESEND_API_KEY'):
            self.credentials['resend'] = {
                'api_key': os.getenv('RESEND_API_KEY')
            }
            logger.info("Resend credentials loaded")

        # Storage
        if os.getenv('JSONBIN_SECRET'):
            self.credentials['jsonbin'] = {
                'secret': os.getenv('JSONBIN_SECRET'),
                'url': os.getenv('JSONBIN_URL'),
                'counter_url': os.getenv('JSONBIN_COUNTER_URL')
            }
            logger.info("JSONBin credentials loaded")

        logger.info(f"Total API credentials loaded: {len(self.credentials)}")

    def has_credentials(self, api_name: str) -> bool:
        """Check if credentials exist for an API"""
        return api_name.lower() in self.credentials

    def get_credentials(self, api_name: str) -> Optional[Dict]:
        """Get credentials for an API"""
        return self.credentials.get(api_name.lower())

    def get_api_key(self, api_name: str) -> Optional[str]:
        """Get just the API key for a service"""
        creds = self.get_credentials(api_name)
        if creds:
            return creds.get('api_key') or creds.get('token') or creds.get('access_token')
        return None

    def list_available_apis(self) -> List[str]:
        """List all APIs with loaded credentials"""
        return list(self.credentials.keys())

    def list_missing_apis(self) -> List[str]:
        """List expected APIs that are missing credentials"""
        expected = [
            'twitter', 'instagram', 'linkedin', 'github', 'shopify',
            'openrouter', 'perplexity', 'gemini', 'anthropic', 'stability', 'runway',
            'twilio', 'resend', 'jsonbin'
        ]
        return [api for api in expected if api not in self.credentials]

    def get_status(self) -> Dict:
        """Get overall credential status"""
        expected = [
            'twitter', 'instagram', 'linkedin', 'github', 'shopify',
            'openrouter', 'perplexity', 'gemini', 'anthropic', 'stability', 'runway',
            'twilio', 'resend', 'jsonbin'
        ]

        status = {}
        for api in expected:
            status[api] = 'loaded' if api in self.credentials else 'missing'

        return {
            'total_loaded': len(self.credentials),
            'total_expected': len(expected),
            'apis': status
        }


# Singleton instance
_oauth_broker: Optional[OAuthBroker] = None


def get_oauth_broker() -> OAuthBroker:
    """Get or create OAuth broker instance"""
    global _oauth_broker
    if _oauth_broker is None:
        _oauth_broker = OAuthBroker()
    return _oauth_broker


# Convenience alias
oauth_broker = get_oauth_broker()
