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
import httpx
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
        # PRIORITY 1: Platform-native outreach (DIRECT API CALLS)
        # ═══════════════════════════════════════════════════════════════════

        # Calculate pricing for messaging
        try:
            from pricing_calculator import calculate_full_pricing, format_pricing_for_message
            pricing_result = calculate_full_pricing(opportunity)
            pricing = format_pricing_for_message(pricing_result)
            market_rate = int(pricing_result.market_rate)
            our_price = int(pricing_result.our_price)
            discount_pct = pricing_result.discount_pct
            fulfillment_type = pricing_result.fulfillment_type
        except ImportError:
            market_rate = int(total_value * 1.5)
            our_price = int(total_value * 0.7)
            discount_pct = 35
            fulfillment_type = 'fulfillment'

        # Get contact name
        contact_name = contact.get('name', 'there')

        # Clean the title (remove hashtags, noise)
        import re
        clean_title = title
        if clean_title:
            clean_title = re.sub(r'#\w+', '', clean_title)
            clean_title = re.sub(r'@\w+', '', clean_title)
            clean_title = re.sub(r'\[(HIRING|URGENT|REMOTE|WFH|CONTRACT|FREELANCE|PAID)\]', '', clean_title, flags=re.IGNORECASE)
            clean_title = re.sub(r'\s+', ' ', clean_title).strip()
            clean_title = clean_title.rstrip('.,;:!?-') or title

        # Detect project type for personalized intro
        from direct_outreach_engine import detect_project_type
        project_type = detect_project_type(clean_title)
        type_labels = {
            'development': 'dev', 'backend': 'backend dev', 'frontend': 'frontend dev',
            'automation': 'automation', 'design': 'designer', 'content': 'content writer',
            'data': 'data analyst', 'marketing': 'marketing', 'default': ''
        }
        type_label = type_labels.get(project_type, '')
        autonomous_intro = f"your autonomous {type_label} AiGentsy" if type_label else "your autonomous AiGentsy"

        # Build DM message for platform outreach - Professional, value-focused
        dm_message = f"""Hi {contact_name}!

Saw your post about {clean_title[:40]} - we can help.

We're AiGentsy. We deliver quality work in minutes at 50% off industry rates.

Your project: ${our_price:,} (vs ${market_rate:,} market rate)

How it works:
• Free preview first
• Pay only if you're happy
• Delivered in minutes

See your proposal: {client_room_url}

— The AiGentsy Team"""

        # ═══════════════════════════════════════════════════════════════════
        # SPAM PREVENTION: Check if we've already contacted this person
        # ═══════════════════════════════════════════════════════════════════
        opportunity_id = opportunity.get('id', '')

        try:
            from outreach import get_outreach_tracker
            tracker = get_outreach_tracker()
        except Exception as e:
            logger.warning(f"Could not load outreach tracker: {e}")
            tracker = None

        # Twitter opportunities → Try PUBLIC REPLY first, then DM fallback
        # Public replies work 100% of the time (no follower restriction)
        if ('twitter' in platform or twitter_handle) and self.available_systems.get('api_keys', {}).get('twitter_dm'):
            if twitter_handle:
                # Check spam prevention first
                can_send_twitter = True
                if tracker:
                    can_contact, reason = tracker.can_contact(twitter_handle, 'twitter', opportunity_id, clean_title)
                    if not can_contact:
                        logger.info(f"⏭️ Skipping Twitter outreach to @{twitter_handle}: {reason}")
                        result.fallback_attempts.append({'method': 'twitter_reply', 'error': f'spam_prevention:{reason}'})
                        can_send_twitter = False
                    else:
                        logger.info(f"✅ Spam check passed for @{twitter_handle}: {reason}")

                if can_send_twitter:
                    twitter_sent = False

                    # Strategy 1: PUBLIC REPLY (preferred - no follower restriction)
                    # Extract tweet_id from opportunity URL or metadata
                    tweet_id = opportunity.get('tweet_id')
                    if not tweet_id:
                        # Try to extract from URL
                        opp_url = opportunity.get('url', '')
                        import re
                        tweet_match = re.search(r'/status/(\d+)', opp_url)
                        if tweet_match:
                            tweet_id = tweet_match.group(1)

                    if tweet_id:
                        try:
                            # Create concise public reply message
                            public_message = self._create_public_reply_message(
                                opportunity=opportunity,
                                client_room_url=client_room_url
                            )
                            logger.info(f"📤 Attempting Twitter PUBLIC REPLY to @{twitter_handle} on tweet {tweet_id}...")
                            reply_result = await self._send_twitter_reply_direct(tweet_id, twitter_handle, public_message)

                            if reply_result.get('success'):
                                result.presented = True
                                result.method = 'twitter_reply'
                                result.channel = 'twitter'
                                result.recipient = f"@{twitter_handle.lstrip('@')}"
                                result.tracking_id = reply_result.get('reply_tweet_id')
                                result.details['twitter_reply'] = reply_result
                                logger.info(f"✅ Twitter PUBLIC REPLY sent to @{twitter_handle}")
                                twitter_sent = True

                                # Record outreach
                                if tracker:
                                    tracker.record_outreach(
                                        recipient=twitter_handle,
                                        recipient_type='twitter',
                                        opportunity_id=opportunity_id,
                                        opportunity_title=clean_title,
                                        contract_id=contract.get('id', contract.get('contract_id', '')),
                                        message_id=reply_result.get('reply_tweet_id')
                                    )

                                return result
                            else:
                                result.fallback_attempts.append({
                                    'method': 'twitter_reply',
                                    'error': reply_result.get('error'),
                                    'details': reply_result.get('details')
                                })
                                logger.warning(f"⚠️ Twitter reply failed: {reply_result.get('error')}, trying DM...")
                        except Exception as e:
                            result.fallback_attempts.append({'method': 'twitter_reply', 'error': str(e)})
                            logger.warning(f"⚠️ Twitter reply exception: {e}, trying DM...")

                    # Strategy 2: DM FALLBACK (only works if they follow us)
                    if not twitter_sent:
                        try:
                            logger.info(f"📤 Attempting Twitter DM to @{twitter_handle}...")
                            dm_result = await self._send_twitter_dm_direct(twitter_handle, dm_message)
                            if dm_result.get('success'):
                                result.presented = True
                                result.method = 'twitter_dm'
                                result.channel = 'twitter'
                                result.recipient = f"@{twitter_handle.lstrip('@')}"
                                result.tracking_id = dm_result.get('message_id')
                                result.details['twitter_dm'] = dm_result
                                logger.info(f"✅ Twitter DM sent to @{twitter_handle}")

                                # Record outreach for spam prevention
                                if tracker:
                                    tracker.record_outreach(
                                        recipient=twitter_handle,
                                        recipient_type='twitter',
                                        opportunity_id=opportunity_id,
                                        opportunity_title=clean_title,
                                        contract_id=contract.get('id', contract.get('contract_id', '')),
                                        message_id=dm_result.get('message_id')
                                    )

                                # Register conversation for auto-reply monitoring
                                try:
                                    from conversation import get_conversation_manager
                                    conv_manager = get_conversation_manager()
                                    conv_manager.register_outreach(
                                        platform='twitter',
                                        user_id=dm_result.get('recipient_id', ''),
                                        username=twitter_handle.lstrip('@'),
                                        contract_id=contract.get('id', contract.get('contract_id', '')),
                                        opportunity_id=opportunity_id,
                                        initial_message=dm_message,
                                        message_id=dm_result.get('message_id')
                                    )
                                    logger.info(f"📝 Registered conversation for @{twitter_handle}")
                                except Exception as conv_err:
                                    logger.warning(f"Could not register conversation: {conv_err}")

                                return result
                            else:
                                result.fallback_attempts.append({
                                    'method': 'twitter_dm',
                                    'error': dm_result.get('error'),
                                    'details': dm_result.get('details')
                                })
                                logger.warning(f"⚠️ Twitter DM failed: {dm_result.get('error')}")
                        except Exception as e:
                            result.fallback_attempts.append({'method': 'twitter_dm', 'error': str(e)})
                            logger.warning(f"⚠️ Twitter DM exception: {e}")

        # LinkedIn opportunities → LinkedIn message (DIRECT API)
        if ('linkedin' in platform or linkedin_id) and self.available_systems.get('api_keys', {}).get('linkedin'):
            if linkedin_id:
                try:
                    logger.info(f"📤 Attempting LinkedIn message to {linkedin_id}...")
                    msg_result = await self._send_linkedin_message_direct(linkedin_id, dm_message)
                    if msg_result.get('success'):
                        result.presented = True
                        result.method = 'linkedin_message'
                        result.channel = 'linkedin'
                        result.recipient = linkedin_id
                        result.tracking_id = msg_result.get('message_id')
                        result.details['linkedin_message'] = msg_result
                        logger.info(f"✅ LinkedIn message sent to {linkedin_id}")
                        return result
                    else:
                        result.fallback_attempts.append({
                            'method': 'linkedin_message',
                            'error': msg_result.get('error'),
                            'details': msg_result.get('details')
                        })
                        logger.warning(f"⚠️ LinkedIn message failed: {msg_result.get('error')}")
                except Exception as e:
                    result.fallback_attempts.append({'method': 'linkedin_message', 'error': str(e)})
                    logger.warning(f"⚠️ LinkedIn message exception: {e}")

        # Instagram opportunities → Instagram DM (DIRECT API)
        instagram_id = contact.get('instagram_id') or metadata.get('instagram_id')
        if ('instagram' in platform or instagram_id) and self.available_systems.get('api_keys', {}).get('instagram_business'):
            if instagram_id:
                try:
                    logger.info(f"📤 Attempting Instagram DM to {instagram_id}...")
                    dm_result = await self._send_instagram_dm_direct(instagram_id, dm_message)
                    if dm_result.get('success'):
                        result.presented = True
                        result.method = 'instagram_dm'
                        result.channel = 'instagram'
                        result.recipient = instagram_id
                        result.tracking_id = dm_result.get('message_id')
                        result.details['instagram_dm'] = dm_result
                        logger.info(f"✅ Instagram DM sent to {instagram_id}")
                        return result
                    else:
                        result.fallback_attempts.append({
                            'method': 'instagram_dm',
                            'error': dm_result.get('error'),
                            'details': dm_result.get('details')
                        })
                        logger.warning(f"⚠️ Instagram DM failed: {dm_result.get('error')}")
                except Exception as e:
                    result.fallback_attempts.append({'method': 'instagram_dm', 'error': str(e)})
                    logger.warning(f"⚠️ Instagram DM exception: {e}")

        # Reddit opportunities → Reddit DM (DIRECT API)
        if ('reddit' in platform or reddit_username) and self.available_systems.get('api_keys', {}).get('reddit'):
            if reddit_username:
                try:
                    logger.info(f"📤 Attempting Reddit DM to u/{reddit_username}...")
                    dm_result = await self._send_reddit_dm_direct(
                        reddit_username,
                        f"Re: {title[:60]}",
                        dm_message
                    )
                    if dm_result.get('success'):
                        result.presented = True
                        result.method = 'reddit_dm'
                        result.channel = 'reddit'
                        result.recipient = f"u/{reddit_username.lstrip('u/')}"
                        result.tracking_id = f"reddit_dm_{reddit_username}"
                        result.details['reddit_dm'] = dm_result
                        logger.info(f"✅ Reddit DM sent to u/{reddit_username}")
                        return result
                    else:
                        result.fallback_attempts.append({
                            'method': 'reddit_dm',
                            'error': dm_result.get('error'),
                            'details': dm_result.get('details')
                        })
                        logger.warning(f"⚠️ Reddit DM failed: {dm_result.get('error')}")
                except Exception as e:
                    result.fallback_attempts.append({'method': 'reddit_dm', 'error': str(e)})
                    logger.warning(f"⚠️ Reddit DM exception: {e}")

        # ═══════════════════════════════════════════════════════════════════
        # GITHUB: MANUAL REVIEW QUEUE (NO AUTOMATION - ToS COMPLIANCE)
        # ═══════════════════════════════════════════════════════════════════
        if 'github' in platform and not email:  # Only queue if no email fallback
            logger.info(f"📋 GitHub opportunity requires manual review (ToS compliance)")
            result.presented = False
            result.method = 'manual_review_queue'
            result.channel = 'github'
            result.details['manual_review'] = {
                'opportunity_id': opportunity.get('id'),
                'platform': 'github',
                'url': url,
                'title': title,
                'author': github_username,
                'contract_value': total_value,
                'client_room_url': client_room_url,
                'reason': 'GitHub automated comments prohibited by ToS',
                'action_needed': 'Human must manually review and comment',
                'added_at': datetime.now(timezone.utc).isoformat()
            }
            # Continue to try email/other channels as fallback
            # If email exists, it will be tried below

        # ═══════════════════════════════════════════════════════════════════
        # INSTAGRAM: Public comment (100% delivery - no restrictions)
        # ═══════════════════════════════════════════════════════════════════
        instagram_post_id = opportunity.get('post_id') or contact.get('instagram_post_id')
        if 'instagram' in platform and instagram_post_id:
            # Check spam prevention
            can_send_instagram = True
            if tracker:
                can_contact, reason = tracker.can_contact(
                    instagram_post_id, 'instagram', opportunity_id, clean_title
                )
                if not can_contact:
                    logger.info(f"⏭️ Skipping Instagram comment: {reason}")
                    result.fallback_attempts.append({'method': 'instagram_comment', 'error': f'spam_prevention:{reason}'})
                    can_send_instagram = False
                else:
                    logger.info(f"✅ Spam check passed for Instagram post {instagram_post_id}")

            if can_send_instagram:
                try:
                    # Use consolidated Instagram pack
                    from platforms.packs.instagram_business_api import post_instagram_comment as send_instagram_comment

                    logger.info(f"📤 Attempting Instagram comment on post {instagram_post_id}...")
                    ig_result = await send_instagram_comment(
                        post_id=instagram_post_id,
                        opportunity=opportunity,
                        client_room_url=client_room_url,
                        pricing={'market_rate': market_rate, 'our_price': our_price}
                    )

                    if ig_result.get('success'):
                        result.presented = True
                        result.method = 'instagram_comment'
                        result.channel = 'instagram'
                        result.recipient = f"post_{instagram_post_id}"
                        result.tracking_id = ig_result.get('comment_id')
                        result.details['instagram_comment'] = ig_result
                        logger.info(f"✅ Instagram comment posted on {instagram_post_id}")

                        # Record outreach
                        if tracker:
                            tracker.record_outreach(
                                recipient=instagram_post_id,
                                recipient_type='instagram',
                                opportunity_id=opportunity_id,
                                opportunity_title=clean_title,
                                contract_id=contract.get('id', contract.get('contract_id', '')),
                                message_id=ig_result.get('comment_id')
                            )

                        return result
                    else:
                        result.fallback_attempts.append({
                            'method': 'instagram_comment',
                            'error': ig_result.get('error')
                        })
                        logger.warning(f"⚠️ Instagram comment failed: {ig_result.get('error')}")
                except Exception as e:
                    result.fallback_attempts.append({'method': 'instagram_comment', 'error': str(e)})
                    logger.warning(f"⚠️ Instagram comment exception: {e}")

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 2: Email via RESEND (DIRECT API)
        # ═══════════════════════════════════════════════════════════════════

        if email and os.getenv('RESEND_API_KEY'):
            # Check spam prevention first
            can_send_email = True
            if tracker:
                can_contact, reason = tracker.can_contact(email, 'email', opportunity_id, clean_title)
                if not can_contact:
                    logger.info(f"⏭️ Skipping email to {email}: {reason}")
                    result.fallback_attempts.append({'method': 'email', 'error': f'spam_prevention:{reason}'})
                    can_send_email = False
                else:
                    logger.info(f"✅ Spam check passed for email {email}: {reason}")

            if can_send_email:
                # Build pricing dict for email templates
                email_pricing = {
                    'market_rate': market_rate,
                    'our_price': our_price,
                    'discount_pct': discount_pct,
                    'fulfillment_type': fulfillment_type
                }
                message = self._build_email_message(title, total_value, client_room_url, pricing=email_pricing)
                html_message = self._build_html_email(title, total_value, client_room_url, pricing=email_pricing)

                try:
                    logger.info(f"📧 Sending email via Resend to {email}...")
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp = await client.post(
                            "https://api.resend.com/emails",
                            headers={
                                "Authorization": f"Bearer {os.getenv('RESEND_API_KEY')}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "from": os.getenv('RESEND_FROM_EMAIL', 'AiGentsy <proposals@aigentsy.com>'),
                                "to": [email],
                                "subject": f"Proposal: {title[:50]}",
                                "html": html_message,
                                "text": message
                            }
                        )

                        if resp.status_code in [200, 201]:
                            resp_data = resp.json()
                            result.presented = True
                            result.method = 'email'
                            result.channel = 'resend'
                            result.recipient = email
                            result.tracking_id = resp_data.get('id')
                            result.details['email'] = resp_data
                            logger.info(f"✅ Email sent via Resend to {email}")

                            # Record outreach for spam prevention
                            if tracker:
                                tracker.record_outreach(
                                    recipient=email,
                                    recipient_type='email',
                                    opportunity_id=opportunity_id,
                                    opportunity_title=clean_title,
                                    contract_id=contract.get('id', contract.get('contract_id', '')),
                                    message_id=resp_data.get('id')
                                )

                            return result
                        else:
                            result.fallback_attempts.append({
                                'method': 'email_resend',
                                'error': f'Status {resp.status_code}',
                                'details': resp.text
                            })
                            logger.warning(f"⚠️ Resend email failed: {resp.status_code}")
                except Exception as e:
                    result.fallback_attempts.append({'method': 'email_resend', 'error': str(e)})
                    logger.warning(f"⚠️ Resend email exception: {e}")

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 3: SMS via TWILIO (DIRECT API)
        # ═══════════════════════════════════════════════════════════════════

        twilio_configured = all([
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN'),
            os.getenv('TWILIO_PHONE_NUMBER') or os.getenv('TWILIO_FROM_NUMBER')
        ])

        if phone and twilio_configured:
            sms_message = self._build_sms_message(title, client_room_url)
            try:
                logger.info(f"📱 Sending SMS via Twilio to {phone}...")
                account_sid = os.getenv('TWILIO_ACCOUNT_SID')
                auth_token = os.getenv('TWILIO_AUTH_TOKEN')
                from_number = os.getenv('TWILIO_PHONE_NUMBER') or os.getenv('TWILIO_FROM_NUMBER')

                async with httpx.AsyncClient(timeout=30) as client:
                    sms_response = await client.post(
                        f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                        data={
                            "To": phone,
                            "From": from_number,
                            "Body": sms_message[:160]
                        },
                        auth=(account_sid, auth_token)
                    )

                    if sms_response.is_success:
                        sms_data = sms_response.json()
                        result.presented = True
                        result.method = 'sms'
                        result.channel = 'twilio'
                        result.recipient = phone
                        result.tracking_id = sms_data.get('sid')
                        result.details['sms'] = sms_data
                        logger.info(f"✅ SMS sent via Twilio to {phone} (SID: {sms_data.get('sid')})")
                        return result
                    else:
                        result.fallback_attempts.append({
                            'method': 'sms_twilio',
                            'error': f'Status {sms_response.status_code}',
                            'details': sms_response.text
                        })
                        logger.warning(f"⚠️ Twilio SMS failed: {sms_response.status_code}")
            except Exception as e:
                result.fallback_attempts.append({'method': 'sms_twilio', 'error': str(e)})
                logger.warning(f"⚠️ Twilio SMS exception: {e}")

        # ═══════════════════════════════════════════════════════════════════
        # PRIORITY 4: WhatsApp via TWILIO (DIRECT API)
        # ═══════════════════════════════════════════════════════════════════

        if phone and os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN'):
            whatsapp_message = f"Hi! Re: {title[:40]}\n\nWe can help with this. View our proposal:\n{client_room_url}"
            try:
                logger.info(f"💬 Sending WhatsApp via Twilio to {phone}...")
                account_sid = os.getenv('TWILIO_ACCOUNT_SID')
                auth_token = os.getenv('TWILIO_AUTH_TOKEN')
                whatsapp_to = phone if phone.startswith('whatsapp:') else f"whatsapp:{phone}"
                whatsapp_from = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')

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
                    else:
                        result.fallback_attempts.append({
                            'method': 'whatsapp_twilio',
                            'error': f'Status {wa_response.status_code}',
                            'details': wa_response.text
                        })
                        logger.warning(f"⚠️ Twilio WhatsApp failed: {wa_response.status_code}")
            except Exception as e:
                result.fallback_attempts.append({'method': 'whatsapp_twilio', 'error': str(e)})
                logger.warning(f"⚠️ Twilio WhatsApp exception: {e}")

        # NOTE: Platform commenting (Priority 5) removed for ToS compliance
        # GitHub/Reddit automated comments are prohibited
        # All platform opportunities fall through to the "no contact" handler below

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

    def _build_email_message(self, title: str, total_value: float, client_room_url: str, pricing: dict = None) -> str:
        """Build professional email message with AiGentsy branding"""
        # Clean the title
        import re
        clean_title = title
        if clean_title:
            clean_title = re.sub(r'#\w+', '', clean_title)
            clean_title = re.sub(r'@\w+', '', clean_title)
            clean_title = re.sub(r'\[(HIRING|URGENT|REMOTE|WFH|CONTRACT|FREELANCE|PAID)\]', '', clean_title, flags=re.IGNORECASE)
            clean_title = re.sub(r'\s+', ' ', clean_title).strip()
            clean_title = clean_title.rstrip('.,;:!?-') or title

        # Calculate pricing if not provided
        if pricing is None:
            market_rate = int(total_value * 1.5)
            our_price = int(total_value * 0.7)
            discount_pct = 35
        else:
            market_rate = pricing.get('market_rate', int(total_value * 1.5))
            our_price = pricing.get('our_price', int(total_value * 0.7))
            discount_pct = pricing.get('discount_pct', 35)

        # Detect project type for personalized intro
        from direct_outreach_engine import detect_project_type
        project_type = detect_project_type(clean_title)
        type_labels = {
            'development': 'dev', 'backend': 'backend dev', 'frontend': 'frontend dev',
            'automation': 'automation', 'design': 'designer', 'content': 'content writer',
            'data': 'data analyst', 'marketing': 'marketing', 'default': ''
        }
        type_label = type_labels.get(project_type, '')
        autonomous_intro = f"your autonomous {type_label} AiGentsy" if type_label else "your autonomous AiGentsy"

        return f"""Hi there,

We noticed your post about {clean_title[:50]} and wanted to reach out.

We're AiGentsy - we deliver quality work in minutes at 50% off industry rates.

**Your project estimate:**
- Market rate: ${market_rate:,}
- Our price: ${our_price:,} (save {discount_pct}%)

**How we work:**
1. You get a free preview of our work first
2. Review it with no obligation
3. Only pay if you're completely satisfied

We deliver consistent, high-quality results with a satisfaction guarantee.

View your personalized proposal: {client_room_url}

Best,
The AiGentsy Team"""

    def _build_html_email(self, title: str, total_value: float, client_room_url: str, pricing: dict = None) -> str:
        """Build HTML email with AiGentsy brand colors"""
        # Clean the title
        import re
        clean_title = title
        if clean_title:
            clean_title = re.sub(r'#\w+', '', clean_title)
            clean_title = re.sub(r'@\w+', '', clean_title)
            clean_title = re.sub(r'\[(HIRING|URGENT|REMOTE|WFH|CONTRACT|FREELANCE|PAID)\]', '', clean_title, flags=re.IGNORECASE)
            clean_title = re.sub(r'\s+', ' ', clean_title).strip()
            clean_title = clean_title.rstrip('.,;:!?-') or title

        # Calculate pricing if not provided
        if pricing is None:
            market_rate = int(total_value * 1.5)
            our_price = int(total_value * 0.7)
            discount_pct = 35
            savings = market_rate - our_price
        else:
            market_rate = pricing.get('market_rate', int(total_value * 1.5))
            our_price = pricing.get('our_price', int(total_value * 0.7))
            discount_pct = pricing.get('discount_pct', 35)
            savings = market_rate - our_price

        # Detect project type for personalized intro
        from direct_outreach_engine import detect_project_type
        project_type = detect_project_type(clean_title)
        type_labels = {
            'development': 'dev', 'backend': 'backend dev', 'frontend': 'frontend dev',
            'automation': 'automation', 'design': 'designer', 'content': 'content writer',
            'data': 'data analyst', 'marketing': 'marketing', 'default': ''
        }
        type_label = type_labels.get(project_type, '')
        autonomous_intro = f"your autonomous {type_label} AiGentsy" if type_label else "your autonomous AiGentsy"

        return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; line-height: 1.6; background: #0e101a; color: #ffffff; margin: 0; padding: 40px 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #111; border: 1px solid #222; border-radius: 12px; overflow: hidden; box-shadow: 0 0 30px rgba(0,240,255,0.1); }}
        .header {{ background: linear-gradient(135deg, #00bfff 0%, #009cd8 100%); color: #000; padding: 32px; }}
        .header h1 {{ margin: 0 0 8px 0; font-size: 24px; font-weight: 700; }}
        .header p {{ margin: 0; opacity: 0.9; }}
        .content {{ padding: 32px; }}
        .greeting {{ color: #00ffcc; font-size: 18px; margin-bottom: 16px; }}
        .intro {{ color: #e0e0e0; margin-bottom: 24px; }}
        .pricing-box {{ background: linear-gradient(135deg, #131722 0%, #1a2030 100%); border: 1px solid #00bfff; border-radius: 8px; padding: 24px; margin: 24px 0; text-align: center; }}
        .price-label {{ color: #888; font-size: 14px; margin-bottom: 8px; }}
        .market-rate {{ color: #888; font-size: 20px; text-decoration: line-through; }}
        .our-price {{ color: #00ffcc; font-size: 36px; font-weight: 700; margin: 8px 0; }}
        .savings {{ color: #0b5; font-size: 16px; font-weight: 600; }}
        .features {{ list-style: none; padding: 0; margin: 24px 0; }}
        .features li {{ padding: 12px 0; padding-left: 32px; position: relative; color: #e0e0e0; border-bottom: 1px solid #222; }}
        .features li:last-child {{ border-bottom: none; }}
        .features li:before {{ content: "✓"; position: absolute; left: 0; color: #00ffcc; font-weight: bold; font-size: 18px; }}
        .cta {{ display: inline-block; background: linear-gradient(135deg, #00bfff 0%, #009cd8 100%); color: #000; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; margin: 24px 0; box-shadow: 0 4px 12px rgba(0,191,255,0.3); }}
        .cta:hover {{ background: linear-gradient(135deg, #00d4ff 0%, #00b8e6 100%); }}
        .footer {{ padding: 24px 32px; border-top: 1px solid #222; text-align: center; }}
        .signature {{ color: #00bfff; font-weight: 600; font-size: 16px; }}
        .tagline {{ color: #888; font-size: 14px; margin-top: 8px; }}
        .website {{ color: #00ffcc; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{clean_title[:50]}</h1>
            <p>Your autonomous AI</p>
        </div>
        <div class="content">
            <p class="greeting">Hey there!</p>

            <p class="intro">Great to meet you! We saw your post about <strong style="color: #00ffcc;">{clean_title[:50]}</strong> and wanted to reach out.</p>

            <p style="color: #e0e0e0;">We're <strong style="color: #00ffcc;">AiGentsy</strong> - your on-demand development team that delivers quality work fast.</p>

            <p style="color: #e0e0e0;">We'll handle everything you need at 50% off industry rates, delivered in minutes.</p>

            <div class="pricing-box">
                <p class="price-label">TYPICAL RATE</p>
                <p class="market-rate">${market_rate:,}</p>
                <p class="our-price">${our_price:,}</p>
                <p class="savings">You save {discount_pct}% (${savings:,} less)</p>
            </div>

            <ul class="features">
                <li><strong>Fast turnaround</strong> - Most projects delivered same day</li>
                <li><strong>Minutes, not days</strong> - Automated delivery</li>
                <li><strong>Free preview first</strong> - See our quality before you pay</li>
                <li><strong>We iterate until perfect</strong> - Not right? We redo it</li>
                <li><strong>Pay only if it's perfect</strong> - Not satisfied? You don't pay</li>
            </ul>

            <center>
                <a href="{client_room_url}" class="cta">See Your Free Preview</a>
            </center>
        </div>
        <div class="footer">
            <p class="signature">— AiGentsy</p>
            <p class="tagline">Your autonomous AI</p>
            <p style="margin-top: 16px;"><a href="https://aigentsy.com" class="website">https://aigentsy.com</a></p>
        </div>
    </div>
</body>
</html>
"""

    def _build_sms_message(self, title: str, client_room_url: str) -> str:
        """Build concise SMS message (160 char limit)"""
        return f"Re: {title[:30]}... We can help! View proposal: {client_room_url}"

    def _create_public_reply_message(self, opportunity: Dict, client_room_url: str) -> str:
        """
        Create concise message for Twitter public reply.
        Must be under 280 chars (minus @mention).
        Public-facing, so keep it professional and concise.
        """
        title = opportunity.get('title', '')[:60]

        # Detect project type for personalization
        title_lower = title.lower()
        if 'react' in title_lower or 'frontend' in title_lower:
            skill = 'React'
        elif 'backend' in title_lower or 'api' in title_lower or 'node' in title_lower:
            skill = 'backend'
        elif 'fullstack' in title_lower or 'full stack' in title_lower:
            skill = 'fullstack'
        elif 'python' in title_lower or 'django' in title_lower:
            skill = 'Python'
        elif 'design' in title_lower or 'ui' in title_lower or 'ux' in title_lower:
            skill = 'design'
        elif 'data' in title_lower or 'ml' in title_lower or 'ai' in title_lower:
            skill = 'AI/ML'
        else:
            skill = 'dev'

        # Concise public message (visible to everyone)
        # Focus on value prop: speed, quality, risk-free
        message = f"""We can help with this {skill} work! AiGentsy delivers in minutes at 50% off industry rates.

Free preview first - pay only if you love it.

Details: {client_room_url}"""

        return message

    # ═══════════════════════════════════════════════════════════════════════════
    # DIRECT API IMPLEMENTATIONS (bypass engines, guaranteed to work)
    # ═══════════════════════════════════════════════════════════════════════════

    async def _send_twitter_dm_direct(
        self,
        twitter_handle: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send Twitter DM using Twitter API v2 directly.

        Requires: TWITTER_BEARER_TOKEN and TWITTER_ACCESS_TOKEN
        """
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        api_key = os.getenv('TWITTER_API_KEY')
        api_secret = os.getenv('TWITTER_API_SECRET')

        if not bearer_token:
            return {'success': False, 'error': 'TWITTER_BEARER_TOKEN not configured'}

        # Clean the handle
        handle = twitter_handle.lstrip('@')

        async with httpx.AsyncClient(timeout=30) as client:
            # Step 1: Look up user ID from handle
            lookup_response = await client.get(
                f"https://api.twitter.com/2/users/by/username/{handle}",
                headers={"Authorization": f"Bearer {bearer_token}"}
            )

            if not lookup_response.is_success:
                return {
                    'success': False,
                    'error': f'User lookup failed: {lookup_response.status_code}',
                    'details': lookup_response.text
                }

            user_data = lookup_response.json()
            if 'data' not in user_data:
                return {'success': False, 'error': f'User @{handle} not found'}

            recipient_id = user_data['data']['id']

            # Step 2: Send DM using OAuth 1.0a (required for DMs)
            # Twitter DMs require OAuth 1.0a, not just Bearer token
            if all([api_key, api_secret, access_token, access_secret]):
                from requests_oauthlib import OAuth1
                import requests

                auth = OAuth1(
                    api_key,
                    client_secret=api_secret,
                    resource_owner_key=access_token,
                    resource_owner_secret=access_secret
                )

                dm_response = requests.post(
                    "https://api.twitter.com/2/dm_conversations/with/:participant_id/messages".replace(
                        ":participant_id", recipient_id
                    ),
                    json={"text": message[:10000]},  # Twitter DM limit
                    auth=auth
                )

                if dm_response.status_code in [200, 201]:
                    dm_data = dm_response.json()
                    return {
                        'success': True,
                        'message_id': dm_data.get('data', {}).get('dm_event_id'),
                        'recipient_id': recipient_id,
                        'recipient_handle': handle
                    }
                else:
                    return {
                        'success': False,
                        'error': f'DM send failed: {dm_response.status_code}',
                        'details': dm_response.text
                    }
            else:
                return {
                    'success': False,
                    'error': 'Twitter OAuth 1.0a credentials not fully configured (need API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)'
                }

    async def _send_twitter_reply_direct(
        self,
        tweet_id: str,
        twitter_handle: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send Twitter PUBLIC REPLY to a tweet.

        This ALWAYS works - no follower restriction!
        Unlike DMs which require the user to follow @AiGentsy.

        Requires: TWITTER_ACCESS_TOKEN with tweet:write scope
        """
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        api_key = os.getenv('TWITTER_API_KEY')
        api_secret = os.getenv('TWITTER_API_SECRET')

        if not all([api_key, api_secret, access_token, access_secret]):
            return {
                'success': False,
                'error': 'Twitter OAuth 1.0a credentials not fully configured'
            }

        # Clean the handle
        handle = twitter_handle.lstrip('@')

        # Format as public reply - must @mention the user
        # Keep it concise for public visibility
        reply_text = f"@{handle} {message}"

        # Ensure under 280 chars
        if len(reply_text) > 280:
            # Truncate but keep the @mention and any URL at the end
            # Find URL in message
            import re
            url_match = re.search(r'https?://\S+', message)
            url = url_match.group(0) if url_match else ''

            # Calculate available space
            mention = f"@{handle} "
            available = 280 - len(mention) - len(url) - 10  # 10 for "... " and buffer

            # Truncate the message content
            content = message.replace(url, '').strip()
            if len(content) > available:
                content = content[:available].rsplit(' ', 1)[0] + '...'

            reply_text = f"{mention}{content} {url}".strip()

        try:
            from requests_oauthlib import OAuth1
            import requests

            auth = OAuth1(
                api_key,
                client_secret=api_secret,
                resource_owner_key=access_token,
                resource_owner_secret=access_secret
            )

            # Twitter API v2 - Create tweet with reply
            response = requests.post(
                "https://api.twitter.com/2/tweets",
                json={
                    "text": reply_text,
                    "reply": {
                        "in_reply_to_tweet_id": str(tweet_id)
                    }
                },
                auth=auth
            )

            if response.status_code in [200, 201]:
                data = response.json()
                reply_tweet_id = data.get('data', {}).get('id')
                logger.info(f"✅ Twitter public reply sent to @{handle} on tweet {tweet_id}")
                return {
                    'success': True,
                    'method': 'twitter_reply',
                    'reply_tweet_id': reply_tweet_id,
                    'original_tweet_id': tweet_id,
                    'recipient_handle': handle,
                    'url': f"https://twitter.com/AiGentsy/status/{reply_tweet_id}"
                }
            else:
                return {
                    'success': False,
                    'error': f'Reply failed: {response.status_code}',
                    'details': response.text
                }

        except Exception as e:
            logger.error(f"Twitter reply error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _send_linkedin_message_direct(
        self,
        linkedin_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send LinkedIn message using LinkedIn Messaging API directly.

        Requires: LINKEDIN_ACCESS_TOKEN with messaging permissions
        Note: LinkedIn messaging API requires approved app and member URN
        """
        access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')

        if not access_token:
            return {'success': False, 'error': 'LINKEDIN_ACCESS_TOKEN not configured'}

        async with httpx.AsyncClient(timeout=30) as client:
            # LinkedIn messaging requires the recipient's member URN
            # Format: urn:li:person:{member_id} or urn:li:member:{member_id}

            # First, get our own profile to get sender URN
            profile_response = await client.get(
                "https://api.linkedin.com/v2/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Restli-Protocol-Version": "2.0.0"
                }
            )

            if not profile_response.is_success:
                return {
                    'success': False,
                    'error': f'Profile lookup failed: {profile_response.status_code}',
                    'details': profile_response.text
                }

            sender_id = profile_response.json().get('id')
            sender_urn = f"urn:li:person:{sender_id}"

            # Construct recipient URN
            recipient_urn = linkedin_id if linkedin_id.startswith('urn:') else f"urn:li:person:{linkedin_id}"

            # Send message via LinkedIn Messaging API
            message_payload = {
                "recipients": [recipient_urn],
                "message": {
                    "body": message[:3000]  # LinkedIn message limit
                }
            }

            msg_response = await client.post(
                "https://api.linkedin.com/v2/messages",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0"
                },
                json=message_payload
            )

            if msg_response.is_success:
                return {
                    'success': True,
                    'message_id': msg_response.headers.get('x-restli-id', 'sent'),
                    'recipient_urn': recipient_urn
                }
            else:
                # Try InMail as fallback (for non-connections)
                inmail_response = await client.post(
                    "https://api.linkedin.com/v2/inMails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0"
                    },
                    json={
                        "recipients": [{"person": {"~path": f"/people/{linkedin_id}"}}],
                        "subject": "Project Proposal",
                        "body": message[:3000]
                    }
                )

                if inmail_response.is_success:
                    return {
                        'success': True,
                        'message_id': inmail_response.headers.get('x-restli-id', 'sent'),
                        'method': 'inmail',
                        'recipient_urn': recipient_urn
                    }

                return {
                    'success': False,
                    'error': f'Message send failed: {msg_response.status_code}',
                    'details': msg_response.text
                }

    async def _send_instagram_dm_direct(
        self,
        instagram_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send Instagram DM using Instagram Graph API directly.

        Requires: INSTAGRAM_ACCESS_TOKEN with instagram_manage_messages permission
        Note: Only works for business/creator accounts responding to users who messaged first
        """
        access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        business_id = os.getenv('INSTAGRAM_BUSINESS_ID')

        if not access_token:
            return {'success': False, 'error': 'INSTAGRAM_ACCESS_TOKEN not configured'}

        if not business_id:
            return {'success': False, 'error': 'INSTAGRAM_BUSINESS_ID not configured'}

        async with httpx.AsyncClient(timeout=30) as client:
            # Instagram messaging via Graph API
            # Note: Can only message users who have messaged the business account first

            # Get Instagram-scoped user ID (IGSID) from username
            user_lookup = await client.get(
                f"https://graph.facebook.com/v18.0/{business_id}",
                params={
                    "fields": "business_discovery.username(" + instagram_id + "){id,username}",
                    "access_token": access_token
                }
            )

            if not user_lookup.is_success:
                return {
                    'success': False,
                    'error': f'User lookup failed: {user_lookup.status_code}',
                    'details': user_lookup.text
                }

            # Send message
            msg_response = await client.post(
                f"https://graph.facebook.com/v18.0/{business_id}/messages",
                params={"access_token": access_token},
                json={
                    "recipient": {"id": instagram_id},
                    "message": {"text": message[:1000]}  # Instagram limit
                }
            )

            if msg_response.is_success:
                msg_data = msg_response.json()
                return {
                    'success': True,
                    'message_id': msg_data.get('message_id'),
                    'recipient_id': instagram_id
                }
            else:
                return {
                    'success': False,
                    'error': f'Message send failed: {msg_response.status_code}',
                    'details': msg_response.text
                }

    async def _send_reddit_dm_direct(
        self,
        reddit_username: str,
        subject: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send Reddit private message using Reddit API directly.

        Requires: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
        """
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        username = os.getenv('REDDIT_USERNAME')
        password = os.getenv('REDDIT_PASSWORD')

        if not all([client_id, client_secret, username, password]):
            return {
                'success': False,
                'error': 'Reddit credentials not fully configured (need CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD)'
            }

        async with httpx.AsyncClient(timeout=30) as client:
            # Step 1: Get OAuth token
            auth_response = await client.post(
                "https://www.reddit.com/api/v1/access_token",
                data={
                    "grant_type": "password",
                    "username": username,
                    "password": password
                },
                auth=(client_id, client_secret),
                headers={"User-Agent": "AiGentsy/1.0"}
            )

            if not auth_response.is_success:
                return {
                    'success': False,
                    'error': f'OAuth failed: {auth_response.status_code}',
                    'details': auth_response.text
                }

            token = auth_response.json().get('access_token')

            # Step 2: Send private message
            msg_response = await client.post(
                "https://oauth.reddit.com/api/compose",
                data={
                    "api_type": "json",
                    "subject": subject[:100],  # Reddit subject limit
                    "text": message[:10000],  # Reddit message limit
                    "to": reddit_username.lstrip('u/')
                },
                headers={
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "AiGentsy/1.0"
                }
            )

            if msg_response.is_success:
                response_data = msg_response.json()
                errors = response_data.get('json', {}).get('errors', [])
                if not errors:
                    return {
                        'success': True,
                        'recipient': reddit_username,
                        'subject': subject
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Reddit API errors: {errors}'
                    }
            else:
                return {
                    'success': False,
                    'error': f'Message send failed: {msg_response.status_code}',
                    'details': msg_response.text
                }

    # NOTE: _send_github_issue_comment_direct removed (GitHub ToS violation for autonomous comments)

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
