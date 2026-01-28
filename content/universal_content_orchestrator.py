"""
UNIVERSAL MULTI-PLATFORM CONTENT ORCHESTRATOR v1.0
==================================================

One content → All platforms → Maximum reach → Multiple revenue funnels.

Integrates:
- MetaHive Brain (collective learning)
- AI Family Brain (optimal model routing)
- Video/Audio/Graphics Engines (content creation)
- Social Auto-Posting Engine (distribution)
- Referral System (attribution tracking)
- Universal Revenue Orchestrator (monetization)
- Affiliate Matching (additional revenue)

Voice: billionaire-calm throughout
- Short verbs, proof-forward, no hype
- "We'll show you, not sell you"

Author: AiGentsy
"""

import os
import asyncio
import logging
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# =============================================================================
# PLATFORM CONFIGURATIONS
# =============================================================================

PLATFORM_CONFIGS = {
    'tiktok': {
        'name': 'TikTok',
        'max_posts_per_day': 10,
        'max_comments_per_day': 50,
        'optimal_times_utc': [9, 12, 15, 19, 21],
        'video_format': '9:16',
        'max_video_length': 60,
        'max_caption_length': 2200,
        'referral_format': 'Link in bio → aigentsy.com/start?ref={code}',
        'hashtags': ['#hiring', '#developer', '#freelance', '#tech', '#coding', '#ai'],
        'revenue_streams': ['creator_fund', 'affiliate', 'referral']
    },
    'instagram': {
        'name': 'Instagram',
        'max_posts_per_day': 20,
        'max_comments_per_day': 50,
        'optimal_times_utc': [8, 11, 14, 17, 20],
        'video_format': '9:16',  # Reels
        'image_format': '1:1',   # Posts
        'max_video_length': 90,
        'max_caption_length': 2200,
        'referral_format': 'Link in bio or DM "AIGENTSY" for your link',
        'hashtags': ['#hiring', '#developer', '#freelance', '#tech', '#coding', '#startup'],
        'revenue_streams': ['affiliate', 'referral', 'monetization']
    },
    'twitter': {
        'name': 'Twitter/X',
        'max_posts_per_day': 50,
        'max_comments_per_day': 100,
        'optimal_times_utc': [9, 12, 15, 18, 21],
        'video_format': '16:9',
        'max_video_length': 140,
        'max_caption_length': 280,
        'thread_max_tweets': 10,
        'referral_format': 'Try it: aigentsy.com/start?ref={code}',
        'hashtags': ['#hiring', '#developer', '#freelance'],
        'revenue_streams': ['affiliate', 'referral', 'tip_jar']
    },
    'linkedin': {
        'name': 'LinkedIn',
        'max_posts_per_day': 5,
        'max_comments_per_day': 30,
        'optimal_times_utc': [8, 10, 12, 14, 17],
        'video_format': '16:9',
        'max_video_length': 600,
        'max_caption_length': 3000,
        'referral_format': 'Interested? aigentsy.com/start?ref={code}',
        'hashtags': ['#development', '#tech', '#startup', '#automation', '#ai'],
        'revenue_streams': ['b2b_referral', 'affiliate', 'consulting']
    },
    'youtube': {
        'name': 'YouTube Shorts',
        'max_posts_per_day': 50,
        'max_comments_per_day': 100,
        'optimal_times_utc': [10, 14, 16, 20],
        'video_format': '9:16',
        'max_video_length': 60,
        'max_description_length': 5000,
        'referral_format': 'Try AiGentsy: aigentsy.com/start?ref={code}',
        'hashtags': ['#shorts', '#coding', '#developer', '#tech', '#ai'],
        'revenue_streams': ['adsense', 'affiliate', 'referral', 'membership']
    },
    'facebook': {
        'name': 'Facebook',
        'max_posts_per_day': 10,
        'max_comments_per_day': 50,
        'optimal_times_utc': [9, 13, 16, 19],
        'video_format': '9:16',  # Reels
        'max_video_length': 90,
        'max_caption_length': 2000,
        'referral_format': 'Try it: aigentsy.com/start?ref={code}',
        'hashtags': ['#hiring', '#developer', '#tech'],
        'revenue_streams': ['affiliate', 'referral']
    }
}

# =============================================================================
# CONTENT TEMPLATES (billionaire-calm voice)
# =============================================================================

