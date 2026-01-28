"""
BROWSER AUTOMATION ENGINE v1.0
==============================

Zero-cost public engagement via browser automation.

Why Browser > API:
- $0 vs $100+/month API costs
- No rate limit restrictions
- Uses existing @AiGentsy accounts
- Looks like real human activity
- No ToS violations (just browsing)

Platforms:
- Twitter: Reply to hiring tweets
- Instagram: Comment on hiring posts
- LinkedIn: Comment on job posts
- Reddit: Comment on r/forhire posts
- TikTok: Comment on #hiring videos

Stack:
- Playwright (headless Chrome)
- Session persistence (stay logged in)
- Human-like delays
- Anti-detection measures

Voice: billionaire-calm (proof-forward, no hype)
"""

import os
import asyncio
import logging
import random
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Session storage directory
SESSION_DIR = Path(os.getenv('SESSION_DIR', '/tmp/aigentsy_sessions'))
SESSION_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class BrowserTarget:
    """Target for browser engagement"""
    platform: str
    post_url: str
    author: str
    text: str
    post_id: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class BrowserResult:
    """Result of browser engagement"""
    platform: str
    success: bool
    action: str  # "reply", "comment"
    post_url: str
    message_sent: str = ""
    error: Optional[str] = None
    screenshot_path: Optional[str] = None


# =============================================================================
# COMMENT TEMPLATES (billionaire-calm voice)
# =============================================================================

BROWSER_TEMPLATES = {
    'twitter': {
        'default': [
            "👋 We do this work. ~50% under market, preview in ~30 min. Pay only if you love it. aigentsy.com/start",
            "Sharp dev help, right now. Preview in ~30 min, ~50% under market. No risk. aigentsy.com/start",
            "We can help. First preview in ~30 min, pay only if perfect. aigentsy.com/start",
        ],
        'react': [
            "👋 React help, delivered fast. Preview in ~30 min, ~50% under market. aigentsy.com/start",
            "We ship React work same-day. Preview first, pay only if you love it. aigentsy.com/start",
        ],
        'backend': [
            "👋 Backend help, right now. API, database, infra—preview in ~30 min. aigentsy.com/start",
            "We do backend. Preview in ~30 min, ~50% under market. aigentsy.com/start",
        ],
    },
    'instagram': {
        'default': [
            "👋 We can help! Autonomous AI dev. ~50% under market. DM us or link in bio 🚀",
            "Dev help, right now! Preview in ~30 min. Pay only if you love it ✨",
            "We got you! ~50% under market, preview first. Link in bio 🔥",
        ],
    },
    'linkedin': {
        'default': [
            "We specialize in rapid AI-powered development. Typical delivery: ~30 minutes to first preview. Pricing ~50% under market. Happy to connect.",
            "We can help with this. Preview in ~30 minutes, pay only if satisfied. Feel free to connect for details.",
            "Our team delivers fast—preview in ~30 min, ~50% under market rate. Happy to discuss.",
        ],
    },
    'reddit': {
        'default': [
            "We do this work. AiGentsy here—autonomous AI dev team. Preview in ~30 min, ~50% under market. Pay only if you're happy. aigentsy.com/start",
            "Can help with this. First preview in ~30 min, no deposit needed. aigentsy.com/start (Not spam—we're actual builders)",
        ],
    },
    'tiktok': {
        'default': [
            "👋 We got you! AiGentsy—dev help in ~30 min, half the price. Link in bio! 🚀",
            "Dev help, right now! ~50% less, preview first. Comment AIGENTSY for your code 🔥",
        ],
    },
}


def get_random_template(platform: str, project_type: str = 'default') -> str:
    """Get random template for variety"""
    templates = BROWSER_TEMPLATES.get(platform, {}).get(project_type, [])
    if not templates:
        templates = BROWSER_TEMPLATES.get(platform, {}).get('default', [])
    if not templates:
        templates = BROWSER_TEMPLATES['twitter']['default']
    return random.choice(templates)


def detect_project_type(text: str) -> str:
    """Detect project type from post text"""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ['react', 'frontend', 'next.js', 'vue']):
        return 'react'
    elif any(kw in text_lower for kw in ['backend', 'api', 'node', 'python', 'django']):
        return 'backend'
    return 'default'


# =============================================================================
# BROWSER AUTOMATION ENGINE
# =============================================================================

