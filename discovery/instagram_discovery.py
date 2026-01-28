"""
Instagram Discovery - Find hiring opportunities via hashtags
═══════════════════════════════════════════════════════════════════════════════

Uses Instagram Graph API to discover job posts via hashtags.

HASHTAGS TO MONITOR:
- #hiring, #lookingfordeveloper, #needadeveloper
- #reactdeveloper, #pythondeveloper, #webdeveloper
- #freelancejobs, #remotework, #techjobs

REQUIREMENTS:
- Instagram Business Account
- Facebook Page linked to Instagram
- Meta Developer App with Instagram Graph API access
- INSTAGRAM_ACCESS_TOKEN env var

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Instagram Graph API config
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
INSTAGRAM_BUSINESS_ID = os.getenv('INSTAGRAM_BUSINESS_ID', '')
GRAPH_API_VERSION = 'v18.0'
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Hashtags to monitor for opportunities
HIRING_HASHTAGS = [
    'hiring', 'lookingfordeveloper', 'needadeveloper', 'developerneeded',
    'reactdeveloper', 'pythondeveloper', 'webdeveloper', 'nodejsdeveloper',
    'freelancejobs', 'remotework', 'techjobs', 'startupjobs',
    'hiringdevelopers', 'seekingdeveloper', 'devjobs'
]

# Keywords that indicate a hiring post
HIRING_KEYWORDS = [
    'hiring', 'looking for', 'need a', 'seeking', 'wanted',
    'developer wanted', 'engineer needed', 'urgently need',
    'help needed', 'project help', 'freelancer needed',
    'who can build', 'who can help', 'dm me if'
]

TECH_KEYWORDS = [
    'developer', 'engineer', 'programmer', 'coder',
    'react', 'python', 'javascript', 'typescript', 'node',
    'api', 'website', 'webapp', 'app', 'backend', 'frontend',
    'fullstack', 'full stack', 'mobile', 'ios', 'android',
    'automation', 'bot', 'scraper', 'ai', 'ml', 'data'
]


class InstagramDiscovery:
    """Discover hiring opportunities on Instagram via hashtags"""

    def __init__(self):
        self.access_token = INSTAGRAM_ACCESS_TOKEN
        self.business_id = INSTAGRAM_BUSINESS_ID
        self.available = bool(self.access_token and self.business_id)

        if self.available:
            logger.info("Instagram Discovery initialized")
        else:
            logger.warning("Instagram Discovery: Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID")

    async def discover_opportunities(
        self,
        hashtags: List[str] = None,
        limit_per_hashtag: int = 20
    ) -> List[Dict]:
        """
        Discover opportunities by searching hashtags.

        Args:
            hashtags: List of hashtags to search (without #)
            limit_per_hashtag: Max posts per hashtag

        Returns:
            List of opportunity dicts
        """
        if not self.available:
            logger.warning("Instagram Discovery not available (missing credentials)")
            return []

        hashtags = hashtags or HIRING_HASHTAGS[:5]  # Limit to avoid rate limits
        opportunities = []
        seen_ids = set()

        try:
            import httpx

            async with httpx.AsyncClient(timeout=30) as client:
                for hashtag in hashtags:
                    try:
                        posts = await self._search_hashtag(client, hashtag, limit_per_hashtag)

                        for post in posts:
                            # Skip duplicates
                            if post.get('id') in seen_ids:
                                continue
                            seen_ids.add(post.get('id'))

                            # Filter for hiring-related posts
                            if self._is_hiring_post(post):
                                opportunity = self._parse_opportunity(post, hashtag)
                                opportunities.append(opportunity)
                                logger.debug(f"Found Instagram opportunity: {opportunity.get('title', '')[:50]}")

                    except Exception as e:
                        logger.warning(f"Error searching hashtag #{hashtag}: {e}")
                        continue

            logger.info(f"Instagram Discovery: Found {len(opportunities)} opportunities from {len(hashtags)} hashtags")
            return opportunities

        except Exception as e:
            logger.error(f"Instagram Discovery error: {e}")
            return []

    async def _search_hashtag(
        self,
        client,
        hashtag: str,
        limit: int
    ) -> List[Dict]:
        """Search posts by hashtag using Instagram Graph API"""

        # Step 1: Get hashtag ID
        search_url = f"{GRAPH_API_BASE}/ig_hashtag_search"
        params = {
            'user_id': self.business_id,
            'q': hashtag,
            'access_token': self.access_token
        }

        response = await client.get(search_url, params=params)

        if not response.is_success:
            logger.warning(f"Hashtag search failed for #{hashtag}: {response.status_code}")
            return []

        data = response.json()
        if not data.get('data'):
            return []

        hashtag_id = data['data'][0]['id']

        # Step 2: Get recent media for hashtag
        media_url = f"{GRAPH_API_BASE}/{hashtag_id}/recent_media"
        params = {
            'user_id': self.business_id,
            'fields': 'id,caption,media_type,media_url,permalink,timestamp,children',
            'access_token': self.access_token,
            'limit': limit
        }

        response = await client.get(media_url, params=params)

        if not response.is_success:
            logger.warning(f"Media fetch failed for #{hashtag}: {response.status_code}")
            return []

        return response.json().get('data', [])

    def _is_hiring_post(self, post: Dict) -> bool:
        """Check if post is about hiring/looking for help"""
        caption = (post.get('caption') or '').lower()

        if not caption:
            return False

        # Must have hiring intent
        has_hiring = any(kw in caption for kw in HIRING_KEYWORDS)

        # Must have tech context
        has_tech = any(kw in caption for kw in TECH_KEYWORDS)

        return has_hiring and has_tech

    def _parse_opportunity(self, post: Dict, source_hashtag: str) -> Dict:
        """Parse Instagram post into opportunity format"""
        caption = post.get('caption', '')
        post_id = post.get('id')
        permalink = post.get('permalink', f"https://instagram.com/p/{post_id}")

        return {
            'id': f"instagram_{post_id}",
            'platform': 'instagram',
            'post_id': post_id,
            'source': f"instagram_hashtag_{source_hashtag}",
            'title': self._extract_title(caption),
            'description': caption[:500] if caption else '',
            'url': permalink,
            'permalink': permalink,
            'timestamp': post.get('timestamp'),
            'media_type': post.get('media_type'),
            'media_url': post.get('media_url'),
            'detected_skills': self._extract_skills(caption),
            'contact': {
                'instagram_post_id': post_id,
                'platform': 'instagram'
            },
            'discovered_at': datetime.now(timezone.utc).isoformat()
        }

    def _extract_title(self, caption: str) -> str:
        """Extract a title from the caption"""
        if not caption:
            return "Instagram Opportunity"

        # Take first line or first 100 chars
        lines = caption.split('\n')
        first_line = lines[0].strip() if lines else caption[:100]

        # Clean up
        first_line = first_line.replace('#', '').strip()

        return first_line[:100] if first_line else "Instagram Opportunity"

    def _extract_skills(self, caption: str) -> List[str]:
        """Extract tech skills mentioned in caption"""
        if not caption:
            return []

        caption_lower = caption.lower()
        skills = []

        skill_map = {
            'react': 'React',
            'vue': 'Vue',
            'angular': 'Angular',
            'next': 'Next.js',
            'python': 'Python',
            'django': 'Django',
            'flask': 'Flask',
            'javascript': 'JavaScript',
            'typescript': 'TypeScript',
            'node': 'Node.js',
            'express': 'Express',
            'api': 'API',
            'rest': 'REST',
            'graphql': 'GraphQL',
            'aws': 'AWS',
            'docker': 'Docker',
            'kubernetes': 'Kubernetes',
            'postgres': 'PostgreSQL',
            'mongodb': 'MongoDB',
            'redis': 'Redis',
            'ai': 'AI',
            'machine learning': 'ML',
            'automation': 'Automation'
        }

        for key, skill in skill_map.items():
            if key in caption_lower and skill not in skills:
                skills.append(skill)

        return skills


# Singleton instance
_instagram_discovery: Optional[InstagramDiscovery] = None


def get_instagram_discovery() -> InstagramDiscovery:
    """Get singleton Instagram Discovery instance"""
    global _instagram_discovery
    if _instagram_discovery is None:
        _instagram_discovery = InstagramDiscovery()
    return _instagram_discovery


# Quick test
if __name__ == "__main__":
    import asyncio

    async def test():
        discovery = get_instagram_discovery()
        opportunities = await discovery.discover_opportunities(
            hashtags=['hiring', 'developerneeded'],
            limit_per_hashtag=5
        )
        print(f"Found {len(opportunities)} opportunities")
        for opp in opportunities[:3]:
            print(f"  - {opp.get('title', '')[:50]}")

    asyncio.run(test())