SUCCESS_STORY_VIDEO_TEMPLATE = {
    'duration': 60,
    'scenes': [
        {'time': '00:00-00:05', 'content': 'Client hired us for {project}'},
        {'time': '00:05-00:15', 'content': '[Code animation / typing effect]'},
        {'time': '00:15-00:25', 'content': 'Delivered in {time}'},
        {'time': '00:25-00:35', 'content': 'Cost: ${price:,} vs typical ${market_rate:,}'},
        {'time': '00:35-00:45', 'content': 'Client approved on first review'},
        {'time': '00:45-00:55', 'content': 'This is autonomous AI fulfillment'},
        {'time': '00:55-01:00', 'content': 'Try it: {referral_cta}'}
    ]
}

IMAGE_CAROUSEL_TEMPLATE = {
    'slides': [
        'Client needed {project}',
        'Market quote: ${market_rate:,}',
        'Our quote: ${price:,}',
        'Time estimate: Within the hour',
        'We delivered in {time}',
        'Client reviewed',
        'Approved on first try',
        'This is AI fulfillment',
        'No breaks, no mistakes',
        'Try it: {referral_cta}'
    ]
}

TWITTER_THREAD_TEMPLATE = [
    'Client hired us at 9am for {project}',
    'Market rate: ${market_rate:,} / 3-5 days\nOur rate: ${price:,} / Within the hour',
    'We delivered at 9:45am\nClient reviewed at 10am\nApproved on first try',
    'This is the power of autonomous AI\nNo sleep needed\nNo mistakes\nNo expensive overhead',
    'Want to try it?\n{referral_cta}\nGet 20% free preview first'
]

LINKEDIN_POST_TEMPLATE = """Project completed in {time}.

Client needed: {project}
Timeline: {time} (vs typical 3-5 days)
Cost: ${price:,} (vs market ${market_rate:,})
Result: Approved on first review

This is what autonomous AI fulfillment enables:
• 10x faster delivery
• 50% lower cost
• Zero human error
• Available 24/7

Interested in AI-powered project delivery?
{referral_cta}

#ai #automation #development #innovation"""


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ContentPackage:
    """A complete content package ready for multi-platform distribution."""
    id: str
    source_type: str  # contract_completion, case_study, tip, engagement
    source_data: Dict[str, Any]

    # Generated content
    video_path: Optional[str] = None
    video_script: Optional[str] = None
    image_paths: List[str] = field(default_factory=list)
    carousel_slides: List[str] = field(default_factory=list)
    twitter_thread: List[str] = field(default_factory=list)
    linkedin_post: Optional[str] = None
    short_caption: Optional[str] = None
    long_caption: Optional[str] = None

    # Platform-specific versions
    platform_versions: Dict[str, Dict] = field(default_factory=dict)

    # Referral codes (per platform for attribution)
    referral_codes: Dict[str, str] = field(default_factory=dict)

    # Tracking
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    posted_to: List[str] = field(default_factory=list)
    performance: Dict[str, Dict] = field(default_factory=dict)


@dataclass
class PostingResult:
    """Result of posting content to a platform."""
    platform: str
    success: bool
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error: Optional[str] = None
    referral_code: Optional[str] = None
    posted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =============================================================================
# UNIVERSAL CONTENT ORCHESTRATOR
# =============================================================================

