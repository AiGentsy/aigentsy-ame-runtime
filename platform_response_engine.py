"""
PLATFORM-NATIVE RESPONSE ENGINE
===============================
Posts helpful comments/replies on platforms BEFORE sending DMs.
Warm-up engagement that builds trust and increases conversion rates.

SUPPORTED PLATFORMS:
- Reddit: Comment on posts in r/forhire, r/freelance, etc.
- Twitter: Reply to tweets
- GitHub: Comment on issues
- HackerNews: Reply to posts
- ProductHunt: Comment on launches
- IndieHackers: Reply to posts

FLOW:
1. Opportunity discovered with platform + post ID
2. Generate helpful, non-salesy comment
3. Post comment on platform
4. Wait 5-10 minutes (configurable)
5. Send DM/email with full pitch
6. Track engagement metrics

PHILOSOPHY:
- Add value FIRST, pitch SECOND
- Comments should be genuinely helpful, not spammy
- Reference the specific problem they mentioned
- Soft CTA only ("happy to help if you need more")
"""

import asyncio
import os
import random
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import httpx


# =============================================================================
# CONFIGURATION
# =============================================================================

class Platform(Enum):
    REDDIT = "reddit"
    TWITTER = "twitter"
    GITHUB = "github"
    HACKERNEWS = "hackernews"
    PRODUCTHUNT = "producthunt"
    INDIEHACKERS = "indiehackers"
    LINKEDIN = "linkedin"


class EngagementStatus(Enum):
    PENDING = "pending"
    COMMENTED = "commented"
    WAITING = "waiting"  # Waiting before DM
    DM_SENT = "dm_sent"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlatformEngagement:
    """Tracks engagement with a single opportunity"""
    engagement_id: str
    opportunity_id: str
    platform: Platform
    
    # Post details
    post_id: str
    post_url: str
    post_title: str
    author_username: str
    
    # Our response
    comment_text: Optional[str] = None
    comment_id: Optional[str] = None
    comment_url: Optional[str] = None
    commented_at: Optional[str] = None
    
    # DM follow-up
    dm_scheduled_at: Optional[str] = None
    dm_sent_at: Optional[str] = None
    
    # Status
    status: EngagementStatus = EngagementStatus.PENDING
    error: Optional[str] = None
    
    # Metrics
    comment_upvotes: int = 0
    author_replied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'engagement_id': self.engagement_id,
            'opportunity_id': self.opportunity_id,
            'platform': self.platform.value,
            'post_id': self.post_id,
            'post_url': self.post_url,
            'post_title': self.post_title,
            'author_username': self.author_username,
            'comment_text': self.comment_text,
            'comment_id': self.comment_id,
            'comment_url': self.comment_url,
            'commented_at': self.commented_at,
            'dm_scheduled_at': self.dm_scheduled_at,
            'dm_sent_at': self.dm_sent_at,
            'status': self.status.value,
            'error': self.error,
            'comment_upvotes': self.comment_upvotes,
            'author_replied': self.author_replied
        }


# =============================================================================
# COMMENT TEMPLATES
# =============================================================================

