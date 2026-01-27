"""
Customer Loop Wiring - Complete Multi-Channel Outreach Integration
═════════════════════════════════════════════════════════════════════════

This wires together ALL EXISTING systems to close:
    Discovery → Contract → [OUTREACH] → Customer Signs → Payment

CONNECTORS WIRED:
1. connectors/sms_connector.py - Twilio SMS
2. connectors/resend_connector.py - Resend email
3. connectors/email_connector.py - Postmark/SendGrid
4. connectors/slack_connector.py - Slack notifications

ENGINES WIRED:
5. direct_outreach_engine.py - Twitter DM, LinkedIn, Reddit DM
6. platform_response_engine.py - GitHub/Reddit/Twitter comments
7. universal_contact_extraction.py - Extract contact from opportunities
8. client_acceptance_portal.py - Stripe payment acceptance

ALL CODE EXISTS. Just wiring it together.
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
    fallback_attempts: List[Dict[str, Any]] = field(default_factory=list)


class CustomerLoopWiring:
    """
    Complete multi-channel customer outreach using ALL available APIs.

    Priority order for outreach:
    1. Platform-native (Twitter DM for Twitter opps, LinkedIn for LinkedIn)
    2. Email (Resend, then SendGrid, then Postmark)
    3. SMS (Twilio)
    4. WhatsApp (Twilio)
    5. Slack (for internal notifications)
    """

    def __init__(self):
        self.available_systems: Dict[str, Any] = {}
        self.connectors: Dict[str, Any] = {}
        self.engines: Dict[str, Any] = {}

        self._detect_all_systems()

    def _detect_all_systems(self):
        """Detect ALL available communication systems"""

        # ═══════════════════════════════════════════════════════════════════
        # CONNECTORS (from connectors/)
        # ═══════════════════════════════════════════════════════════════════

        # 1. SMS Connector (Twilio)
        try:
            from connectors.sms_connector import SMSConnector
            self.connectors['sms'] = SMSConnector()
            twilio_configured = all([
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN'),
                os.getenv('TWILIO_FROM_NUMBER')
            ])
            self.available_systems['sms_twilio'] = {
                'loaded': True,
                'configured': twilio_configured,
                'connector': 'SMSConnector'
            }
            if twilio_configured:
                logger.info("✅ SMS: Twilio configured")
            else:
                logger.warning("⚠️ SMS: Twilio loaded but not configured")
        except ImportError as e:
            logger.warning(f"⚠️ SMS connector not available: {e}")

        # 2. Resend Connector (Email)
        try:
            from connectors.resend_connector import ResendConnector
            self.connectors['resend'] = ResendConnector()
            resend_configured = bool(os.getenv('RESEND_API_KEY'))
            self.available_systems['email_resend'] = {
                'loaded': True,
                'configured': resend_configured,
                'connector': 'ResendConnector'
            }
            if resend_configured:
                logger.info("✅ Email: Resend configured")
        except ImportError as e:
            logger.warning(f"⚠️ Resend connector not available: {e}")

        # 3. Email Connector (Postmark/SendGrid)
        try:
            from connectors.email_connector import EmailConnector
            self.connectors['email'] = EmailConnector()
            email_configured = bool(os.getenv('POSTMARK_API_KEY') or os.getenv('SENDGRID_API_KEY'))
            self.available_systems['email_generic'] = {
                'loaded': True,
                'configured': email_configured,
                'connector': 'EmailConnector',
                'provider': 'postmark' if os.getenv('POSTMARK_API_KEY') else 'sendgrid' if os.getenv('SENDGRID_API_KEY') else None
            }
            if email_configured:
                logger.info("✅ Email: Postmark/SendGrid configured")
        except ImportError as e:
            logger.warning(f"⚠️ Email connector not available: {e}")

        # 4. Slack Connector
        try:
            from connectors.slack_connector import SlackConnector
            self.connectors['slack'] = SlackConnector()
            slack_configured = bool(os.getenv('SLACK_BOT_TOKEN') or os.getenv('SLACK_WEBHOOK_URL'))
            self.available_systems['slack'] = {
                'loaded': True,
                'configured': slack_configured,
                'connector': 'SlackConnector'
            }
            if slack_configured:
                logger.info("✅ Slack: Configured")
        except ImportError as e:
            logger.warning(f"⚠️ Slack connector not available: {e}")

        # 5. Stripe Connector (Payments)
        try:
            from connectors.stripe_connector import StripeConnector
            self.connectors['stripe'] = StripeConnector()
            stripe_configured = bool(os.getenv('STRIPE_SECRET_KEY'))
            self.available_systems['payment_stripe'] = {
                'loaded': True,
                'configured': stripe_configured,
                'connector': 'StripeConnector'
            }
            if stripe_configured:
                logger.info("✅ Payment: Stripe configured")
        except ImportError as e:
            logger.warning(f"⚠️ Stripe connector not available: {e}")

        # ═══════════════════════════════════════════════════════════════════
        # ENGINES (standalone modules)
        # ═══════════════════════════════════════════════════════════════════

        # 6. Direct Outreach Engine
        try:
            from direct_outreach_engine import get_outreach_engine
            self.engines['outreach'] = get_outreach_engine()
            stats = self.engines['outreach'].get_stats()
            self.available_systems['direct_outreach'] = {
                'loaded': True,
                'channels': stats.get('channels_configured', {}),
                'daily_limit': self.engines['outreach'].max_daily_outreach,
            }
            logger.info("✅ DirectOutreachEngine loaded")
        except Exception as e:
            logger.warning(f"⚠️ DirectOutreachEngine not available: {e}")

        # 7. Platform Response Engine
        try:
            from platform_response_engine import get_platform_response_engine
            self.engines['platform_response'] = get_platform_response_engine()
            supported = self.engines['platform_response'].get_supported_platforms()
            self.available_systems['platform_response'] = {
                'loaded': True,
                'platforms': supported,
            }
            logger.info("✅ PlatformResponseEngine loaded")
        except Exception as e:
            logger.warning(f"⚠️ PlatformResponseEngine not available: {e}")

        # 8. Universal Contact Extractor
        try:
            from universal_contact_extraction import get_contact_extractor, enrich_opportunity_with_contact
            self.engines['contact_extractor'] = get_contact_extractor()
            self._enrich_opportunity = enrich_opportunity_with_contact
            self.available_systems['contact_extraction'] = {'loaded': True}
            logger.info("✅ UniversalContactExtractor loaded")
        except Exception as e:
            logger.warning(f"⚠️ ContactExtractor not available: {e}")
            self._enrich_opportunity = None

        # 9. Client Acceptance Portal
        try:
            from client_acceptance_portal import create_accept_link, get_deal, accept_deal, AI_SERVICE_CATALOG
            self.engines['acceptance_portal'] = {
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
        except Exception as e:
            logger.warning(f"⚠️ AcceptancePortal not available: {e}")

        # ═══════════════════════════════════════════════════════════════════
        # API KEY DETECTION (complete list from Render environment)
        # ═══════════════════════════════════════════════════════════════════

        self.available_systems['api_keys'] = {
            # === EMAIL ===
            'resend': bool(os.getenv('RESEND_API_KEY')),
            'postmark': bool(os.getenv('POSTMARK_API_KEY')),
            'sendgrid': bool(os.getenv('SENDGRID_API_KEY')),

            # === SMS/VOICE/WHATSAPP (Twilio) ===
            'twilio_sms': all([
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN'),
                os.getenv('TWILIO_FROM_NUMBER') or os.getenv('TWILIO_PHONE_NUMBER')
            ]),
            'twilio_whatsapp': all([
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            ]),  # WhatsApp doesn't need FROM_NUMBER (uses sandbox or approved number)
            'twilio_voice': all([
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN'),
                os.getenv('TWILIO_FROM_NUMBER') or os.getenv('TWILIO_PHONE_NUMBER')
            ]),

            # === PAYMENT ===
            'stripe': bool(os.getenv('STRIPE_SECRET_KEY')),
            'stripe_webhook': bool(os.getenv('STRIPE_WEBHOOK_SECRET')),

            # === SOCIAL PLATFORMS ===
            'twitter': bool(os.getenv('TWITTER_BEARER_TOKEN') or os.getenv('TWITTER_API_KEY')),
            'twitter_dm': bool(os.getenv('TWITTER_ACCESS_TOKEN')),
            'reddit': bool(os.getenv('REDDIT_CLIENT_ID') and os.getenv('REDDIT_CLIENT_SECRET')),
            'github': bool(os.getenv('GITHUB_TOKEN')),
            'linkedin': bool(os.getenv('LINKEDIN_ACCESS_TOKEN')),
            'instagram': bool(os.getenv('INSTAGRAM_ACCESS_TOKEN')),
            'instagram_business': bool(os.getenv('INSTAGRAM_ACCESS_TOKEN') and os.getenv('INSTAGRAM_BUSINESS_ID')),

            # === TEAM MESSAGING ===
            'slack': bool(os.getenv('SLACK_BOT_TOKEN') or os.getenv('SLACK_WEBHOOK_URL')),
            'discord': bool(os.getenv('DISCORD_WEBHOOK_URL') or os.getenv('DISCORD_BOT_TOKEN')),
            'telegram': bool(os.getenv('TELEGRAM_BOT_TOKEN')),

            # === AI/LLM ===
            'openrouter': bool(os.getenv('OPENROUTER_API_KEY')),
            'gemini': bool(os.getenv('GEMINI_API_KEY')),
            'perplexity': bool(os.getenv('PERPLEXITY_API_KEY')),
            'anthropic': bool(os.getenv('ANTHROPIC_API_KEY')),
            'openai': bool(os.getenv('OPENAI_API_KEY')),

            # === STORAGE/DATA ===
            'jsonbin': bool(os.getenv('JSONBIN_SECRET')),
            'airtable': bool(os.getenv('AIRTABLE_API_KEY')),
            'supabase': bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_KEY')),

            # === ECOMMERCE ===
            'shopify': bool(os.getenv('SHOPIFY_ACCESS_TOKEN') or os.getenv('SHOPIFY_ADMIN_TOKEN')),

            # === MEDIA/CREATIVE ===
            'stability': bool(os.getenv('STABILITY_API_KEY')),
            'runway': bool(os.getenv('RUNWAY_API_KEY')),
            'heygen': bool(os.getenv('HEYGEN_API_KEY')),
            'synthesia': bool(os.getenv('SYNTHESIA_API_KEY')),
            'elevenlabs': bool(os.getenv('ELEVENLABS_API_KEY')),

            # === SEARCH/DISCOVERY ===
            'serpapi': bool(os.getenv('SERPAPI_KEY')),
            'browserless': bool(os.getenv('BROWSERLESS_API_KEY')),
        }

        # Count configured APIs
        configured_count = sum(1 for v in self.available_systems['api_keys'].values() if v)
        total_count = len(self.available_systems['api_keys'])
        logger.info(f"📊 API Keys: {configured_count}/{total_count} configured")

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
        Present contract using BEST available channel for this opportunity.

        Priority order:
        1. Platform-native (Twitter DM for Twitter, LinkedIn for LinkedIn)
        2. Email (Resend → SendGrid → Postmark)
        3. SMS (Twilio)
        4. WhatsApp (Twilio)
        """
        result = PresentationResult()

        # Enrich opportunity with contact if not already done
        if 'contact' not in opportunity:
            opportunity = self.enrich_with_contact(opportunity)

        contact = opportunity.get('contact', {})
        metadata = opportunity.get('metadata', {})

        # Determine platform: prefer contact.platform (from enrichment) over source field
        # This is important for hybrid discovery where source is "perplexity_*" but
        # contact.platform correctly identifies the original platform (reddit, twitter, etc.)
        platform = (
            contact.get('platform', '').lower() or
            opportunity.get('platform', '').lower() or
            opportunity.get('source', '').lower()
        )

        # Also detect platform from URL if contact.platform is missing
        url = opportunity.get('url', '') or opportunity.get('canonical_url', '')
        if not platform or 'perplexity' in platform:
            if 'reddit.com' in url or 'redd.it' in url:
                platform = 'reddit'
            elif 'twitter.com' in url or 'x.com' in url:
                platform = 'twitter'
            elif 'github.com' in url:
                platform = 'github'
            elif 'linkedin.com' in url:
                platform = 'linkedin'
            elif 'news.ycombinator.com' in url:
                platform = 'hackernews'

        # Extract contact details
        email = contact.get('email') or metadata.get('poster_email') or metadata.get('email')
        phone = contact.get('phone') or metadata.get('poster_phone') or metadata.get('phone')
        twitter_handle = contact.get('twitter_handle') or metadata.get('poster_handle')
        linkedin_id = contact.get('linkedin_id') or metadata.get('poster_id')
        reddit_username = contact.get('reddit_username') or metadata.get('poster_username')
        github_username = contact.get('github_username') or metadata.get('poster_username')
        hackernews_username = contact.get('hackernews_username') or metadata.get('poster_username')

        # Build messages
        title = opportunity.get('title', 'your project')
        total_value = contract.get('total_amount_usd', sow.get('total_value_usd', 0) if sow else 0)

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 1: Platform-native outreach
        # ═══════════════════════════════════════════════════════════════════

        # Twitter opportunities → Twitter DM
        if 'twitter' in platform and 'outreach' in self.engines:
            engine = self.engines['outreach']
            if engine.get_stats().get('channels_configured', {}).get('twitter_dm'):
                if twitter_handle:
                    try:
                        outreach_result = await engine.process_opportunity(opportunity, contact)
                        if outreach_result and outreach_result.status.value == 'sent':
                            result.presented = True
                            result.method = 'twitter_dm'
                            result.channel = 'twitter'
                            result.recipient = twitter_handle
                            result.tracking_id = outreach_result.tracking_id
                            logger.info(f"✅ Twitter DM sent to @{twitter_handle}")
                            return result
                    except Exception as e:
                        result.fallback_attempts.append({'method': 'twitter_dm', 'error': str(e)})
                        logger.warning(f"⚠️ Twitter DM failed: {e}")

        # LinkedIn opportunities → LinkedIn message
        if 'linkedin' in platform and 'outreach' in self.engines:
            engine = self.engines['outreach']
            if engine.get_stats().get('channels_configured', {}).get('linkedin_message'):
                if linkedin_id:
                    try:
                        outreach_result = await engine.process_opportunity(opportunity, contact)
                        if outreach_result and outreach_result.status.value == 'sent':
                            result.presented = True
                            result.method = 'linkedin_message'
                            result.channel = 'linkedin'
                            result.recipient = linkedin_id
                            result.tracking_id = outreach_result.tracking_id
                            logger.info(f"✅ LinkedIn message sent to {linkedin_id}")
                            return result
                    except Exception as e:
                        result.fallback_attempts.append({'method': 'linkedin_message', 'error': str(e)})

        # Reddit opportunities → Reddit DM
        if 'reddit' in platform and 'outreach' in self.engines:
            engine = self.engines['outreach']
            if engine.get_stats().get('channels_configured', {}).get('reddit_dm'):
                if reddit_username:
                    try:
                        outreach_result = await engine.process_opportunity(opportunity, contact)
                        if outreach_result and outreach_result.status.value == 'sent':
                            result.presented = True
                            result.method = 'reddit_dm'
                            result.channel = 'reddit'
                            result.recipient = reddit_username
                            result.tracking_id = outreach_result.tracking_id
                            logger.info(f"✅ Reddit DM sent to u/{reddit_username}")
                            return result
                    except Exception as e:
                        result.fallback_attempts.append({'method': 'reddit_dm', 'error': str(e)})

        # GitHub opportunities → GitHub comment on issue
        if ('github' in platform or github_username) and 'platform_response' in self.engines:
            engine = self.engines['platform_response']
            if engine.get_supported_platforms().get('github'):
                try:
                    engagement = await engine.engage_with_opportunity(opportunity, send_dm_after=False)
                    if engagement and engagement.status.value in ['commented', 'sent']:
                        result.presented = True
                        result.method = 'github_comment'
                        result.channel = 'github'
                        result.recipient = github_username or 'issue author'
                        result.tracking_id = engagement.engagement_id
                        logger.info(f"✅ GitHub comment posted for {github_username}")
                        return result
                except Exception as e:
                    result.fallback_attempts.append({'method': 'github_comment', 'error': str(e)})

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 2: Email (Resend → SendGrid → Postmark)
        # ═══════════════════════════════════════════════════════════════════

        if email:
            message = self._build_email_message(title, total_value, client_room_url)

            # Try Resend first (modern, reliable)
            if 'resend' in self.connectors and self.available_systems.get('email_resend', {}).get('configured'):
                try:
                    email_result = await self.connectors['resend'].execute(
                        action='send_email',
                        params={
                            'to': email,
                            'subject': f"Proposal: {title[:50]}",
                            'body': message,
                            'html': self._build_html_email(title, total_value, client_room_url),
                        }
                    )
                    if email_result.ok:
                        result.presented = True
                        result.method = 'email'
                        result.channel = 'resend'
                        result.recipient = email
                        result.tracking_id = email_result.data.get('message_id')
                        result.details['email'] = email_result.data
                        logger.info(f"✅ Email sent via Resend to {email}")
                        return result
                except Exception as e:
                    result.fallback_attempts.append({'method': 'email_resend', 'error': str(e)})
                    logger.warning(f"⚠️ Resend email failed: {e}")

            # Fallback to generic email connector (SendGrid/Postmark)
            if 'email' in self.connectors and self.available_systems.get('email_generic', {}).get('configured'):
                try:
                    email_result = await self.connectors['email'].execute(
                        action='send_email',
                        params={
                            'to': email,
                            'subject': f"Proposal: {title[:50]}",
                            'body': message,
                        }
                    )
                    if email_result.ok:
                        result.presented = True
                        result.method = 'email'
                        result.channel = self.available_systems['email_generic'].get('provider', 'email')
                        result.recipient = email
                        result.tracking_id = email_result.data.get('message_id')
                        logger.info(f"✅ Email sent via {result.channel} to {email}")
                        return result
                except Exception as e:
                    result.fallback_attempts.append({'method': 'email_generic', 'error': str(e)})

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 3: SMS (Twilio)
        # ═══════════════════════════════════════════════════════════════════

        if phone and 'sms' in self.connectors and self.available_systems.get('sms_twilio', {}).get('configured'):
            sms_message = self._build_sms_message(title, client_room_url)
            try:
                sms_result = await self.connectors['sms'].execute(
                    action='send_sms',
                    params={
                        'to': phone,
                        'body': sms_message,
                    }
                )
                if sms_result.ok:
                    result.presented = True
                    result.method = 'sms'
                    result.channel = 'twilio'
                    result.recipient = phone
                    result.tracking_id = sms_result.data.get('message_sid')
                    result.details['sms'] = sms_result.data
                    logger.info(f"✅ SMS sent via Twilio to {phone}")
                    return result
            except Exception as e:
                result.fallback_attempts.append({'method': 'sms_twilio', 'error': str(e)})
                logger.warning(f"⚠️ Twilio SMS failed: {e}")

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 4: WhatsApp (Twilio) - if phone available
        # ═══════════════════════════════════════════════════════════════════

        if phone and self.available_systems.get('api_keys', {}).get('twilio_whatsapp'):
            whatsapp_message = f"Hi! Re: {title[:40]}\n\nWe can help with this. View our proposal:\n{client_room_url}"
            try:
                # Use SMS connector with WhatsApp prefix
                if 'sms' in self.connectors:
                    # Twilio WhatsApp requires whatsapp: prefix
                    whatsapp_to = phone if phone.startswith('whatsapp:') else f"whatsapp:{phone}"
                    whatsapp_from = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')  # Sandbox default

                    import httpx
                    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
                    auth_token = os.getenv('TWILIO_AUTH_TOKEN')

                    async with httpx.AsyncClient(timeout=30) as client:
                        wa_response = await client.post(
                            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                            data={
                                "To": whatsapp_to,
                                "From": whatsapp_from,
                                "Body": whatsapp_message[:1600]
                            },
                            auth=(account_sid, auth_token)
                        )

                        if wa_response.is_success:
                            wa_data = wa_response.json()
                            result.presented = True
                            result.method = 'whatsapp'
                            result.channel = 'twilio_whatsapp'
                            result.recipient = phone
                            result.tracking_id = wa_data.get('sid')
                            result.details['whatsapp'] = wa_data
                            logger.info(f"✅ WhatsApp sent via Twilio to {phone}")
                            return result
            except Exception as e:
                result.fallback_attempts.append({'method': 'whatsapp_twilio', 'error': str(e)})
                logger.warning(f"⚠️ Twilio WhatsApp failed: {e}")

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 5: Platform comment (GitHub, Reddit) - public visibility
        # ═══════════════════════════════════════════════════════════════════

        if 'platform_response' in self.engines:
            engine = self.engines['platform_response']
            supported = engine.get_supported_platforms()
            if supported.get(platform, False):
                try:
                    engagement = await engine.engage_with_opportunity(
                        opportunity,
                        send_dm_after=False
                    )
                    if engagement and engagement.status.value in ['commented', 'waiting']:
                        result.presented = True
                        result.method = 'platform_comment'
                        result.channel = platform
                        result.tracking_id = engagement.engagement_id
                        result.details['engagement'] = engagement.to_dict()
                        logger.info(f"✅ Comment posted on {platform}")
                        return result
                except Exception as e:
                    result.fallback_attempts.append({'method': 'platform_comment', 'error': str(e)})

        # ═══════════════════════════════════════════════════════════════════
        # NO CONTACT METHOD AVAILABLE
        # ═══════════════════════════════════════════════════════════════════

        if not result.presented:
            # Collect what we have and what's missing
            available = []
            gaps = []

            if email:
                available.append(f'email:{email[:20]}')
            else:
                gaps.append('email')

            if phone:
                available.append(f'phone:{phone}')
            else:
                gaps.append('phone')

            if twitter_handle:
                available.append(f'twitter:@{twitter_handle}')
            elif 'twitter' in platform:
                gaps.append('twitter_handle')

            if reddit_username:
                available.append(f'reddit:u/{reddit_username}')

            if github_username:
                available.append(f'github:{github_username}')

            if hackernews_username:
                available.append(f'hn:{hackernews_username}')

            # Build error message
            if available:
                result.error = f"Contact found ({', '.join(available)}) but no working outreach channel. Platform: {platform}"
                result.details['available_contacts'] = available
            else:
                result.error = f"No contact info found. Missing: {', '.join(gaps) or 'all contact info'}. Platform: {platform}"

            logger.warning(f"⚠️ Could not present contract: {result.error}")

            # Notify via Slack if configured (internal alert)
            if 'slack' in self.connectors and self.available_systems.get('slack', {}).get('configured'):
                try:
                    await self.connectors['slack'].execute(
                        action='send_slack_message',
                        params={
                            'text': f"⚠️ Contract presentation failed for {title[:50]}: {result.error}\n\nClient Room: {client_room_url}"
                        }
                    )
                except Exception:
                    pass

        return result

    def _build_email_message(self, title: str, total_value: float, client_room_url: str) -> str:
        """Build professional email message"""
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

    def _build_html_email(self, title: str, total_value: float, client_room_url: str) -> str:
        """Build HTML email with better formatting"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .cta {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
        .features {{ list-style: none; padding: 0; }}
        .features li {{ padding: 10px 0; padding-left: 30px; position: relative; }}
        .features li:before {{ content: "✓"; position: absolute; left: 0; color: #667eea; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin:0;">Proposal for Your Project</h1>
            <p style="margin:10px 0 0 0; opacity: 0.9;">{title[:60]}</p>
        </div>
        <div class="content">
            <p>Hi,</p>
            <p>I came across your post and wanted to reach out. We can handle this for you.</p>

            <h3>What we'll deliver:</h3>
            <ul class="features">
                <li>{title[:50]} - done, end-to-end</li>
                <li>Delivered within hours, not days</li>
                <li>Iterate until it's exactly right</li>
                <li>You only pay when you approve</li>
            </ul>

            <a href="{client_room_url}" class="cta">View Full Proposal →</a>

            <p style="margin-top:30px;">Let me know if you have any questions!</p>
            <p>— AiGentsy Team</p>
        </div>
    </div>
</body>
</html>
"""

    def _build_sms_message(self, title: str, client_room_url: str) -> str:
        """Build concise SMS message (160 char limit)"""
        return f"Re: {title[:30]}... We can help! View proposal: {client_room_url}"

    def get_status(self) -> Dict[str, Any]:
        """Get complete status of customer loop wiring"""

        configured_channels = []
        missing_channels = []
        api_keys = self.available_systems.get('api_keys', {})

        # === EMAIL ===
        if api_keys.get('resend'):
            configured_channels.append('email:resend')
        else:
            missing_channels.append('email:resend')
        if api_keys.get('sendgrid'):
            configured_channels.append('email:sendgrid')
        if api_keys.get('postmark'):
            configured_channels.append('email:postmark')

        # === SMS/WHATSAPP/VOICE ===
        if api_keys.get('twilio_sms'):
            configured_channels.append('sms:twilio')
        else:
            missing_channels.append('sms:twilio')
        if api_keys.get('twilio_whatsapp'):
            configured_channels.append('whatsapp:twilio')
        if api_keys.get('twilio_voice'):
            configured_channels.append('voice:twilio')

        # === SOCIAL DMs ===
        if api_keys.get('twitter_dm'):
            configured_channels.append('dm:twitter')
        else:
            missing_channels.append('dm:twitter')
        if api_keys.get('linkedin'):
            configured_channels.append('message:linkedin')
        if api_keys.get('reddit'):
            configured_channels.append('dm:reddit')
        if api_keys.get('instagram'):
            configured_channels.append('dm:instagram')
        if api_keys.get('instagram_business'):
            configured_channels.append('api:instagram_business')

        # === PLATFORM COMMENTS ===
        if api_keys.get('github'):
            configured_channels.append('comment:github')
        if api_keys.get('twitter'):
            configured_channels.append('comment:twitter')

        # === TEAM NOTIFICATIONS ===
        if api_keys.get('slack'):
            configured_channels.append('notify:slack')
        if api_keys.get('discord'):
            configured_channels.append('notify:discord')
        if api_keys.get('telegram'):
            configured_channels.append('notify:telegram')

        # === PAYMENT ===
        if api_keys.get('stripe'):
            configured_channels.append('payment:stripe')
        else:
            missing_channels.append('payment:stripe')
        if api_keys.get('stripe_webhook'):
            configured_channels.append('webhook:stripe')

        # === AI/LLM ===
        if api_keys.get('openrouter'):
            configured_channels.append('ai:openrouter')
        if api_keys.get('gemini'):
            configured_channels.append('ai:gemini')
        if api_keys.get('perplexity'):
            configured_channels.append('ai:perplexity')
        if api_keys.get('anthropic'):
            configured_channels.append('ai:anthropic')

        # === MEDIA ===
        if api_keys.get('stability'):
            configured_channels.append('media:stability')
        if api_keys.get('runway'):
            configured_channels.append('media:runway')

        # === STORAGE ===
        if api_keys.get('jsonbin'):
            configured_channels.append('storage:jsonbin')

        # Categorize channels
        outreach_channels = [c for c in configured_channels if c.startswith(('email:', 'sms:', 'whatsapp:', 'dm:', 'message:'))]
        comment_channels = [c for c in configured_channels if c.startswith('comment:')]
        payment_channels = [c for c in configured_channels if c.startswith('payment:')]
        ai_channels = [c for c in configured_channels if c.startswith('ai:')]

        return {
            'systems_loaded': self.available_systems,
            'connectors_loaded': list(self.connectors.keys()),
            'engines_loaded': list(self.engines.keys()),
            'configured_channels': configured_channels,
            'missing_channels': missing_channels,
            'channel_count': len(configured_channels),
            'outreach_channels': outreach_channels,
            'comment_channels': comment_channels,
            'payment_channels': payment_channels,
            'ai_channels': ai_channels,
            'can_present_contracts': len(outreach_channels) > 0,
            'can_accept_payments': api_keys.get('stripe', False),
            'api_key_summary': {
                'configured': sum(1 for v in api_keys.values() if v),
                'total': len(api_keys),
            },
            'recommendation': self._get_recommendation(configured_channels, missing_channels),
        }

    def _get_recommendation(self, configured: List[str], missing: List[str]) -> str:
        """Get actionable recommendation"""
        if not any(c.startswith(('email:', 'sms:')) for c in configured):
            return "CRITICAL: No direct contact channels. Set RESEND_API_KEY for email or TWILIO_* for SMS."

        if 'payment:stripe' not in configured:
            return "Set STRIPE_SECRET_KEY to enable payment collection."

        if 'sms:twilio' not in configured:
            return "Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER for SMS outreach."

        if len(configured) < 5:
            return f"Consider adding more channels. Missing: {', '.join(missing[:3])}"

        return "Customer loop is fully operational with multi-channel outreach."


# Singleton instance
_customer_loop_wiring = None


def get_customer_loop_wiring() -> CustomerLoopWiring:
    """Get singleton customer loop wiring instance"""
    global _customer_loop_wiring
    if _customer_loop_wiring is None:
        _customer_loop_wiring = CustomerLoopWiring()
    return _customer_loop_wiring


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
        'fallback_attempts': result.fallback_attempts,
    }
