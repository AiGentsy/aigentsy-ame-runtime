"""
INSTAGRAM BUSINESS API PACK: Business Account Integration

Priority: 100 (highest - premium API access)

Features:
- Media search from business accounts
- Opportunity keyword filtering
- Engagement metrics
"""

import os
import logging
from typing import Dict, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def instagram_business_search() -> List[Dict]:
    """
    Instagram Business API - Find opportunities

    Searches recent media for opportunity keywords:
    - #hiring, #freelance, #collaboration
    - Comments asking for services
    """
    import httpx

    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    business_id = os.getenv('INSTAGRAM_BUSINESS_ID')

    if not access_token or not business_id:
        logger.debug("No Instagram credentials, skipping")
        return []

    opportunities = []

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            # Get recent media from business account feed
            response = await client.get(
                f'https://graph.instagram.com/{business_id}/media',
                params={
                    'fields': 'id,caption,comments_count,like_count,timestamp,permalink,media_url',
                    'access_token': access_token,
                    'limit': 50
                }
            )

            if response.status_code == 200:
                data = response.json()
                posts = data.get('data', [])

                # Filter for opportunity keywords
                opportunity_keywords = [
                    'hiring', 'freelance', 'collaboration', 'looking for',
                    'need help', 'opportunity', 'gig', 'contract', 'project'
                ]

                for post in posts:
                    caption = (post.get('caption') or '').lower()
                    if any(keyword in caption for keyword in opportunity_keywords):
                        opportunities.append(post)

                logger.info(f"Instagram: {len(opportunities)} opportunities from {len(posts)} posts")
            else:
                logger.warning(f"Instagram API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Instagram search failed: {e}")

    return opportunities


def instagram_normalizer(raw: dict) -> Dict:
    """Normalize Instagram API response"""

    post_id = raw.get('id', '')
    caption = raw.get('caption', '')
    permalink = raw.get('permalink', '')
    likes = raw.get('like_count', 0)
    comments = raw.get('comments_count', 0)

    # Calculate signals
    engagement = likes + comments * 2

    # Contactability (very high - can DM directly)
    contactability = 0.8
    if comments > 5:
        contactability += 0.1

    # Payment proximity
    payment_keywords = ['pay', 'budget', 'rate', 'compensation', 'price', '$']
    payment_proximity = 0.4
    caption_lower = (caption or '').lower()
    for keyword in payment_keywords:
        if keyword in caption_lower:
            payment_proximity = min(1.0, payment_proximity + 0.15)

    # Reputation (based on engagement)
    reputation = 0.5
    if engagement > 100:
        reputation += 0.3
    if comments > 10:
        reputation += 0.2

    return {
        'id': f"instagram_{post_id}",
        'platform': 'instagram_business_api',
        'url': permalink or f"https://instagram.com/p/{post_id}",
        'canonical_url': permalink or f"https://instagram.com/p/{post_id}",
        'title': (caption or '')[:200],
        'body': caption or '',
        'discovered_at': datetime.now(timezone.utc).isoformat(),
        'value': 800,
        'payment_proximity': min(1.0, payment_proximity),
        'contactability': min(1.0, contactability),
        'poster_reputation': min(1.0, reputation),
        'type': 'opportunity',
        'source': 'api',
        'metadata': {
            'post_id': post_id,
            'likes': likes,
            'comments': comments,
            'engagement': engagement
        }
    }


# Pack registration
INSTAGRAM_PACK = {
    'name': 'instagram_business_api',
    'priority': 100,
    'api_func': instagram_business_search,
    'normalizer': instagram_normalizer,
    'requires_auth': True,
    'has_api': True
}