class CommentGenerator:
    """
    Generates helpful, non-spammy comments for each platform.
    Comments should add value and NOT be overtly salesy.
    """
    
    def __init__(self):
        # Category-specific helpful tips to include
        self.helpful_tips = {
            'development': [
                "A few things to consider: make sure to scope out the full requirements upfront - it saves a lot of back-and-forth later.",
                "Pro tip: break this down into milestones with clear deliverables. Makes it easier to track progress and catch issues early.",
                "This sounds like a solid project. Consider getting a technical spec document before starting - it'll save you headaches.",
            ],
            'design': [
                "Nice project! Make sure to get brand guidelines and any existing assets upfront - consistency is key.",
                "Tip: ask for examples of designs they like. Visual references make alignment so much easier.",
                "Good scope. Consider asking about file formats they need - some clients have specific requirements.",
            ],
            'content': [
                "Solid brief! Pro tip: clarify the target audience and tone early. Content that resonates needs that context.",
                "Nice project. Make sure to get SEO keywords if this is for web - can make a big difference.",
                "Consider asking about their content calendar - helps with timing and topic alignment.",
            ],
            'automation': [
                "Interesting use case! Make sure to map out all the edge cases upfront - automation breaks on exceptions.",
                "Good project. Ask about their current tools/stack - integration points matter a lot here.",
                "Pro tip: start with a simple MVP flow before adding complexity. Easier to debug and iterate.",
            ],
            'marketing': [
                "Nice campaign! Make sure to align on KPIs upfront - different metrics need different approaches.",
                "Good scope. Ask about their existing audience data - targeting is everything.",
                "Consider asking about past campaigns - learning from what worked (and didn't) is valuable.",
            ],
            'default': [
                "Solid project! Make sure to get all requirements documented upfront - saves time later.",
                "Nice scope. Consider breaking this into phases with clear milestones.",
                "Good brief! Clear communication on timeline expectations will help a lot here.",
            ]
        }
        
        # Soft CTAs (not pushy)
        self.soft_ctas = [
            "Happy to share more thoughts if helpful!",
            "Let me know if you want to chat through any of this.",
            "Feel free to reach out if you have questions.",
            "I've worked on similar projects - happy to help if needed.",
            "DM me if you want some more specific guidance.",
        ]
    
    def generate_comment(
        self, 
        platform: Platform, 
        post_title: str, 
        post_description: str,
        category: str = "default"
    ) -> str:
        """Generate a helpful comment for the platform"""
        
        # Get category-specific tip
        tips = self.helpful_tips.get(category, self.helpful_tips['default'])
        tip = random.choice(tips)
        
        # Get soft CTA
        cta = random.choice(self.soft_ctas)
        
        # Platform-specific formatting
        if platform == Platform.REDDIT:
            return self._format_reddit_comment(post_title, tip, cta)
        elif platform == Platform.TWITTER:
            return self._format_twitter_reply(post_title, tip, cta)
        elif platform == Platform.GITHUB:
            return self._format_github_comment(post_title, tip, cta)
        elif platform == Platform.LINKEDIN:
            return self._format_linkedin_comment(post_title, tip, cta)
        elif platform == Platform.HACKERNEWS:
            return self._format_hn_comment(post_title, tip, cta)
        else:
            return self._format_generic_comment(tip, cta)
    
    def _format_reddit_comment(self, title: str, tip: str, cta: str) -> str:
        """Reddit comment format"""
        return f"""{tip}

{cta}"""
    
    def _format_twitter_reply(self, title: str, tip: str, cta: str) -> str:
        """Twitter reply format (280 char limit)"""
        # Keep it short for Twitter
        short_tip = tip[:200] if len(tip) > 200 else tip
        return f"{short_tip} 🧵"
    
    def _format_github_comment(self, title: str, tip: str, cta: str) -> str:
        """GitHub issue comment format"""
        return f"""Hey! Saw this issue and wanted to share some thoughts:

{tip}

{cta}"""
    
    def _format_linkedin_comment(self, title: str, tip: str, cta: str) -> str:
        """LinkedIn comment format (professional tone)"""
        return f"""Great post! {tip}

{cta} 💼"""
    
    def _format_hn_comment(self, title: str, tip: str, cta: str) -> str:
        """HackerNews comment format (plain text, no markdown)"""
        return f"""{tip}

{cta}"""
    
    def _format_generic_comment(self, tip: str, cta: str) -> str:
        """Generic comment format"""
        return f"""{tip}

{cta}"""


# =============================================================================
# PLATFORM API CLIENTS
# =============================================================================

