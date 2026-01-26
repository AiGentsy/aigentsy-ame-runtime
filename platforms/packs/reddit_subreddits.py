"""
REDDIT SUBREDDITS: 12 Hiring/Freelance Subreddits

Subreddits:
- forhire (highest priority - direct hiring)
- slavelabour (quick gigs)
- jobs
- startups
- entrepreneur
- sideproject
- programming
- webdev
- freelance
- designjobs
- remotejs
- hireawriter
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from ..pack_interface import PlatformPack, PackPriority, ExtractionContext


# Subreddit configurations
SUBREDDIT_CONFIGS = {
    'forhire': {'priority': 85, 'value': 1000, 'payment_proximity': 0.7},
    'slavelabour': {'priority': 80, 'value': 100, 'payment_proximity': 0.8},
    'jobs': {'priority': 75, 'value': 2000, 'payment_proximity': 0.5},
    'startups': {'priority': 70, 'value': 1500, 'payment_proximity': 0.4},
    'entrepreneur': {'priority': 70, 'value': 1000, 'payment_proximity': 0.3},
    'sideproject': {'priority': 75, 'value': 500, 'payment_proximity': 0.3},
    'programming': {'priority': 65, 'value': 500, 'payment_proximity': 0.2},
    'webdev': {'priority': 70, 'value': 800, 'payment_proximity': 0.3},
    'freelance': {'priority': 80, 'value': 1000, 'payment_proximity': 0.6},
    'designjobs': {'priority': 70, 'value': 800, 'payment_proximity': 0.5},
    'remotejs': {'priority': 75, 'value': 1500, 'payment_proximity': 0.5},
    'hireawriter': {'priority': 70, 'value': 500, 'payment_proximity': 0.6},
}


class RedditSubredditPack(PlatformPack):
    """Base class for Reddit subreddit packs"""

    BASE_URL = "https://www.reddit.com"
    RATE_LIMIT = 0.5
    REQUIRES_AUTH = False
    PRIORITY = PackPriority.API

    # Override in subclass
    SUBREDDIT = "forhire"

    def __init__(self):
        super().__init__()
        config = SUBREDDIT_CONFIGS.get(self.SUBREDDIT, {})
        self.value_estimate = config.get('value', 500)
        self.payment_proximity = config.get('payment_proximity', 0.3)

    async def discover(self, context: ExtractionContext) -> List[Dict]:
        self.stats['extractions'] += 1

        if HTTPX_AVAILABLE:
            opportunities = await self._fetch_via_api()
            if opportunities:
                self.stats['api_successes'] += 1
                return opportunities

        self.stats['failures'] += 1
        return []

    async def _fetch_via_api(self) -> List[Dict]:
        """Fetch posts via Reddit JSON API"""
        opportunities = []

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self.BASE_URL}/r/{self.SUBREDDIT}/new.json?limit=100",
                    headers={'User-Agent': 'AiGentsyBot/1.0'},
                    follow_redirects=True,
                )

                if response.status_code != 200:
                    return []

                data = response.json()
                posts = data.get('data', {}).get('children', [])

                for post_wrapper in posts:
                    post = post_wrapper.get('data', {})
                    if post and not post.get('removed'):
                        opp = self._normalize_post(post)
                        if opp:
                            opportunities.append(opp)

        except Exception as e:
            logger.error(f"[{self.PLATFORM}] API fetch error: {e}")

        return opportunities

    def _normalize_post(self, post: Dict) -> Optional[Dict]:
        """Normalize Reddit post to opportunity"""
        title = post.get('title', '')
        if not title or len(title) < 10:
            return None

        post_id = post.get('id', '')
        permalink = post.get('permalink', '')
        url = f"{self.BASE_URL}{permalink}" if permalink else ''

        # Determine type from title/flair
        flair = (post.get('link_flair_text') or '').lower()
        title_lower = title.lower()

        if '[hiring]' in title_lower or 'hiring' in flair:
            opp_type = 'job'
        elif '[for hire]' in title_lower or 'for hire' in flair:
            opp_type = 'gig'
        else:
            opp_type = 'opportunity'

        return {
            'id': f"{self.PLATFORM}_{post_id}",
            'platform': self.PLATFORM,
            'url': url,
            'canonical_url': url,
            'title': title[:200],
            'body': (post.get('selftext', '') or '')[:1000],
            'type': opp_type,
            'value': self.value_estimate,
            'discovered_at': datetime.now(timezone.utc).isoformat(),
            'enrichment': {
                'payment_proximity': self.payment_proximity,
            },
            'source_data': {
                'reddit_id': post_id,
                'subreddit': self.SUBREDDIT,
                'author': post.get('author'),
                'score': post.get('score', 0),
                'upvote_ratio': post.get('upvote_ratio', 0),
                'num_comments': post.get('num_comments', 0),
                'created_utc': post.get('created_utc'),
                'flair': post.get('link_flair_text'),
            }
        }


# Generate pack classes for each subreddit
class RedditForHirePack(RedditSubredditPack):
    PLATFORM = "reddit_forhire"
    SUBREDDIT = "forhire"


class RedditSlaveLaborPack(RedditSubredditPack):
    PLATFORM = "reddit_slavelabour"
    SUBREDDIT = "slavelabour"


class RedditJobsPack(RedditSubredditPack):
    PLATFORM = "reddit_jobs"
    SUBREDDIT = "jobs"


class RedditStartupsPack(RedditSubredditPack):
    PLATFORM = "reddit_startups"
    SUBREDDIT = "startups"


class RedditEntrepreneurPack(RedditSubredditPack):
    PLATFORM = "reddit_entrepreneur"
    SUBREDDIT = "entrepreneur"


class RedditSideProjectPack(RedditSubredditPack):
    PLATFORM = "reddit_sideproject"
    SUBREDDIT = "SideProject"


class RedditProgrammingPack(RedditSubredditPack):
    PLATFORM = "reddit_programming"
    SUBREDDIT = "programming"


class RedditWebDevPack(RedditSubredditPack):
    PLATFORM = "reddit_webdev"
    SUBREDDIT = "webdev"


class RedditFreelancePack(RedditSubredditPack):
    PLATFORM = "reddit_freelance"
    SUBREDDIT = "freelance"


class RedditDesignJobsPack(RedditSubredditPack):
    PLATFORM = "reddit_designjobs"
    SUBREDDIT = "DesignJobs"


class RedditRemoteJSPack(RedditSubredditPack):
    PLATFORM = "reddit_remotejs"
    SUBREDDIT = "remotejs"


class RedditHireAWriterPack(RedditSubredditPack):
    PLATFORM = "reddit_hireawriter"
    SUBREDDIT = "HireaWriter"


# Export all packs
REDDIT_SUBREDDIT_PACKS = [
    RedditForHirePack(),
    RedditSlaveLaborPack(),
    RedditJobsPack(),
    RedditStartupsPack(),
    RedditEntrepreneurPack(),
    RedditSideProjectPack(),
    RedditProgrammingPack(),
    RedditWebDevPack(),
    RedditFreelancePack(),
    RedditDesignJobsPack(),
    RedditRemoteJSPack(),
    RedditHireAWriterPack(),
]
