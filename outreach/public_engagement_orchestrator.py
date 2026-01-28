"""
PUBLIC ENGAGEMENT ORCHESTRATOR v1.0
===================================

Universal system for PUBLIC outreach across all platforms.

STRATEGY: Public comments/replies > DMs (DMs are restricted)

Why Public > DM:
- DMs require followers/connections (80% fail rate)
- Public comments ALWAYS work (0% fail rate)
- Public comments = social proof
- Viral potential through visibility

Platforms:
- Twitter: Public replies to hiring tweets
- Instagram: Comments on hiring posts
- LinkedIn: Comments on job/hiring posts
- GitHub: Comments on help-wanted issues
- Reddit: Comments on hiring posts
- TikTok: Comments on tech/hiring content

Rate Limits (safe, anti-ban):
- Twitter: 100 replies/day, 5 min spacing
- Instagram: 50 comments/day, 10 min spacing
- LinkedIn: 30 comments/day, 15 min spacing
- GitHub: 20 comments/day, 30 min spacing
- Reddit: 30 comments/day, 10 min spacing
- TikTok: 50 comments/day, 10 min spacing

Voice: billionaire-calm (proof-forward, no hype)

Referral Integration:
- Every comment includes platform-specific referral code
- AIGX-TW001, AIGX-IG001, AIGX-LI001, AIGX-GH001, AIGX-RD001, AIGX-TT001
- Track: which platform drives conversions?
"""

