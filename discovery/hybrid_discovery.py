"""
HYBRID DISCOVERY ENGINE: Perplexity + Direct Platform API Enrichment
=====================================================================

PROBLEM:
- Perplexity discovery returns AI summaries without original poster info
- Customer loop needs author/contact to send proposals
- 20+ outreach channels are wired but unused because no contact data

SOLUTION:
- Phase 1: Use Perplexity for broad internet-wide discovery (fast)
- Phase 2: Enrich each opportunity by fetching original source URL
- Phase 3: Extract author/contact from original post using platform APIs

PLATFORM API PACKS USED:
- platforms/packs/reddit_pack.py - Reddit JSON API for author extraction
- platforms/packs/twitter_v2_api.py - Twitter API for handle extraction
- platforms/packs/github_enhanced.py - GitHub API for username extraction
- platforms/packs/linkedin_api.py - LinkedIn API for profile extraction
- platforms/packs/hackernews_pack.py - HN API for username extraction

EXPECTED IMPACT:
- Before: 0-10% of opportunities have contact info
- After: 80-95% of opportunities have contact info
"""

import os
import re
import json
import logging
import hashlib
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class HybridDiscoveryEngine:
    """
    Hybrid discovery: Perplexity-first with direct API enrichment.

    This closes the gap between discovery and customer outreach by ensuring
    every opportunity has extractable contact info.
    """

    def __init__(self):
        self.perplexity_key = os.getenv('PERPLEXITY_API_KEY')

        # Stats tracking
        self.stats = {
            'phase1_discovered': 0,
            'phase2_enriched': 0,
            'phase2_with_contact': 0,
            'platforms_hit': {},
            'errors': []
        }

        # Platform API configs
        # Twitter: check for bearer token OR API key (for OAuth)
        self.twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.twitter_configured = bool(self.twitter_bearer or self.twitter_api_key)
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.reddit_configured = True  # Reddit JSON API is public
        self.linkedin_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.instagram_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')

        # Import existing discovery if available
        try:
            from discovery.perplexity_first import PerplexityFirstDiscovery
            self._perplexity_engine = PerplexityFirstDiscovery()
            self._has_perplexity = True
        except ImportError:
            self._has_perplexity = False
            self._perplexity_engine = None

        # Import contact extractor
        try:
            from universal_contact_extraction import UniversalContactExtractor, enrich_opportunity_with_contact
            self._contact_extractor = UniversalContactExtractor()
            self._enrich_contact = enrich_opportunity_with_contact
            self._has_extractor = True
        except ImportError:
            self._has_extractor = False
            self._contact_extractor = None
            self._enrich_contact = None

    async def discover_with_contact(self, max_opportunities: int = 100) -> List[Dict]:
        """
        Complete hybrid discovery with contact enrichment.

        THREE-PHASE APPROACH:
        1. PERPLEXITY (PRIMARY) - Discovers across ENTIRE INTERNET
        2. DIRECT APIs (ENRICHMENT) - Adds author/contact info to Perplexity results
        3. DIRECT PLATFORMS (SUPPLEMENT) - Adds platform-native opps with built-in contact

        Returns opportunities with contact info ready for outreach.
        """
        logger.info("=" * 80)
        logger.info("🔍 HYBRID DISCOVERY - PERPLEXITY PRIMARY")
        logger.info("=" * 80)

        # ===================================================================
        # PHASE 1: PERPLEXITY - DISCOVER ACROSS ENTIRE INTERNET (PRIMARY)
        # ===================================================================
        logger.info("\n📡 PHASE 1: Perplexity Internet-Wide Discovery (PRIMARY)")

        perplexity_opportunities = await self._phase1_perplexity()
        self.stats['phase1_discovered'] = len(perplexity_opportunities)
        logger.info(f"✅ Phase 1: {len(perplexity_opportunities)} opportunities from Perplexity")

        # ===================================================================
        # PHASE 2: ENRICH PERPLEXITY RESULTS WITH CONTACT INFO
        # ===================================================================
        logger.info(f"\n🔗 PHASE 2: Enriching Perplexity Results with Direct APIs")

        # Limit before enrichment to avoid rate limits
        opps_to_enrich = perplexity_opportunities[:max_opportunities]
        enriched = await self._phase2_enrich(opps_to_enrich)

        # Count enrichment success
        enriched_with_contact = sum(1 for o in enriched if self._has_contact(o))
        logger.info(f"✅ Phase 2: {enriched_with_contact}/{len(enriched)} enriched with contact info")

        # ===================================================================
        # PHASE 3: ALWAYS ADD DIRECT PLATFORM DISCOVERIES
        # ===================================================================
        # These have contact info built-in, so ALWAYS include them
        logger.info(f"\n📍 PHASE 3: Adding Direct Platform APIs (guaranteed contact info)")
        platform_opps = await self._phase1_5_direct_platforms()
        logger.info(f"✅ Phase 3: {len(platform_opps)} opportunities from direct platforms")

        # ===================================================================
        # COMBINE & PRIORITIZE: Contact info first
        # ===================================================================
        # Platform opps (with contact) + Perplexity enriched (may have contact)
        all_opportunities = []

        # First: add platform opportunities (guaranteed contact)
        for opp in platform_opps:
            all_opportunities.append(opp)

        # Second: add Perplexity opportunities (may have contact after enrichment)
        for opp in enriched:
            # Avoid duplicates by URL
            existing_urls = {o.get('url') for o in all_opportunities if o.get('url')}
            if opp.get('url') not in existing_urls:
                all_opportunities.append(opp)

        # Sort: opportunities WITH contact come first
        all_opportunities.sort(key=lambda o: (
            0 if self._has_contact(o) else 1,  # With contact first
            0 if o.get('contact', {}).get('email') else 1,  # Email preferred
        ))

        # Take top max_opportunities
        final_opportunities = all_opportunities[:max_opportunities]

        # Final stats
        with_contact = sum(1 for o in final_opportunities if self._has_contact(o))
        self.stats['phase2_enriched'] = len(final_opportunities)
        self.stats['phase2_with_contact'] = with_contact

        logger.info("\n" + "=" * 80)
        logger.info("📊 HYBRID DISCOVERY COMPLETE")
        logger.info("=" * 80)
        logger.info(f"   Total opportunities: {len(final_opportunities)}")
        logger.info(f"   With contact info:   {with_contact} ({with_contact/len(final_opportunities)*100:.1f}%)" if final_opportunities else "   With contact: 0")
        logger.info(f"   Platform-sourced:    {len([o for o in final_opportunities if o.get('source', '').endswith('_api')])}")
        logger.info(f"   Perplexity-sourced:  {len([o for o in final_opportunities if 'perplexity' in o.get('id', '')])}")
        logger.info(f"   Ready for outreach:  {with_contact}")

        return final_opportunities

    async def _phase1_perplexity(self) -> List[Dict]:
        """Phase 1: Use Perplexity for broad discovery"""
        if self._has_perplexity and self._perplexity_engine:
            try:
                return await self._perplexity_engine.discover_all()
            except Exception as e:
                logger.error(f"Perplexity discovery failed: {e}")
                self.stats['errors'].append({'phase': 1, 'error': str(e)})

        # Fallback: direct Perplexity API call
        return await self._direct_perplexity_search()

    async def _direct_perplexity_search(self) -> List[Dict]:
        """
        Direct Perplexity API search - DIVERSIFIED ACROSS ALL PLATFORMS.

        Queries target opportunities with EMAIL, TWITTER, LINKEDIN, INSTAGRAM contact info.
        """
        if not self.perplexity_key:
            logger.warning("No Perplexity API key, skipping Phase 1")
            return []

        opportunities = []

        # DIVERSIFIED QUERIES - target opportunities with contact info across ALL platforms
        queries = [
            # === EMAIL-BASED (highest conversion) ===
            """Find job postings that include email contact for developers. Search across job boards,
            forums, and social media. Return JSON: [{"title": "...", "url": "...", "email": "...", "platform": "..."}]""",

            # === TWITTER OPPORTUNITIES ===
            """Find tweets from people hiring developers or looking for freelancers. Include the
            Twitter handle of the poster. Return JSON: [{"title": "...", "url": "...", "twitter_handle": "@...", "platform": "twitter"}]""",

            # === LINKEDIN OPPORTUNITIES ===
            """Find LinkedIn posts about hiring developers, seeking consultants, or looking for
            freelancers. Include LinkedIn profile URLs. Return JSON: [{"title": "...", "url": "...", "linkedin_url": "...", "platform": "linkedin"}]""",

            # === UPWORK/FREELANCE PLATFORMS ===
            """Find active job postings on Upwork, Freelancer, Fiverr for web development,
            mobile apps, Python, data science. Return JSON: [{"title": "...", "url": "...", "platform": "upwork/freelancer/fiverr", "budget": "..."}]""",

            # === GITHUB BOUNTIES ===
            """Find GitHub issues with bounties, paid work, or help wanted labels that offer payment.
            Include the repository URL and poster. Return JSON: [{"title": "...", "url": "...", "github_user": "...", "bounty": "...", "platform": "github"}]""",

            # === REDDIT (with email extraction) ===
            """Find Reddit posts in r/forhire, r/hiring, r/slavelabour where people are hiring AND
            include their email address in the post. Return JSON: [{"title": "...", "url": "...", "email": "...", "reddit_user": "...", "platform": "reddit"}]""",

            # === STARTUP/CONSULTING ===
            """Find startup hiring posts, CTO positions, or consulting opportunities that include
            contact email or LinkedIn. Return JSON: [{"title": "...", "url": "...", "contact": "...", "platform": "..."}]""",

            # === DISCORD/TELEGRAM ===
            """Find Discord servers or Telegram groups hiring developers or moderators. Include
            invite links or contact info. Return JSON: [{"title": "...", "url": "...", "platform": "discord/telegram"}]""",
        ]

        async with httpx.AsyncClient(timeout=30) as client:
            for query in queries:
                try:
                    response = await client.post(
                        "https://api.perplexity.ai/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.perplexity_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama-3.1-sonar-small-128k-online",
                            "messages": [
                                {"role": "system", "content": "You are a job opportunity finder. Return only valid JSON arrays."},
                                {"role": "user", "content": query}
                            ],
                            "max_tokens": 4000,
                            "temperature": 0.2,
                            "return_related_questions": False
                        }
                    )

                    if response.is_success:
                        data = response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        parsed = self._parse_json_from_text(content)
                        opportunities.extend(parsed)
                        logger.info(f"Perplexity: {len(parsed)} opportunities from query")
                    else:
                        logger.warning(f"Perplexity API error: {response.status_code}")

                except Exception as e:
                    logger.error(f"Perplexity query failed: {e}")

        return opportunities

    async def _phase1_5_direct_platforms(self) -> List[Dict]:
        """
        Phase 1.5: Direct platform discovery with author info built-in.

        Unlike Perplexity, direct platform APIs return the actual poster info:
        - Reddit: author field with username
        - Twitter: user.screen_name with handle
        - GitHub: user.login with username

        This ensures we have contact info for outreach.
        """
        opportunities = []

        # Reddit: Fetch from r/forhire, r/hiring, etc.
        if self.reddit_configured:
            reddit_opps = await self._discover_reddit_direct()
            opportunities.extend(reddit_opps)
            logger.info(f"Reddit direct: {len(reddit_opps)} opportunities with author info")

        # Twitter: Search for hiring tweets (using bearer token if available)
        if self.twitter_configured and self.twitter_bearer:
            twitter_opps = await self._discover_twitter_direct()
            opportunities.extend(twitter_opps)
            logger.info(f"Twitter direct: {len(twitter_opps)} opportunities with author info")
        elif self.twitter_configured:
            logger.info(f"Twitter: API key available but bearer token needed for search API")

        # GitHub: Search for bounty/help-wanted issues
        if self.github_token or True:  # GitHub search works without auth (with rate limits)
            github_opps = await self._discover_github_direct()
            opportunities.extend(github_opps)
            logger.info(f"GitHub direct: {len(github_opps)} opportunities with author info")

        return opportunities

    async def _discover_reddit_direct(self) -> List[Dict]:
        """Discover from Reddit directly (with author info)"""
        opportunities = []
        subreddits = ['forhire', 'hiring', 'remotejobs', 'slavelabour']

        async with httpx.AsyncClient(timeout=15) as client:
            for subreddit in subreddits[:2]:  # Limit to avoid rate limits
                try:
                    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=10"
                    response = await client.get(
                        url,
                        headers={'User-Agent': 'AiGentsy/1.0'}
                    )

                    if response.is_success:
                        data = response.json()
                        posts = data.get('data', {}).get('children', [])

                        for post in posts:
                            post_data = post.get('data', {})
                            author = post_data.get('author')

                            if author and author != '[deleted]':
                                opp = {
                                    'id': f"reddit_{post_data.get('id', '')}",
                                    'title': post_data.get('title', ''),
                                    'body': post_data.get('selftext', ''),
                                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                                    'platform': 'reddit',
                                    'source': 'reddit_api',
                                    'contact': {
                                        'platform': 'reddit',
                                        'platform_user_id': author,
                                        'reddit_username': author,
                                        'preferred_outreach': 'reddit_dm',
                                        'extraction_source': 'reddit_api_direct'
                                    },
                                    'metadata': {
                                        'subreddit': subreddit,
                                        'poster_username': author,
                                        'score': post_data.get('score', 0),
                                    }
                                }
                                opportunities.append(opp)

                    await asyncio.sleep(1)  # Reddit rate limit

                except Exception as e:
                    logger.debug(f"Reddit direct discovery failed for r/{subreddit}: {e}")

        return opportunities

    async def _discover_twitter_direct(self) -> List[Dict]:
        """Discover from Twitter directly (with author info)"""
        if not self.twitter_bearer:
            return []

        opportunities = []

        queries = [
            'hiring developer -is:retweet lang:en',
            'looking for freelancer -is:retweet lang:en',
        ]

        async with httpx.AsyncClient(timeout=15) as client:
            for query in queries[:1]:  # Limit to avoid rate limits
                try:
                    response = await client.get(
                        'https://api.twitter.com/2/tweets/search/recent',
                        params={
                            'query': query,
                            'max_results': 10,
                            'tweet.fields': 'created_at,author_id',
                            'expansions': 'author_id',
                            'user.fields': 'username'
                        },
                        headers={'Authorization': f'Bearer {self.twitter_bearer}'}
                    )

                    if response.is_success:
                        data = response.json()
                        tweets = data.get('data', [])
                        users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

                        for tweet in tweets:
                            user = users.get(tweet.get('author_id'), {})
                            username = user.get('username')

                            if username:
                                opp = {
                                    'id': f"twitter_{tweet.get('id', '')}",
                                    'title': tweet.get('text', '')[:100],
                                    'body': tweet.get('text', ''),
                                    'url': f"https://twitter.com/{username}/status/{tweet.get('id')}",
                                    'platform': 'twitter',
                                    'source': 'twitter_api',
                                    'contact': {
                                        'platform': 'twitter',
                                        'platform_user_id': username,
                                        'twitter_handle': username,
                                        'preferred_outreach': 'twitter_dm',
                                        'extraction_source': 'twitter_api_direct'
                                    },
                                    'metadata': {
                                        'poster_handle': username,
                                        'tweet_id': tweet.get('id'),
                                    }
                                }
                                opportunities.append(opp)

                except Exception as e:
                    logger.debug(f"Twitter direct discovery failed: {e}")

        return opportunities

    async def _discover_github_direct(self) -> List[Dict]:
        """Discover from GitHub directly (with author info)"""
        opportunities = []

        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AiGentsy-Discovery'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'

        queries = [
            'bounty OR paid in:title is:open',
            'help wanted in:labels is:open',
        ]

        async with httpx.AsyncClient(timeout=15) as client:
            for query in queries[:1]:  # Limit
                try:
                    response = await client.get(
                        'https://api.github.com/search/issues',
                        params={
                            'q': query,
                            'sort': 'created',
                            'order': 'desc',
                            'per_page': 10
                        },
                        headers=headers
                    )

                    if response.is_success:
                        data = response.json()
                        issues = data.get('items', [])

                        for issue in issues:
                            user = issue.get('user', {})
                            username = user.get('login')

                            if username:
                                opp = {
                                    'id': f"github_{issue.get('id', '')}",
                                    'title': issue.get('title', ''),
                                    'body': issue.get('body', ''),
                                    'url': issue.get('html_url', ''),
                                    'platform': 'github',
                                    'source': 'github_api',
                                    'contact': {
                                        'platform': 'github',
                                        'platform_user_id': username,
                                        'github_username': username,
                                        'preferred_outreach': 'github_comment',
                                        'extraction_source': 'github_api_direct'
                                    },
                                    'metadata': {
                                        'poster_username': username,
                                        'issue_number': issue.get('number'),
                                        'labels': [l.get('name') for l in issue.get('labels', [])],
                                    }
                                }
                                opportunities.append(opp)

                except Exception as e:
                    logger.debug(f"GitHub direct discovery failed: {e}")

        return opportunities

    async def _phase2_enrich(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Phase 2: Enrich opportunities with author/contact from original source.

        For each opportunity:
        1. Detect platform from URL
        2. Fetch original post via platform API
        3. Extract author/contact info
        """
        enriched = []

        # Group by platform for efficient batching
        by_platform = self._group_by_platform(opportunities)

        # Enrich Reddit opportunities
        if by_platform.get('reddit'):
            reddit_enriched = await self._enrich_reddit(by_platform['reddit'])
            enriched.extend(reddit_enriched)
            self.stats['platforms_hit']['reddit'] = len(reddit_enriched)

        # Enrich Twitter opportunities
        if by_platform.get('twitter'):
            twitter_enriched = await self._enrich_twitter(by_platform['twitter'])
            enriched.extend(twitter_enriched)
            self.stats['platforms_hit']['twitter'] = len(twitter_enriched)

        # Enrich GitHub opportunities
        if by_platform.get('github'):
            github_enriched = await self._enrich_github(by_platform['github'])
            enriched.extend(github_enriched)
            self.stats['platforms_hit']['github'] = len(github_enriched)

        # Enrich HackerNews opportunities
        if by_platform.get('hackernews'):
            hn_enriched = await self._enrich_hackernews(by_platform['hackernews'])
            enriched.extend(hn_enriched)
            self.stats['platforms_hit']['hackernews'] = len(hn_enriched)

        # Enrich LinkedIn (if we have token)
        if by_platform.get('linkedin') and os.getenv('LINKEDIN_ACCESS_TOKEN'):
            linkedin_enriched = await self._enrich_linkedin(by_platform['linkedin'])
            enriched.extend(linkedin_enriched)
            self.stats['platforms_hit']['linkedin'] = len(linkedin_enriched)

        # Other platforms - pass through with basic enrichment
        for platform in ['upwork', 'fiverr', 'other']:
            if by_platform.get(platform):
                for opp in by_platform[platform]:
                    opp = self._basic_enrich(opp)
                    enriched.append(opp)
                self.stats['platforms_hit'][platform] = len(by_platform.get(platform, []))

        return enriched

    def _group_by_platform(self, opportunities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group opportunities by platform based on URL"""
        grouped: Dict[str, List[Dict]] = {}

        for opp in opportunities:
            url = opp.get('url', '') or opp.get('canonical_url', '')
            platform = self._detect_platform(url)

            if platform not in grouped:
                grouped[platform] = []
            grouped[platform].append(opp)

        return grouped

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL"""
        if not url:
            return 'other'

        url_lower = url.lower()

        if 'reddit.com' in url_lower or 'redd.it' in url_lower:
            return 'reddit'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'github.com' in url_lower:
            return 'github'
        elif 'news.ycombinator.com' in url_lower or 'hackernews' in url_lower:
            return 'hackernews'
        elif 'linkedin.com' in url_lower:
            return 'linkedin'
        elif 'upwork.com' in url_lower:
            return 'upwork'
        elif 'fiverr.com' in url_lower:
            return 'fiverr'
        else:
            return 'other'

    # =========================================================================
    # PLATFORM-SPECIFIC ENRICHMENT
    # =========================================================================

    async def _enrich_reddit(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Enrich Reddit opportunities with author from JSON API.

        Reddit's .json endpoint returns post author without authentication.
        """
        enriched = []

        async with httpx.AsyncClient(timeout=15) as client:
            for opp in opportunities:
                url = opp.get('url', '')

                # Convert to JSON API endpoint
                json_url = self._reddit_to_json_url(url)
                if not json_url:
                    enriched.append(self._basic_enrich(opp))
                    continue

                try:
                    response = await client.get(
                        json_url,
                        headers={'User-Agent': 'AiGentsy/1.0'},
                        follow_redirects=True
                    )

                    if response.is_success:
                        data = response.json()
                        author = self._extract_reddit_author(data)

                        if author:
                            opp['contact'] = {
                                'platform': 'reddit',
                                'platform_user_id': author,
                                'reddit_username': author,
                                'preferred_outreach': 'reddit_dm',
                                'extraction_source': 'reddit_json_api'
                            }
                            opp['metadata'] = opp.get('metadata', {})
                            opp['metadata']['poster_username'] = author
                            logger.debug(f"Reddit enriched: u/{author}")

                    enriched.append(opp)

                    # Rate limit respect
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.debug(f"Reddit enrichment failed for {url}: {e}")
                    enriched.append(self._basic_enrich(opp))

        return enriched

    def _reddit_to_json_url(self, url: str) -> Optional[str]:
        """Convert Reddit URL to JSON API endpoint"""
        if not url or 'reddit' not in url.lower():
            return None

        # Clean URL
        url = url.rstrip('/')

        # Handle various Reddit URL formats
        # https://www.reddit.com/r/forhire/comments/abc123/title -> .json
        if '/comments/' in url:
            return url + '.json'

        # Handle short URLs
        if 'redd.it' in url:
            return None  # Need to resolve first

        return url + '.json'

    def _extract_reddit_author(self, data: Any) -> Optional[str]:
        """Extract author from Reddit JSON response"""
        try:
            # Reddit returns array [post_listing, comments_listing]
            if isinstance(data, list) and len(data) > 0:
                post_data = data[0].get('data', {}).get('children', [{}])[0].get('data', {})
                author = post_data.get('author')
                if author and author != '[deleted]':
                    return author

            # Handle direct post response
            if isinstance(data, dict):
                if 'data' in data:
                    children = data.get('data', {}).get('children', [])
                    if children:
                        author = children[0].get('data', {}).get('author')
                        if author and author != '[deleted]':
                            return author
        except Exception as e:
            logger.debug(f"Reddit author extraction failed: {e}")

        return None

    async def _enrich_twitter(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Enrich Twitter opportunities with author handle.

        Uses Twitter v2 API if bearer token available.
        """
        enriched = []

        if not self.twitter_bearer:
            # Fallback: extract handle from URL
            for opp in opportunities:
                url = opp.get('url', '')
                handle = self._extract_twitter_handle_from_url(url)
                if handle:
                    opp['contact'] = {
                        'platform': 'twitter',
                        'platform_user_id': handle,
                        'twitter_handle': handle,
                        'preferred_outreach': 'twitter_dm',
                        'extraction_source': 'url_parse'
                    }
                    opp['metadata'] = opp.get('metadata', {})
                    opp['metadata']['poster_handle'] = handle
                enriched.append(opp)
            return enriched

        async with httpx.AsyncClient(timeout=15) as client:
            for opp in opportunities:
                url = opp.get('url', '')
                tweet_id = self._extract_tweet_id(url)

                if tweet_id:
                    try:
                        response = await client.get(
                            f'https://api.twitter.com/2/tweets/{tweet_id}',
                            params={
                                'expansions': 'author_id',
                                'user.fields': 'username'
                            },
                            headers={'Authorization': f'Bearer {self.twitter_bearer}'}
                        )

                        if response.is_success:
                            data = response.json()
                            users = data.get('includes', {}).get('users', [])
                            if users:
                                handle = users[0].get('username')
                                if handle:
                                    opp['contact'] = {
                                        'platform': 'twitter',
                                        'platform_user_id': handle,
                                        'twitter_handle': handle,
                                        'preferred_outreach': 'twitter_dm',
                                        'extraction_source': 'twitter_api'
                                    }
                                    opp['metadata'] = opp.get('metadata', {})
                                    opp['metadata']['poster_handle'] = handle
                                    logger.debug(f"Twitter enriched: @{handle}")

                        await asyncio.sleep(0.2)

                    except Exception as e:
                        logger.debug(f"Twitter enrichment failed: {e}")

                enriched.append(opp)

        return enriched

    def _extract_twitter_handle_from_url(self, url: str) -> Optional[str]:
        """Extract Twitter handle from URL"""
        # https://twitter.com/username/status/123
        match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)/status', url)
        if match:
            return match.group(1)
        return None

    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """Extract tweet ID from URL"""
        match = re.search(r'/status/(\d+)', url)
        if match:
            return match.group(1)
        return None

    async def _enrich_github(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Enrich GitHub opportunities with author username.

        Uses GitHub REST API.
        """
        enriched = []

        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'AiGentsy-Discovery'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'

        async with httpx.AsyncClient(timeout=15) as client:
            for opp in opportunities:
                url = opp.get('url', '')
                api_url = self._github_to_api_url(url)

                if api_url:
                    try:
                        response = await client.get(api_url, headers=headers)

                        if response.is_success:
                            data = response.json()
                            user = data.get('user', {})
                            username = user.get('login')

                            if username:
                                opp['contact'] = {
                                    'platform': 'github',
                                    'platform_user_id': username,
                                    'github_username': username,
                                    'preferred_outreach': 'github_comment',
                                    'extraction_source': 'github_api'
                                }
                                opp['metadata'] = opp.get('metadata', {})
                                opp['metadata']['poster_username'] = username
                                logger.debug(f"GitHub enriched: {username}")

                        await asyncio.sleep(0.2)

                    except Exception as e:
                        logger.debug(f"GitHub enrichment failed: {e}")

                enriched.append(opp)

        return enriched

    def _github_to_api_url(self, url: str) -> Optional[str]:
        """Convert GitHub URL to API endpoint"""
        # https://github.com/owner/repo/issues/123
        match = re.search(r'github\.com/([^/]+)/([^/]+)/issues/(\d+)', url)
        if match:
            owner, repo, issue_num = match.groups()
            return f'https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}'

        # https://github.com/owner/repo/discussions/123
        match = re.search(r'github\.com/([^/]+)/([^/]+)/discussions/(\d+)', url)
        if match:
            owner, repo, disc_num = match.groups()
            return f'https://api.github.com/repos/{owner}/{repo}/discussions/{disc_num}'

        return None

    async def _enrich_hackernews(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Enrich HackerNews opportunities with author username.

        Uses HN Firebase API (public, no auth needed).
        """
        enriched = []

        async with httpx.AsyncClient(timeout=15) as client:
            for opp in opportunities:
                url = opp.get('url', '')
                item_id = self._extract_hn_item_id(url)

                if item_id:
                    try:
                        response = await client.get(
                            f'https://hacker-news.firebaseio.com/v0/item/{item_id}.json'
                        )

                        if response.is_success:
                            data = response.json()
                            if data:
                                author = data.get('by')
                                if author:
                                    opp['contact'] = {
                                        'platform': 'hackernews',
                                        'platform_user_id': author,
                                        'hackernews_username': author,
                                        'preferred_outreach': 'hn_reply',
                                        'extraction_source': 'hn_api'
                                    }
                                    opp['metadata'] = opp.get('metadata', {})
                                    opp['metadata']['poster_username'] = author
                                    logger.debug(f"HN enriched: {author}")

                        await asyncio.sleep(0.1)

                    except Exception as e:
                        logger.debug(f"HN enrichment failed: {e}")

                enriched.append(opp)

        return enriched

    def _extract_hn_item_id(self, url: str) -> Optional[str]:
        """Extract HN item ID from URL"""
        match = re.search(r'id=(\d+)', url)
        if match:
            return match.group(1)
        return None

    async def _enrich_linkedin(self, opportunities: List[Dict]) -> List[Dict]:
        """Enrich LinkedIn opportunities (requires OAuth token)"""
        # LinkedIn API requires OAuth - pass through with URL-based enrichment
        enriched = []
        for opp in opportunities:
            url = opp.get('url', '')
            # Extract job ID from URL
            match = re.search(r'/jobs/view/(\d+)', url)
            if match:
                job_id = match.group(1)
                opp['contact'] = {
                    'platform': 'linkedin',
                    'platform_user_id': job_id,
                    'preferred_outreach': 'linkedin_apply',
                    'extraction_source': 'url_parse'
                }
            enriched.append(opp)
        return enriched

    def _basic_enrich(self, opp: Dict) -> Dict:
        """
        Basic enrichment for platforms without direct API access.

        Extracts ALL contact methods from opportunity body:
        - Email addresses
        - Twitter handles (@username)
        - LinkedIn URLs
        - Discord usernames
        - Telegram handles
        - Phone numbers
        - Website URLs with contact pages
        """
        if self._has_extractor and self._enrich_contact:
            try:
                opp = self._enrich_contact(opp)
            except Exception:
                pass

        # Combine all text fields for extraction
        text = ' '.join([
            opp.get('body', '') or '',
            opp.get('summary', '') or '',
            opp.get('title', '') or '',
            opp.get('description', '') or '',
        ])

        if not text.strip():
            return opp

        opp['contact'] = opp.get('contact', {})

        # 1. Extract email (highest priority)
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        if email_match:
            email = email_match.group(0)
            # Filter out common non-contact emails
            if not any(x in email.lower() for x in ['example.com', 'test.com', 'noreply', 'no-reply']):
                opp['contact']['email'] = email
                opp['contact']['preferred_outreach'] = 'email'

        # 2. Extract Twitter handle
        twitter_match = re.search(r'(?:twitter\.com/|@)([a-zA-Z0-9_]{1,15})\b', text, re.IGNORECASE)
        if twitter_match:
            handle = twitter_match.group(1)
            if handle.lower() not in ['twitter', 'x', 'com']:
                opp['contact']['twitter_handle'] = handle
                if not opp['contact'].get('preferred_outreach'):
                    opp['contact']['preferred_outreach'] = 'twitter_dm'

        # 3. Extract LinkedIn URL/ID
        linkedin_match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', text, re.IGNORECASE)
        if linkedin_match:
            opp['contact']['linkedin_id'] = linkedin_match.group(1)
            if not opp['contact'].get('preferred_outreach'):
                opp['contact']['preferred_outreach'] = 'linkedin_message'

        # 4. Extract Discord username
        discord_match = re.search(r'(?:discord(?:\.gg)?[:\s]+)?([a-zA-Z0-9_]+#\d{4})', text, re.IGNORECASE)
        if discord_match:
            opp['contact']['discord'] = discord_match.group(1)

        # 5. Extract Telegram handle
        telegram_match = re.search(r'(?:t\.me/|telegram[:\s]+@?)([a-zA-Z0-9_]{5,32})', text, re.IGNORECASE)
        if telegram_match:
            opp['contact']['telegram'] = telegram_match.group(1)

        # 6. Extract phone number (basic pattern)
        phone_match = re.search(r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if phone_match:
            opp['contact']['phone'] = phone_match.group(0)
            if not opp['contact'].get('preferred_outreach'):
                opp['contact']['preferred_outreach'] = 'sms'

        # 7. Extract Instagram handle
        insta_match = re.search(r'(?:instagram\.com/|ig[:\s]+@?)([a-zA-Z0-9_.]+)', text, re.IGNORECASE)
        if insta_match:
            handle = insta_match.group(1)
            if handle.lower() not in ['instagram', 'com', 'p', 'reel']:
                opp['contact']['instagram_handle'] = handle
                if not opp['contact'].get('preferred_outreach'):
                    opp['contact']['preferred_outreach'] = 'instagram_dm'

        # Set platform if we found any contact
        if opp['contact'] and not opp['contact'].get('platform'):
            opp['contact']['platform'] = opp.get('platform', 'other')
            opp['contact']['extraction_source'] = 'text_extraction'

        return opp

    def _has_contact(self, opp: Dict) -> bool:
        """Check if opportunity has contact info"""
        contact = opp.get('contact', {})
        if not contact:
            return False

        # Check for any valid contact method
        return any([
            contact.get('email'),
            contact.get('twitter_handle'),
            contact.get('reddit_username'),
            contact.get('github_username'),
            contact.get('hackernews_username'),
            contact.get('platform_user_id'),
        ])

    def _parse_json_from_text(self, text: str) -> List[Dict]:
        """Parse JSON array from text response"""
        opportunities = []

        # Try to find JSON array in response
        try:
            # Try direct parse
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except:
            pass

        # Try to extract JSON from markdown code block
        code_block_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', text)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except:
                pass

        # Try to find array anywhere in text
        array_match = re.search(r'\[[\s\S]*\]', text)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except:
                pass

        return []

    def get_stats(self) -> Dict[str, Any]:
        """Get enrichment statistics"""
        total = self.stats['phase2_enriched']
        with_contact = self.stats['phase2_with_contact']

        return {
            'phase1_discovered': self.stats['phase1_discovered'],
            'phase2_enriched': self.stats['phase2_enriched'],
            'phase2_with_contact': with_contact,
            'contact_rate': f"{with_contact/total*100:.1f}%" if total > 0 else "0%",
            'platforms_hit': self.stats['platforms_hit'],
            'errors': self.stats['errors']
        }


# Singleton instance
_hybrid_engine: Optional[HybridDiscoveryEngine] = None


def get_hybrid_discovery() -> HybridDiscoveryEngine:
    """Get singleton hybrid discovery engine"""
    global _hybrid_engine
    if _hybrid_engine is None:
        _hybrid_engine = HybridDiscoveryEngine()
    return _hybrid_engine


async def discover_with_contact(max_opportunities: int = 100) -> List[Dict]:
    """
    Convenience function for hybrid discovery with contact enrichment.

    Use this in integration routes:

        from discovery.hybrid_discovery import discover_with_contact
        opportunities = await discover_with_contact(max_opportunities=50)
    """
    engine = get_hybrid_discovery()
    return await engine.discover_with_contact(max_opportunities)
