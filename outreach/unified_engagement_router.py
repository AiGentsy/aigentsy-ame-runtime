"""
UNIFIED ENGAGEMENT ROUTER v1.0
===============================

Routes ALL discovery results to the best available channel.

Discovery (Perplexity, Twitter, Reddit, LinkedIn, Instagram, GitHub, OpenRouter)
    |
    v
Unified Router -> determines best channel per opportunity:
    |
    +-> Public Comment (Twitter reply, Reddit comment, LinkedIn comment, Instagram comment)
    +-> Email (Resend API)
    +-> SMS (Twilio)
    +-> WhatsApp (Twilio)
    +-> Twitter DM
    +-> LinkedIn DM
    +-> Reddit DM

Channel priority (per opportunity):
1. Public comment (if post is on a commentable platform) — highest visibility
2. Email (if email address found) — highest conversion
3. SMS (if phone number found) — highest open rate
4. WhatsApp (if phone number found) — high engagement
5. Platform DM (Twitter/LinkedIn/Reddit handle found) — warm channel

Voice: billionaire-calm (proof-forward, no hype)
"""

import os
import asyncio
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class EngagementChannel(Enum):
    PUBLIC_COMMENT = "public_comment"
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    TWITTER_DM = "twitter_dm"
    LINKEDIN_DM = "linkedin_dm"
    REDDIT_DM = "reddit_dm"


@dataclass
class RoutedEngagement:
    """Result of a routed engagement attempt"""
    opportunity_id: str
    channel: EngagementChannel
    success: bool
    platform: str = ""
    recipient: str = ""
    message_preview: str = ""
    referral_code: str = ""
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Commentable platforms
COMMENTABLE_PLATFORMS = {'twitter', 'reddit', 'linkedin', 'instagram'}

# SMS/WhatsApp message template (billionaire-calm)
SMS_TEMPLATE = "Hi—AiGentsy here. Re: {title}. We deliver this work fast, ~50% under market. Preview in ~30 min, pay only if you love it. {url}"

WHATSAPP_TEMPLATE = """Hi—AiGentsy here.

Re: {title}

We do this work. Preview in ~30 min, ~50% under market. Pay only if you love it.

View proposal: {url}"""


# =============================================================================
# UNIFIED ENGAGEMENT ROUTER
# =============================================================================

