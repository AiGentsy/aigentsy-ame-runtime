"""
GITHUB ENHANCED API PACK: Authenticated GitHub Search

Priority: 90

Features:
- Authenticated API access (higher rate limits)
- Issues/discussions search for opportunities
- Bounty and hiring keyword detection
"""

import os
import logging
import hashlib
from typing import Dict, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def github_enhanced_search() -> List[Dict]:
    """
    Enhanced GitHub search with authentication

    Better rate limits and more features than unauthenticated
    """
    import httpx

    token = os.getenv('GITHUB_TOKEN')

    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'AiGentsy-Access-Panel'
    }
    if token:
        headers['Authorization'] = f'token {token}'

    all_items = []

    queries = [
        'hiring OR looking OR bounty in:title is:open',
        'paid OR freelance OR contract in:title is:open type:issue',
        'help wanted in:labels is:open'
    ]

    async with httpx.AsyncClient(timeout=15) as client:
        for query in queries:
            try:
                response = await client.get(
                    'https://api.github.com/search/issues',
                    params={
                        'q': query,
                        'sort': 'created',
                        'order': 'desc',
                        'per_page': 30
                    },
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    all_items.extend(items)
                    logger.info(f"GitHub enhanced: {len(items)} items for '{query[:30]}'")
                elif response.status_code == 403:
                    logger.warning("GitHub rate limit hit")
                    break
                else:
                    logger.warning(f"GitHub API error: {response.status_code}")

            except Exception as e:
                logger.error(f"GitHub search failed: {e}")

    return all_items


def github_normalizer(raw: dict) -> Dict:
    """Normalize GitHub API response"""

    issue_id = raw.get('id', '')
    title = raw.get('title', '')
    url = raw.get('html_url', '')
    body = raw.get('body', '') or ''
    user = raw.get('user', {})
    username = user.get('login', '')
    labels = [l.get('name', '') for l in raw.get('labels', [])]

    # Payment signals
    payment_keywords = ['bounty', 'paid', '$', 'reward', 'compensation']
    payment_proximity = 0.3
    text_lower = (title + ' ' + body).lower()
    for keyword in payment_keywords:
        if keyword in text_lower:
            payment_proximity = min(1.0, payment_proximity + 0.2)

    # Contactability (high - can comment directly)
    contactability = 0.8

    # Reputation (GitHub users are usually legit)
    reputation = 0.7

    return {
        'id': f"github_enhanced_{issue_id}",
        'platform': 'github_enhanced',
        'url': url,
        'canonical_url': url,
        'title': title[:200],
        'body': body[:1000],
        'discovered_at': datetime.now(timezone.utc).isoformat(),
        'value': 500 if 'bounty' in text_lower else 200,
        'payment_proximity': payment_proximity,
        'contactability': contactability,
        'poster_reputation': reputation,
        'type': 'opportunity',
        'source': 'api',
        'metadata': {
            'issue_id': issue_id,
            'username': username,
            'labels': labels
        }
    }


# Pack registration
GITHUB_ENHANCED_PACK = {
    'name': 'github_enhanced',
    'priority': 90,
    'api_func': github_enhanced_search,
    'normalizer': github_normalizer,
    'requires_auth': True,
    'has_api': True
}