class PlatformResponseEngine:
    """
    Posts comments/replies on platforms and manages warm-up engagement.
    """
    
    def __init__(self):
        # API credentials - matching Render env vars
        
        # Reddit
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.reddit_username = os.getenv("REDDIT_USERNAME", "")
        self.reddit_password = os.getenv("REDDIT_PASSWORD", "")
        
        # Twitter - matching your Render env
        self.twitter_api_key = os.getenv("TWITTER_API_KEY", "")
        self.twitter_api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.twitter_access_secret = os.getenv("TWITTER_ACCESS_SECRET", "")
        
        # GitHub
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        
        # LinkedIn - matching your Render env
        self.linkedin_access_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.linkedin_client_id = os.getenv("LINKEDIN_CLIENT_ID", "")
        self.linkedin_client_secret = os.getenv("LINKEDIN_CLIENT_SECRET", "")
        
        # Instagram - matching your Render env
        self.instagram_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.instagram_business_id = os.getenv("INSTAGRAM_BUSINESS_ID", "")
        
        # HackerNews (no API, placeholder)
        self.hn_username = os.getenv("HN_USERNAME", "")
        self.hn_password = os.getenv("HN_PASSWORD", "")
        
        # Comment generator
        self.comment_generator = CommentGenerator()
        
        # Engagement tracking
        self.engagements: Dict[str, PlatformEngagement] = {}
        self.pending_dm_queue: List[str] = []  # engagement_ids waiting for DM
        
        # Rate limiting
        self.daily_comments: Dict[str, int] = {}  # platform -> count
        self.daily_limit = 20  # comments per platform per day
        
        # Timing
        self.dm_delay_minutes = (5, 15)  # Wait 5-15 min before DM
        
        # Stats
        self.stats = {
            'comments_posted': 0,
            'comments_failed': 0,
            'dms_sent_after_comment': 0,
            'author_replies': 0,
            'conversions_from_comments': 0
        }
    
    # =========================================================================
    # MAIN ENGAGEMENT FLOW
    # =========================================================================
    
    async def engage_with_opportunity(
        self,
        opportunity: Dict[str, Any],
        send_dm_after: bool = True
    ) -> Optional[PlatformEngagement]:
        """
        Full engagement flow:
        1. Generate helpful comment
        2. Post on platform
        3. Schedule DM follow-up
        """
        # Extract details
        platform_str = opportunity.get('source', '').lower()
        post_id = opportunity.get('platform_id', '')
        post_url = opportunity.get('url', '')
        post_title = opportunity.get('title', '')
        post_description = opportunity.get('description', '')
        author = opportunity.get('author', '')
        opportunity_id = opportunity.get('id', '')
        
        # Map to platform enum
        platform_map = {
            'reddit': Platform.REDDIT,
            'twitter': Platform.TWITTER,
            'github': Platform.GITHUB,
            'github_bounties': Platform.GITHUB,
            'hackernews': Platform.HACKERNEWS,
            'producthunt': Platform.PRODUCTHUNT,
            'indiehackers': Platform.INDIEHACKERS,
            'linkedin': Platform.LINKEDIN,
            'linkedin_jobs': Platform.LINKEDIN,
        }
        
        platform = platform_map.get(platform_str)
        if not platform:
            print(f"⚠️ Unsupported platform for comments: {platform_str}")
            return None
        
        # Check rate limits
        if not self._check_rate_limit(platform):
            print(f"⚠️ Rate limit reached for {platform.value}")
            return None
        
        # Create engagement record
        engagement_id = f"eng_{hashlib.md5(f'{opportunity_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        
        engagement = PlatformEngagement(
            engagement_id=engagement_id,
            opportunity_id=opportunity_id,
            platform=platform,
            post_id=post_id,
            post_url=post_url,
            post_title=post_title,
            author_username=author
        )
        
        # Detect category from content
        category = self._detect_category(post_title, post_description)
        
        # Generate comment
        comment_text = self.comment_generator.generate_comment(
            platform=platform,
            post_title=post_title,
            post_description=post_description,
            category=category
        )
        
        engagement.comment_text = comment_text
        
        # Post the comment
        success = await self._post_comment(engagement)
        
        if success:
            engagement.status = EngagementStatus.COMMENTED
            engagement.commented_at = datetime.now(timezone.utc).isoformat()
            self.stats['comments_posted'] += 1
            self._increment_rate_limit(platform)
            
            # Schedule DM follow-up
            if send_dm_after and author:
                delay_minutes = random.randint(*self.dm_delay_minutes)
                dm_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
                engagement.dm_scheduled_at = dm_time.isoformat()
                engagement.status = EngagementStatus.WAITING
                self.pending_dm_queue.append(engagement_id)
                print(f"📝 Comment posted, DM scheduled in {delay_minutes} min")
        else:
            engagement.status = EngagementStatus.FAILED
            self.stats['comments_failed'] += 1
        
        # Store engagement
        self.engagements[engagement_id] = engagement
        
        return engagement
    
    def _detect_category(self, title: str, description: str) -> str:
        """Detect the category of the opportunity"""
        text = f"{title} {description}".lower()
        
        if any(kw in text for kw in ['code', 'developer', 'api', 'bug', 'app', 'software', 'programming']):
            return 'development'
        elif any(kw in text for kw in ['design', 'logo', 'ui', 'ux', 'graphic', 'brand']):
            return 'design'
        elif any(kw in text for kw in ['content', 'blog', 'article', 'copywriting', 'writing', 'seo']):
            return 'content'
        elif any(kw in text for kw in ['automat', 'workflow', 'integration', 'zapier', 'bot']):
            return 'automation'
        elif any(kw in text for kw in ['marketing', 'ads', 'campaign', 'social media', 'growth']):
            return 'marketing'
        else:
            return 'default'
    
    def _check_rate_limit(self, platform: Platform) -> bool:
        """Check if we're under rate limit for platform"""
        today = datetime.now().strftime('%Y-%m-%d')
        key = f"{platform.value}_{today}"
        count = self.daily_comments.get(key, 0)
        return count < self.daily_limit
    
    def _increment_rate_limit(self, platform: Platform):
        """Increment rate limit counter"""
        today = datetime.now().strftime('%Y-%m-%d')
        key = f"{platform.value}_{today}"
        self.daily_comments[key] = self.daily_comments.get(key, 0) + 1
    
    # =========================================================================
    # PLATFORM-SPECIFIC POSTING
    # =========================================================================
    
    async def _post_comment(self, engagement: PlatformEngagement) -> bool:
        """Route to platform-specific posting method"""
        try:
            if engagement.platform == Platform.REDDIT:
                return await self._post_reddit_comment(engagement)
            elif engagement.platform == Platform.TWITTER:
                return await self._post_twitter_reply(engagement)
            elif engagement.platform == Platform.GITHUB:
                return await self._post_github_comment(engagement)
            elif engagement.platform == Platform.LINKEDIN:
                return await self._post_linkedin_comment(engagement)
            elif engagement.platform == Platform.HACKERNEWS:
                return await self._post_hn_comment(engagement)
            else:
                print(f"⚠️ Posting not implemented for {engagement.platform.value}")
                return False
        except Exception as e:
            engagement.error = str(e)
            print(f"⚠️ Comment posting error: {e}")
            return False
    
    async def _post_reddit_comment(self, engagement: PlatformEngagement) -> bool:
        """Post a comment on Reddit"""
        if not all([self.reddit_client_id, self.reddit_client_secret, 
                    self.reddit_username, self.reddit_password]):
            engagement.error = "Reddit credentials not configured"
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                # Get access token
                auth = (self.reddit_client_id, self.reddit_client_secret)
                token_response = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=auth,
                    data={
                        "grant_type": "password",
                        "username": self.reddit_username,
                        "password": self.reddit_password
                    },
                    headers={"User-Agent": "AiGentsy/1.0"},
                    timeout=30
                )
                
                if token_response.status_code != 200:
                    engagement.error = f"Reddit auth failed: {token_response.status_code}"
                    return False
                
                access_token = token_response.json().get('access_token')
                
                # Post comment
                comment_response = await client.post(
                    "https://oauth.reddit.com/api/comment",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "User-Agent": "AiGentsy/1.0"
                    },
                    data={
                        "thing_id": f"t3_{engagement.post_id}",  # t3_ prefix for posts
                        "text": engagement.comment_text
                    },
                    timeout=30
                )
                
                if comment_response.status_code == 200:
                    result = comment_response.json()
                    # Extract comment ID from response
                    if 'json' in result and 'data' in result['json']:
                        things = result['json']['data'].get('things', [])
                        if things:
                            engagement.comment_id = things[0].get('data', {}).get('id', '')
                            engagement.comment_url = f"https://reddit.com{things[0].get('data', {}).get('permalink', '')}"
                    return True
                else:
                    engagement.error = f"Reddit comment failed: {comment_response.status_code}"
                    return False
                    
        except Exception as e:
            engagement.error = str(e)
            return False
    
    async def _post_twitter_reply(self, engagement: PlatformEngagement) -> bool:
        """Post a reply on Twitter"""
        if not all([self.twitter_api_key, self.twitter_api_secret,
                    self.twitter_access_token, self.twitter_access_secret]):
            engagement.error = "Twitter credentials not configured"
            return False
        
        try:
            # Twitter API v2 requires OAuth 1.0a for posting
            # This is a simplified version - production would use tweepy or similar
            async with httpx.AsyncClient() as client:
                # For Twitter API v2, you'd typically use a library like tweepy
                # This is a placeholder for the API call structure
                
                response = await client.post(
                    "https://api.twitter.com/2/tweets",
                    headers={
                        "Authorization": f"Bearer {self.twitter_bearer}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": engagement.comment_text,
                        "reply": {
                            "in_reply_to_tweet_id": engagement.post_id
                        }
                    },
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    engagement.comment_id = result.get('data', {}).get('id', '')
                    return True
                else:
                    engagement.error = f"Twitter reply failed: {response.status_code}"
                    return False
                    
        except Exception as e:
            engagement.error = str(e)
            return False
    
    async def _post_github_comment(self, engagement: PlatformEngagement) -> bool:
        """Post a comment on a GitHub issue"""
        if not self.github_token:
            engagement.error = "GitHub token not configured"
            return False
        
        try:
            # Extract owner/repo from URL
            # URL format: https://github.com/owner/repo/issues/123
            url_parts = engagement.post_url.split('/')
            if 'github.com' in engagement.post_url and len(url_parts) >= 7:
                owner = url_parts[3]
                repo = url_parts[4]
                issue_number = url_parts[6]
            else:
                engagement.error = "Could not parse GitHub URL"
                return False
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
                    headers={
                        "Authorization": f"token {self.github_token}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    json={"body": engagement.comment_text},
                    timeout=30
                )
                
                if response.status_code == 201:
                    result = response.json()
                    engagement.comment_id = str(result.get('id', ''))
                    engagement.comment_url = result.get('html_url', '')
                    return True
                else:
                    engagement.error = f"GitHub comment failed: {response.status_code}"
                    return False
                    
        except Exception as e:
            engagement.error = str(e)
            return False
    
    async def _post_linkedin_comment(self, engagement: PlatformEngagement) -> bool:
        """Post a comment on a LinkedIn post"""
        if not self.linkedin_access_token:
            engagement.error = "LinkedIn access token not configured"
            return False
        
        try:
            # LinkedIn API v2 for comments
            # The post URN is needed - extract from URL or use stored ID
            post_urn = engagement.post_id
            
            # If post_id isn't a URN, try to construct it
            if not post_urn.startswith('urn:li:'):
                # LinkedIn post URLs: linkedin.com/posts/username_activity-id
                # or linkedin.com/feed/update/urn:li:activity:id
                if 'activity' in engagement.post_url:
                    # Extract activity ID
                    import re
                    match = re.search(r'activity[:\-](\d+)', engagement.post_url)
                    if match:
                        post_urn = f"urn:li:activity:{match.group(1)}"
                    else:
                        engagement.error = "Could not extract LinkedIn activity ID from URL"
                        return False
                else:
                    engagement.error = "LinkedIn post URN format not recognized"
                    return False
            
            async with httpx.AsyncClient() as client:
                # LinkedIn Comments API
                response = await client.post(
                    "https://api.linkedin.com/v2/socialActions/{}/comments".format(post_urn.replace(':', '%3A')),
                    headers={
                        "Authorization": f"Bearer {self.linkedin_access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0"
                    },
                    json={
                        "actor": f"urn:li:person:{self.linkedin_client_id}",  # Your LinkedIn ID
                        "message": {
                            "text": engagement.comment_text
                        }
                    },
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    engagement.comment_id = result.get('id', '')
                    return True
                else:
                    engagement.error = f"LinkedIn comment failed: {response.status_code} - {response.text[:200]}"
                    return False
                    
        except Exception as e:
            engagement.error = str(e)
            return False
    
    async def _post_hn_comment(self, engagement: PlatformEngagement) -> bool:
        """Post a comment on HackerNews"""
        # HN doesn't have a public API for posting
        # Would need to use web scraping/automation
        engagement.error = "HN commenting requires browser automation (not implemented)"
        return False
    
    # =========================================================================
    # DM FOLLOW-UP MANAGEMENT
    # =========================================================================
    
    async def process_pending_dms(self) -> Dict[str, int]:
        """Process engagements that are ready for DM follow-up"""
        now = datetime.now(timezone.utc)
        sent = 0
        pending = 0
        
        for engagement_id in list(self.pending_dm_queue):
            engagement = self.engagements.get(engagement_id)
            if not engagement:
                self.pending_dm_queue.remove(engagement_id)
                continue
            
            if engagement.status != EngagementStatus.WAITING:
                self.pending_dm_queue.remove(engagement_id)
                continue
            
            # Check if it's time to send DM
            if engagement.dm_scheduled_at:
                scheduled = datetime.fromisoformat(engagement.dm_scheduled_at.replace('Z', '+00:00'))
                if now >= scheduled:
                    # Time to send DM - return engagement for outreach engine
                    engagement.status = EngagementStatus.DM_SENT
                    engagement.dm_sent_at = now.isoformat()
                    self.pending_dm_queue.remove(engagement_id)
                    self.stats['dms_sent_after_comment'] += 1
                    sent += 1
                else:
                    pending += 1
        
        return {'sent': sent, 'pending': pending}
    
    def get_ready_for_dm(self) -> List[PlatformEngagement]:
        """Get engagements that are ready for DM (delay has passed)"""
        now = datetime.now(timezone.utc)
        ready = []
        
        for engagement_id in self.pending_dm_queue:
            engagement = self.engagements.get(engagement_id)
            if not engagement or engagement.status != EngagementStatus.WAITING:
                continue
            
            if engagement.dm_scheduled_at:
                scheduled = datetime.fromisoformat(engagement.dm_scheduled_at.replace('Z', '+00:00'))
                if now >= scheduled:
                    ready.append(engagement)
        
        return ready
    
    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================
    
    async def engage_batch(
        self,
        opportunities: List[Dict[str, Any]],
        max_comments: int = 10
    ) -> Dict[str, Any]:
        """Engage with multiple opportunities"""
        results = {
            'processed': 0,
            'commented': 0,
            'failed': 0,
            'skipped': 0,
            'engagements': []
        }
        
        for opp in opportunities[:max_comments]:
            # Skip if no author (can't DM later)
            if not opp.get('author'):
                results['skipped'] += 1
                continue
            
            # Skip unsupported platforms
            platform = opp.get('source', '').lower()
            if platform not in ['reddit', 'twitter', 'github', 'github_bounties', 'linkedin', 'linkedin_jobs']:
                results['skipped'] += 1
                continue
            
            engagement = await self.engage_with_opportunity(opp)
            results['processed'] += 1
            
            if engagement:
                if engagement.status in [EngagementStatus.COMMENTED, EngagementStatus.WAITING]:
                    results['commented'] += 1
                else:
                    results['failed'] += 1
                results['engagements'].append(engagement.to_dict())
            else:
                results['failed'] += 1
            
            # Small delay between comments
            await asyncio.sleep(2)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engagement stats"""
        return {
            **self.stats,
            'pending_dms': len(self.pending_dm_queue),
            'total_engagements': len(self.engagements),
            'daily_comments': dict(self.daily_comments)
        }


# =============================================================================
# SINGLETON
# =============================================================================

_platform_response_engine = None

def get_platform_response_engine() -> PlatformResponseEngine:
    global _platform_response_engine
    if _platform_response_engine is None:
        _platform_response_engine = PlatformResponseEngine()
    return _platform_response_engine