class UnifiedEngagementRouter:
    """
    Routes ALL discovery results to the best available engagement channel.

    Connects the full discovery fabric (Perplexity, Twitter, Reddit, etc.)
    to ALL outreach channels (public comments, email, SMS, WhatsApp, DMs).
    """

    def __init__(self):
        self.results: List[RoutedEngagement] = []
        self.daily_counts: Dict[str, int] = {c.value: 0 for c in EngagementChannel}
        self.max_daily: Dict[str, int] = {
            EngagementChannel.PUBLIC_COMMENT.value: 200,
            EngagementChannel.EMAIL.value: 100,
            EngagementChannel.SMS.value: 50,
            EngagementChannel.WHATSAPP.value: 50,
            EngagementChannel.TWITTER_DM.value: 50,
            EngagementChannel.LINKEDIN_DM.value: 30,
            EngagementChannel.REDDIT_DM.value: 30,
        }
        self.engaged_ids: set = set()

        # Check which channels are configured
        self.channels_available = self._check_channels()
        logger.info(f"Unified Router initialized. Available channels: {[c for c, v in self.channels_available.items() if v]}")

    def _check_channels(self) -> Dict[str, bool]:
        """Check which engagement channels are configured"""
        return {
            'public_comment': True,  # Always available if platform APIs work
            'email': bool(os.getenv('RESEND_API_KEY')),
            'sms': bool(os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN') and os.getenv('TWILIO_PHONE_NUMBER')),
            'whatsapp': bool(os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN')),
            'twitter_dm': bool(os.getenv('TWITTER_ACCESS_TOKEN')),
            'linkedin_dm': bool(os.getenv('LINKEDIN_ACCESS_TOKEN')),
            'reddit_dm': bool(os.getenv('REDDIT_CLIENT_ID') and os.getenv('REDDIT_CLIENT_SECRET')),
        }

    def _generate_referral_code(self, channel: str, opp_id: str) -> str:
        """Generate referral code for tracking"""
        prefix_map = {
            'public_comment': 'AIGX-PC',
            'email': 'AIGX-EM',
            'sms': 'AIGX-SM',
            'whatsapp': 'AIGX-WA',
            'twitter_dm': 'AIGX-TD',
            'linkedin_dm': 'AIGX-LD',
            'reddit_dm': 'AIGX-RD',
        }
        prefix = prefix_map.get(channel, 'AIGX')
        suffix = hashlib.md5(f"{opp_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:6].upper()
        return f"{prefix}-{suffix}"

    def _generate_referral_url(self, code: str) -> str:
        return f"https://aigentsy.com/start?ref={code}"

    # =========================================================================
    # CHANNEL ROUTING
    # =========================================================================

    def determine_channels(self, opportunity: Dict) -> List[EngagementChannel]:
        """
        Determine which channels to use for an opportunity, in priority order.

        Returns list of channels to try (first success wins).
        """
        channels = []
        contact = opportunity.get('contact', {})
        platform = opportunity.get('platform', '').lower()

        # 1. Public comment if it's a commentable platform
        if platform in COMMENTABLE_PLATFORMS and self.channels_available.get('public_comment'):
            channels.append(EngagementChannel.PUBLIC_COMMENT)

        # 2. Email if available
        email = contact.get('email', '')
        if email and '@' in email and self.channels_available.get('email'):
            channels.append(EngagementChannel.EMAIL)

        # 3. SMS if phone available
        phone = contact.get('phone', '') or contact.get('phone_number', '')
        if phone and self.channels_available.get('sms'):
            channels.append(EngagementChannel.SMS)

        # 4. WhatsApp if phone available
        if phone and self.channels_available.get('whatsapp'):
            channels.append(EngagementChannel.WHATSAPP)

        # 5. Platform DMs
        twitter_handle = contact.get('twitter_handle', '')
        if twitter_handle and self.channels_available.get('twitter_dm'):
            channels.append(EngagementChannel.TWITTER_DM)

        linkedin_url = contact.get('linkedin_url', '') or contact.get('linkedin_id', '')
        if linkedin_url and self.channels_available.get('linkedin_dm'):
            channels.append(EngagementChannel.LINKEDIN_DM)

        reddit_user = contact.get('reddit_username', '')
        if reddit_user and self.channels_available.get('reddit_dm'):
            channels.append(EngagementChannel.REDDIT_DM)

        return channels

    # =========================================================================
    # CHANNEL EXECUTORS
    # =========================================================================

    async def _execute_public_comment(self, opportunity: Dict, referral_code: str) -> RoutedEngagement:
        """Route to public engagement orchestrator"""
        try:
            from outreach.public_engagement_orchestrator import (
                PublicEngagementOrchestrator, PublicEngagementTarget, EngagementPlatform
            )

            platform_str = opportunity.get('platform', '').lower()
            platform_map = {
                'twitter': EngagementPlatform.TWITTER,
                'instagram': EngagementPlatform.INSTAGRAM,
                'linkedin': EngagementPlatform.LINKEDIN,
                'reddit': EngagementPlatform.REDDIT,
            }
            platform = platform_map.get(platform_str)
            if not platform:
                return RoutedEngagement(
                    opportunity_id=opportunity.get('id', ''),
                    channel=EngagementChannel.PUBLIC_COMMENT,
                    success=False, platform=platform_str,
                    error=f"No comment method for {platform_str}"
                )

            metadata = opportunity.get('metadata', {})
            contact = opportunity.get('contact', {})
            compound_id = opportunity.get('id', '')

            # Extract raw post ID
            orchestrator = PublicEngagementOrchestrator()
            post_id = orchestrator._extract_raw_post_id(compound_id, platform_str, metadata)

            author = (
                contact.get('twitter_handle', '') or
                contact.get('reddit_username', '') or
                contact.get('username', '') or
                metadata.get('author_handle', '') or
                metadata.get('author', '') or ''
            )

            target = PublicEngagementTarget(
                platform=platform,
                post_id=str(post_id),
                post_url=opportunity.get('url', ''),
                author_handle=author,
                title=opportunity.get('title', ''),
                body=opportunity.get('body', ''),
            )

            # Use singleton orchestrator
            from outreach.public_engagement_orchestrator import get_public_engagement_orchestrator
            orch = get_public_engagement_orchestrator()
            result = await orch._engage_target(target)

            return RoutedEngagement(
                opportunity_id=opportunity.get('id', ''),
                channel=EngagementChannel.PUBLIC_COMMENT,
                success=result.success,
                platform=platform_str,
                recipient=author,
                message_preview=result.message_sent[:150] if result.message_sent else '',
                referral_code=result.referral_code or referral_code,
                error=result.error,
            )

        except Exception as e:
            logger.error(f"Public comment failed: {e}")
            return RoutedEngagement(
                opportunity_id=opportunity.get('id', ''),
                channel=EngagementChannel.PUBLIC_COMMENT,
                success=False, error=str(e)
            )

    async def _execute_email(self, opportunity: Dict, referral_code: str) -> RoutedEngagement:
        """Send email via Resend"""
        try:
            import httpx

            api_key = os.getenv('RESEND_API_KEY')
            from_email = os.getenv('AIGENTSY_FROM_EMAIL', 'noreply@aigentsy.com')
            contact = opportunity.get('contact', {})
            to_email = contact.get('email', '')
            title = opportunity.get('title', 'Your Project')
            referral_url = self._generate_referral_url(referral_code)

            subject = f"Re: {title[:50]}"
            body = f"""Hi—AiGentsy here.

We do {title[:40]} work for teams that need world-class output fast. Typical delivery is minutes to first preview, and we price ~50% under market.

What you'd get today:
- A first preview in ~30 minutes
- Clear scope + transparent pricing (~50% under market)
- Only pay if you love it (no risk)

If that helps, reply "GO" and we'll drop a private preview link.

{referral_url}

---
Know someone who needs this? Share: {referral_url}
Start your own AI agency -> aigentsy.com/start

--AiGentsy"""

            try:
                from direct_outreach_engine import _ifx_quote_strip
                estimated_value = opportunity.get('estimated_value', opportunity.get('value', 500))
                body += _ifx_quote_strip("email", estimated_value, 1.0, referral_url)
            except ImportError:
                pass

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": f"AiGentsy <{from_email}>",
                        "to": [to_email],
                        "subject": subject,
                        "text": body,
                    }
                )

                if resp.status_code in [200, 201]:
                    data = resp.json()
                    return RoutedEngagement(
                        opportunity_id=opportunity.get('id', ''),
                        channel=EngagementChannel.EMAIL,
                        success=True,
                        recipient=to_email,
                        message_preview=subject,
                        referral_code=referral_code,
                        metadata={'message_id': data.get('id')},
                    )
                else:
                    return RoutedEngagement(
                        opportunity_id=opportunity.get('id', ''),
                        channel=EngagementChannel.EMAIL,
                        success=False,
                        recipient=to_email,
                        error=f"Resend {resp.status_code}: {resp.text[:200]}",
                    )

        except Exception as e:
            return RoutedEngagement(
                opportunity_id=opportunity.get('id', ''),
                channel=EngagementChannel.EMAIL,
                success=False, error=str(e)
            )

    async def _execute_sms(self, opportunity: Dict, referral_code: str) -> RoutedEngagement:
        """Send SMS via Twilio"""
        try:
            import httpx

            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')
            contact = opportunity.get('contact', {})
            phone = contact.get('phone', '') or contact.get('phone_number', '')
            title = opportunity.get('title', 'Your Project')[:30]
            referral_url = self._generate_referral_url(referral_code)

            # Normalize phone
            phone = phone.strip()
            if not phone.startswith('+'):
                phone = f"+1{phone}"

            message = SMS_TEMPLATE.format(title=title, url=referral_url)

            try:
                from direct_outreach_engine import _ifx_quote_strip
                estimated_value = opportunity.get('estimated_value', opportunity.get('value', 500))
                message += _ifx_quote_strip("sms", estimated_value, 1.0, referral_url)
            except ImportError:
                pass

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                    data={"To": phone, "From": from_number, "Body": message[:1600]},
                    auth=(account_sid, auth_token)
                )

                if resp.is_success:
                    data = resp.json()
                    return RoutedEngagement(
                        opportunity_id=opportunity.get('id', ''),
                        channel=EngagementChannel.SMS,
                        success=True,
                        recipient=phone,
                        message_preview=message[:100],
                        referral_code=referral_code,
                        metadata={'message_sid': data.get('sid')},
                    )
                else:
                    return RoutedEngagement(
                        opportunity_id=opportunity.get('id', ''),
                        channel=EngagementChannel.SMS,
                        success=False,
                        recipient=phone,
                        error=f"Twilio {resp.status_code}: {resp.text[:200]}",
                    )

        except Exception as e:
            return RoutedEngagement(
                opportunity_id=opportunity.get('id', ''),
                channel=EngagementChannel.SMS,
                success=False, error=str(e)
            )

    async def _execute_whatsapp(self, opportunity: Dict, referral_code: str) -> RoutedEngagement:
        """Send WhatsApp via Twilio"""
        try:
            import httpx

            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            whatsapp_from = os.getenv('TWILIO_WHATSAPP_NUMBER', f"whatsapp:{os.getenv('TWILIO_PHONE_NUMBER', '')}")
            contact = opportunity.get('contact', {})
            phone = contact.get('phone', '') or contact.get('phone_number', '')
            title = opportunity.get('title', 'Your Project')[:40]
            referral_url = self._generate_referral_url(referral_code)

            # Format for WhatsApp
            whatsapp_to = phone if phone.startswith('whatsapp:') else f"whatsapp:{phone.strip()}"
            if not whatsapp_from.startswith('whatsapp:'):
                whatsapp_from = f"whatsapp:{whatsapp_from}"

            message = WHATSAPP_TEMPLATE.format(title=title, url=referral_url)

            try:
                from direct_outreach_engine import _ifx_quote_strip
                estimated_value = opportunity.get('estimated_value', opportunity.get('value', 500))
                message += _ifx_quote_strip("whatsapp", estimated_value, 1.0, referral_url)
            except ImportError:
                pass

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                    data={"To": whatsapp_to, "From": whatsapp_from, "Body": message[:1600]},
                    auth=(account_sid, auth_token)
                )

                if resp.is_success:
                    data = resp.json()
                    return RoutedEngagement(
                        opportunity_id=opportunity.get('id', ''),
                        channel=EngagementChannel.WHATSAPP,
                        success=True,
                        recipient=phone,
                        message_preview=message[:100],
                        referral_code=referral_code,
                        metadata={'message_sid': data.get('sid')},
                    )
                else:
                    return RoutedEngagement(
                        opportunity_id=opportunity.get('id', ''),
                        channel=EngagementChannel.WHATSAPP,
                        success=False,
                        recipient=phone,
                        error=f"Twilio WhatsApp {resp.status_code}: {resp.text[:200]}",
                    )

        except Exception as e:
            return RoutedEngagement(
                opportunity_id=opportunity.get('id', ''),
                channel=EngagementChannel.WHATSAPP,
                success=False, error=str(e)
            )

    async def _execute_dm(self, opportunity: Dict, referral_code: str, channel: EngagementChannel) -> RoutedEngagement:
        """Route to direct_outreach_engine for DMs"""
        try:
            from direct_outreach_engine import send_direct_outreach
            contact = opportunity.get('contact', {})
            result = await send_direct_outreach(opportunity, contact)

            if result and result.status.value == 'sent':
                return RoutedEngagement(
                    opportunity_id=opportunity.get('id', ''),
                    channel=channel,
                    success=True,
                    recipient=result.recipient or '',
                    message_preview=result.message_preview[:150] if hasattr(result, 'message_preview') else '',
                    referral_code=referral_code,
                )
            else:
                error = result.error if result else 'No result returned'
                return RoutedEngagement(
                    opportunity_id=opportunity.get('id', ''),
                    channel=channel,
                    success=False,
                    error=str(error),
                )

        except Exception as e:
            return RoutedEngagement(
                opportunity_id=opportunity.get('id', ''),
                channel=channel,
                success=False, error=str(e)
            )

    # =========================================================================
    # MAIN ORCHESTRATION
    # =========================================================================

    async def route_opportunity(self, opportunity: Dict) -> RoutedEngagement:
        """
        Route a single opportunity to the best available channel.
        Tries channels in priority order, returns first success.
        """
        opp_id = opportunity.get('id', '')

        if opp_id in self.engaged_ids:
            return RoutedEngagement(
                opportunity_id=opp_id,
                channel=EngagementChannel.PUBLIC_COMMENT,
                success=False, error="Already engaged"
            )

        channels = self.determine_channels(opportunity)
        if not channels:
            return RoutedEngagement(
                opportunity_id=opp_id,
                channel=EngagementChannel.PUBLIC_COMMENT,
                success=False,
                error="No available channel (no contact info found)"
            )

        # Try channels in priority order
        for channel in channels:
            # Check daily limit
            if self.daily_counts.get(channel.value, 0) >= self.max_daily.get(channel.value, 50):
                continue

            referral_code = self._generate_referral_code(channel.value, opp_id)

            if channel == EngagementChannel.PUBLIC_COMMENT:
                result = await self._execute_public_comment(opportunity, referral_code)
            elif channel == EngagementChannel.EMAIL:
                result = await self._execute_email(opportunity, referral_code)
            elif channel == EngagementChannel.SMS:
                result = await self._execute_sms(opportunity, referral_code)
            elif channel == EngagementChannel.WHATSAPP:
                result = await self._execute_whatsapp(opportunity, referral_code)
            elif channel in (EngagementChannel.TWITTER_DM, EngagementChannel.LINKEDIN_DM, EngagementChannel.REDDIT_DM):
                result = await self._execute_dm(opportunity, referral_code, channel)
            else:
                continue

            if result.success:
                self.daily_counts[channel.value] = self.daily_counts.get(channel.value, 0) + 1
                self.engaged_ids.add(opp_id)
                self.results.append(result)
                return result

        # All channels failed — return last result
        if channels:
            self.results.append(result)
            return result

        return RoutedEngagement(
            opportunity_id=opp_id,
            channel=EngagementChannel.PUBLIC_COMMENT,
            success=False, error="All channels failed"
        )

    async def run_unified_cycle(self, max_opportunities: int = 50) -> Dict[str, Any]:
        """
        Run a full unified engagement cycle.

        1. Discover across ALL sources (Perplexity, Twitter, Reddit, etc.)
        2. Route each opportunity to the best channel
        3. Return detailed results
        """
        logger.info("=" * 60)
        logger.info("UNIFIED ENGAGEMENT CYCLE")
        logger.info("=" * 60)
        logger.info(f"Available channels: {[c for c, v in self.channels_available.items() if v]}")

        # Step 1: Full discovery
        try:
            from discovery.multi_source_discovery import MultiSourceDiscovery
            discovery = MultiSourceDiscovery()
            opportunities = await discovery.discover(max_opportunities=max_opportunities)
            logger.info(f"Discovered {len(opportunities)} total opportunities")
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return {'error': str(e), 'total_discovered': 0}

        # Step 2: Route each opportunity
        results = []
        for opp in opportunities:
            result = await self.route_opportunity(opp)
            results.append(result)

            # Brief pause between engagements
            if result.success:
                await asyncio.sleep(2)

        # Step 3: Summarize
        summary = {
            'total_discovered': len(opportunities),
            'total_routed': len(results),
            'successes': sum(1 for r in results if r.success),
            'failures': sum(1 for r in results if not r.success),
            'by_channel': {},
            'by_source_platform': {},
            'channels_available': self.channels_available,
            'daily_counts': self.daily_counts.copy(),
            'attempts': [],
        }

        for channel in EngagementChannel:
            channel_results = [r for r in results if r.channel == channel]
            if channel_results:
                summary['by_channel'][channel.value] = {
                    'attempted': len(channel_results),
                    'succeeded': sum(1 for r in channel_results if r.success),
                    'failed': sum(1 for r in channel_results if not r.success),
                }

        # Platform breakdown
        for opp in opportunities:
            plat = opp.get('platform', 'unknown')
            if plat not in summary['by_source_platform']:
                summary['by_source_platform'][plat] = 0
            summary['by_source_platform'][plat] += 1

        # Detailed attempts
        for r in results:
            attempt = {
                'opportunity_id': r.opportunity_id,
                'channel': r.channel.value,
                'success': r.success,
                'platform': r.platform,
                'recipient': r.recipient[:50] if r.recipient else '',
            }
            if r.success:
                attempt['referral_code'] = r.referral_code
                attempt['message_preview'] = r.message_preview[:100]
            else:
                attempt['error'] = r.error
            summary['attempts'].append(attempt)

        # Contribute to MetaHive
        await self._contribute_to_metahive(results)

        logger.info(f"Unified cycle complete: {summary['successes']}/{summary['total_routed']} succeeded")
        return summary

    async def _contribute_to_metahive(self, results: List[RoutedEngagement]):
        """Contribute engagement learnings to MetaHive"""
        try:
            from meta_hive_brain import get_metahive_brain
            brain = get_metahive_brain()
            if brain:
                for r in results:
                    if r.success:
                        brain.contribute_pattern(
                            pattern_type='unified_engagement',
                            pattern_key=f"{r.channel.value}:{r.platform}",
                            pattern_data={
                                'channel': r.channel.value,
                                'platform': r.platform,
                                'success': r.success,
                                'referral_code': r.referral_code,
                            },
                            user_id='system',
                            confidence=0.8
                        )
        except Exception:
            pass

    def get_stats(self) -> Dict:
        """Get unified router statistics"""
        return {
            'channels_available': self.channels_available,
            'daily_counts': self.daily_counts.copy(),
            'max_daily': self.max_daily.copy(),
            'total_engaged': len(self.engaged_ids),
            'total_results': len(self.results),
            'success_rate': sum(1 for r in self.results if r.success) / max(len(self.results), 1),
            'by_channel': {
                c.value: {
                    'used': self.daily_counts.get(c.value, 0),
                    'max': self.max_daily.get(c.value, 0),
                    'available': self.channels_available.get(c.value, False),
                }
                for c in EngagementChannel
            }
        }


# =============================================================================
# SINGLETON & EXPORTS
# =============================================================================

_router_instance: Optional[UnifiedEngagementRouter] = None


def get_unified_router() -> UnifiedEngagementRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = UnifiedEngagementRouter()
    return _router_instance


async def run_unified_engagement(max_opportunities: int = 50) -> Dict[str, Any]:
    """Run a unified engagement cycle across all channels"""
    router = get_unified_router()
    return await router.run_unified_cycle(max_opportunities)
