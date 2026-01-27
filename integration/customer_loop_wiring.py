"""
Customer Loop Wiring - Connects EXISTING Systems to Close the Revenue Gap
═════════════════════════════════════════════════════════════════════════

This wires together EXISTING systems to close:
    Discovery → Contract → [GAP] → Customer Signs → Payment

Systems wired (ALL EXISTING):
1. direct_outreach_engine.py - Email, Twitter DM, LinkedIn, Reddit DM
2. platform_response_engine.py - GitHub comments, Reddit comments, etc.
3. universal_contact_extraction.py - Extract contact from any opportunity
4. client_acceptance_portal.py - Stripe payment acceptance flow
5. connectors/email_connector.py - Postmark/SendGrid email delivery
6. routes/client_room.py - Client-facing dashboard

NO NEW FEATURES. Just wiring existing code.
"""

import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class PresentationResult:
    """Result of presenting contract to customer"""
    presented: bool = False
    method: Optional[str] = None
    channel: Optional[str] = None
    recipient: Optional[str] = None
    error: Optional[str] = None
    tracking_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = field(default_factory=dict)


class CustomerLoopWiring:
    """
    Wires existing systems to close the customer interaction loop.

    Uses ONLY existing, working code - no placeholders.
    """

    def __init__(self):
        self.available_systems: Dict[str, Any] = {}
        self.outreach_engine = None
        self.platform_response_engine = None
        self.contact_extractor = None
        self.email_connector = None
        self.acceptance_portal = None

        self._detect_available_systems()

    def _detect_available_systems(self):
        """Detect which customer interaction systems exist and are configured"""

        # 1. Direct Outreach Engine
        try:
            from direct_outreach_engine import DirectOutreachEngine, get_outreach_engine
            self.outreach_engine = get_outreach_engine()
            stats = self.outreach_engine.get_stats()
            self.available_systems['direct_outreach'] = {
                'loaded': True,
                'channels': stats.get('channels_configured', {}),
                'daily_limit': self.outreach_engine.max_daily_outreach,
            }
            logger.info("✅ DirectOutreachEngine loaded")
        except ImportError as e:
            logger.warning(f"⚠️ DirectOutreachEngine not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ DirectOutreachEngine error: {e}")

        # 2. Platform Response Engine
        try:
            from platform_response_engine import PlatformResponseEngine, get_platform_response_engine
            self.platform_response_engine = get_platform_response_engine()
            supported = self.platform_response_engine.get_supported_platforms()
            self.available_systems['platform_response'] = {
                'loaded': True,
                'platforms': supported,
            }
            logger.info("✅ PlatformResponseEngine loaded")
        except ImportError as e:
            logger.warning(f"⚠️ PlatformResponseEngine not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ PlatformResponseEngine error: {e}")

        # 3. Universal Contact Extractor
        try:
            from universal_contact_extraction import (
                UniversalContactExtractor,
                get_contact_extractor,
                enrich_opportunity_with_contact
            )
            self.contact_extractor = get_contact_extractor()
            self.available_systems['contact_extraction'] = {
                'loaded': True,
            }
            self._enrich_opportunity = enrich_opportunity_with_contact
            logger.info("✅ UniversalContactExtractor loaded")
        except ImportError as e:
            logger.warning(f"⚠️ UniversalContactExtractor not available: {e}")
            self._enrich_opportunity = None
        except Exception as e:
            logger.warning(f"⚠️ UniversalContactExtractor error: {e}")
            self._enrich_opportunity = None

        # 4. Email Connector
        try:
            from connectors.email_connector import EmailConnector
            self.email_connector = EmailConnector()
            health = self.email_connector.health()
            self.available_systems['email_connector'] = {
                'loaded': True,
                'configured': os.getenv('POSTMARK_API_KEY') or os.getenv('SENDGRID_API_KEY'),
            }
            logger.info("✅ EmailConnector loaded")
        except ImportError as e:
            logger.warning(f"⚠️ EmailConnector not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ EmailConnector error: {e}")

        # 5. Client Acceptance Portal
        try:
            from client_acceptance_portal import (
                create_accept_link,
                get_deal,
                accept_deal,
                AI_SERVICE_CATALOG
            )
            self.acceptance_portal = {
                'create_accept_link': create_accept_link,
                'get_deal': get_deal,
                'accept_deal': accept_deal,
            }
            self.available_systems['acceptance_portal'] = {
                'loaded': True,
                'services': len(AI_SERVICE_CATALOG),
                'stripe_configured': bool(os.getenv('STRIPE_SECRET_KEY')),
            }
            logger.info("✅ ClientAcceptancePortal loaded")
        except ImportError as e:
            logger.warning(f"⚠️ ClientAcceptancePortal not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ ClientAcceptancePortal error: {e}")

        # 6. Check API keys
        self.available_systems['api_keys'] = {
            'resend': bool(os.getenv('RESEND_API_KEY')),
            'postmark': bool(os.getenv('POSTMARK_API_KEY')),
            'sendgrid': bool(os.getenv('SENDGRID_API_KEY')),
            'stripe': bool(os.getenv('STRIPE_SECRET_KEY')),
            'twitter': bool(os.getenv('TWITTER_API_KEY')),
            'reddit': bool(os.getenv('REDDIT_CLIENT_ID')),
            'github': bool(os.getenv('GITHUB_TOKEN')),
            'linkedin': bool(os.getenv('LINKEDIN_ACCESS_TOKEN')),
        }

        logger.info(f"📊 Available systems: {list(self.available_systems.keys())}")

    def enrich_with_contact(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Add contact info to opportunity using existing extractor"""
        if self._enrich_opportunity:
            return self._enrich_opportunity(opportunity)

        # Fallback: basic extraction
        opportunity['contact'] = {
            'platform': opportunity.get('source', 'unknown'),
            'platform_user_id': opportunity.get('author', ''),
            'has_contact': bool(opportunity.get('author')),
        }
        return opportunity

    def generate_client_room_url(self, contract_id: str, token: Optional[str] = None) -> str:
        """Generate client room URL for a contract"""
        base_url = os.getenv('AIGENTSY_BASE_URL', 'https://aigentsy-ame-runtime.onrender.com')
        if token:
            return f"{base_url}/client-room/{contract_id}?token={token}"
        return f"{base_url}/client-room/{contract_id}"

    async def present_contract_to_customer(
        self,
        opportunity: Dict[str, Any],
        contract: Dict[str, Any],
        client_room_url: str,
        sow: Optional[Dict[str, Any]] = None,
    ) -> PresentationResult:
        """
        Present contract to customer using existing outreach systems.

        Tries methods in order:
        1. Platform-native response (comment on their post)
        2. Direct outreach (DM/email)
        3. Email via connector

        Uses whatever exists and is configured.
        """
        result = PresentationResult()

        # Enrich opportunity with contact if not already done
        if 'contact' not in opportunity:
            opportunity = self.enrich_with_contact(opportunity)

        contact = opportunity.get('contact', {})
        platform = opportunity.get('source', '').lower()

        # Extract key contract info for message
        total_value = contract.get('total_amount_usd', sow.get('total_value_usd', 0) if sow else 0)
        title = opportunity.get('title', 'your project')

        # Build message
        message = self._build_outreach_message(
            title=title,
            total_value=total_value,
            client_room_url=client_room_url,
            platform=platform
        )

        # Method 1: Platform-native response (comment on their post)
        if self.platform_response_engine:
            supported = self.platform_response_engine.get_supported_platforms()
            if supported.get(platform, False):
                try:
                    engagement = await self.platform_response_engine.engage_with_opportunity(
                        opportunity,
                        send_dm_after=False  # Just comment, outreach handles DM
                    )
                    if engagement and engagement.status.value in ['commented', 'waiting']:
                        result.presented = True
                        result.method = 'platform_comment'
                        result.channel = platform
                        result.tracking_id = engagement.engagement_id
                        result.details = engagement.to_dict()
                        logger.info(f"✅ Posted comment on {platform}: {engagement.comment_url}")
                        # Don't return yet - also try DM/email for better conversion
                except Exception as e:
                    logger.warning(f"⚠️ Platform comment failed: {e}")

        # Method 2: Direct outreach (DM/email via outreach engine)
        if self.outreach_engine and contact.get('has_contact', False):
            try:
                outreach_result = await self.outreach_engine.process_opportunity(
                    opportunity,
                    contact
                )
                if outreach_result and outreach_result.status.value == 'sent':
                    result.presented = True
                    result.method = 'direct_outreach'
                    result.channel = outreach_result.channel.value
                    result.recipient = contact.get('email') or contact.get('twitter_handle') or contact.get('reddit_username')
                    result.tracking_id = outreach_result.tracking_id
                    result.details['outreach'] = {
                        'proposal_id': outreach_result.proposal_id,
                        'channel': outreach_result.channel.value,
                        'status': outreach_result.status.value,
                    }
                    logger.info(f"✅ Direct outreach sent via {outreach_result.channel.value}")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Direct outreach failed: {e}")

        # Method 3: Email via connector (if we have email and connector)
        email = contact.get('email')
        if email and self.email_connector:
            try:
                import asyncio
                email_result = await self.email_connector.execute(
                    action='send_email',
                    params={
                        'to': email,
                        'subject': f"Re: {title[:50]}",
                        'body': message,
                    }
                )
                if email_result.ok:
                    result.presented = True
                    result.method = 'email_connector'
                    result.channel = 'email'
                    result.recipient = email
                    result.tracking_id = email_result.data.get('message_id')
                    result.details['email'] = email_result.data
                    logger.info(f"✅ Email sent via connector to {email}")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Email connector failed: {e}")

        # If nothing worked, log what's missing
        if not result.presented:
            gaps = []
            if not self.platform_response_engine:
                gaps.append('platform_response_engine')
            if not self.outreach_engine:
                gaps.append('outreach_engine')
            if not contact.get('has_contact'):
                gaps.append('contact_info')
            if not email:
                gaps.append('email')
            if not self.email_connector:
                gaps.append('email_connector')

            result.error = f"No working outreach method. Missing: {', '.join(gaps)}"
            logger.warning(f"⚠️ Could not present contract: {result.error}")

        return result

    def _build_outreach_message(
        self,
        title: str,
        total_value: float,
        client_room_url: str,
        platform: str
    ) -> str:
        """Build platform-appropriate outreach message"""

        if platform in ['twitter', 'x']:
            # Short for Twitter
            return f"""Saw your post about {title[:30]}... We can handle this.

View our proposal: {client_room_url}

Pay only when you approve the result."""

        elif platform == 'reddit':
            return f"""Hey! Saw your post about {title[:50]}.

We can take care of this for you. AiGentsy is a fully autonomous fulfillment company - think of us as your complete team for exactly this.

**What we'll deliver:**
- {title[:60]} - done, end-to-end
- Delivered within hours, not days
- You only pay when satisfied

View our full proposal here: {client_room_url}

Happy to answer any questions!"""

        elif platform in ['github', 'github_bounties']:
            return f"""Hi! Saw this issue and we can help.

**AiGentsy** can handle this end-to-end:
- Full implementation of {title[:50]}
- Delivered quickly
- Pay only on approval

View our proposal: {client_room_url}"""

        else:
            # Default email/professional format
            return f"""Hi,

I came across your post about {title} and wanted to reach out.

We can handle this for you. AiGentsy is a fully autonomous fulfillment company - essentially your complete team for exactly this type of work.

What we'll deliver:
• {title[:60]} - done, end-to-end
• Delivered within hours, not days
• Iterate until it's exactly right
• You only pay when you approve

View our full proposal and pricing here:
{client_room_url}

Let me know if you have any questions!

— AiGentsy Team"""

    def get_status(self) -> Dict[str, Any]:
        """Get complete status of customer loop wiring"""

        # Check what's actually configured vs just loaded
        configured_channels = []
        missing_channels = []

        # Outreach channels
        if self.outreach_engine:
            stats = self.outreach_engine.get_stats()
            channels = stats.get('channels_configured', {})
            for channel, configured in channels.items():
                if configured:
                    configured_channels.append(f"outreach:{channel}")
                else:
                    missing_channels.append(f"outreach:{channel}")

        # Platform response
        if self.platform_response_engine:
            platforms = self.platform_response_engine.get_supported_platforms()
            for platform, configured in platforms.items():
                if configured:
                    configured_channels.append(f"comment:{platform}")
                else:
                    missing_channels.append(f"comment:{platform}")

        # Email connector
        if self.available_systems.get('email_connector', {}).get('configured'):
            configured_channels.append('email:postmark_or_sendgrid')
        else:
            missing_channels.append('email:postmark_or_sendgrid')

        # Payment
        if self.available_systems.get('acceptance_portal', {}).get('stripe_configured'):
            configured_channels.append('payment:stripe')
        else:
            missing_channels.append('payment:stripe')

        return {
            'systems_loaded': self.available_systems,
            'configured_channels': configured_channels,
            'missing_channels': missing_channels,
            'can_present_contracts': len(configured_channels) > 0,
            'can_accept_payments': self.available_systems.get('acceptance_portal', {}).get('stripe_configured', False),
            'recommendation': self._get_recommendation(configured_channels, missing_channels),
        }

    def _get_recommendation(self, configured: List[str], missing: List[str]) -> str:
        """Get actionable recommendation"""
        if not configured:
            return "CRITICAL: No outreach channels configured. Set RESEND_API_KEY or POSTMARK_API_KEY for email."

        if 'payment:stripe' not in configured:
            return "Set STRIPE_SECRET_KEY to enable payment collection."

        if len(configured) < 3:
            return f"Consider adding more channels for better reach. Missing: {', '.join(missing[:3])}"

        return "Customer loop is operational. Monitor conversion rates."


# Singleton instance
_customer_loop_wiring = None

def get_customer_loop_wiring() -> CustomerLoopWiring:
    """Get singleton customer loop wiring instance"""
    global _customer_loop_wiring
    if _customer_loop_wiring is None:
        _customer_loop_wiring = CustomerLoopWiring()
    return _customer_loop_wiring


# Convenience function for integration routes
async def present_contract_after_creation(
    opportunity: Dict[str, Any],
    contract: Dict[str, Any],
    sow: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Wire into discover-and-execute flow after contract creation.

    Call this after creating contract to present to customer.
    """
    wiring = get_customer_loop_wiring()

    # Generate client room URL
    client_room_url = wiring.generate_client_room_url(
        contract.get('id', contract.get('contract_id', 'unknown'))
    )

    # Present to customer
    result = await wiring.present_contract_to_customer(
        opportunity=opportunity,
        contract=contract,
        client_room_url=client_room_url,
        sow=sow,
    )

    return {
        'presented': result.presented,
        'method': result.method,
        'channel': result.channel,
        'recipient': result.recipient,
        'tracking_id': result.tracking_id,
        'client_room_url': client_room_url,
        'error': result.error,
    }
