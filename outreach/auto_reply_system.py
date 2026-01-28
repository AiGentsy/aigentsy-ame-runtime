"""
AUTO-REPLY SYSTEM v1.0
======================

Monitors engagement on our content and auto-replies with personalized referral codes.

Flow:
1. Monitor comments on our posts (keywords: "interested", "how", "AIGENTSY", "price")
2. Generate unique referral code for each person
3. Reply with personalized link + referral bonus info
4. Guide to handshake flow → sale → close

Voice: billionaire-calm (proof-forward, no hype)

When someone engages → they get their own referral code
When they convert → we close the sale
When they refer others → they earn 10%

Platforms: Twitter, Instagram, LinkedIn, TikTok, YouTube, Facebook
"""

import os
import asyncio
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# INTEREST KEYWORDS (triggers auto-reply)
# =============================================================================

INTEREST_KEYWORDS = {
    'high_intent': [
        'aigentsy', 'interested', 'sign me up', 'want this',
        'how do i start', 'lets go', "let's go", 'im in', "i'm in",
        'send link', 'send me', 'dm me', 'price', 'cost',
        'how much', 'take my money', 'need this', 'want to try',
    ],
    'medium_intent': [
        'how does this work', 'tell me more', 'explain',
        'is this real', 'sounds interesting', 'cool', 'amazing',
        'how', 'what is this', 'more info', 'details',
    ],
    'referral_claim': [
        'my code', 'my link', 'referral', 'share link',
        'how do i refer', 'earn money', 'referral bonus',
    ],
}


# =============================================================================
# AUTO-REPLY TEMPLATES (billionaire-calm voice)
# =============================================================================

