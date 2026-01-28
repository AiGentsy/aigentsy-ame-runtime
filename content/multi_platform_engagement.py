"""
MULTI-PLATFORM ENGAGEMENT BOT v1.0
==================================

Automated engagement across all platforms:
- Search for hiring/developer posts
- Comment with billionaire-calm pitch
- Track engagement and conversions
- Feed learnings to MetaHive

Platforms: TikTok, Instagram, Twitter, LinkedIn, YouTube, Facebook

Rate Limits:
- TikTok: 50 comments/day
- Instagram: 50 comments/day
- Twitter: 100 replies/day
- LinkedIn: 30 comments/day

Voice: billionaire-calm (proof-forward, no hype)
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# =============================================================================
# ENGAGEMENT CONFIGURATIONS
# =============================================================================

ENGAGEMENT_CONFIG = {
    'twitter': {
        'max_comments_per_day': 100,
        'search_queries': [
            'looking for developer',
            'need a developer',
            'hiring developer',
            'seeking React developer',
            'need backend help',
            'looking for Python developer'
        ],
        'min_wait_seconds': 60,
        'enabled': True
    },
    'linkedin': {
        'max_comments_per_day': 30,
        'search_queries': [
            "who's hiring developer",
            'looking for developer',
            'need engineer',
            'hiring React',
            'contract developer'
        ],
        'min_wait_seconds': 120,
        'enabled': True
    },
    'instagram': {
        'max_comments_per_day': 50,
        'hashtags': [
            'hiring', 'needadeveloper', 'freelancejobs',
            'techjobs', 'developerjobs', 'remotework'
        ],
        'min_wait_seconds': 90,
        'enabled': True
    },
    'tiktok': {
        'max_comments_per_day': 50,
        'hashtags': [
            'hiring', 'developer', 'freelance',
            'tech', 'coding', 'startuplife'
        ],
        'min_wait_seconds': 90,
        'enabled': False  # Requires Playwright setup
    },
    'youtube': {
        'max_comments_per_day': 50,
        'search_queries': [
            'hiring developer tutorial',
            'freelance developer tips',
            'startup hiring'
        ],
        'min_wait_seconds': 120,
        'enabled': False  # Requires YouTube API
    },
    'facebook': {
        'max_comments_per_day': 50,
        'groups': [
            'Freelance Developers',
            'Remote Work Jobs',
            'Startup Hiring'
        ],
        'min_wait_seconds': 120,
        'enabled': False  # Requires Facebook API
    }
}

# =============================================================================
# COMMENT TEMPLATES (billionaire-calm voice)
# =============================================================================

COMMENT_TEMPLATES = {
    'default': """Sharp dev help, right now.

World-class quality. Minutes-fast. ~50% under market.

Free first preview—pay only if it lands.

{referral_cta}""",

    'react': """Sharp React help, right now.

First preview in ~30 min. ~50% under market.

Pay only if you love it.

{referral_cta}""",

    'backend': """Sharp backend help, right now.

API, database, infrastructure—delivered in minutes.

~50% under market. Pay only if it lands.

{referral_cta}""",

    'python': """Sharp Python help, right now.

Automation, APIs, data—delivered in minutes.

~50% under market. Pay only if it lands.

{referral_cta}""",

    'fullstack': """Sharp full-stack help, right now.

Frontend to backend—delivered same day.

~50% under market. Pay only if it lands.

{referral_cta}""",

    'urgent': """We can ship a preview in ~30 min.

World-class quality. ~50% under market.

No deposit. Pay only if you love it.