class BrowserAutomation:
    """
    Browser-based engagement using Playwright.

    Zero API costs, uses existing @AiGentsy accounts.
    """

    def __init__(self):
        self.browser = None
        self.context = None
        self.results: List[BrowserResult] = []
        self.daily_counts = {
            'twitter': 0, 'instagram': 0, 'linkedin': 0,
            'reddit': 0, 'tiktok': 0
        }
        self.max_daily = {
            'twitter': 100, 'instagram': 50, 'linkedin': 30,
            'reddit': 30, 'tiktok': 50
        }

        # Credentials from environment
        self.credentials = {
            'twitter': {
                'username': os.getenv('TWITTER_USERNAME'),
                'password': os.getenv('TWITTER_PASSWORD'),
            },
            'instagram': {
                'username': os.getenv('INSTAGRAM_USERNAME'),
                'password': os.getenv('INSTAGRAM_PASSWORD'),
            },
            'linkedin': {
                'username': os.getenv('LINKEDIN_USERNAME') or os.getenv('LINKEDIN_EMAIL'),
                'password': os.getenv('LINKEDIN_PASSWORD'),
            },
            'reddit': {
                'username': os.getenv('REDDIT_USERNAME'),
                'password': os.getenv('REDDIT_PASSWORD'),
            },
        }

        logger.info("🌐 Browser Automation Engine initialized")

    async def _init_browser(self):
        """Initialize Playwright browser with persistent session"""
        if self.browser:
            return

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()

            # Use persistent context to stay logged in
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                ]
            )

            # Create context with user data dir for session persistence
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
            )

            logger.info("✅ Browser initialized (headless)")

        except Exception as e:
            logger.error(f"Browser init failed: {e}")
            raise

    async def _human_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Add human-like delay"""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)

    async def _type_human(self, page, selector: str, text: str):
        """Type text with human-like speed"""
        await page.click(selector)
        await self._human_delay(200, 500)

        for char in text:
            await page.keyboard.type(char, delay=random.randint(30, 100))

    async def close(self):
        """Close browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()

    # =========================================================================
    # TWITTER AUTOMATION
    # =========================================================================

    async def twitter_login(self, page) -> bool:
        """Login to Twitter if needed"""
        try:
            # Check if already logged in
            await page.goto('https://twitter.com/home', wait_until='networkidle')
            await self._human_delay(1000, 2000)

            # If we see the home timeline, we're logged in
            if await page.query_selector('[data-testid="primaryColumn"]'):
                logger.info("✅ Already logged into Twitter")
                return True

            # Need to login
            creds = self.credentials['twitter']
            if not creds['username'] or not creds['password']:
                logger.error("Twitter credentials not configured")
                return False

            await page.goto('https://twitter.com/login', wait_until='networkidle')
            await self._human_delay(1000, 2000)

            # Enter username
            await self._type_human(page, 'input[autocomplete="username"]', creds['username'])
            await self._human_delay(500, 1000)

            # Click next
            await page.click('text=Next')
            await self._human_delay(1000, 2000)

            # Enter password
            await self._type_human(page, 'input[type="password"]', creds['password'])
            await self._human_delay(500, 1000)

            # Click login
            await page.click('[data-testid="LoginForm_Login_Button"]')
            await self._human_delay(2000, 4000)

            # Verify login
            if await page.query_selector('[data-testid="primaryColumn"]'):
                logger.info("✅ Twitter login successful")
                return True
            else:
                logger.error("Twitter login failed")
                return False

        except Exception as e:
            logger.error(f"Twitter login error: {e}")
            return False

    async def twitter_search_and_reply(self, query: str, max_replies: int = 5) -> List[BrowserResult]:
        """Search Twitter and reply to hiring tweets"""
        results = []

        try:
            await self._init_browser()
            page = await self.context.new_page()

            # Login
            if not await self.twitter_login(page):
                return [BrowserResult(
                    platform='twitter', success=False, action='login',
                    post_url='', error='Login failed'
                )]

            # Search for hiring tweets
            search_url = f'https://twitter.com/search?q={query.replace(" ", "%20")}&f=live'
            await page.goto(search_url, wait_until='networkidle')
            await self._human_delay(2000, 3000)

            # Find tweets
            tweets = await page.query_selector_all('[data-testid="tweet"]')
            logger.info(f"Found {len(tweets)} tweets for '{query}'")

            replied = 0
            for tweet in tweets[:max_replies * 2]:  # Get extra in case some fail
                if replied >= max_replies:
                    break

                if self.daily_counts['twitter'] >= self.max_daily['twitter']:
                    logger.info("Twitter daily limit reached")
                    break

                try:
                    # Get tweet text
                    text_elem = await tweet.query_selector('[data-testid="tweetText"]')
                    tweet_text = await text_elem.inner_text() if text_elem else ""

                    # Get tweet URL
                    time_elem = await tweet.query_selector('time')
                    parent_link = await time_elem.evaluate('el => el.closest("a")?.href') if time_elem else None
                    tweet_url = parent_link or ""

                    # Click reply button
                    reply_btn = await tweet.query_selector('[data-testid="reply"]')
                    if not reply_btn:
                        continue

                    await reply_btn.click()
                    await self._human_delay(1000, 2000)

                    # Get template based on project type
                    project_type = detect_project_type(tweet_text)
                    message = get_random_template('twitter', project_type)

                    # Type reply
                    reply_box = await page.query_selector('[data-testid="tweetTextarea_0"]')
                    if reply_box:
                        await reply_box.click()
                        await self._human_delay(300, 600)
                        await page.keyboard.type(message, delay=random.randint(20, 60))
                        await self._human_delay(500, 1000)

                        # Send reply
                        send_btn = await page.query_selector('[data-testid="tweetButtonInline"]')
                        if send_btn:
                            await send_btn.click()
                            await self._human_delay(2000, 3000)

                            results.append(BrowserResult(
                                platform='twitter',
                                success=True,
                                action='reply',
                                post_url=tweet_url,
                                message_sent=message
                            ))
                            self.daily_counts['twitter'] += 1
                            replied += 1
                            logger.info(f"✅ Twitter reply sent ({replied}/{max_replies})")

                except Exception as e:
                    logger.warning(f"Tweet reply failed: {e}")
                    continue

                # Human delay between replies
                await self._human_delay(3000, 6000)

            await page.close()

        except Exception as e:
            logger.error(f"Twitter automation error: {e}")
            results.append(BrowserResult(
                platform='twitter', success=False, action='search',
                post_url='', error=str(e)
            ))

        return results

    # =========================================================================
    # INSTAGRAM AUTOMATION
    # =========================================================================

    async def instagram_login(self, page) -> bool:
        """Login to Instagram if needed"""
        try:
            await page.goto('https://www.instagram.com/', wait_until='networkidle')
            await self._human_delay(2000, 3000)

            # Check if logged in
            if await page.query_selector('[aria-label="Home"]'):
                logger.info("✅ Already logged into Instagram")
                return True

            creds = self.credentials['instagram']
            if not creds['username'] or not creds['password']:
                logger.error("Instagram credentials not configured")
                return False

            # Enter username
            await self._type_human(page, 'input[name="username"]', creds['username'])
            await self._human_delay(500, 1000)

            # Enter password
            await self._type_human(page, 'input[name="password"]', creds['password'])
            await self._human_delay(500, 1000)

            # Click login
            await page.click('button[type="submit"]')
            await self._human_delay(3000, 5000)

            # Handle "Save Login Info" popup
            try:
                not_now = await page.query_selector('text=Not Now')
                if not_now:
                    await not_now.click()
                    await self._human_delay(1000, 2000)
            except:
                pass

            # Handle notifications popup
            try:
                not_now = await page.query_selector('text=Not Now')
                if not_now:
                    await not_now.click()
            except:
                pass

            if await page.query_selector('[aria-label="Home"]'):
                logger.info("✅ Instagram login successful")
                return True

            return False

        except Exception as e:
            logger.error(f"Instagram login error: {e}")
            return False

    async def instagram_search_and_comment(self, hashtag: str, max_comments: int = 5) -> List[BrowserResult]:
        """Search Instagram hashtag and comment on posts"""
        results = []

        try:
            await self._init_browser()
            page = await self.context.new_page()

            if not await self.instagram_login(page):
                return [BrowserResult(
                    platform='instagram', success=False, action='login',
                    post_url='', error='Login failed'
                )]

            # Go to hashtag page
            hashtag_url = f'https://www.instagram.com/explore/tags/{hashtag}/'
            await page.goto(hashtag_url, wait_until='networkidle')
            await self._human_delay(2000, 3000)

            # Find posts
            posts = await page.query_selector_all('article a[href*="/p/"]')
            logger.info(f"Found {len(posts)} posts for #{hashtag}")

            commented = 0
            for post in posts[:max_comments * 2]:
                if commented >= max_comments:
                    break

                if self.daily_counts['instagram'] >= self.max_daily['instagram']:
                    logger.info("Instagram daily limit reached")
                    break

                try:
                    # Click post
                    await post.click()
                    await self._human_delay(2000, 3000)

                    post_url = page.url

                    # Find comment input
                    comment_input = await page.query_selector('textarea[placeholder*="comment"]')
                    if comment_input:
                        message = get_random_template('instagram')

                        await comment_input.click()
                        await self._human_delay(300, 600)
                        await page.keyboard.type(message, delay=random.randint(30, 80))
                        await self._human_delay(500, 1000)

                        # Post comment
                        post_btn = await page.query_selector('button:has-text("Post")')
                        if post_btn:
                            await post_btn.click()
                            await self._human_delay(2000, 3000)

                            results.append(BrowserResult(
                                platform='instagram',
                                success=True,
                                action='comment',
                                post_url=post_url,
                                message_sent=message
                            ))
                            self.daily_counts['instagram'] += 1
                            commented += 1
                            logger.info(f"✅ Instagram comment posted ({commented}/{max_comments})")

                    # Close modal
                    close_btn = await page.query_selector('[aria-label="Close"]')
                    if close_btn:
                        await close_btn.click()
                        await self._human_delay(1000, 2000)

                except Exception as e:
                    logger.warning(f"Instagram comment failed: {e}")
                    # Try to close any modal
                    try:
                        await page.keyboard.press('Escape')
                    except:
                        pass

                await self._human_delay(5000, 10000)

            await page.close()

        except Exception as e:
            logger.error(f"Instagram automation error: {e}")
            results.append(BrowserResult(
                platform='instagram', success=False, action='search',
                post_url='', error=str(e)
            ))

        return results

    # =========================================================================
    # LINKEDIN AUTOMATION
    # =========================================================================

    async def linkedin_login(self, page) -> bool:
        """Login to LinkedIn if needed"""
        try:
            await page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
            await self._human_delay(2000, 3000)

            # Check if logged in
            if await page.query_selector('[data-control-name="nav.settings"]') or await page.query_selector('.feed-identity-module'):
                logger.info("✅ Already logged into LinkedIn")
                return True

            creds = self.credentials['linkedin']
            if not creds['username'] or not creds['password']:
                logger.error("LinkedIn credentials not configured")
                return False

            await page.goto('https://www.linkedin.com/login', wait_until='networkidle')
            await self._human_delay(1000, 2000)

            # Enter email
            await self._type_human(page, '#username', creds['username'])
            await self._human_delay(500, 1000)

            # Enter password
            await self._type_human(page, '#password', creds['password'])
            await self._human_delay(500, 1000)

            # Click login
            await page.click('button[type="submit"]')
            await self._human_delay(3000, 5000)

            if await page.query_selector('.feed-identity-module') or 'feed' in page.url:
                logger.info("✅ LinkedIn login successful")
                return True

            return False

        except Exception as e:
            logger.error(f"LinkedIn login error: {e}")
            return False

    async def linkedin_search_and_comment(self, query: str, max_comments: int = 5) -> List[BrowserResult]:
        """Search LinkedIn and comment on job posts"""
        results = []

        try:
            await self._init_browser()
            page = await self.context.new_page()

            if not await self.linkedin_login(page):
                return [BrowserResult(
                    platform='linkedin', success=False, action='login',
                    post_url='', error='Login failed'
                )]

            # Search for posts
            search_url = f'https://www.linkedin.com/search/results/content/?keywords={query.replace(" ", "%20")}'
            await page.goto(search_url, wait_until='networkidle')
            await self._human_delay(2000, 3000)

            # Find posts
            posts = await page.query_selector_all('.feed-shared-update-v2')
            logger.info(f"Found {len(posts)} LinkedIn posts for '{query}'")

            commented = 0
            for post in posts[:max_comments * 2]:
                if commented >= max_comments:
                    break

                if self.daily_counts['linkedin'] >= self.max_daily['linkedin']:
                    logger.info("LinkedIn daily limit reached")
                    break

                try:
                    # Click comment button
                    comment_btn = await post.query_selector('button[aria-label*="Comment"]')
                    if comment_btn:
                        await comment_btn.click()
                        await self._human_delay(1000, 2000)

                        # Find comment input
                        comment_input = await page.query_selector('.ql-editor[data-placeholder*="comment"]')
                        if comment_input:
                            message = get_random_template('linkedin')

                            await comment_input.click()
                            await self._human_delay(300, 600)
                            await page.keyboard.type(message, delay=random.randint(30, 80))
                            await self._human_delay(500, 1000)

                            # Post comment
                            post_btn = await page.query_selector('button.comments-comment-box__submit-button')
                            if post_btn:
                                await post_btn.click()
                                await self._human_delay(2000, 3000)

                                results.append(BrowserResult(
                                    platform='linkedin',
                                    success=True,
                                    action='comment',
                                    post_url=page.url,
                                    message_sent=message
                                ))
                                self.daily_counts['linkedin'] += 1
                                commented += 1
                                logger.info(f"✅ LinkedIn comment posted ({commented}/{max_comments})")

                except Exception as e:
                    logger.warning(f"LinkedIn comment failed: {e}")

                await self._human_delay(5000, 10000)

            await page.close()

        except Exception as e:
            logger.error(f"LinkedIn automation error: {e}")
            results.append(BrowserResult(
                platform='linkedin', success=False, action='search',
                post_url='', error=str(e)
            ))

        return results

    # =========================================================================
    # REDDIT AUTOMATION
    # =========================================================================

    async def reddit_login(self, page) -> bool:
        """Login to Reddit if needed"""
        try:
            await page.goto('https://www.reddit.com/', wait_until='networkidle')
            await self._human_delay(2000, 3000)

            # Check if logged in
            if await page.query_selector('[data-testid="user-drawer-button"]'):
                logger.info("✅ Already logged into Reddit")
                return True

            creds = self.credentials['reddit']
            if not creds['username'] or not creds['password']:
                logger.error("Reddit credentials not configured")
                return False

            # Click login
            login_btn = await page.query_selector('a[href*="login"]')
            if login_btn:
                await login_btn.click()
                await self._human_delay(2000, 3000)

            # Enter username
            await self._type_human(page, '#loginUsername', creds['username'])
            await self._human_delay(500, 1000)

            # Enter password
            await self._type_human(page, '#loginPassword', creds['password'])
            await self._human_delay(500, 1000)

            # Click login
            await page.click('button[type="submit"]')
            await self._human_delay(3000, 5000)

            if await page.query_selector('[data-testid="user-drawer-button"]'):
                logger.info("✅ Reddit login successful")
                return True

            return False

        except Exception as e:
            logger.error(f"Reddit login error: {e}")
            return False

    async def reddit_comment_on_subreddit(self, subreddit: str, max_comments: int = 5) -> List[BrowserResult]:
        """Comment on posts in a subreddit"""
        results = []

        try:
            await self._init_browser()
            page = await self.context.new_page()

            if not await self.reddit_login(page):
                return [BrowserResult(
                    platform='reddit', success=False, action='login',
                    post_url='', error='Login failed'
                )]

            # Go to subreddit
            await page.goto(f'https://www.reddit.com/r/{subreddit}/new/', wait_until='networkidle')
            await self._human_delay(2000, 3000)

            # Find posts
            posts = await page.query_selector_all('[data-testid="post-container"]')
            logger.info(f"Found {len(posts)} posts in r/{subreddit}")

            commented = 0
            for post in posts[:max_comments * 2]:
                if commented >= max_comments:
                    break

                if self.daily_counts['reddit'] >= self.max_daily['reddit']:
                    logger.info("Reddit daily limit reached")
                    break

                try:
                    # Click on post
                    await post.click()
                    await self._human_delay(2000, 3000)

                    post_url = page.url

                    # Find comment input
                    comment_box = await page.query_selector('[data-testid="comment-composer-wrapper"] [contenteditable="true"]')
                    if comment_box:
                        message = get_random_template('reddit')

                        await comment_box.click()
                        await self._human_delay(300, 600)
                        await page.keyboard.type(message, delay=random.randint(30, 80))
                        await self._human_delay(500, 1000)

                        # Post comment
                        submit_btn = await page.query_selector('button:has-text("Comment")')
                        if submit_btn:
                            await submit_btn.click()
                            await self._human_delay(2000, 3000)

                            results.append(BrowserResult(
                                platform='reddit',
                                success=True,
                                action='comment',
                                post_url=post_url,
                                message_sent=message
                            ))
                            self.daily_counts['reddit'] += 1
                            commented += 1
                            logger.info(f"✅ Reddit comment posted ({commented}/{max_comments})")

                    # Go back
                    await page.go_back()
                    await self._human_delay(2000, 3000)

                except Exception as e:
                    logger.warning(f"Reddit comment failed: {e}")
                    try:
                        await page.go_back()
                    except:
                        pass

                await self._human_delay(5000, 10000)

            await page.close()

        except Exception as e:
            logger.error(f"Reddit automation error: {e}")
            results.append(BrowserResult(
                platform='reddit', success=False, action='search',
                post_url='', error=str(e)
            ))

        return results

    # =========================================================================
    # MAIN ORCHESTRATION
    # =========================================================================

    async def run_engagement_cycle(
        self,
        platforms: List[str] = None,
        max_per_platform: int = 5
    ) -> Dict[str, Any]:
        """
        Run engagement cycle across platforms.

        Args:
            platforms: List of platforms to engage on
            max_per_platform: Max engagements per platform

        Returns:
            Results summary
        """
        if platforms is None:
            platforms = ['twitter', 'instagram', 'linkedin']

        all_results = []

        for platform in platforms:
            logger.info(f"🌐 Starting {platform} engagement...")

            if platform == 'twitter':
                queries = ['hiring developer', 'need a developer', 'looking for React']
                query = random.choice(queries)
                results = await self.twitter_search_and_reply(query, max_per_platform)
                all_results.extend(results)

            elif platform == 'instagram':
                hashtags = ['hiring', 'needadeveloper', 'techjobs']
                hashtag = random.choice(hashtags)
                results = await self.instagram_search_and_comment(hashtag, max_per_platform)
                all_results.extend(results)

            elif platform == 'linkedin':
                queries = ['hiring developer', "who's hiring"]
                query = random.choice(queries)
                results = await self.linkedin_search_and_comment(query, max_per_platform)
                all_results.extend(results)

            elif platform == 'reddit':
                subreddits = ['forhire', 'hiring']
                subreddit = random.choice(subreddits)
                results = await self.reddit_comment_on_subreddit(subreddit, max_per_platform)
                all_results.extend(results)

        # Close browser
        await self.close()

        # Calculate summary
        summary = {
            'total_attempts': len(all_results),
            'successes': sum(1 for r in all_results if r.success),
            'failures': sum(1 for r in all_results if not r.success),
            'by_platform': {},
            'daily_counts': self.daily_counts.copy(),
        }

        for platform in platforms:
            platform_results = [r for r in all_results if r.platform == platform]
            summary['by_platform'][platform] = {
                'attempts': len(platform_results),
                'successes': sum(1 for r in platform_results if r.success),
                'failures': sum(1 for r in platform_results if not r.success),
            }

        self.results = all_results
        return summary

    def get_stats(self) -> Dict:
        """Get automation statistics"""
        return {
            'daily_counts': self.daily_counts.copy(),
            'max_daily': self.max_daily.copy(),
            'remaining': {
                platform: self.max_daily[platform] - self.daily_counts[platform]
                for platform in self.daily_counts
            },
            'total_today': sum(self.daily_counts.values()),
        }


# =============================================================================
# SINGLETON & EXPORTS
# =============================================================================

_browser_instance: Optional[BrowserAutomation] = None


def get_browser_automation() -> BrowserAutomation:
    """Get singleton instance of Browser Automation"""
    global _browser_instance
    if _browser_instance is None:
        _browser_instance = BrowserAutomation()
    return _browser_instance


async def run_browser_engagement(
    platforms: List[str] = None,
    max_per_platform: int = 5
) -> Dict[str, Any]:
    """Run browser-based engagement cycle"""
    automation = get_browser_automation()
    return await automation.run_engagement_cycle(platforms, max_per_platform)