import os
import asyncio
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class EngagementPlatform(Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    GITHUB = "github"
    REDDIT = "reddit"
    TIKTOK = "tiktok"


@dataclass
class PublicEngagementTarget:
    """Target for public engagement (a post/tweet/issue to comment on)"""
    platform: EngagementPlatform
    post_id: str
    post_url: str
    author_handle: str
    title: str
    body: str = ""
    discovered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    engagement_score: float = 0.0
    project_type: str = "default"
    estimated_value: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class PublicEngagementResult:
    """Result of a public engagement attempt"""
    target: PublicEngagementTarget
    success: bool
    method: str  # "comment", "reply", "issue_comment"
    comment_id: Optional[str] = None
    referral_code: str = ""
    message_sent: str = ""
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =============================================================================
# PLATFORM CONFIGURATIONS
# =============================================================================

PLATFORM_CONFIGS = {
    EngagementPlatform.TWITTER: {
        'max_per_day': 100,
        'min_spacing_seconds': 300,  # 5 min
        'code_prefix': 'AIGX-TW',
        'enabled': True,
        'search_queries': [
            'looking for developer',
            'need a developer',
            'hiring developer',
            'need backend engineer',
            'looking for React',
            'need Python developer',
            'hiring freelancer',
            'need help with code',
            'looking for programmer',
        ],
    },
    EngagementPlatform.INSTAGRAM: {
        'max_per_day': 50,
        'min_spacing_seconds': 600,  # 10 min
        'code_prefix': 'AIGX-IG',
        'enabled': True,
        'hashtags': [
            'hiring', 'needadeveloper', 'lookingfordeveloper',
            'freelancejobs', 'techjobs', 'developerjobs',
            'remotework', 'startuplife', 'techhiring',
        ],
    },
    EngagementPlatform.LINKEDIN: {
        'max_per_day': 30,
        'min_spacing_seconds': 900,  # 15 min
        'code_prefix': 'AIGX-LI',
        'enabled': True,
        'search_queries': [
            "who's hiring",
            'looking for developer',
            'hiring engineer',
            'need a freelancer',
            'contract developer needed',
        ],
    },
    EngagementPlatform.GITHUB: {
        'max_per_day': 20,
        'min_spacing_seconds': 1800,  # 30 min
        'code_prefix': 'AIGX-GH',
        'enabled': True,
        'labels': [
            'help wanted',
            'good first issue',
            'bounty',
            'paid',
            'bug',
        ],
    },
    EngagementPlatform.REDDIT: {
        'max_per_day': 30,
        'min_spacing_seconds': 600,  # 10 min
        'code_prefix': 'AIGX-RD',
        'enabled': True,
        'subreddits': [
            'forhire',
            'hiring',
            'jobbit',
            'remotejs',
            'PythonJobs',
            'reactjobs',
        ],
    },
    EngagementPlatform.TIKTOK: {
        'max_per_day': 50,
        'min_spacing_seconds': 600,  # 10 min
        'code_prefix': 'AIGX-TT',
        'enabled': False,  # Requires Playwright
        'hashtags': [
            'hiring', 'developer', 'tech',
            'freelance', 'coding', 'startup',
        ],
    },
}


# =============================================================================
# COMMENT TEMPLATES (billionaire-calm voice)
# =============================================================================

def get_comment_template(platform: EngagementPlatform, project_type: str = "default") -> str:
    """Get platform-specific comment template"""

    templates = {
        EngagementPlatform.TWITTER: {
            'default': """👋 We do this work.

~50% under market, preview in ~30 min.
Pay only if you love it.

{referral_url}""",
            'react': """👋 Sharp React help, right now.

Preview in ~30 min, ~50% under market.
Pay only if it lands.

{referral_url}""",
            'backend': """👋 Backend help, delivered fast.

API, database, infra—preview in ~30 min.
~50% under market.

{referral_url}""",
            'python': """👋 Python/automation help, right now.

Preview in ~30 min, ~50% under market.
Pay only if it lands.

{referral_url}""",
        },
        EngagementPlatform.INSTAGRAM: {
            'default': """👋 We can help!

Autonomous AI dev. ~50% under market.
Preview first, pay only if you love it.

DM us or link in bio 🚀""",
            'design': """👋 Design help, right now!

Preview in ~30 min. ~50% under market.
DM us or link in bio 🚀""",
        },
        EngagementPlatform.LINKEDIN: {
            'default': """We specialize in rapid AI-powered development.

Typical delivery: ~30 minutes to first preview.
Pricing: ~50% under market rate.
Terms: Pay only if you're satisfied.

Happy to connect and discuss. Free preview available.""",
            'enterprise': """We deliver enterprise-grade solutions with AI acceleration.

First preview: ~30 minutes
Pricing: ~50% under typical agency rates
Risk: None—pay only upon approval

Happy to connect and share case studies.""",
        },
        EngagementPlatform.GITHUB: {
            'default': """We can help with this.

Our team ships fixes/features fast—typical preview in ~30 minutes.
We price ~50% under market. Pay only if the code works.

Free preview available: {referral_url}

— AiGentsy (AI-powered dev team)""",
            'bug': """We've fixed issues like this before.

Preview: ~30 minutes to first patch
Price: ~50% under typical contractor rates
Risk: None—pay only if it passes your tests

{referral_url}""",
        },
        EngagementPlatform.REDDIT: {
            'default': """We do this work. AiGentsy here.

Typical delivery: ~30 min to first preview
Price: ~50% under what you'd pay elsewhere
Terms: Pay only if you're happy

Free preview: {referral_url}

(Not spam—we're actual builders who use AI to ship fast)""",
        },
        EngagementPlatform.TIKTOK: {
            'default': """👋 We got you! AiGentsy here.

~30 min to preview, half the price.
Link in bio or comment 'AIGENTSY' for your code! 🚀""",
        },
    }

    platform_templates = templates.get(platform, templates[EngagementPlatform.TWITTER])
    return platform_templates.get(project_type, platform_templates.get('default', ''))


# =============================================================================
# PUBLIC ENGAGEMENT ORCHESTRATOR
# =============================================================================

class PublicEngagementOrchestrator:
    """
    Main orchestrator for public engagement across all platforms.

    Strategy: PUBLIC comments > DMs (DMs are restricted)

    Flow:
    1. Discover hiring posts across all platforms
    2. Filter for real opportunities
    3. Post public comments with referral codes
    4. Track engagement and conversions
    5. Feed learnings to MetaHive
    """

    def __init__(self):
        self.daily_counts: Dict[str, int] = {}
        self.last_engagement: Dict[str, datetime] = {}
        self.engaged_posts: set = set()  # Prevent duplicate engagement
        self.results: List[PublicEngagementResult] = []

        # Initialize daily counts
        for platform in EngagementPlatform:
            self.daily_counts[platform.value] = 0
            self.last_engagement[platform.value] = datetime.min.replace(tzinfo=timezone.utc)

        logger.info("🎯 Public Engagement Orchestrator initialized")

    def _generate_referral_code(self, platform: EngagementPlatform, post_id: str) -> str:
        """Generate unique referral code for this engagement"""
        config = PLATFORM_CONFIGS.get(platform, {})
        prefix = config.get('code_prefix', 'AIGX')

        # Create unique suffix from post_id
        hash_suffix = hashlib.md5(f"{post_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:6].upper()

        return f"{prefix}-{hash_suffix}"

    def _generate_referral_url(self, referral_code: str) -> str:
        """Generate referral URL"""
        return f"https://aigentsy.com/start?ref={referral_code}"

    def _can_engage(self, platform: EngagementPlatform) -> Tuple[bool, str]:
        """Check if we can engage on this platform (rate limits)"""
        config = PLATFORM_CONFIGS.get(platform, {})

        if not config.get('enabled', False):
            return False, f"{platform.value} is disabled"

        # Check daily limit
        max_per_day = config.get('max_per_day', 50)
        current_count = self.daily_counts.get(platform.value, 0)
        if current_count >= max_per_day:
            return False, f"Daily limit reached ({current_count}/{max_per_day})"

        # Check spacing
        min_spacing = config.get('min_spacing_seconds', 300)
        last_time = self.last_engagement.get(platform.value, datetime.min.replace(tzinfo=timezone.utc))
        elapsed = (datetime.now(timezone.utc) - last_time).total_seconds()
        if elapsed < min_spacing:
            wait_time = int(min_spacing - elapsed)
            return False, f"Must wait {wait_time}s (spacing)"

        return True, "OK"

    def _detect_project_type(self, title: str, body: str = "") -> str:
        """Detect project type from title/body"""
        text = f"{title} {body}".lower()

        if any(kw in text for kw in ['react', 'frontend', 'vue', 'angular', 'next.js', 'nextjs']):
            return 'react'
        elif any(kw in text for kw in ['backend', 'api', 'node', 'express', 'django', 'flask', 'fastapi']):
            return 'backend'
        elif any(kw in text for kw in ['python', 'automation', 'script', 'scraping', 'bot']):
            return 'python'
        elif any(kw in text for kw in ['full stack', 'fullstack', 'full-stack']):
            return 'fullstack'
        elif any(kw in text for kw in ['design', 'ui', 'ux', 'figma', 'logo']):
            return 'design'
        elif any(kw in text for kw in ['bug', 'fix', 'issue', 'error', 'broken']):
            return 'bug'
        elif any(kw in text for kw in ['enterprise', 'b2b', 'saas', 'startup']):
            return 'enterprise'

        return 'default'

    # =========================================================================
    # PLATFORM-SPECIFIC ENGAGEMENT METHODS
    # =========================================================================

    async def engage_twitter(self, target: PublicEngagementTarget) -> PublicEngagementResult:
        """Post public reply to a Twitter hiring tweet"""
        platform = EngagementPlatform.TWITTER

        can_engage, reason = self._can_engage(platform)
        if not can_engage:
            return PublicEngagementResult(
                target=target, success=False, method="twitter_reply",
                error=reason
            )

        try:
            from platforms.packs.twitter_v2_api import post_tweet

            # Generate referral code and message
            referral_code = self._generate_referral_code(platform, target.post_id)
            referral_url = self._generate_referral_url(referral_code)

            template = get_comment_template(platform, target.project_type)
            message = f"@{target.author_handle} " + template.format(referral_url=referral_url)

            # Post public reply
            result = await post_tweet(message, reply_to=target.post_id)

            if result.get('success'):
                self.daily_counts[platform.value] += 1
                self.last_engagement[platform.value] = datetime.now(timezone.utc)
                self.engaged_posts.add(f"twitter:{target.post_id}")

                logger.info(f"✅ Twitter reply sent to @{target.author_handle}")

                # Record outreach
                await self._record_outreach(target, referral_code, "twitter_reply")

                return PublicEngagementResult(
                    target=target, success=True, method="twitter_reply",
                    comment_id=result.get('tweet_id'),
                    referral_code=referral_code,
                    message_sent=message
                )
            else:
                return PublicEngagementResult(
                    target=target, success=False, method="twitter_reply",
                    error=result.get('error', 'Unknown error')
                )

        except Exception as e:
            logger.error(f"Twitter engagement failed: {e}")
            return PublicEngagementResult(
                target=target, success=False, method="twitter_reply",
                error=str(e)
            )

    async def engage_instagram(self, target: PublicEngagementTarget) -> PublicEngagementResult:
        """Post comment on Instagram hiring post"""
        platform = EngagementPlatform.INSTAGRAM

        can_engage, reason = self._can_engage(platform)
        if not can_engage:
            return PublicEngagementResult(
                target=target, success=False, method="instagram_comment",
                error=reason
            )

        try:
            from platforms.packs.instagram_business_api import post_instagram_comment

            referral_code = self._generate_referral_code(platform, target.post_id)

            # Build opportunity dict for existing function
            opportunity = {
                'title': target.title,
                'body': target.body,
                'platform': 'instagram',
            }

            result = await post_instagram_comment(
                post_id=target.post_id,
                opportunity=opportunity,
                client_room_url=self._generate_referral_url(referral_code),
            )

            if result.get('success'):
                self.daily_counts[platform.value] += 1
                self.last_engagement[platform.value] = datetime.now(timezone.utc)
                self.engaged_posts.add(f"instagram:{target.post_id}")

                logger.info(f"✅ Instagram comment posted on {target.post_id}")

                await self._record_outreach(target, referral_code, "instagram_comment")

                return PublicEngagementResult(
                    target=target, success=True, method="instagram_comment",
                    comment_id=result.get('comment_id'),
                    referral_code=referral_code,
                    message_sent=result.get('message', '')
                )
            else:
                return PublicEngagementResult(
                    target=target, success=False, method="instagram_comment",
                    error=result.get('error', 'Unknown error')
                )

        except Exception as e:
            logger.error(f"Instagram engagement failed: {e}")
            return PublicEngagementResult(
                target=target, success=False, method="instagram_comment",
                error=str(e)
            )

    async def engage_linkedin(self, target: PublicEngagementTarget) -> PublicEngagementResult:
        """Post comment on LinkedIn hiring post"""
        platform = EngagementPlatform.LINKEDIN

        can_engage, reason = self._can_engage(platform)
        if not can_engage:
            return PublicEngagementResult(
                target=target, success=False, method="linkedin_comment",
                error=reason
            )

        try:
            from platforms.packs.linkedin_api import post_linkedin_comment

            referral_code = self._generate_referral_code(platform, target.post_id)

            opportunity = {
                'title': target.title,
                'body': target.body,
                'platform': 'linkedin',
            }

            result = await post_linkedin_comment(
                post_urn=target.post_id,
                opportunity=opportunity,
            )

            if result.get('success'):
                self.daily_counts[platform.value] += 1
                self.last_engagement[platform.value] = datetime.now(timezone.utc)
                self.engaged_posts.add(f"linkedin:{target.post_id}")

                logger.info(f"✅ LinkedIn comment posted on {target.post_id}")

                await self._record_outreach(target, referral_code, "linkedin_comment")

                return PublicEngagementResult(
                    target=target, success=True, method="linkedin_comment",
                    comment_id=result.get('comment_id'),
                    referral_code=referral_code,
                    message_sent=result.get('message', '')
                )
            else:
                return PublicEngagementResult(
                    target=target, success=False, method="linkedin_comment",
                    error=result.get('error', 'Unknown error')
                )

        except Exception as e:
            logger.error(f"LinkedIn engagement failed: {e}")
            return PublicEngagementResult(
                target=target, success=False, method="linkedin_comment",
                error=str(e)
            )

    async def engage_github(self, target: PublicEngagementTarget) -> PublicEngagementResult:
        """Post comment on GitHub issue"""
        platform = EngagementPlatform.GITHUB

        can_engage, reason = self._can_engage(platform)
        if not can_engage:
            return PublicEngagementResult(
                target=target, success=False, method="github_comment",
                error=reason
            )

        try:
            referral_code = self._generate_referral_code(platform, target.post_id)
            referral_url = self._generate_referral_url(referral_code)

            # Extract owner/repo/issue_number from URL or metadata
            repo = target.metadata.get('repo', '')
            issue_number = target.metadata.get('issue_number') or target.metadata.get('number')

            if not repo or not issue_number:
                # Try to extract from URL
                import re
                match = re.search(r'github\.com/([^/]+/[^/]+)/issues/(\d+)', target.post_url)
                if match:
                    repo = match.group(1)
                    issue_number = match.group(2)

            if not repo or not issue_number:
                return PublicEngagementResult(
                    target=target, success=False, method="github_comment",
                    error="Could not extract repo/issue from URL"
                )

            template = get_comment_template(platform, target.project_type)
            message = template.format(referral_url=referral_url)

            # Post GitHub issue comment
            result = await self._post_github_comment(repo, issue_number, message)

            if result.get('success'):
                self.daily_counts[platform.value] += 1
                self.last_engagement[platform.value] = datetime.now(timezone.utc)
                self.engaged_posts.add(f"github:{target.post_id}")

                logger.info(f"✅ GitHub comment posted on {repo}#{issue_number}")

                await self._record_outreach(target, referral_code, "github_comment")

                return PublicEngagementResult(
                    target=target, success=True, method="github_comment",
                    comment_id=result.get('comment_id'),
                    referral_code=referral_code,
                    message_sent=message
                )
            else:
                return PublicEngagementResult(
                    target=target, success=False, method="github_comment",
                    error=result.get('error', 'Unknown error')
                )

        except Exception as e:
            logger.error(f"GitHub engagement failed: {e}")
            return PublicEngagementResult(
                target=target, success=False, method="github_comment",
                error=str(e)
            )

    async def engage_reddit(self, target: PublicEngagementTarget) -> PublicEngagementResult:
        """Post comment on Reddit hiring post"""
        platform = EngagementPlatform.REDDIT

        can_engage, reason = self._can_engage(platform)
        if not can_engage:
            return PublicEngagementResult(
                target=target, success=False, method="reddit_comment",
                error=reason
            )

        try:
            referral_code = self._generate_referral_code(platform, target.post_id)
            referral_url = self._generate_referral_url(referral_code)

            template = get_comment_template(platform, target.project_type)
            message = template.format(referral_url=referral_url)

            # Post Reddit comment
            result = await self._post_reddit_comment(target.post_id, message)

            if result.get('success'):
                self.daily_counts[platform.value] += 1
                self.last_engagement[platform.value] = datetime.now(timezone.utc)
                self.engaged_posts.add(f"reddit:{target.post_id}")

                logger.info(f"✅ Reddit comment posted on {target.post_id}")

                await self._record_outreach(target, referral_code, "reddit_comment")

                return PublicEngagementResult(
                    target=target, success=True, method="reddit_comment",
                    comment_id=result.get('comment_id'),
                    referral_code=referral_code,
                    message_sent=message
                )
            else:
                return PublicEngagementResult(
                    target=target, success=False, method="reddit_comment",
                    error=result.get('error', 'Unknown error')
                )

        except Exception as e:
            logger.error(f"Reddit engagement failed: {e}")
            return PublicEngagementResult(
                target=target, success=False, method="reddit_comment",
                error=str(e)
            )

    # =========================================================================
    # PLATFORM API IMPLEMENTATIONS
    # =========================================================================

    async def _post_github_comment(self, repo: str, issue_number: int, message: str) -> Dict:
        """Post comment on GitHub issue using GitHub API"""
        try:
            import aiohttp

            token = os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_ACCESS_TOKEN')
            if not token:
                return {'success': False, 'error': 'GITHUB_TOKEN not configured'}

            url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'AiGentsy-Bot'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json={'body': message},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return {
                            'success': True,
                            'comment_id': str(data.get('id')),
                            'html_url': data.get('html_url')
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"GitHub API error {response.status}: {error_text[:200]}"
                        }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _post_reddit_comment(self, post_id: str, message: str) -> Dict:
        """Post comment on Reddit using Reddit API"""
        try:
            import aiohttp

            # Get Reddit credentials
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            username = os.getenv('REDDIT_USERNAME')
            password = os.getenv('REDDIT_PASSWORD')

            if not all([client_id, client_secret, username, password]):
                return {'success': False, 'error': 'Reddit credentials not configured'}

            async with aiohttp.ClientSession() as session:
                # Get access token
                auth = aiohttp.BasicAuth(client_id, client_secret)
                token_url = 'https://www.reddit.com/api/v1/access_token'
                token_data = {
                    'grant_type': 'password',
                    'username': username,
                    'password': password
                }

                async with session.post(
                    token_url,
                    data=token_data,
                    auth=auth,
                    headers={'User-Agent': 'AiGentsy-Bot/1.0'}
                ) as token_response:
                    if token_response.status != 200:
                        return {'success': False, 'error': 'Failed to get Reddit token'}

                    token_json = await token_response.json()
                    access_token = token_json.get('access_token')

                # Post comment
                comment_url = 'https://oauth.reddit.com/api/comment'
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'User-Agent': 'AiGentsy-Bot/1.0'
                }
                comment_data = {
                    'thing_id': f't3_{post_id}' if not post_id.startswith('t3_') else post_id,
                    'text': message
                }

                async with session.post(
                    comment_url,
                    data=comment_data,
                    headers=headers
                ) as comment_response:
                    if comment_response.status == 200:
                        result = await comment_response.json()
                        # Extract comment ID from response
                        comment_data = result.get('json', {}).get('data', {}).get('things', [{}])[0].get('data', {})
                        return {
                            'success': True,
                            'comment_id': comment_data.get('id', ''),
                            'permalink': comment_data.get('permalink', '')
                        }
                    else:
                        error_text = await comment_response.text()
                        return {
                            'success': False,
                            'error': f"Reddit API error {comment_response.status}: {error_text[:200]}"
                        }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # DISCOVERY & ENGAGEMENT ORCHESTRATION
    # =========================================================================

    async def discover_and_engage(self, platforms: List[EngagementPlatform] = None) -> List[PublicEngagementResult]:
        """
        Main orchestration: discover hiring posts and engage publicly.

        Flow:
        1. Discover hiring posts across platforms
        2. Filter for real opportunities
        3. Post public comments with referral codes
        4. Track results
        """
        if platforms is None:
            platforms = [p for p in EngagementPlatform if PLATFORM_CONFIGS.get(p, {}).get('enabled')]

        all_results = []

        # Discover targets across platforms
        targets = await self._discover_targets(platforms)
        logger.info(f"🔍 Discovered {len(targets)} engagement targets")

        # Engage with each target
        for target in targets:
            # Skip if already engaged
            key = f"{target.platform.value}:{target.post_id}"
            if key in self.engaged_posts:
                continue

            # Check rate limits
            can_engage, reason = self._can_engage(target.platform)
            if not can_engage:
                logger.debug(f"Skipping {key}: {reason}")
                continue

            # Engage based on platform
            result = await self._engage_target(target)
            all_results.append(result)
            self.results.append(result)

            # Respect rate limits
            if result.success:
                config = PLATFORM_CONFIGS.get(target.platform, {})
                await asyncio.sleep(config.get('min_spacing_seconds', 300))

        # Feed learnings to MetaHive
        await self._contribute_to_metahive(all_results)

        return all_results

    async def _discover_targets(self, platforms: List[EngagementPlatform]) -> List[PublicEngagementTarget]:
        """Discover engagement targets from all platforms"""
        targets = []

        try:
            from discovery.multi_source_discovery import MultiSourceDiscovery

            discovery = MultiSourceDiscovery()
            opportunities = await discovery.discover_parallel()

            for opp in opportunities:
                platform_str = opp.get('platform', '').lower()

                # Map to EngagementPlatform
                platform_map = {
                    'twitter': EngagementPlatform.TWITTER,
                    'instagram': EngagementPlatform.INSTAGRAM,
                    'linkedin': EngagementPlatform.LINKEDIN,
                    'github': EngagementPlatform.GITHUB,
                    'reddit': EngagementPlatform.REDDIT,
                    'tiktok': EngagementPlatform.TIKTOK,
                }

                platform = platform_map.get(platform_str)
                if not platform or platform not in platforms:
                    continue

                # Extract post ID
                post_id = opp.get('source_data', {}).get('tweet_id') or \
                         opp.get('source_data', {}).get('post_id') or \
                         opp.get('source_data', {}).get('id') or \
                         opp.get('id', '')

                if not post_id:
                    continue

                target = PublicEngagementTarget(
                    platform=platform,
                    post_id=str(post_id),
                    post_url=opp.get('url', ''),
                    author_handle=opp.get('contact', {}).get('twitter_handle', '') or \
                                 opp.get('contact', {}).get('username', '') or \
                                 opp.get('source_data', {}).get('user', ''),
                    title=opp.get('title', ''),
                    body=opp.get('body', ''),
                    project_type=self._detect_project_type(opp.get('title', ''), opp.get('body', '')),
                    estimated_value=opp.get('estimated_value', 0),
                    metadata=opp.get('source_data', {})
                )

                targets.append(target)

        except Exception as e:
            logger.error(f"Discovery failed: {e}")

        return targets

    async def _engage_target(self, target: PublicEngagementTarget) -> PublicEngagementResult:
        """Engage with a target based on its platform"""
        engage_methods = {
            EngagementPlatform.TWITTER: self.engage_twitter,
            EngagementPlatform.INSTAGRAM: self.engage_instagram,
            EngagementPlatform.LINKEDIN: self.engage_linkedin,
            EngagementPlatform.GITHUB: self.engage_github,
            EngagementPlatform.REDDIT: self.engage_reddit,
        }

        method = engage_methods.get(target.platform)
        if method:
            return await method(target)

        return PublicEngagementResult(
            target=target, success=False, method="unknown",
            error=f"No engagement method for {target.platform.value}"
        )

    async def _record_outreach(self, target: PublicEngagementTarget, referral_code: str, method: str):
        """Record outreach for spam prevention and tracking"""
        try:
            from outreach import get_outreach_tracker
            tracker = get_outreach_tracker()
            if tracker:
                tracker.record_outreach(
                    recipient=target.author_handle,
                    recipient_type=target.platform.value,
                    opportunity_id=target.post_id,
                    opportunity_title=target.title,
                    contract_id=referral_code,
                    message_id=method
                )
        except Exception as e:
            logger.debug(f"Could not record outreach: {e}")

    async def _contribute_to_metahive(self, results: List[PublicEngagementResult]):
        """Contribute engagement learnings to MetaHive"""
        try:
            from meta_hive_brain import get_metahive_brain
            brain = get_metahive_brain()

            if brain:
                for result in results:
                    if result.success:
                        brain.contribute_pattern(
                            pattern_type='public_engagement',
                            pattern_key=f"{result.target.platform.value}:{result.target.project_type}",
                            pattern_data={
                                'platform': result.target.platform.value,
                                'project_type': result.target.project_type,
                                'method': result.method,
                                'success': result.success,
                                'referral_code': result.referral_code,
                            },
                            user_id='system',
                            confidence=0.8
                        )
        except Exception as e:
            logger.debug(f"Could not contribute to MetaHive: {e}")

    def get_stats(self) -> Dict:
        """Get engagement statistics"""
        return {
            'daily_counts': self.daily_counts.copy(),
            'total_engaged': len(self.engaged_posts),
            'results_count': len(self.results),
            'success_rate': sum(1 for r in self.results if r.success) / max(len(self.results), 1),
            'platform_limits': {
                p.value: {
                    'used': self.daily_counts.get(p.value, 0),
                    'max': PLATFORM_CONFIGS.get(p, {}).get('max_per_day', 0),
                    'enabled': PLATFORM_CONFIGS.get(p, {}).get('enabled', False)
                }
                for p in EngagementPlatform
            }
        }

    def reset_daily_counts(self):
        """Reset daily counts (call at midnight)"""
        for platform in EngagementPlatform:
            self.daily_counts[platform.value] = 0
        logger.info("🔄 Daily engagement counts reset")


# =============================================================================
# SINGLETON & EXPORTS
# =============================================================================

_orchestrator_instance: Optional[PublicEngagementOrchestrator] = None


def get_public_engagement_orchestrator() -> PublicEngagementOrchestrator:
    """Get singleton instance of Public Engagement Orchestrator"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = PublicEngagementOrchestrator()
    return _orchestrator_instance


async def run_public_engagement_cycle(platforms: List[str] = None) -> Dict:
    """Run a full public engagement cycle"""
    orchestrator = get_public_engagement_orchestrator()

    platform_list = None
    if platforms:
        platform_list = [EngagementPlatform(p) for p in platforms if p in [e.value for e in EngagementPlatform]]

    results = await orchestrator.discover_and_engage(platform_list)

    return {
        'total_attempts': len(results),
        'successes': sum(1 for r in results if r.success),
        'failures': sum(1 for r in results if not r.success),
        'by_platform': {
            p.value: sum(1 for r in results if r.target.platform == p and r.success)
            for p in EngagementPlatform
        },
        'stats': orchestrator.get_stats()
    }