{referral_cta}"""
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EngagementTarget:
    """A post/content to engage with."""
    platform: str
    post_id: str
    post_url: str
    author: str
    text: str
    detected_need: str  # react, backend, python, etc.
    engagement_score: float  # Higher = more valuable
    discovered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class EngagementResult:
    """Result of an engagement attempt."""
    platform: str
    target_id: str
    success: bool
    comment_id: Optional[str] = None
    error: Optional[str] = None
    referral_code: str = ''
    engaged_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =============================================================================
# MULTI-PLATFORM ENGAGEMENT BOT
# =============================================================================

class MultiPlatformEngagementBot:
    """
    Automated engagement across all social platforms.

    Features:
    - Multi-platform search for opportunities
    - Rate-limited commenting
    - Referral code tracking
    - MetaHive learning integration
    """

    def __init__(self):
        self.config = ENGAGEMENT_CONFIG
        self.templates = COMMENT_TEMPLATES
        self.daily_counts: Dict[str, int] = {}
        self.last_engagement: Dict[str, datetime] = {}
        self.engagement_history: List[EngagementResult] = []

        self.stats = {
            'total_comments': 0,
            'successful_comments': 0,
            'by_platform': {},
            'referral_clicks': 0,
            'conversions': 0
        }

        self._init_brain_connection()

        logger.info("=" * 60)
        logger.info("MULTI-PLATFORM ENGAGEMENT BOT INITIALIZED")
        logger.info("=" * 60)
        enabled = [p for p, c in self.config.items() if c.get('enabled')]
        logger.info(f"Enabled platforms: {enabled}")

    def _init_brain_connection(self):
        """Initialize MetaHive connection for learning."""
        try:
            from metahive_brain import contribute_to_hive, query_hive
            self.metahive_contribute = contribute_to_hive
            self.metahive_query = query_hive
            self.brain_connected = True
        except:
            self.brain_connected = False
            self.metahive_contribute = None
            self.metahive_query = None

    # =========================================================================
    # REFERRAL CODE GENERATION
    # =========================================================================

    def _generate_referral_code(self, platform: str) -> str:
        """Generate unique referral code for engagement tracking."""
        import hashlib
        platform_prefix = {
            'twitter': 'TW', 'linkedin': 'LI', 'instagram': 'IG',
            'tiktok': 'TT', 'youtube': 'YT', 'facebook': 'FB'
        }
        prefix = platform_prefix.get(platform, 'XX')
        hash_input = f"engage_{platform}_{datetime.now().timestamp()}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:6].upper()
        return f"AIGX-{prefix}-{hash_value}"

    def _get_referral_cta(self, platform: str, code: str) -> str:
        """Get platform-specific referral CTA."""
        ctas = {
            'twitter': f'Try it: aigentsy.com/start?ref={code}',
            'linkedin': f'Interested? aigentsy.com/start?ref={code}',
            'instagram': f'Link in bio or DM "GO" @AiGentsy',
            'tiktok': f'Link in bio → aigentsy.com/start?ref={code}',
            'youtube': f'Try AiGentsy: aigentsy.com/start?ref={code}',
            'facebook': f'Try it: aigentsy.com/start?ref={code}'
        }
        return ctas.get(platform, f'aigentsy.com/start?ref={code}')

    # =========================================================================
    # NEED DETECTION
    # =========================================================================

    def _detect_need(self, text: str) -> str:
        """Detect the type of help needed from post text."""
        text_lower = text.lower()

        if any(k in text_lower for k in ['react', 'vue', 'angular', 'frontend', 'front-end']):
            return 'react'
        elif any(k in text_lower for k in ['backend', 'back-end', 'api', 'database', 'server']):
            return 'backend'
        elif any(k in text_lower for k in ['python', 'django', 'flask', 'automation']):
            return 'python'
        elif any(k in text_lower for k in ['fullstack', 'full-stack', 'full stack']):
            return 'fullstack'
        elif any(k in text_lower for k in ['urgent', 'asap', 'immediately', 'quickly']):
            return 'urgent'
        else:
            return 'default'

    def _get_comment_for_need(self, need: str, referral_cta: str) -> str:
        """Get appropriate comment template for detected need."""
        template = self.templates.get(need, self.templates['default'])
        return template.format(referral_cta=referral_cta)

    # =========================================================================
    # RATE LIMITING
    # =========================================================================

    def _can_engage(self, platform: str) -> tuple[bool, str]:
        """Check if we can engage on this platform (rate limits)."""
        config = self.config.get(platform, {})

        if not config.get('enabled', False):
            return False, 'Platform not enabled'

        # Check daily limit
        today = datetime.now(timezone.utc).date().isoformat()
        count_key = f"{platform}_{today}"
        current_count = self.daily_counts.get(count_key, 0)
        max_count = config.get('max_comments_per_day', 50)

        if current_count >= max_count:
            return False, f'Daily limit reached ({current_count}/{max_count})'

        # Check minimum wait time
        last_time = self.last_engagement.get(platform)
        if last_time:
            min_wait = config.get('min_wait_seconds', 60)
            elapsed = (datetime.now(timezone.utc) - last_time).total_seconds()
            if elapsed < min_wait:
                return False, f'Rate limit: wait {int(min_wait - elapsed)}s'

        return True, 'OK'

    def _record_engagement(self, platform: str):
        """Record that we just engaged on a platform."""
        today = datetime.now(timezone.utc).date().isoformat()
        count_key = f"{platform}_{today}"
        self.daily_counts[count_key] = self.daily_counts.get(count_key, 0) + 1
        self.last_engagement[platform] = datetime.now(timezone.utc)

    # =========================================================================
    # DISCOVERY
    # =========================================================================

    async def discover_targets(self, platform: str, limit: int = 10) -> List[EngagementTarget]:
        """Discover engagement targets on a platform."""
        config = self.config.get(platform, {})
        targets = []

        if platform == 'twitter':
            targets = await self._discover_twitter_targets(config, limit)
        elif platform == 'linkedin':
            targets = await self._discover_linkedin_targets(config, limit)
        elif platform == 'instagram':
            targets = await self._discover_instagram_targets(config, limit)
        # Add other platforms as needed

        return targets

    async def _discover_twitter_targets(self, config: Dict, limit: int) -> List[EngagementTarget]:
        """Discover engagement targets on Twitter."""
        targets = []

        try:
            from platforms.packs.twitter_v2_api import twitter_v2_search

            # Use existing Twitter search
            tweets = await twitter_v2_search()

            for tweet in tweets[:limit]:
                text = tweet.get('text', '')
                if not text:
                    continue

                need = self._detect_need(text)
                username = tweet.get('user', {}).get('username', '')

                target = EngagementTarget(
                    platform='twitter',
                    post_id=tweet.get('id', ''),
                    post_url=f"https://twitter.com/{username}/status/{tweet.get('id', '')}",
                    author=username,
                    text=text,
                    detected_need=need,
                    engagement_score=self._calculate_engagement_score(tweet)
                )
                targets.append(target)

        except Exception as e:
            logger.warning(f"Twitter discovery error: {e}")

        return targets

    async def _discover_linkedin_targets(self, config: Dict, limit: int) -> List[EngagementTarget]:
        """Discover engagement targets on LinkedIn."""
        targets = []

        try:
            from platforms.packs.linkedin_api import linkedin_post_discovery

            posts = await linkedin_post_discovery(
                search_queries=config.get('search_queries', []),
                limit=limit
            )

            for post in posts:
                text = post.get('description', '')
                need = self._detect_need(text)

                target = EngagementTarget(
                    platform='linkedin',
                    post_id=post.get('post_id', ''),
                    post_url=post.get('url', ''),
                    author=post.get('author', ''),
                    text=text,
                    detected_need=need,
                    engagement_score=0.8  # LinkedIn posts are high value
                )
                targets.append(target)

        except Exception as e:
            logger.warning(f"LinkedIn discovery error: {e}")

        return targets

    async def _discover_instagram_targets(self, config: Dict, limit: int) -> List[EngagementTarget]:
        """Discover engagement targets on Instagram."""
        targets = []

        try:
            from platforms.packs.instagram_business_api import instagram_hashtag_discovery

            posts = await instagram_hashtag_discovery(
                hashtags=config.get('hashtags', []),
                limit_per_hashtag=limit // len(config.get('hashtags', ['hiring']))
            )

            for post in posts:
                text = post.get('description', '')
                need = self._detect_need(text)

                target = EngagementTarget(
                    platform='instagram',
                    post_id=post.get('post_id', ''),
                    post_url=post.get('url', ''),
                    author='',
                    text=text,
                    detected_need=need,
                    engagement_score=0.7
                )
                targets.append(target)

        except Exception as e:
            logger.warning(f"Instagram discovery error: {e}")

        return targets

    def _calculate_engagement_score(self, content: Dict) -> float:
        """Calculate engagement value score for a piece of content."""
        score = 0.5

        # Higher engagement = more valuable
        metrics = content.get('public_metrics', {})
        likes = metrics.get('like_count', 0)
        replies = metrics.get('reply_count', 0)
        retweets = metrics.get('retweet_count', 0)

        engagement = likes + replies * 2 + retweets * 3
        if engagement > 100:
            score += 0.3
        elif engagement > 10:
            score += 0.15

        # Verified = more valuable
        if content.get('user', {}).get('verified'):
            score += 0.1

        # Keywords indicating immediate need
        text = content.get('text', '').lower()
        urgent_keywords = ['urgent', 'asap', 'immediately', 'today', 'now']
        if any(k in text for k in urgent_keywords):
            score += 0.1

        return min(1.0, score)

    # =========================================================================
    # ENGAGEMENT EXECUTION
    # =========================================================================

    async def engage_with_target(self, target: EngagementTarget) -> EngagementResult:
        """Engage with a specific target (post comment)."""
        can_engage, reason = self._can_engage(target.platform)

        if not can_engage:
            return EngagementResult(
                platform=target.platform,
                target_id=target.post_id,
                success=False,
                error=reason
            )

        # Generate referral code
        referral_code = self._generate_referral_code(target.platform)
        referral_cta = self._get_referral_cta(target.platform, referral_code)

        # Get appropriate comment
        comment = self._get_comment_for_need(target.detected_need, referral_cta)

        # Post comment based on platform
        result = await self._post_comment(target, comment, referral_code)

        # Record engagement
        if result.success:
            self._record_engagement(target.platform)
            self.stats['successful_comments'] += 1
            self.stats['by_platform'][target.platform] = \
                self.stats['by_platform'].get(target.platform, 0) + 1

        self.stats['total_comments'] += 1
        self.engagement_history.append(result)

        # Feed to MetaHive
        await self._contribute_engagement_to_metahive(target, result)

        return result

    async def _post_comment(
        self,
        target: EngagementTarget,
        comment: str,
        referral_code: str
    ) -> EngagementResult:
        """Post comment to the target's platform."""
        try:
            if target.platform == 'twitter':
                return await self._post_twitter_comment(target, comment, referral_code)
            elif target.platform == 'linkedin':
                return await self._post_linkedin_comment(target, comment, referral_code)
            elif target.platform == 'instagram':
                return await self._post_instagram_comment(target, comment, referral_code)
            else:
                return EngagementResult(
                    platform=target.platform,
                    target_id=target.post_id,
                    success=False,
                    error=f'Platform {target.platform} not implemented',
                    referral_code=referral_code
                )
        except Exception as e:
            return EngagementResult(
                platform=target.platform,
                target_id=target.post_id,
                success=False,
                error=str(e),
                referral_code=referral_code
            )

    async def _post_twitter_comment(
        self,
        target: EngagementTarget,
        comment: str,
        referral_code: str
    ) -> EngagementResult:
        """Post reply to Twitter."""
        try:
            from platforms.packs.twitter_v2_api import post_tweet

            # Add @mention
            mention = f"@{target.author} " if target.author else ""
            full_comment = f"{mention}{comment}"

            # Truncate to Twitter limit
            if len(full_comment) > 280:
                full_comment = full_comment[:277] + "..."

            result = await post_tweet(full_comment, reply_to=target.post_id)

            if result.get('success'):
                return EngagementResult(
                    platform='twitter',
                    target_id=target.post_id,
                    success=True,
                    comment_id=result.get('tweet_id'),
                    referral_code=referral_code
                )
            else:
                return EngagementResult(
                    platform='twitter',
                    target_id=target.post_id,
                    success=False,
                    error=result.get('error'),
                    referral_code=referral_code
                )
        except Exception as e:
            return EngagementResult(
                platform='twitter',
                target_id=target.post_id,
                success=False,
                error=str(e),
                referral_code=referral_code
            )

    async def _post_linkedin_comment(
        self,
        target: EngagementTarget,
        comment: str,
        referral_code: str
    ) -> EngagementResult:
        """Post comment to LinkedIn."""
        try:
            from platforms.packs.linkedin_api import post_linkedin_comment

            result = await post_linkedin_comment(
                post_urn=target.post_id,
                opportunity={'title': target.text[:100]},
                pricing=None
            )

            if result.get('success'):
                return EngagementResult(
                    platform='linkedin',
                    target_id=target.post_id,
                    success=True,
                    comment_id=result.get('comment_id'),
                    referral_code=referral_code
                )
            else:
                return EngagementResult(
                    platform='linkedin',
                    target_id=target.post_id,
                    success=False,
                    error=result.get('error'),
                    referral_code=referral_code
                )
        except Exception as e:
            return EngagementResult(
                platform='linkedin',
                target_id=target.post_id,
                success=False,
                error=str(e),
                referral_code=referral_code
            )

    async def _post_instagram_comment(
        self,
        target: EngagementTarget,
        comment: str,
        referral_code: str
    ) -> EngagementResult:
        """Post comment to Instagram."""
        try:
            from platforms.packs.instagram_business_api import post_instagram_comment

            result = await post_instagram_comment(
                post_id=target.post_id,
                opportunity={'title': target.text[:100]},
                client_room_url=f"https://aigentsy.com/start?ref={referral_code}",
                pricing=None
            )

            if result.get('success'):
                return EngagementResult(
                    platform='instagram',
                    target_id=target.post_id,
                    success=True,
                    comment_id=result.get('comment_id'),
                    referral_code=referral_code
                )
            else:
                return EngagementResult(
                    platform='instagram',
                    target_id=target.post_id,
                    success=False,
                    error=result.get('error'),
                    referral_code=referral_code
                )
        except Exception as e:
            return EngagementResult(
                platform='instagram',
                target_id=target.post_id,
                success=False,
                error=str(e),
                referral_code=referral_code
            )

    # =========================================================================
    # BATCH ENGAGEMENT
    # =========================================================================

    async def run_engagement_cycle(
        self,
        platforms: List[str] = None,
        targets_per_platform: int = 5
    ) -> Dict[str, Any]:
        """
        Run one complete engagement cycle across platforms.

        Discovers targets and engages with rate limiting.
        """
        platforms = platforms or [p for p, c in self.config.items() if c.get('enabled')]
        results = {
            'platforms_processed': [],
            'targets_found': 0,
            'engagements_attempted': 0,
            'engagements_successful': 0,
            'by_platform': {}
        }

        for platform in platforms:
            platform_results = {
                'targets_found': 0,
                'engagements_attempted': 0,
                'engagements_successful': 0,
                'errors': []
            }

            # Discover targets
            targets = await self.discover_targets(platform, targets_per_platform)
            platform_results['targets_found'] = len(targets)
            results['targets_found'] += len(targets)

            # Engage with each target
            for target in targets:
                result = await self.engage_with_target(target)
                platform_results['engagements_attempted'] += 1
                results['engagements_attempted'] += 1

                if result.success:
                    platform_results['engagements_successful'] += 1
                    results['engagements_successful'] += 1
                else:
                    platform_results['errors'].append(result.error)

                # Wait between engagements
                await asyncio.sleep(self.config[platform].get('min_wait_seconds', 60))

            results['by_platform'][platform] = platform_results
            results['platforms_processed'].append(platform)

        return results

    # =========================================================================
    # METAHIVE INTEGRATION
    # =========================================================================

    async def _contribute_engagement_to_metahive(
        self,
        target: EngagementTarget,
        result: EngagementResult
    ):
        """Contribute engagement pattern to MetaHive."""
        if not self.metahive_contribute:
            return

        try:
            self.metahive_contribute(
                pattern_type='outreach_sequence',
                pattern={
                    'platform': target.platform,
                    'detected_need': target.detected_need,
                    'engagement_score': target.engagement_score,
                    'success': result.success
                },
                context={
                    'content_type': 'engagement_comment',
                    'target_keywords': target.text[:100]
                },
                outcome_score=1.0 if result.success else 0.0,
                revenue_impact=0.0  # Updated when conversion happens
            )
        except Exception as e:
            logger.warning(f"MetaHive contribution failed: {e}")

    # =========================================================================
    # STATS
    # =========================================================================

    def get_stats(self) -> Dict:
        """Get engagement bot statistics."""
        return {
            **self.stats,
            'daily_counts': dict(self.daily_counts),
            'history_size': len(self.engagement_history),
            'brain_connected': self.brain_connected
        }

    def get_daily_remaining(self) -> Dict[str, int]:
        """Get remaining engagement capacity per platform."""
        today = datetime.now(timezone.utc).date().isoformat()
        remaining = {}

        for platform, config in self.config.items():
            if not config.get('enabled'):
                remaining[platform] = 0
                continue

            count_key = f"{platform}_{today}"
            current = self.daily_counts.get(count_key, 0)
            max_count = config.get('max_comments_per_day', 50)
            remaining[platform] = max(0, max_count - current)

        return remaining


# =============================================================================
# MODULE-LEVEL
# =============================================================================

_engagement_bot: Optional[MultiPlatformEngagementBot] = None


def get_engagement_bot() -> MultiPlatformEngagementBot:
    """Get or create the singleton engagement bot."""
    global _engagement_bot
    if _engagement_bot is None:
        _engagement_bot = MultiPlatformEngagementBot()
    return _engagement_bot


async def run_daily_engagement() -> Dict:
    """Run a full day's engagement cycle."""
    bot = get_engagement_bot()
    return await bot.run_engagement_cycle()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MultiPlatformEngagementBot',
    'EngagementTarget',
    'EngagementResult',
    'get_engagement_bot',
    'run_daily_engagement',
    'ENGAGEMENT_CONFIG'
]