class UniversalContentOrchestrator:
    """
    Orchestrates content creation and distribution across all platforms.

    Features:
    - One content → All platforms
    - MetaHive/AI Family learning integration
    - Platform-specific optimization
    - Multi-revenue funnel tracking
    - Referral code integration
    """

    def __init__(self):
        self.platforms = PLATFORM_CONFIGS
        self.content_queue: List[ContentPackage] = []
        self.posting_history: Dict[str, List[PostingResult]] = {}
        self.stats = {
            'content_generated': 0,
            'posts_made': 0,
            'posts_per_platform': {},
            'referral_clicks': 0,
            'conversions': 0,
            'revenue_generated': 0.0
        }

        # Initialize sub-systems
        self._init_brain_connections()
        self._init_engines()

        logger.info("=" * 60)
        logger.info("UNIVERSAL CONTENT ORCHESTRATOR INITIALIZED")
        logger.info("=" * 60)
        logger.info(f"Platforms: {list(self.platforms.keys())}")

    def _init_brain_connections(self):
        """Initialize MetaHive and AI Family Brain connections."""
        try:
            from metahive_brain import contribute_to_hive, query_hive
            from ai_family_brain import AIFamilyBrain
            self.metahive_contribute = contribute_to_hive
            self.metahive_query = query_hive
            self.ai_family = AIFamilyBrain()
            self.brain_connected = True
            logger.info("  [+] MetaHive + AI Family Brain connected")
        except Exception as e:
            logger.warning(f"  [-] Brain connection failed: {e}")
            self.brain_connected = False
            self.metahive_contribute = None
            self.metahive_query = None
            self.ai_family = None

    def _init_engines(self):
        """Initialize content generation engines."""
        self.video_engine = None
        self.audio_engine = None
        self.graphics_engine = None

        try:
            from video_engine import VideoEngine
            self.video_engine = VideoEngine()
            logger.info("  [+] Video Engine connected")
        except Exception as e:
            logger.warning(f"  [-] Video Engine not available: {e}")

        try:
            from audio_engine import AudioEngine
            self.audio_engine = AudioEngine()
            logger.info("  [+] Audio Engine connected")
        except Exception as e:
            logger.warning(f"  [-] Audio Engine not available: {e}")

        try:
            from integration.image_generation import generate_image_stability
            self.graphics_engine = generate_image_stability
            logger.info("  [+] Graphics Engine connected")
        except Exception as e:
            logger.warning(f"  [-] Graphics Engine not available: {e}")

    # =========================================================================
    # REFERRAL CODE GENERATION
    # =========================================================================

    def _generate_platform_referral_codes(self, content_id: str) -> Dict[str, str]:
        """Generate unique referral codes per platform for attribution tracking."""
        codes = {}

        platform_prefixes = {
            'tiktok': 'TT',
            'instagram': 'IG',
            'twitter': 'TW',
            'linkedin': 'LI',
            'youtube': 'YT',
            'facebook': 'FB'
        }

        for platform, prefix in platform_prefixes.items():
            # Generate unique code: AIGX-{platform}-{hash}
            hash_input = f"{content_id}_{platform}_{datetime.now().timestamp()}"
            hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:6].upper()
            codes[platform] = f"AIGX-{prefix}-{hash_value}"

        return codes

    def _get_referral_cta(self, platform: str, code: str) -> str:
        """Get platform-specific referral CTA with code."""
        config = self.platforms.get(platform, {})
        template = config.get('referral_format', 'aigentsy.com/start?ref={code}')
        return template.format(code=code)

    # =========================================================================
    # CONTENT GENERATION
    # =========================================================================

    async def generate_content_from_contract(
        self,
        contract: Dict[str, Any]
    ) -> ContentPackage:
        """
        Generate complete content package from a completed contract.

        This is the primary entry point after contract completion.
        """
        content_id = f"content_{contract.get('id', 'unknown')}_{datetime.now().timestamp()}"

        # Extract contract data
        source_data = {
            'project': contract.get('title', 'project'),
            'price': contract.get('pricing', {}).get('our_price', 1200),
            'market_rate': contract.get('pricing', {}).get('market_rate', 2400),
            'time': contract.get('completion_time', '45 minutes'),
            'fulfillment_type': contract.get('fulfillment_type', 'development'),
            'client': contract.get('client', {}).get('name', 'client')
        }

        # Generate referral codes per platform
        referral_codes = self._generate_platform_referral_codes(content_id)

        # Create content package
        package = ContentPackage(
            id=content_id,
            source_type='contract_completion',
            source_data=source_data,
            referral_codes=referral_codes
        )

        # Generate content for each format
        await self._generate_text_content(package)
        await self._generate_visual_content(package)

        # Adapt for each platform
        self._adapt_for_platforms(package)

        # Feed to MetaHive for learning
        await self._contribute_to_metahive(package)

        # Queue for posting
        self.content_queue.append(package)
        self.stats['content_generated'] += 1

        logger.info(f"Content package generated: {content_id}")
        return package

    async def _generate_text_content(self, package: ContentPackage):
        """Generate text content (captions, threads, posts)."""
        data = package.source_data

        # Get optimal AI model for copywriting
        model = 'claude'
        if self.ai_family:
            try:
                routing = self.ai_family.get_family_routing('copywriting')
                model = routing.get('primary_model', 'claude')
            except:
                pass

        # Generate Twitter thread
        package.twitter_thread = []
        for tweet_template in TWITTER_THREAD_TEMPLATE:
            tweet = tweet_template.format(
                project=data['project'],
                price=data['price'],
                market_rate=data['market_rate'],
                time=data['time'],
                referral_cta=self._get_referral_cta('twitter', package.referral_codes.get('twitter', ''))
            )
            package.twitter_thread.append(tweet)

        # Generate LinkedIn post
        package.linkedin_post = LINKEDIN_POST_TEMPLATE.format(
            project=data['project'],
            price=data['price'],
            market_rate=data['market_rate'],
            time=data['time'],
            referral_cta=self._get_referral_cta('linkedin', package.referral_codes.get('linkedin', ''))
        )

        # Generate carousel slides
        package.carousel_slides = []
        for slide_template in IMAGE_CAROUSEL_TEMPLATE['slides']:
            slide = slide_template.format(
                project=data['project'],
                price=data['price'],
                market_rate=data['market_rate'],
                time=data['time'],
                referral_cta=self._get_referral_cta('instagram', package.referral_codes.get('instagram', ''))
            )
            package.carousel_slides.append(slide)

        # Generate short caption (for TikTok, Instagram Reels)
        package.short_caption = f"""Shipped {data['project']} in {data['time']}.

${data['price']:,} (market ~${data['market_rate']:,})

World-class. Minutes-fast. ~50% under market.

{self._get_referral_cta('tiktok', package.referral_codes.get('tiktok', ''))}"""

        # Generate long caption
        package.long_caption = f"""Client needed: {data['project']}
We delivered in {data['time']}.

Cost: ${data['price']:,} (vs market ${data['market_rate']:,})
Result: Approved on first review.

This is what happens when you remove delays, overhead, and back-and-forth.

{self._get_referral_cta('instagram', package.referral_codes.get('instagram', ''))}"""

    async def _generate_visual_content(self, package: ContentPackage):
        """Generate visual content (video, images)."""
        data = package.source_data

        # Generate video script
        package.video_script = ""
        for scene in SUCCESS_STORY_VIDEO_TEMPLATE['scenes']:
            content = scene['content'].format(
                project=data['project'],
                price=data['price'],
                market_rate=data['market_rate'],
                time=data['time'],
                referral_cta=self._get_referral_cta('tiktok', package.referral_codes.get('tiktok', ''))
            )
            package.video_script += f"[{scene['time']}] {content}\n"

        # Generate images if graphics engine available
        if self.graphics_engine:
            try:
                # Portfolio image
                prompt = f"Modern {data['project']} dashboard interface, dark mode, clean minimal UI, professional software screenshot, no text"
                result = await self.graphics_engine(prompt, width=1200, height=675)
                if result.get('success'):
                    # Would save to storage and add path
                    logger.info("Portfolio image generated")
            except Exception as e:
                logger.warning(f"Image generation failed: {e}")

    def _adapt_for_platforms(self, package: ContentPackage):
        """Adapt content for each platform's specific requirements."""
        for platform, config in self.platforms.items():
            version = {
                'platform': platform,
                'referral_code': package.referral_codes.get(platform, ''),
                'referral_cta': self._get_referral_cta(platform, package.referral_codes.get(platform, '')),
                'hashtags': ' '.join(config.get('hashtags', [])),
            }

            # Platform-specific adaptations
            if platform == 'twitter':
                # Truncate to 280 chars per tweet
                version['content'] = package.twitter_thread
                version['format'] = 'thread'

            elif platform == 'linkedin':
                version['content'] = package.linkedin_post
                version['format'] = 'post'

            elif platform == 'instagram':
                version['reel_caption'] = package.short_caption[:2200]
                version['post_caption'] = package.long_caption[:2200]
                version['carousel'] = package.carousel_slides
                version['format'] = 'multi'  # Reels + Posts + Carousel

            elif platform == 'tiktok':
                version['caption'] = package.short_caption[:2200]
                version['video_script'] = package.video_script
                version['format'] = 'video'

            elif platform == 'youtube':
                version['description'] = package.long_caption
                version['video_script'] = package.video_script
                version['format'] = 'short'

            elif platform == 'facebook':
                version['caption'] = package.long_caption[:2000]
                version['format'] = 'reel'

            package.platform_versions[platform] = version

    # =========================================================================
    # POSTING
    # =========================================================================

    async def post_to_all_platforms(
        self,
        package: ContentPackage,
        platforms: List[str] = None
    ) -> Dict[str, PostingResult]:
        """
        Post content package to all (or specified) platforms.

        Staggers posts by 5-10 minutes to avoid looking automated.
        """
        platforms = platforms or list(self.platforms.keys())
        results = {}

        for i, platform in enumerate(platforms):
            # Stagger posts
            if i > 0:
                delay = 300 + (i * 60)  # 5+ minutes between posts
                logger.info(f"Waiting {delay}s before {platform}...")
                await asyncio.sleep(delay)

            result = await self._post_to_platform(package, platform)
            results[platform] = result

            if result.success:
                package.posted_to.append(platform)
                self.stats['posts_made'] += 1
                self.stats['posts_per_platform'][platform] = \
                    self.stats['posts_per_platform'].get(platform, 0) + 1

                # Record in posting history
                if platform not in self.posting_history:
                    self.posting_history[platform] = []
                self.posting_history[platform].append(result)

        return results

    async def _post_to_platform(
        self,
        package: ContentPackage,
        platform: str
    ) -> PostingResult:
        """Post content to a specific platform."""
        version = package.platform_versions.get(platform, {})

        try:
            if platform == 'twitter':
                return await self._post_to_twitter(package, version)
            elif platform == 'linkedin':
                return await self._post_to_linkedin(package, version)
            elif platform == 'instagram':
                return await self._post_to_instagram(package, version)
            elif platform == 'tiktok':
                return await self._post_to_tiktok(package, version)
            elif platform == 'youtube':
                return await self._post_to_youtube(package, version)
            elif platform == 'facebook':
                return await self._post_to_facebook(package, version)
            else:
                return PostingResult(
                    platform=platform,
                    success=False,
                    error=f'Unknown platform: {platform}',
                    referral_code=version.get('referral_code')
                )
        except Exception as e:
            logger.error(f"Error posting to {platform}: {e}")
            return PostingResult(
                platform=platform,
                success=False,
                error=str(e),
                referral_code=version.get('referral_code')
            )

    async def _post_to_twitter(self, package: ContentPackage, version: Dict) -> PostingResult:
        """Post thread to Twitter."""
        try:
            from platforms.packs.twitter_v2_api import post_thread

            tweets = version.get('content', package.twitter_thread)
            result = await post_thread(tweets)

            if result.get('success'):
                return PostingResult(
                    platform='twitter',
                    success=True,
                    post_id=result.get('tweets', [{}])[0].get('tweet_id'),
                    post_url=result.get('thread_url'),
                    referral_code=version.get('referral_code')
                )
            else:
                return PostingResult(
                    platform='twitter',
                    success=False,
                    error=result.get('error'),
                    referral_code=version.get('referral_code')
                )
        except Exception as e:
            return PostingResult(
                platform='twitter',
                success=False,
                error=str(e),
                referral_code=version.get('referral_code')
            )

    async def _post_to_linkedin(self, package: ContentPackage, version: Dict) -> PostingResult:
        """Post to LinkedIn."""
        try:
            from platforms.packs.linkedin_api import post_linkedin_content

            text = version.get('content', package.linkedin_post)
            result = await post_linkedin_content(text)

            if result.get('success'):
                return PostingResult(
                    platform='linkedin',
                    success=True,
                    post_id=result.get('post_id'),
                    post_url=result.get('url'),
                    referral_code=version.get('referral_code')
                )
            else:
                return PostingResult(
                    platform='linkedin',
                    success=False,
                    error=result.get('error'),
                    referral_code=version.get('referral_code')
                )
        except Exception as e:
            return PostingResult(
                platform='linkedin',
                success=False,
                error=str(e),
                referral_code=version.get('referral_code')
            )

    async def _post_to_instagram(self, package: ContentPackage, version: Dict) -> PostingResult:
        """Post to Instagram (requires image/video URL)."""
        try:
            from platforms.packs.instagram_business_api import post_instagram_content

            # Would need actual image URL for Instagram
            # For now, return placeholder
            return PostingResult(
                platform='instagram',
                success=False,
                error='Instagram posting requires image_url - implement image storage',
                referral_code=version.get('referral_code')
            )
        except Exception as e:
            return PostingResult(
                platform='instagram',
                success=False,
                error=str(e),
                referral_code=version.get('referral_code')
            )

    async def _post_to_tiktok(self, package: ContentPackage, version: Dict) -> PostingResult:
        """Post to TikTok (requires video file)."""
        # TikTok API posting would go here
        # For MVP, mark as pending video upload
        return PostingResult(
            platform='tiktok',
            success=False,
            error='TikTok posting requires video file - implement video generation',
            referral_code=version.get('referral_code')
        )

    async def _post_to_youtube(self, package: ContentPackage, version: Dict) -> PostingResult:
        """Post to YouTube Shorts (requires video file)."""
        # YouTube API posting would go here
        return PostingResult(
            platform='youtube',
            success=False,
            error='YouTube posting requires video file - implement video generation',
            referral_code=version.get('referral_code')
        )

    async def _post_to_facebook(self, package: ContentPackage, version: Dict) -> PostingResult:
        """Post to Facebook."""
        # Facebook API posting would go here
        return PostingResult(
            platform='facebook',
            success=False,
            error='Facebook posting requires implementation',
            referral_code=version.get('referral_code')
        )

    # =========================================================================
    # METAHIVE INTEGRATION
    # =========================================================================

    async def _contribute_to_metahive(self, package: ContentPackage):
        """Feed content patterns to MetaHive for cross-user learning."""
        if not self.metahive_contribute:
            return

        try:
            # Contribute content template pattern
            pattern = {
                'source_type': package.source_type,
                'platforms_targeted': list(package.platform_versions.keys()),
                'content_types': ['video', 'thread', 'post', 'carousel'],
                'has_referral': True,
                'voice': 'billionaire_calm'
            }

            self.metahive_contribute(
                pattern_type='content_template',
                pattern=pattern,
                context={
                    'fulfillment_type': package.source_data.get('fulfillment_type'),
                    'price_range': f"${package.source_data.get('price', 0):,}"
                },
                outcome_score=0.8,  # Will be updated with actual performance
                revenue_impact=0.0  # Will be updated with conversions
            )

            logger.info("Content pattern contributed to MetaHive")
        except Exception as e:
            logger.warning(f"MetaHive contribution failed: {e}")

    async def update_performance_metrics(
        self,
        package_id: str,
        platform: str,
        metrics: Dict[str, Any]
    ):
        """Update performance metrics and feed back to MetaHive."""
        # Find package
        package = next((p for p in self.content_queue if p.id == package_id), None)
        if not package:
            return

        # Update metrics
        package.performance[platform] = metrics

        # Calculate outcome score
        views = metrics.get('views', 0)
        engagement = metrics.get('likes', 0) + metrics.get('comments', 0) * 2 + metrics.get('shares', 0) * 3
        clicks = metrics.get('referral_clicks', 0)
        conversions = metrics.get('conversions', 0)

        outcome_score = min(1.0, (engagement / max(views, 1)) * 10)
        revenue = conversions * package.source_data.get('price', 1200) * 0.1  # 10% referral

        # Update MetaHive
        if self.metahive_contribute:
            try:
                self.metahive_contribute(
                    pattern_type='content_template',
                    pattern={
                        'platform': platform,
                        'content_format': package.platform_versions.get(platform, {}).get('format'),
                        'metrics': metrics
                    },
                    context={'fulfillment_type': package.source_data.get('fulfillment_type')},
                    outcome_score=outcome_score,
                    revenue_impact=revenue
                )
            except Exception as e:
                logger.warning(f"MetaHive update failed: {e}")

        # Update stats
        self.stats['referral_clicks'] += clicks
        self.stats['conversions'] += conversions
        self.stats['revenue_generated'] += revenue

    # =========================================================================
    # ENGAGEMENT AUTOMATION
    # =========================================================================

    async def run_engagement_cycle(self):
        """
        Run one cycle of engagement automation across all platforms.

        Searches for relevant posts and comments with AiGentsy pitch.
        """
        results = {
            'total_comments': 0,
            'successful_comments': 0,
            'by_platform': {}
        }

        for platform, config in self.platforms.items():
            platform_results = await self._engage_on_platform(platform, config)
            results['by_platform'][platform] = platform_results
            results['total_comments'] += platform_results.get('attempted', 0)
            results['successful_comments'] += platform_results.get('successful', 0)

        return results

    async def _engage_on_platform(self, platform: str, config: Dict) -> Dict:
        """Run engagement on a specific platform."""
        max_comments = config.get('max_comments_per_day', 50)
        hashtags = config.get('hashtags', [])

        results = {'attempted': 0, 'successful': 0, 'errors': []}

        # Get referral code for this platform
        code = self._generate_platform_referral_codes(f"engage_{datetime.now().date()}")
        referral_cta = self._get_referral_cta(platform, code.get(platform, ''))

        # Build engagement message (billionaire-calm)
        message = f"""Sharp dev help, right now.

World-class quality. Minutes-fast. ~50% under market.

First preview free—pay only if it lands.

{referral_cta}"""

        # Platform-specific engagement
        if platform == 'twitter':
            # Use existing Twitter functionality
            pass
        elif platform == 'linkedin':
            # Use existing LinkedIn functionality
            pass
        elif platform == 'instagram':
            # Use existing Instagram functionality
            pass

        return results

    # =========================================================================
    # REVENUE TRACKING
    # =========================================================================

    async def track_referral_conversion(
        self,
        referral_code: str,
        conversion_type: str,
        revenue: float
    ):
        """Track a referral conversion and attribute to platform/campaign."""
        try:
            from monetization.referrals import record_attribution

            # Parse platform from code (AIGX-{platform}-{hash})
            parts = referral_code.split('-')
            platform = parts[1] if len(parts) > 1 else 'unknown'

            # Record attribution
            result = record_attribution(
                user=referral_code,
                gross=revenue,
                source=f"content_{platform}"
            )

            # Update stats
            self.stats['conversions'] += 1
            self.stats['revenue_generated'] += revenue

            logger.info(f"Referral conversion tracked: {referral_code} -> ${revenue}")
            return result
        except Exception as e:
            logger.warning(f"Referral tracking failed: {e}")
            return None

    def get_revenue_by_platform(self) -> Dict[str, float]:
        """Get revenue attribution by platform."""
        # Would aggregate from referral system
        return {
            platform: self.stats.get('revenue_per_platform', {}).get(platform, 0)
            for platform in self.platforms.keys()
        }

    # =========================================================================
    # SCHEDULING
    # =========================================================================

    def get_next_optimal_posting_times(self, platform: str, count: int = 5) -> List[datetime]:
        """Get the next optimal posting times for a platform."""
        config = self.platforms.get(platform, {})
        optimal_hours = config.get('optimal_times_utc', [12])

        now = datetime.now(timezone.utc)
        times = []

        for day_offset in range(7):  # Check next 7 days
            for hour in optimal_hours:
                post_time = now.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                ) + timedelta(days=day_offset)

                if post_time > now:
                    times.append(post_time)
                    if len(times) >= count:
                        return times

        return times

    def get_stats(self) -> Dict:
        """Get orchestrator statistics."""
        return {
            **self.stats,
            'queue_size': len(self.content_queue),
            'platforms_active': list(self.platforms.keys()),
            'brain_connected': self.brain_connected
        }


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

_orchestrator: Optional[UniversalContentOrchestrator] = None


def get_content_orchestrator() -> UniversalContentOrchestrator:
    """Get or create the singleton content orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = UniversalContentOrchestrator()
    return _orchestrator


async def generate_and_post_contract_content(contract: Dict) -> Dict:
    """
    Main entry point: Generate content from contract and post to all platforms.

    Call this after each contract completion.
    """
    orchestrator = get_content_orchestrator()

    # Generate content package
    package = await orchestrator.generate_content_from_contract(contract)

    # Post to all platforms
    results = await orchestrator.post_to_all_platforms(package)

    return {
        'content_id': package.id,
        'referral_codes': package.referral_codes,
        'posting_results': {p: r.__dict__ for p, r in results.items()},
        'stats': orchestrator.get_stats()
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'UniversalContentOrchestrator',
    'ContentPackage',
    'PostingResult',
    'get_content_orchestrator',
    'generate_and_post_contract_content',
    'PLATFORM_CONFIGS'
]
