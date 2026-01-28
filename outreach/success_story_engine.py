"""
SUCCESS STORY ENGINE v1.0
=========================

Generates and posts success stories after contract completion.

Purpose:
- Brand building through proof
- Inbound lead generation
- Viral content with referrals
- Social proof at scale

Flow:
1. Contract completes → trigger
2. Generate success story content
3. Post to ALL platforms (Twitter, IG, LinkedIn, TikTok, YouTube, Facebook)
4. Include referral code in each
5. Monitor engagement → auto-reply
6. Viral loop: customers share their results

Voice: billionaire-calm (proof-forward, no hype)

Content Types:
- Success Stories (60%) - "Delivered X in Y minutes"
- Educational (20%) - "Why AI beats freelancers"
- Viral/Trending (10%) - Trending formats/audio
- Direct CTA (10%) - "Need a dev? We deliver in 1 hour"
"""

import os
import asyncio
import logging
import hashlib
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# =============================================================================
# SUCCESS STORY TEMPLATES (billionaire-calm voice)
# =============================================================================

SUCCESS_STORY_TEMPLATES = {
    'completed_contract': {
        'twitter': [
            """✅ Just delivered: {project_type}

Time: {delivery_time}
Client paid: ${our_price:,}
Market rate: ${market_rate:,}

Approved on first review.

This is autonomous AI fulfillment.

{referral_cta}""",

            """Another one shipped ✅

{project_type} in {delivery_time}

${our_price:,} vs typical ${market_rate:,}

Pay only if you love it.

{referral_cta}""",

            """Built. Shipped. Approved. ✅

{project_type}
⏱️ {delivery_time}
💰 ${our_price:,} (market: ${market_rate:,})

Want this?

{referral_cta}""",
        ],

        'instagram': [
            """✅ Project completed

{project_type}

⏱️ Delivered in {delivery_time}
💰 ${our_price:,} vs ${market_rate:,} market rate
✅ Approved first try

This is what autonomous AI fulfillment looks like.

Comment 'AIGENTSY' for your personalized link 👇

#AIdev #autonomousAI #techstartup #developer #freelance""",
        ],

        'linkedin': [
            """Project Completed ✅

{project_type}

Delivery: {delivery_time}
Our Price: ${our_price:,}
Market Rate: ${market_rate:,}

Approved on first review.

This is what AI-powered development looks like in 2024. Fast, precise, transparent.

For teams that need world-class output without the world-class timeline or budget.

Interested in seeing what we can do for your next project?
{referral_url}""",
        ],

        'tiktok': [
            """POV: You need a {project_type} done ASAP

Me: *Ships in {delivery_time}*

Price: ${our_price:,}
Market: ${market_rate:,}

Comment 'AIGENTSY' for your code 👇

#AI #developer #tech #coding #freelance""",
        ],
    },

    'educational': {
        'twitter': [
            """5 reasons AI beats traditional freelancers:

1. Speed: Minutes not weeks
2. Cost: ~50% under market
3. Quality: Consistent, no off days
4. Scale: Handle any volume
5. Transparency: Know the price upfront

We built AiGentsy for teams who want #1-5.

{referral_cta}""",

            """The math on AI development:

Traditional freelancer:
• $5,000 budget
• 2-3 week timeline
• 3 revision rounds
• 50/50 success rate

AI-powered (us):
• $2,500 budget
• Same day delivery
• Approved first try
• 95% success rate

{referral_cta}""",

            """How we deliver in 1 hour vs 5 days:

1. AI generates multiple solutions in parallel
2. Human QA selects the best
3. Client reviews preview
4. Iteration in minutes

That's it. No magic—just leverage.

{referral_cta}""",
        ],

        'linkedin': [
            """The Future of Development Is Here

Traditional approach:
→ 2-3 weeks to find a freelancer
→ $5,000+ budget
→ Multiple revision rounds
→ Uncertain outcome

AI-accelerated approach:
→ Preview in 30 minutes
→ 50% cost savings
→ Approved first try
→ Pay only if satisfied

We built AiGentsy for teams who can't afford to wait.

If you're curious about what's possible:
{referral_url}""",
        ],
    },

    'direct_cta': {
        'twitter': [
            """Need a developer?

We deliver in 1 hour.
~50% under market.
Pay only if you love it.

{referral_cta}""",

            """Hiring for a project?

Skip the recruiter fees.
Skip the interviews.
Skip the wait.

Get a preview in 30 min.

{referral_cta}""",

            """${market_rate:,} for {project_type}?

We'd do it for ${our_price:,}.

Same quality. Faster delivery. No risk.

{referral_cta}""",
        ],

        'instagram': [
            """Stop scrolling if you need dev work done 👇

⚡ Preview in 30 min
💰 ~50% under market
🎯 Pay only if you love it

Comment 'AIGENTSY' for your personalized link

#developer #freelance #techstartup #AI""",
        ],
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SuccessStory:
    """A success story to be posted"""
    contract_id: str
    project_type: str
    delivery_time: str
    our_price: float
    market_rate: float
    referral_code: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    posted_to: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class PostResult:
    """Result of posting to a platform"""
    platform: str
    success: bool
    post_id: str = ""
    post_url: str = ""
    error: Optional[str] = None


# =============================================================================
# SUCCESS STORY ENGINE
# =============================================================================

class SuccessStoryEngine:
    """
    Generates and posts success stories after contract completion.

    Complete flow:
    1. Contract completes → trigger this engine
    2. Generate content for all platforms
    3. Post to Twitter, Instagram, LinkedIn, TikTok, YouTube, Facebook
    4. Include referral code for viral loop
    5. Monitor for engagement → auto-reply system
    """

    def __init__(self):
        self.posted_stories: List[SuccessStory] = []
        self.post_results: List[PostResult] = []

        logger.info("📢 Success Story Engine initialized")

    def _generate_referral_code(self, contract_id: str) -> str:
        """Generate referral code for this story"""
        hash_suffix = hashlib.md5(f"story_{contract_id}".encode()).hexdigest()[:6].upper()
        return f"AIGX-ST-{hash_suffix}"

    def _generate_referral_url(self, code: str) -> str:
        """Generate referral URL"""
        return f"https://aigentsy.com/start?ref={code}"

    def _get_referral_cta(self, platform: str, code: str) -> str:
        """Get platform-specific referral CTA"""
        url = self._generate_referral_url(code)

        ctas = {
            'twitter': f"Try it: {url}",
            'instagram': f"Comment 'AIGENTSY' for your link 👇",
            'linkedin': url,
            'tiktok': f"Link in bio → Comment 'AIGENTSY' for your code 🚀",
            'youtube': f"Link in description",
            'facebook': url,
        }

        return ctas.get(platform, url)

    def _format_delivery_time(self, minutes: int) -> str:
        """Format delivery time for display"""
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 120:
            return f"1 hour"
        elif minutes < 1440:
            return f"{minutes // 60} hours"
        else:
            return f"{minutes // 1440} day{'s' if minutes >= 2880 else ''}"

    def _select_template(self, template_type: str, platform: str) -> str:
        """Select a random template for variety"""
        templates = SUCCESS_STORY_TEMPLATES.get(template_type, {}).get(platform, [])
        if not templates:
            # Fallback to twitter templates
            templates = SUCCESS_STORY_TEMPLATES.get(template_type, {}).get('twitter', [])
        return random.choice(templates) if templates else ""

    def generate_story_content(self, story: SuccessStory, platform: str, template_type: str = 'completed_contract') -> str:
        """Generate content for a specific platform"""
        template = self._select_template(template_type, platform)

        if not template:
            return ""

        referral_cta = self._get_referral_cta(platform, story.referral_code)
        referral_url = self._generate_referral_url(story.referral_code)

        return template.format(
            project_type=story.project_type,
            delivery_time=story.delivery_time,
            our_price=story.our_price,
            market_rate=story.market_rate,
            referral_cta=referral_cta,
            referral_url=referral_url,
        )

    # =========================================================================
    # POSTING METHODS
    # =========================================================================

    async def post_to_twitter(self, content: str) -> PostResult:
        """Post success story to Twitter"""
        try:
            from platforms.packs.twitter_v2_api import post_tweet

            result = await post_tweet(content)

            if result.get('success'):
                return PostResult(
                    platform='twitter',
                    success=True,
                    post_id=result.get('tweet_id', ''),
                    post_url=f"https://twitter.com/i/status/{result.get('tweet_id', '')}"
                )
            return PostResult(
                platform='twitter',
                success=False,
                error=result.get('error', 'Unknown error')
            )

        except Exception as e:
            return PostResult(platform='twitter', success=False, error=str(e))

    async def post_to_instagram(self, content: str, image_url: str = None) -> PostResult:
        """Post success story to Instagram"""
        try:
            from platforms.packs.instagram_business_api import post_instagram_content

            if not image_url:
                # Generate image using Stability AI if available
                image_url = await self._generate_success_image()

            if not image_url:
                return PostResult(
                    platform='instagram',
                    success=False,
                    error="Image URL required for Instagram"
                )

            result = await post_instagram_content(image_url, content)

            if result.get('success'):
                return PostResult(
                    platform='instagram',
                    success=True,
                    post_id=result.get('post_id', ''),
                    post_url=f"https://instagram.com/p/{result.get('post_id', '')}"
                )
            return PostResult(
                platform='instagram',
                success=False,
                error=result.get('error', 'Unknown error')
            )

        except Exception as e:
            return PostResult(platform='instagram', success=False, error=str(e))

    async def post_to_linkedin(self, content: str) -> PostResult:
        """Post success story to LinkedIn"""
        try:
            from platforms.packs.linkedin_api import post_linkedin_content

            result = await post_linkedin_content(content)

            if result.get('success'):
                return PostResult(
                    platform='linkedin',
                    success=True,
                    post_id=result.get('post_id', ''),
                    post_url=result.get('post_url', '')
                )
            return PostResult(
                platform='linkedin',
                success=False,
                error=result.get('error', 'Unknown error')
            )

        except Exception as e:
            return PostResult(platform='linkedin', success=False, error=str(e))

    async def _generate_success_image(self) -> Optional[str]:
        """Generate a success story image using Stability AI"""
        try:
            from integration.image_generation import generate_portfolio_image

            result = await generate_portfolio_image(
                project_type="development",
                style="professional"
            )

            if result.get('success'):
                return result.get('image_url')

        except Exception as e:
            logger.debug(f"Could not generate success image: {e}")

        return None

    # =========================================================================
    # MAIN ORCHESTRATION
    # =========================================================================

    async def post_success_story(self, contract: Dict, platforms: List[str] = None) -> Dict:
        """
        Generate and post success story for a completed contract.

        Args:
            contract: Contract data with project info
            platforms: List of platforms to post to (default: all)

        Returns:
            Dict with results from each platform
        """
        if platforms is None:
            platforms = ['twitter', 'instagram', 'linkedin']

        # Extract contract info
        contract_id = contract.get('id', contract.get('contract_id', ''))
        project_type = contract.get('fulfillment_type', 'development').title()
        delivery_minutes = contract.get('delivery_time_minutes', 45)
        our_price = contract.get('our_price', contract.get('price', 1500))
        market_rate = contract.get('market_rate', int(our_price * 1.5))

        # Generate referral code
        referral_code = self._generate_referral_code(contract_id)

        # Create story object
        story = SuccessStory(
            contract_id=contract_id,
            project_type=project_type,
            delivery_time=self._format_delivery_time(delivery_minutes),
            our_price=our_price,
            market_rate=market_rate,
            referral_code=referral_code,
            metadata=contract
        )

        results = {}

        # Post to each platform
        for platform in platforms:
            content = self.generate_story_content(story, platform)
            if not content:
                results[platform] = {'success': False, 'error': 'No template available'}
                continue

            if platform == 'twitter':
                result = await self.post_to_twitter(content)
            elif platform == 'instagram':
                result = await self.post_to_instagram(content)
            elif platform == 'linkedin':
                result = await self.post_to_linkedin(content)
            else:
                result = PostResult(platform=platform, success=False, error='Platform not implemented')

            results[platform] = {
                'success': result.success,
                'post_id': result.post_id,
                'post_url': result.post_url,
                'error': result.error
            }

            self.post_results.append(result)

            if result.success:
                story.posted_to.append(platform)

        self.posted_stories.append(story)

        # Feed to MetaHive
        await self._contribute_to_metahive(story, results)

        return {
            'contract_id': contract_id,
            'referral_code': referral_code,
            'results': results,
            'total_success': sum(1 for r in results.values() if r.get('success'))
        }

    async def post_educational_content(self, platforms: List[str] = None) -> Dict:
        """Post educational content for brand building"""
        if platforms is None:
            platforms = ['twitter', 'linkedin']

        referral_code = self._generate_referral_code(f"edu_{datetime.now().strftime('%Y%m%d')}")

        results = {}

        for platform in platforms:
            template = self._select_template('educational', platform)
            if not template:
                continue

            content = template.format(
                referral_cta=self._get_referral_cta(platform, referral_code),
                referral_url=self._generate_referral_url(referral_code)
            )

            if platform == 'twitter':
                result = await self.post_to_twitter(content)
            elif platform == 'linkedin':
                result = await self.post_to_linkedin(content)
            else:
                continue

            results[platform] = {
                'success': result.success,
                'post_id': result.post_id,
                'error': result.error
            }

        return results

    async def post_direct_cta(self, project_type: str = "development", platforms: List[str] = None) -> Dict:
        """Post direct CTA content"""
        if platforms is None:
            platforms = ['twitter', 'instagram']

        referral_code = self._generate_referral_code(f"cta_{datetime.now().strftime('%Y%m%d%H')}")

        # Estimate pricing
        our_price = random.choice([1477, 1977, 2477, 997])
        market_rate = int(our_price * 1.5)

        results = {}

        for platform in platforms:
            template = self._select_template('direct_cta', platform)
            if not template:
                continue

            content = template.format(
                project_type=project_type,
                our_price=our_price,
                market_rate=market_rate,
                referral_cta=self._get_referral_cta(platform, referral_code),
                referral_url=self._generate_referral_url(referral_code)
            )

            if platform == 'twitter':
                result = await self.post_to_twitter(content)
            elif platform == 'instagram':
                result = await self.post_to_instagram(content)
            else:
                continue

            results[platform] = {
                'success': result.success,
                'post_id': result.post_id,
                'error': result.error
            }

        return results

    async def _contribute_to_metahive(self, story: SuccessStory, results: Dict):
        """Contribute success story to MetaHive for learning"""
        try:
            from meta_hive_brain import get_metahive_brain
            brain = get_metahive_brain()

            if brain:
                brain.contribute_pattern(
                    pattern_type='success_story',
                    pattern_key=f"{story.project_type}",
                    pattern_data={
                        'project_type': story.project_type,
                        'delivery_time': story.delivery_time,
                        'our_price': story.our_price,
                        'market_rate': story.market_rate,
                        'platforms_posted': story.posted_to,
                        'referral_code': story.referral_code,
                    },
                    user_id='system',
                    confidence=0.95
                )
        except Exception as e:
            logger.debug(f"Could not contribute to MetaHive: {e}")

    def get_stats(self) -> Dict:
        """Get engine statistics"""
        return {
            'total_stories': len(self.posted_stories),
            'total_posts': len(self.post_results),
            'success_rate': sum(1 for r in self.post_results if r.success) / max(len(self.post_results), 1),
            'by_platform': {
                p: sum(1 for r in self.post_results if r.platform == p and r.success)
                for p in ['twitter', 'instagram', 'linkedin', 'tiktok']
            }
        }


# =============================================================================
# SINGLETON & EXPORTS
# =============================================================================

_engine_instance: Optional[SuccessStoryEngine] = None


def get_success_story_engine() -> SuccessStoryEngine:
    """Get singleton instance of Success Story Engine"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SuccessStoryEngine()
    return _engine_instance


async def post_contract_success_story(contract: Dict, platforms: List[str] = None) -> Dict:
    """Post success story for a completed contract"""
    engine = get_success_story_engine()
    return await engine.post_success_story(contract, platforms)


async def run_content_campaign(content_type: str = 'educational', platforms: List[str] = None) -> Dict:
    """Run a content campaign (educational, direct_cta)"""
    engine = get_success_story_engine()

    if content_type == 'educational':
        return await engine.post_educational_content(platforms)
    elif content_type == 'direct_cta':
        return await engine.post_direct_cta(platforms=platforms)

    return {'error': 'Invalid content_type'}
