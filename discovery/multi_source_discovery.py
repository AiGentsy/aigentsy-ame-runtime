"""
MULTI-SOURCE DISCOVERY ENGINE
=============================
Auto-detects and uses ALL configured APIs for maximum discovery coverage.

Sources (in priority order):
1. PERPLEXITY (PRIMARY) - Internet-wide search with web access
2. TWITTER (SOCIAL) - Real-time hiring tweets with @handles
3. GITHUB (OPEN SOURCE) - Bounties and help-wanted issues
4. OPENROUTER (BACKUP) - Perplexity model via OpenRouter
5. REDDIT (DIRECT) - r/forhire and r/hiring posts

All sources run in PARALLEL for maximum speed.
Results are INTERLEAVED for platform diversity.
Contact info is EXTRACTED and ENRICHED automatically.

Author: AiGentsy
Updated: January 2026
"""

import os
import asyncio
import logging
import hashlib
import re
import json
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


class MultiSourceDiscovery:
    """
    Enterprise-grade multi-source discovery engine.

    Automatically detects configured APIs and runs all discovery
    sources in parallel for maximum coverage and speed.
    """

    def __init__(self):
        """Initialize discovery engine and detect available sources."""
        self.sources = self._detect_available_sources()
        self.stats = {
            'sources_enabled': list(self.sources.keys()),
            'discovery_runs': 0,
            'total_discovered': 0,
            'by_source': defaultdict(int),
            'by_platform': defaultdict(int),
            'with_contact': 0,
            'errors': []
        }

        logger.info("=" * 60)
        logger.info("MULTI-SOURCE DISCOVERY ENGINE INITIALIZED")
        logger.info("=" * 60)
        logger.info(f"Enabled sources: {list(self.sources.keys())}")

    def _detect_available_sources(self) -> Dict[str, Dict[str, Any]]:
        """
        Auto-detect which APIs are configured based on environment variables.
        Returns dict of source_name -> config.
        """
        sources = {}

        # PERPLEXITY - Primary internet-wide search
        perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        if perplexity_key:
            sources['perplexity'] = {
                'api_key': perplexity_key,
                'priority': 1,
                'description': 'Internet-wide search (PRIMARY)'
            }
            logger.info("  [1] Perplexity API - Internet-wide search (PRIMARY)")

        # TWITTER - Social discovery with @handles
        twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
        if twitter_bearer:
            sources['twitter'] = {
                'bearer_token': twitter_bearer,
                'priority': 2,
                'description': 'Twitter search with @handles'
            }
            logger.info(f"  [2] Twitter Bearer Token - Social search (token length: {len(twitter_bearer)})")
        else:
            # Check what Twitter keys ARE available
            has_api_key = bool(os.getenv('TWITTER_API_KEY'))
            has_access = bool(os.getenv('TWITTER_ACCESS_TOKEN'))
            logger.warning(f"  [!] TWITTER_BEARER_TOKEN not set (API_KEY={has_api_key}, ACCESS_TOKEN={has_access})")
            logger.warning("      Twitter SEARCH requires Bearer Token, not OAuth keys")

        # GITHUB - Open source bounties
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            sources['github'] = {
                'token': github_token,
                'priority': 3,
                'description': 'GitHub bounties and issues'
            }
            logger.info("  [3] GitHub Token - Bounties & issues")

        # OPENROUTER - Backup via Perplexity model
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if openrouter_key:
            sources['openrouter'] = {
                'api_key': openrouter_key,
                'priority': 4,
                'description': 'OpenRouter backup search'
            }
            logger.info("  [4] OpenRouter API - Backup search")

        # REDDIT - Always available (public JSON API)
        sources['reddit'] = {
            'priority': 5,
            'description': 'Reddit r/forhire & r/hiring'
        }
        logger.info("  [5] Reddit JSON API - Direct posts")

        return sources

    async def discover(self, max_opportunities: int = 100) -> List[Dict[str, Any]]:
        """
        Run ALL discovery sources in parallel and return combined results.

        Args:
            max_opportunities: Maximum opportunities to return

        Returns:
            List of opportunities with contact info, interleaved by source
        """
        self.stats['discovery_runs'] += 1
        start_time = datetime.now(timezone.utc)

        logger.info("\n" + "=" * 80)
        logger.info("MULTI-SOURCE DISCOVERY - PARALLEL EXECUTION")
        logger.info("=" * 80)
        logger.info(f"Running {len(self.sources)} sources in parallel...")

        # Build tasks for all enabled sources
        tasks = []
        task_names = []

        if 'perplexity' in self.sources:
            tasks.append(self._discover_perplexity())
            task_names.append('perplexity')

        if 'twitter' in self.sources:
            tasks.append(self._discover_twitter())
            task_names.append('twitter')

        if 'github' in self.sources:
            tasks.append(self._discover_github())
            task_names.append('github')

        if 'openrouter' in self.sources:
            tasks.append(self._discover_openrouter())
            task_names.append('openrouter')

        if 'reddit' in self.sources:
            tasks.append(self._discover_reddit())
            task_names.append('reddit')

        # Execute ALL sources in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results from all sources
        all_opportunities = []
        source_counts = {}

        for i, result in enumerate(results):
            source_name = task_names[i] if i < len(task_names) else f'source_{i}'

            if isinstance(result, Exception):
                logger.error(f"  [{source_name}] FAILED: {type(result).__name__}: {result}")
                self.stats['errors'].append({
                    'source': source_name,
                    'error': str(result),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                source_counts[source_name] = 0
            elif isinstance(result, list):
                source_counts[source_name] = len(result)
                all_opportunities.extend(result)
                self.stats['by_source'][source_name] += len(result)
            else:
                source_counts[source_name] = 0

        # Log source breakdown
        logger.info("\n" + "-" * 40)
        logger.info("DISCOVERY RESULTS BY SOURCE:")
        logger.info("-" * 40)
        for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            status = "OK" if count > 0 else "EMPTY"
            logger.info(f"  [{status}] {source}: {count}")
        logger.info(f"  TOTAL RAW: {len(all_opportunities)}")

        # Deduplicate by URL
        unique_opportunities = self._deduplicate(all_opportunities)
        logger.info(f"  AFTER DEDUP: {len(unique_opportunities)}")

        # Count by platform
        platform_counts = defaultdict(int)
        for opp in unique_opportunities:
            platform = opp.get('platform', 'unknown')
            platform_counts[platform] += 1
            self.stats['by_platform'][platform] += 1

        logger.info("\n" + "-" * 40)
        logger.info("PLATFORM DIVERSITY:")
        logger.info("-" * 40)
        for platform, count in sorted(platform_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {platform}: {count}")

        # Interleave for diversity
        interleaved = self._interleave_by_source(unique_opportunities)

        # Take top N
        final = interleaved[:max_opportunities]

        # AI-powered contact enrichment for opportunities missing contact
        if 'openrouter' in self.sources:
            logger.info("\n" + "-" * 40)
            logger.info("AI CONTACT ENRICHMENT (OpenRouter)")
            logger.info("-" * 40)
            final = await self._ai_contact_enrichment(final)

        # Count with contact
        with_contact = sum(1 for o in final if self._has_contact(o))
        self.stats['with_contact'] += with_contact
        self.stats['total_discovered'] += len(final)

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("DISCOVERY COMPLETE")
        logger.info("=" * 80)
        logger.info(f"  Total opportunities: {len(final)}")
        logger.info(f"  With contact info: {with_contact} ({with_contact/len(final)*100:.1f}%)" if final else "  With contact: 0")
        logger.info(f"  Time elapsed: {elapsed:.2f}s")

        return final

    async def _discover_perplexity(self) -> List[Dict[str, Any]]:
        """
        PERPLEXITY (PRIMARY) - Internet-wide search with web access.

        Searches across the entire internet for job opportunities,
        freelance requests, and hiring posts with contact information.
        """
        api_key = self.sources['perplexity']['api_key']
        opportunities = []

        # OPTIMIZED queries - focus on posts with EXPLICIT email addresses
        # These patterns indicate someone publicly sharing their contact
        queries = [
            # HIGH PRIORITY: Posts with explicit email patterns
            '"email me at" developer hire 2025',
            '"send resume to" software engineer job',
            '"contact me at" gmail.com developer freelance',
            '"reach out" email developer project needed',
            '"apply via email" developer remote job',

            # Email domain patterns (people often share gmail/outlook)
            'hiring developer "@gmail.com" contact',
            'need developer "@outlook.com" project',
            'freelance engineer "send to" email',

            # Twitter/X with DM requests
            '"DM me" hiring developer Twitter 2025',
            '"DMs open" need developer urgent',
            'X.com "@" hiring engineer contact',

            # LinkedIn with profile URLs
            '"linkedin.com/in/" hiring developer',
            'connect LinkedIn developer needed',

            # Job boards with direct apply
            'Upwork developer "$5000" urgent contract',
            'Freelancer high budget developer project',

            # Startup founder posts (often include email)
            'startup founder "looking for" developer email',
            'cofounder "contact" developer equity',
            'YC startup hiring engineer "reach out"',
        ]

        logger.info(f"  [perplexity] Running {len(queries)} queries...")

        async with httpx.AsyncClient(timeout=45) as client:
            # Run queries in small batches to avoid rate limits
            batch_size = 5
            for batch_start in range(0, len(queries), batch_size):
                batch = queries[batch_start:batch_start + batch_size]

                batch_tasks = [
                    self._run_perplexity_query(client, api_key, q)
                    for q in batch
                ]

                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                for result in batch_results:
                    if isinstance(result, list):
                        opportunities.extend(result)

                # Small delay between batches
                if batch_start + batch_size < len(queries):
                    await asyncio.sleep(1)

        logger.info(f"  [perplexity] Found {len(opportunities)} opportunities")
        return opportunities

    async def _run_perplexity_query(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """Execute a single Perplexity query and parse results."""
        try:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You find job opportunities with contact information.
Return ONLY a JSON array. Each item must have: title, url, contact, platform, description.
The contact field should contain any email address, Twitter @handle, or phone number visible.
Only include REAL opportunities with actual URLs."""
                        },
                        {
                            "role": "user",
                            "content": f"Find 5 recent job/project opportunities matching: {query}\n\nReturn JSON array only:"
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.1
                }
            )

            if response.status_code != 200:
                logger.debug(f"Perplexity error {response.status_code}: {response.text[:200]}")
                return []

            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

            # Parse JSON from response
            return self._parse_perplexity_response(content, query)

        except httpx.TimeoutException:
            logger.debug(f"Perplexity query timed out: {query[:30]}...")
            return []
        except Exception as e:
            logger.debug(f"Perplexity query failed: {e}")
            return []

    def _parse_perplexity_response(self, content: str, query: str) -> List[Dict[str, Any]]:
        """Parse Perplexity response content into structured opportunities."""
        opportunities = []

        # Try to extract JSON array from response
        json_match = re.search(r'\[[\s\S]*\]', content)
        if not json_match:
            return []

        try:
            results = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return []

        for r in results:
            if not isinstance(r, dict):
                continue

            url = r.get('url', '')
            if not url or 'example.com' in url:
                continue

            # Generate unique ID
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]

            opp = {
                'id': f"pplx_{url_hash}",
                'title': r.get('title', 'Untitled')[:200],
                'url': url,
                'platform': self._detect_platform(url),
                'body': r.get('description', ''),
                'summary': r.get('description', '')[:300] if r.get('description') else '',
                'source': 'perplexity',
                'metadata': {
                    'query': query,
                    'discovered_at': datetime.now(timezone.utc).isoformat()
                }
            }

            # Parse contact information
            contact_str = r.get('contact', '')
            if contact_str:
                contact = self._parse_contact_string(str(contact_str))
                if contact:
                    opp['contact'] = contact

            opportunities.append(opp)

        return opportunities

    async def _discover_twitter(self) -> List[Dict[str, Any]]:
        """
        TWITTER - Search recent tweets for hiring posts.

        Uses Twitter API v2 with Bearer Token for search.
        Returns tweets with author @handles for DM outreach.
        """
        bearer_token = self.sources['twitter']['bearer_token']
        opportunities = []

        logger.info(f"  [twitter] Starting Twitter discovery...")
        logger.info(f"  [twitter] Bearer token present: {bool(bearer_token)}")
        logger.info(f"  [twitter] Bearer token length: {len(bearer_token) if bearer_token else 0}")

        queries = [
            "hiring developer",
            "looking for engineer",
            "need developer DM",
            "hiring React",
            "freelance developer",
            "contract developer",
            "hiring Python",
            "looking developer"
        ]

        logger.info(f"  [twitter] Running {len(queries)} search queries...")

        async with httpx.AsyncClient(timeout=30) as client:
            for query in queries[:5]:  # Limit to avoid rate limits
                try:
                    response = await client.get(
                        "https://api.twitter.com/2/tweets/search/recent",
                        headers={"Authorization": f"Bearer {bearer_token}"},
                        params={
                            "query": f"{query} -is:retweet -is:reply lang:en",
                            "max_results": 10,
                            "tweet.fields": "author_id,created_at,public_metrics,entities",
                            "expansions": "author_id",
                            "user.fields": "username,name,description"
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        tweets = data.get('data', [])
                        users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

                        for tweet in tweets:
                            author_id = tweet.get('author_id')
                            user = users.get(author_id, {})
                            username = user.get('username')

                            if not username:
                                continue

                            tweet_id = tweet['id']
                            tweet_text = tweet.get('text', '')

                            opportunities.append({
                                'id': f"twitter_{tweet_id}",
                                'title': tweet_text[:100],
                                'url': f"https://twitter.com/{username}/status/{tweet_id}",
                                'platform': 'twitter',
                                'body': tweet_text,
                                'summary': tweet_text[:200],
                                'source': 'twitter_api',
                                'contact': {
                                    'twitter_handle': username,
                                    'platform': 'twitter',
                                    'preferred_outreach': 'twitter_dm'
                                },
                                'metadata': {
                                    'author_id': author_id,
                                    'author_name': user.get('name', ''),
                                    'author_handle': username,
                                    'created_at': tweet.get('created_at'),
                                    'retweet_count': tweet.get('public_metrics', {}).get('retweet_count', 0),
                                    'like_count': tweet.get('public_metrics', {}).get('like_count', 0)
                                }
                            })

                    elif response.status_code == 429:
                        logger.warning("  [twitter] Rate limit hit - stopping Twitter search")
                        break
                    elif response.status_code == 401:
                        logger.error(f"  [twitter] UNAUTHORIZED (401) - Bearer token may be invalid")
                        logger.error(f"  [twitter] Response: {response.text[:200]}")
                        break
                    elif response.status_code == 403:
                        logger.error(f"  [twitter] FORBIDDEN (403) - API access denied")
                        logger.error(f"  [twitter] Response: {response.text[:200]}")
                        break
                    else:
                        logger.warning(f"  [twitter] Error {response.status_code}: {response.text[:100]}")

                    # Small delay between queries
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.debug(f"Twitter search error: {e}")

        logger.info(f"  [twitter] Found {len(opportunities)} opportunities")
        return opportunities

    async def _discover_github(self) -> List[Dict[str, Any]]:
        """
        GITHUB - Search for bounties and help-wanted issues.

        Uses GitHub Search API to find issues with bounty labels,
        help-wanted tags, or payment mentions.
        """
        token = self.sources['github']['token']
        opportunities = []

        queries = [
            "label:bounty is:issue is:open",
            "label:help-wanted is:issue is:open",
            "bounty in:title is:issue is:open",
            "paid in:title is:issue is:open",
            "label:good-first-issue is:issue is:open"
        ]

        logger.info(f"  [github] Running {len(queries)} search queries...")

        async with httpx.AsyncClient(timeout=30) as client:
            for query in queries[:3]:  # Limit to avoid rate limits
                try:
                    response = await client.get(
                        "https://api.github.com/search/issues",
                        headers={
                            "Authorization": f"token {token}",
                            "Accept": "application/vnd.github.v3+json"
                        },
                        params={
                            "q": query,
                            "per_page": 10,
                            "sort": "created",
                            "order": "desc"
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()

                        for issue in data.get('items', []):
                            issue_id = issue['id']
                            author = issue.get('user', {}).get('login', '')

                            opportunities.append({
                                'id': f"github_{issue_id}",
                                'title': issue['title'][:200],
                                'url': issue['html_url'],
                                'platform': 'github',
                                'body': issue.get('body', '') or '',
                                'summary': (issue.get('body', '') or '')[:300],
                                'source': 'github_api',
                                'contact': {
                                    'github_username': author,
                                    'platform': 'github',
                                    'preferred_outreach': 'github_issue'  # Manual review required
                                },
                                'metadata': {
                                    'author': author,
                                    'state': issue.get('state'),
                                    'created_at': issue.get('created_at'),
                                    'labels': [l['name'] for l in issue.get('labels', [])],
                                    'comments': issue.get('comments', 0),
                                    'repository': issue.get('repository_url', '').split('/')[-1] if issue.get('repository_url') else ''
                                }
                            })

                    elif response.status_code == 403:
                        logger.warning("  [github] Rate limit hit")
                        break

                    await asyncio.sleep(1)  # GitHub rate limit

                except Exception as e:
                    logger.debug(f"GitHub search error: {e}")

        logger.info(f"  [github] Found {len(opportunities)} opportunities")
        return opportunities

    async def _discover_openrouter(self) -> List[Dict[str, Any]]:
        """
        OPENROUTER (BACKUP) - Use Perplexity model via OpenRouter.

        Provides backup internet search capability using OpenRouter's
        access to Perplexity models with web search.
        """
        api_key = self.sources['openrouter']['api_key']
        opportunities = []

        queries = [
            "developer for hire contact email urgent 2025",
            "freelance engineer available hire immediately"
        ]

        logger.info(f"  [openrouter] Running {len(queries)} queries...")

        async with httpx.AsyncClient(timeout=60) as client:
            for query in queries:
                try:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "https://aigentsy.com",
                            "X-Title": "AiGentsy Discovery"
                        },
                        json={
                            "model": "perplexity/llama-3.1-sonar-large-128k-online",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": f"""Find 5 job/project opportunities: {query}

Return ONLY a JSON array with format:
[{{"title": "...", "url": "actual_url", "contact": "email or @handle", "description": "..."}}]

JSON only:"""
                                }
                            ],
                            "temperature": 0.1,
                            "max_tokens": 2000
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

                        # Parse JSON
                        json_match = re.search(r'\[[\s\S]*\]', content)
                        if json_match:
                            try:
                                results = json.loads(json_match.group(0))
                                for r in results:
                                    if isinstance(r, dict) and r.get('url'):
                                        url = r['url']
                                        if 'example.com' in url:
                                            continue

                                        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]

                                        opp = {
                                            'id': f"openrouter_{url_hash}",
                                            'title': r.get('title', 'Untitled')[:200],
                                            'url': url,
                                            'platform': self._detect_platform(url),
                                            'body': r.get('description', ''),
                                            'summary': r.get('description', '')[:300] if r.get('description') else '',
                                            'source': 'openrouter',
                                            'metadata': {
                                                'query': query,
                                                'discovered_at': datetime.now(timezone.utc).isoformat()
                                            }
                                        }

                                        if r.get('contact'):
                                            contact = self._parse_contact_string(str(r['contact']))
                                            if contact:
                                                opp['contact'] = contact

                                        opportunities.append(opp)
                            except json.JSONDecodeError:
                                pass

                except Exception as e:
                    logger.debug(f"OpenRouter search error: {e}")

        logger.info(f"  [openrouter] Found {len(opportunities)} opportunities")
        return opportunities

    async def _discover_reddit(self) -> List[Dict[str, Any]]:
        """
        REDDIT - Direct API access to r/forhire and r/hiring.

        Uses Reddit's public JSON API to fetch recent posts.
        Returns posts with author usernames for DM outreach.
        """
        opportunities = []

        subreddits = ['forhire', 'hiring', 'remotejobs', 'freelance_forhire']

        logger.info(f"  [reddit] Fetching from {len(subreddits)} subreddits...")

        # Use more realistic headers to avoid rate limiting
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        async with httpx.AsyncClient(timeout=15) as client:
            for subreddit in subreddits[:2]:  # Reduce to 2 to avoid rate limits
                try:
                    # Add delay BEFORE request to help with rate limiting
                    await asyncio.sleep(2)

                    response = await client.get(
                        f"https://www.reddit.com/r/{subreddit}/new.json",
                        headers=headers,
                        params={'limit': 10}
                    )

                    logger.info(f"  [reddit] r/{subreddit} response: {response.status_code}")

                    if response.status_code == 200:
                        data = response.json()
                        posts = data.get('data', {}).get('children', [])
                        logger.info(f"  [reddit] r/{subreddit} returned {len(posts)} posts")

                        for post in posts:
                            post_data = post.get('data', {})
                            author = post_data.get('author')

                            if not author or author == '[deleted]':
                                continue

                            post_id = post_data.get('id', '')
                            title = post_data.get('title', '')
                            body = post_data.get('selftext', '')
                            permalink = post_data.get('permalink', '')

                            # Extract ALL contact methods from post body
                            contact = {
                                'reddit_username': author,
                                'platform': 'reddit',
                                'preferred_outreach': 'reddit_dm'
                            }

                            # Combine title and body for extraction
                            full_text = f"{title} {body}"

                            # 1. Email (highest priority)
                            email_match = re.search(
                                r'[\w.+-]+@[\w-]+\.[\w.-]+',
                                full_text,
                                re.IGNORECASE
                            )
                            if email_match:
                                email = email_match.group(0).lower()
                                # Filter out common non-contact emails
                                if not any(x in email for x in ['example.', 'test.', 'noreply', 'no-reply']):
                                    contact['email'] = email
                                    contact['preferred_outreach'] = 'email'

                            # 2. Twitter/X handle
                            twitter_match = re.search(
                                r'(?:twitter\.com/|x\.com/|@)([a-zA-Z0-9_]{1,15})\b',
                                full_text,
                                re.IGNORECASE
                            )
                            if twitter_match:
                                handle = twitter_match.group(1)
                                if handle.lower() not in ['twitter', 'x', 'com', 'status', 'i']:
                                    contact['twitter_handle'] = handle
                                    if not contact.get('email'):
                                        contact['preferred_outreach'] = 'twitter_dm'

                            # 3. LinkedIn URL
                            linkedin_match = re.search(
                                r'linkedin\.com/in/([a-zA-Z0-9-]+)',
                                full_text,
                                re.IGNORECASE
                            )
                            if linkedin_match:
                                contact['linkedin_id'] = linkedin_match.group(1)
                                if not contact.get('email') and not contact.get('twitter_handle'):
                                    contact['preferred_outreach'] = 'linkedin_message'

                            # 4. Phone number (with validation)
                            phone_match = re.search(
                                r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                                full_text
                            )
                            if phone_match:
                                # Validate and normalize phone
                                try:
                                    from enrichment.ai_contact_extractor import normalize_phone_number
                                    normalized = normalize_phone_number(phone_match.group(0))
                                    if normalized:
                                        contact['phone'] = normalized
                                        if not contact.get('email'):
                                            contact['preferred_outreach'] = 'sms'
                                except ImportError:
                                    # Fallback without validation
                                    contact['phone'] = phone_match.group(0)
                                    if not contact.get('email'):
                                        contact['preferred_outreach'] = 'sms'

                            # 5. Discord
                            discord_match = re.search(
                                r'(?:discord[:\s]+)?([a-zA-Z0-9_]+#\d{4})',
                                full_text,
                                re.IGNORECASE
                            )
                            if discord_match:
                                contact['discord'] = discord_match.group(1)

                            opportunities.append({
                                'id': f"reddit_{post_id}",
                                'title': title[:200],
                                'url': f"https://reddit.com{permalink}",
                                'platform': 'reddit',
                                'body': body,
                                'summary': body[:300] if body else title,
                                'source': 'reddit_api',
                                'contact': contact,
                                'metadata': {
                                    'subreddit': subreddit,
                                    'author': author,
                                    'score': post_data.get('score', 0),
                                    'created_utc': post_data.get('created_utc'),
                                    'num_comments': post_data.get('num_comments', 0)
                                }
                            })

                    elif response.status_code == 429:
                        logger.warning(f"  [reddit] Rate limited on r/{subreddit}")
                        break
                    elif response.status_code == 403:
                        logger.warning(f"  [reddit] Forbidden on r/{subreddit} - may be blocked")
                    else:
                        logger.warning(f"  [reddit] r/{subreddit} error {response.status_code}: {response.text[:100]}")

                    await asyncio.sleep(3)  # Longer delay to avoid Reddit rate limiting

                except Exception as e:
                    logger.warning(f"  [reddit] Exception for r/{subreddit}: {type(e).__name__}: {e}")

        logger.info(f"  [reddit] Found {len(opportunities)} opportunities")
        return opportunities

    async def _ai_contact_enrichment(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Use AI (OpenRouter + Gemini) to extract contact info from opportunity text/body.

        For opportunities missing contact info, analyzes the body text
        to extract email, phone, Twitter handle, etc.

        Uses the enrichment.ai_contact_extractor module for:
        - Phone number validation and normalization
        - Email validation
        - AI-powered extraction with fallback
        """
        # Check if we have any AI available
        has_openrouter = bool(self.sources.get('openrouter', {}).get('api_key'))
        has_gemini = bool(os.getenv('GEMINI_API_KEY'))

        if not has_openrouter and not has_gemini:
            logger.info("  No AI available for contact enrichment (need OpenRouter or Gemini)")
            return opportunities

        # Find opportunities missing usable contact (email/phone/twitter)
        needs_enrichment = [
            (i, opp) for i, opp in enumerate(opportunities)
            if not self._has_usable_contact(opp) and opp.get('body')
        ]

        if not needs_enrichment:
            logger.info("  All opportunities already have usable contact info")
            return opportunities

        logger.info(f"  AI enriching {len(needs_enrichment)} opportunities...")

        # Import AI extractor
        try:
            from enrichment.ai_contact_extractor import extract_contact_with_ai
        except ImportError:
            logger.warning("  AI contact extractor not available")
            return opportunities

        for idx, opp in needs_enrichment[:15]:  # Limit to 15 to control cost
            body = opp.get('body', '')
            title = opp.get('title', '')
            url = opp.get('url', '')

            if not body.strip():
                continue

            # Combine title and body for analysis
            text = f"Title: {title}\n\nBody: {body}"

            contact = await extract_contact_with_ai(text, url)

            if contact:
                # Merge with existing contact (preserve reddit/github usernames)
                existing = opp.get('contact', {})
                merged = {**existing, **contact}
                opportunities[idx]['contact'] = merged
                logger.info(f"    Enriched: {opp.get('id')[:20]} -> {contact.get('preferred_outreach')}")

            await asyncio.sleep(0.3)  # Rate limit

        enriched_count = sum(1 for i, _ in needs_enrichment if self._has_usable_contact(opportunities[i]))
        logger.info(f"  AI enriched {enriched_count}/{len(needs_enrichment)} opportunities with usable contact")

        return opportunities

    def _has_usable_contact(self, opportunity: Dict[str, Any]) -> bool:
        """Check if opportunity has USABLE contact info (email, phone, or twitter for DM)."""
        contact = opportunity.get('contact', {})
        if not contact:
            return False

        # Usable = can actually reach out
        return bool(
            contact.get('email') or
            contact.get('phone') or
            contact.get('twitter_handle')
        )

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL."""
        if not url:
            return 'web'

        url_lower = url.lower()

        platform_patterns = {
            'twitter': ['twitter.com', 'x.com'],
            'linkedin': ['linkedin.com'],
            'github': ['github.com'],
            'reddit': ['reddit.com', 'redd.it'],
            'upwork': ['upwork.com'],
            'freelancer': ['freelancer.com'],
            'fiverr': ['fiverr.com'],
            'toptal': ['toptal.com'],
            'hackernews': ['news.ycombinator.com'],
            'indiehackers': ['indiehackers.com'],
            'producthunt': ['producthunt.com'],
            'angellist': ['angel.co', 'wellfound.com'],
            'indeed': ['indeed.com'],
            'glassdoor': ['glassdoor.com'],
            'stackoverflow': ['stackoverflow.com'],
            'dev.to': ['dev.to']
        }

        for platform, patterns in platform_patterns.items():
            for pattern in patterns:
                if pattern in url_lower:
                    return platform

        return 'web'

    def _parse_contact_string(self, contact_str: str) -> Optional[Dict[str, Any]]:
        """Parse contact string into structured format with validation."""
        if not contact_str:
            return None

        contact = {}

        # Import validators
        try:
            from enrichment.ai_contact_extractor import validate_email, normalize_phone_number
            has_validators = True
        except ImportError:
            has_validators = False

        # Email extraction with validation
        email_match = re.search(
            r'[\w.+-]+@[\w-]+\.[\w.-]+',
            contact_str,
            re.IGNORECASE
        )
        if email_match:
            raw_email = email_match.group(0).lower()
            if has_validators:
                validated = validate_email(raw_email)
                if validated:
                    contact['email'] = validated
                    contact['preferred_outreach'] = 'email'
            else:
                contact['email'] = raw_email
                contact['preferred_outreach'] = 'email'

        # Twitter handle extraction
        twitter_match = re.search(r'@([a-zA-Z0-9_]{1,15})', contact_str)
        if twitter_match:
            contact['twitter_handle'] = twitter_match.group(1)
            if 'preferred_outreach' not in contact:
                contact['preferred_outreach'] = 'twitter_dm'

        # Phone number extraction with validation
        phone_match = re.search(
            r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            contact_str
        )
        if phone_match:
            raw_phone = phone_match.group(0)
            if has_validators:
                normalized = normalize_phone_number(raw_phone)
                if normalized:
                    contact['phone'] = normalized
                    if 'preferred_outreach' not in contact:
                        contact['preferred_outreach'] = 'sms'
            else:
                contact['phone'] = raw_phone
                if 'preferred_outreach' not in contact:
                    contact['preferred_outreach'] = 'sms'

        return contact if contact else None

    def _has_contact(self, opportunity: Dict[str, Any]) -> bool:
        """Check if opportunity has usable contact information."""
        contact = opportunity.get('contact', {})
        if not contact:
            return False

        # Check for any contact method
        return bool(
            contact.get('email') or
            contact.get('twitter_handle') or
            contact.get('phone') or
            contact.get('reddit_username') or
            contact.get('github_username') or
            contact.get('linkedin_id')
        )

    def _deduplicate(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate opportunities by URL."""
        seen_urls: Set[str] = set()
        unique = []

        for opp in opportunities:
            url = opp.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique.append(opp)

        return unique

    def _interleave_by_source(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Interleave opportunities by source for platform diversity.

        Uses round-robin selection from each source to ensure
        diverse platform representation in final results.
        """
        by_source = defaultdict(list)

        for opp in opportunities:
            source = opp.get('source', 'unknown')
            by_source[source].append(opp)

        # Priority order for interleaving
        source_priority = [
            'twitter_api',      # Best for DM outreach
            'perplexity',       # Internet-wide coverage
            'reddit_api',       # Good with email extraction
            'github_api',       # Manual review
            'openrouter'        # Backup
        ]

        # Add any sources not in priority list
        for source in by_source.keys():
            if source not in source_priority:
                source_priority.append(source)

        # Round-robin interleaving
        interleaved = []
        max_len = max(len(opps) for opps in by_source.values()) if by_source else 0

        for i in range(max_len):
            for source in source_priority:
                if source in by_source and i < len(by_source[source]):
                    interleaved.append(by_source[source][i])

        return interleaved

    def get_stats(self) -> Dict[str, Any]:
        """Return discovery statistics."""
        return dict(self.stats)


# Singleton instance
_multi_source_discovery: Optional[MultiSourceDiscovery] = None


def get_multi_source_discovery() -> MultiSourceDiscovery:
    """Get or create the multi-source discovery singleton."""
    global _multi_source_discovery
    if _multi_source_discovery is None:
        _multi_source_discovery = MultiSourceDiscovery()
    return _multi_source_discovery


async def discover_all(max_opportunities: int = 100) -> List[Dict[str, Any]]:
    """
    Convenience function to run multi-source discovery.

    Args:
        max_opportunities: Maximum opportunities to return

    Returns:
        List of opportunities with contact info
    """
    discovery = get_multi_source_discovery()
    return await discovery.discover(max_opportunities)
