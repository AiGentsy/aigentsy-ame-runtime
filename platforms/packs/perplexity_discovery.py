"""
PERPLEXITY DISCOVERY PACK: Internet-Wide Search

Priority: 95 (GAME CHANGER - searches ENTIRE internet)

Features:
- Real-time web search via Perplexity AI
- Multiple verticals (jobs, freelance, projects, creative)
- Structured JSON response extraction
- Can replace 50+ scraping packs with one API call
"""

import os
import logging
import json
import hashlib
from typing import Dict, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def perplexity_opportunity_search() -> List[Dict]:
    """
    GAME CHANGER: Use Perplexity to search THE ENTIRE INTERNET

    Instead of scraping 111 sites, ask Perplexity to search everything!

    Perplexity has real-time web access and returns structured results.
    This could replace 50+ scraping packs while being faster & more reliable!
    """
    import httpx

    api_key = os.getenv('PERPLEXITY_API_KEY')
    if not api_key:
        logger.debug("No Perplexity key, skipping")
        return []

    # Queries covering different verticals
    searches = [
        "Find recent job postings for software developers posted today on Reddit, Twitter, HackerNews, and tech forums",
        "Find freelance opportunities for designers and developers posted in the last 24 hours",
        "Find project collaboration requests and gig opportunities posted today on startup communities",
        "Find contract work and remote job opportunities posted today with budget information"
    ]

    all_opportunities = []

    async with httpx.AsyncClient(timeout=60) as client:
        for query in searches:
            try:
                response = await client.post(
                    'https://api.perplexity.ai/chat/completions',
                    json={
                        'model': 'sonar',
                        'messages': [{
                            'role': 'user',
                            'content': f"""{query}

Return ONLY a JSON array of opportunities with this exact format:
[
  {{
    "title": "job/gig title",
    "url": "direct URL to posting",
    "platform": "source platform name",
    "description": "brief description",
    "payment_mentioned": true or false,
    "contact_available": true or false
  }}
]

No markdown fences, no explanation, ONLY the JSON array."""
                        }],
                        'max_tokens': 4000,
                        'temperature': 0.2,
                        'search_recency_filter': 'day'
                    },
                    headers={'Authorization': f'Bearer {api_key}'}
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']

                    # Parse JSON response
                    opportunities = _parse_perplexity_response(content)
                    all_opportunities.extend(opportunities)
                    logger.info(f"Perplexity: {len(opportunities)} from '{query[:50]}'")

                else:
                    logger.warning(f"Perplexity API error: {response.status_code}")

            except Exception as e:
                logger.error(f"Perplexity search failed: {e}")

    logger.info(f"Perplexity TOTAL: {len(all_opportunities)} opportunities from internet-wide search")

    return all_opportunities


def _parse_perplexity_response(content: str) -> List[Dict]:
    """Parse Perplexity's JSON response"""
    try:
        # Clean markdown fences
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]

        opportunities = json.loads(content.strip())

        if isinstance(opportunities, list):
            return opportunities
        else:
            logger.warning("Perplexity returned non-list")
            return []

    except json.JSONDecodeError as e:
        logger.warning(f"Perplexity JSON parse failed: {e}")
        return []


def perplexity_normalizer(raw: dict) -> Dict:
    """Normalize Perplexity discovery results"""

    title = raw.get('title', '')
    url = raw.get('url', '')
    description = raw.get('description', '')
    source_platform = raw.get('platform', 'unknown')
    payment_mentioned = raw.get('payment_mentioned', False)
    contact_available = raw.get('contact_available', False)

    # Generate stable ID from URL
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    # Signals
    payment_proximity = 0.7 if payment_mentioned else 0.4
    contactability = 0.8 if contact_available else 0.5

    return {
        'id': f"perplexity_{url_hash}",
        'platform': 'perplexity_discovery',
        'url': url,
        'canonical_url': url,
        'title': title[:200],
        'body': description,
        'discovered_at': datetime.now(timezone.utc).isoformat(),
        'value': 1000,
        'payment_proximity': payment_proximity,
        'contactability': contactability,
        'poster_reputation': 0.6,
        'type': 'opportunity',
        'source': 'api',
        'metadata': {
            'source_platform': source_platform,
            'discovered_via': 'perplexity_ai',
            'search_engine': 'internet_wide'
        }
    }


# Pack registration
PERPLEXITY_PACK = {
    'name': 'perplexity_discovery',
    'priority': 95,
    'api_func': perplexity_opportunity_search,
    'normalizer': perplexity_normalizer,
    'requires_auth': True,
    'has_api': True
}