AUTO_REPLY_TEMPLATES = {
    'high_intent': {
        'twitter': """Here's your personalized link:

{referral_url}

Preview in ~30 min. Pay only if you love it.

When you share that link + someone converts, you earn 10%.

—AiGentsy""",

        'instagram': """Your link is ready 🚀

{referral_url}

Preview in ~30 min. No deposit needed.
Pay only if it lands.

Share your link → earn 10% on referrals.""",

        'linkedin': """Here's your personalized link:

{referral_url}

We'll have a preview ready in ~30 minutes. No payment required upfront—you pay only if you're satisfied with the work.

Additionally, when you share this link and someone converts, you earn 10% of their first project.

Looking forward to delivering for you.

—AiGentsy""",

        'default': """Your personalized link:

{referral_url}

Preview: ~30 min
Payment: Only if you love it
Referral bonus: Earn 10% when you share

—AiGentsy""",
    },

    'medium_intent': {
        'twitter': """Quick version:

1. You describe what you need
2. We ship a preview in ~30 min
3. You pay only if you love it

~50% under market. No risk.

{referral_url}""",

        'instagram': """Here's how it works 👇

1. Tell us what you need
2. Preview in ~30 min
3. Pay only if you love it

~50% under market. No deposit.

Link in bio or DM for your code 🚀""",

        'linkedin': """Here's the overview:

1. Share your project requirements
2. We deliver a preview within ~30 minutes
3. You pay only if you're satisfied

Our pricing runs ~50% below market rate. No risk—if the preview doesn't meet your standards, you owe nothing.

Happy to share more details:
{referral_url}""",

        'default': """How it works:

1. Describe your project
2. Preview in ~30 min
3. Pay only if perfect

~50% under market. No risk.

{referral_url}""",
    },

    'referral_claim': {
        'default': """Your referral link is ready:

{referral_url}

How it works:
• Share this link anywhere
• When someone converts → you earn 10%
• Earnings go to your connected Stripe

The more you share, the more you earn.

—AiGentsy""",
    },
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EngagementComment:
    """A comment/reply on our content"""
    platform: str
    post_id: str
    comment_id: str
    author_handle: str
    author_id: str
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    intent_level: str = "low"  # high, medium, low
    metadata: Dict = field(default_factory=dict)


@dataclass
class AutoReplyResult:
    """Result of an auto-reply attempt"""
    comment: EngagementComment
    success: bool
    referral_code: str = ""
    reply_id: str = ""
    reply_text: str = ""
    error: Optional[str] = None


# =============================================================================
# AUTO-REPLY SYSTEM
# =============================================================================

class AutoReplySystem:
    """
    Monitors comments on our content and auto-replies with personalized codes.

    Complete flow: Comment → Reply → Sale → Referral

    When someone comments "interested":
    1. Generate their unique referral code
    2. Reply with personalized link
    3. They click → enter handshake flow
    4. They convert → contract + escrow
    5. They share → earn 10% on referrals
    """

    def __init__(self):
        self.replied_comments: set = set()  # Prevent duplicate replies
        self.generated_codes: Dict[str, str] = {}  # author_id → referral_code
        self.daily_replies: Dict[str, int] = {
            'twitter': 0, 'instagram': 0, 'linkedin': 0,
            'tiktok': 0, 'youtube': 0, 'facebook': 0
        }
        self.max_replies_per_day = {
            'twitter': 200, 'instagram': 100, 'linkedin': 50,
            'tiktok': 100, 'youtube': 100, 'facebook': 100
        }

        logger.info("🤖 Auto-Reply System initialized")

    def _detect_intent(self, text: str) -> str:
        """Detect intent level from comment text"""
        text_lower = text.lower().strip()

        # Check high intent first
        for keyword in INTEREST_KEYWORDS['high_intent']:
            if keyword in text_lower:
                return 'high_intent'

        # Check referral claim
        for keyword in INTEREST_KEYWORDS['referral_claim']:
            if keyword in text_lower:
                return 'referral_claim'

        # Check medium intent
        for keyword in INTEREST_KEYWORDS['medium_intent']:
            if keyword in text_lower:
                return 'medium_intent'

        return 'low'

    def _generate_referral_code(self, platform: str, author_id: str) -> str:
        """Generate unique referral code for this user"""
        # Check if we already generated one for this user
        cache_key = f"{platform}:{author_id}"
        if cache_key in self.generated_codes:
            return self.generated_codes[cache_key]

        # Generate new code
        prefix_map = {
            'twitter': 'AIGX-TW',
            'instagram': 'AIGX-IG',
            'linkedin': 'AIGX-LI',
            'tiktok': 'AIGX-TT',
            'youtube': 'AIGX-YT',
            'facebook': 'AIGX-FB',
            'github': 'AIGX-GH',
            'reddit': 'AIGX-RD',
        }
        prefix = prefix_map.get(platform, 'AIGX')

        # Create unique suffix from author_id
        hash_suffix = hashlib.md5(f"{author_id}_{platform}".encode()).hexdigest()[:6].upper()
        code = f"{prefix}-{hash_suffix}"

        # Cache it
        self.generated_codes[cache_key] = code

        # Register in referral system
        self._register_referral_code(code, author_id, platform)

        return code

    def _register_referral_code(self, code: str, author_id: str, platform: str):
        """Register referral code in the monetization system"""
        try:
            from monetization.referrals import register_chain
            # Register as a new chain with this user as the referrer
            # The code becomes part of their referral identity
            register_chain(
                user=f"{platform}:{author_id}:{code}",
                chain=[author_id]  # They're the start of a new chain
            )
            logger.debug(f"Registered referral code {code} for {author_id}")
        except Exception as e:
            logger.debug(f"Could not register referral code: {e}")

    def _get_reply_template(self, platform: str, intent_level: str) -> str:
        """Get appropriate reply template"""
        intent_templates = AUTO_REPLY_TEMPLATES.get(intent_level, AUTO_REPLY_TEMPLATES['medium_intent'])
        return intent_templates.get(platform, intent_templates.get('default', ''))

    def _generate_referral_url(self, code: str) -> str:
        """Generate referral URL"""
        return f"https://aigentsy.com/start?ref={code}"

    async def process_comment(self, comment: EngagementComment) -> Optional[AutoReplyResult]:
        """Process a single comment and generate auto-reply if appropriate"""

        # Skip if already replied
        key = f"{comment.platform}:{comment.comment_id}"
        if key in self.replied_comments:
            return None

        # Check daily limit
        if self.daily_replies.get(comment.platform, 0) >= self.max_replies_per_day.get(comment.platform, 100):
            return AutoReplyResult(
                comment=comment, success=False,
                error=f"Daily reply limit reached for {comment.platform}"
            )

        # Detect intent
        intent = self._detect_intent(comment.text)
        if intent == 'low':
            return None  # Don't reply to low-intent comments

        # Generate referral code and URL
        referral_code = self._generate_referral_code(comment.platform, comment.author_id)
        referral_url = self._generate_referral_url(referral_code)

        # Get reply template
        template = self._get_reply_template(comment.platform, intent)
        reply_text = template.format(referral_url=referral_url)

        # Post reply
        result = await self._post_reply(comment, reply_text)

        if result.get('success'):
            self.replied_comments.add(key)
            self.daily_replies[comment.platform] = self.daily_replies.get(comment.platform, 0) + 1

            logger.info(f"✅ Auto-replied to {comment.author_handle} on {comment.platform}")

            # Track in MetaHive
            await self._track_engagement(comment, referral_code, intent)

            return AutoReplyResult(
                comment=comment,
                success=True,
                referral_code=referral_code,
                reply_id=result.get('reply_id', ''),
                reply_text=reply_text
            )
        else:
            return AutoReplyResult(
                comment=comment,
                success=False,
                error=result.get('error', 'Unknown error')
            )

    async def _post_reply(self, comment: EngagementComment, reply_text: str) -> Dict:
        """Post reply to comment based on platform"""
        try:
            if comment.platform == 'twitter':
                return await self._reply_twitter(comment, reply_text)
            elif comment.platform == 'instagram':
                return await self._reply_instagram(comment, reply_text)
            elif comment.platform == 'linkedin':
                return await self._reply_linkedin(comment, reply_text)
            else:
                return {'success': False, 'error': f'Platform {comment.platform} not supported'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _reply_twitter(self, comment: EngagementComment, reply_text: str) -> Dict:
        """Reply to Twitter comment/mention"""
        try:
            from platforms.packs.twitter_v2_api import post_tweet

            # Include @mention
            full_reply = f"@{comment.author_handle} {reply_text}"

            result = await post_tweet(full_reply, reply_to=comment.comment_id)

            if result.get('success'):
                return {
                    'success': True,
                    'reply_id': result.get('tweet_id', '')
                }
            return {'success': False, 'error': result.get('error', 'Tweet failed')}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _reply_instagram(self, comment: EngagementComment, reply_text: str) -> Dict:
        """Reply to Instagram comment"""
        try:
            from platforms.packs.instagram_business_api import reply_to_instagram_comment

            result = await reply_to_instagram_comment(comment.comment_id, reply_text)

            if result.get('success'):
                return {
                    'success': True,
                    'reply_id': result.get('reply_id', '')
                }
            return {'success': False, 'error': result.get('error', 'Reply failed')}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _reply_linkedin(self, comment: EngagementComment, reply_text: str) -> Dict:
        """Reply to LinkedIn comment"""
        try:
            import aiohttp

            access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
            if not access_token:
                return {'success': False, 'error': 'LINKEDIN_ACCESS_TOKEN not configured'}

            # LinkedIn reply to comment
            url = f"https://api.linkedin.com/v2/socialActions/{comment.post_id}/comments/{comment.comment_id}/comments"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }

            person_urn = os.getenv('LINKEDIN_PERSON_URN')

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={
                        'actor': person_urn,
                        'message': {'text': reply_text}
                    },
                    headers=headers
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return {
                            'success': True,
                            'reply_id': data.get('id', '')
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"LinkedIn API error {response.status}: {error_text[:200]}"
                        }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _track_engagement(self, comment: EngagementComment, referral_code: str, intent: str):
        """Track engagement in MetaHive for learning"""
        try:
            from meta_hive_brain import get_metahive_brain
            brain = get_metahive_brain()

            if brain:
                brain.contribute_pattern(
                    pattern_type='auto_reply_engagement',
                    pattern_key=f"{comment.platform}:{intent}",
                    pattern_data={
                        'platform': comment.platform,
                        'intent_level': intent,
                        'referral_code': referral_code,
                        'author_id': comment.author_id,
                        'comment_text': comment.text[:100],
                    },
                    user_id='system',
                    confidence=0.9
                )
        except Exception as e:
            logger.debug(f"Could not track in MetaHive: {e}")

    # =========================================================================
    # MONITORING METHODS
    # =========================================================================

    async def monitor_twitter_mentions(self) -> List[EngagementComment]:
        """Fetch Twitter mentions of our account"""
        comments = []
        try:
            import tweepy

            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            if not bearer_token:
                return comments

            client = tweepy.Client(bearer_token=bearer_token)

            # Get mentions
            mentions = client.get_users_mentions(
                id=os.getenv('TWITTER_USER_ID'),
                max_results=50,
                tweet_fields=['author_id', 'created_at', 'in_reply_to_user_id']
            )

            if mentions.data:
                for tweet in mentions.data:
                    comments.append(EngagementComment(
                        platform='twitter',
                        post_id=str(tweet.in_reply_to_user_id or ''),
                        comment_id=str(tweet.id),
                        author_handle=tweet.author_id,  # Will need user lookup
                        author_id=str(tweet.author_id),
                        text=tweet.text,
                        timestamp=tweet.created_at.isoformat() if tweet.created_at else ''
                    ))

        except Exception as e:
            logger.error(f"Twitter mention monitoring failed: {e}")

        return comments

    async def monitor_instagram_comments(self, post_ids: List[str] = None) -> List[EngagementComment]:
        """Fetch comments on our Instagram posts"""
        comments = []
        try:
            import aiohttp

            access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
            if not access_token:
                return comments

            async with aiohttp.ClientSession() as session:
                for post_id in (post_ids or []):
                    url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
                    params = {
                        'access_token': access_token,
                        'fields': 'id,text,from,timestamp'
                    }

                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            for comment in data.get('data', []):
                                from_data = comment.get('from', {})
                                comments.append(EngagementComment(
                                    platform='instagram',
                                    post_id=post_id,
                                    comment_id=comment.get('id', ''),
                                    author_handle=from_data.get('username', ''),
                                    author_id=from_data.get('id', ''),
                                    text=comment.get('text', ''),
                                    timestamp=comment.get('timestamp', '')
                                ))

        except Exception as e:
            logger.error(f"Instagram comment monitoring failed: {e}")

        return comments

    async def run_monitoring_cycle(self, post_ids: Dict[str, List[str]] = None) -> Dict:
        """Run a full monitoring + auto-reply cycle"""

        all_comments = []
        all_results = []

        # Monitor each platform
        twitter_comments = await self.monitor_twitter_mentions()
        all_comments.extend(twitter_comments)

        if post_ids and post_ids.get('instagram'):
            instagram_comments = await self.monitor_instagram_comments(post_ids['instagram'])
            all_comments.extend(instagram_comments)

        logger.info(f"📬 Found {len(all_comments)} comments to process")

        # Process each comment
        for comment in all_comments:
            result = await self.process_comment(comment)
            if result:
                all_results.append(result)

        return {
            'comments_found': len(all_comments),
            'replies_sent': sum(1 for r in all_results if r.success),
            'failures': sum(1 for r in all_results if not r.success),
            'by_platform': {
                platform: sum(1 for r in all_results if r.comment.platform == platform and r.success)
                for platform in ['twitter', 'instagram', 'linkedin']
            }
        }

    def reset_daily_counts(self):
        """Reset daily reply counts (call at midnight)"""
        for platform in self.daily_replies:
            self.daily_replies[platform] = 0
        logger.info("🔄 Daily auto-reply counts reset")

    def get_stats(self) -> Dict:
        """Get auto-reply statistics"""
        return {
            'total_replied': len(self.replied_comments),
            'codes_generated': len(self.generated_codes),
            'daily_counts': self.daily_replies.copy(),
        }


# =============================================================================
# SINGLETON & EXPORTS
# =============================================================================

_auto_reply_instance: Optional[AutoReplySystem] = None


def get_auto_reply_system() -> AutoReplySystem:
    """Get singleton instance of Auto-Reply System"""
    global _auto_reply_instance
    if _auto_reply_instance is None:
        _auto_reply_instance = AutoReplySystem()
    return _auto_reply_instance


async def run_auto_reply_cycle(post_ids: Dict[str, List[str]] = None) -> Dict:
    """Run a full auto-reply monitoring cycle"""
    system = get_auto_reply_system()
    return await system.run_monitoring_cycle(post_ids)
