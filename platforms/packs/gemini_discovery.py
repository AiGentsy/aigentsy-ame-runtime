"""
GEMINI DISCOVERY PACK: Google AI Search Integration

Priority: 90

Features:
- Google AI with web search capabilities
- Multiple search queries
- Structured response extraction
"""

import os
import logging
import json
import hashlib
from typing import Dict, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def gemini_opportunity_search() -> List[Dict]:
    """
    Use Gemini (Google AI) for opportunity discovery

    Gemini has access to Google Search + AI reasoning
    """
    import httpx

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.debug("No Gemini key, skipping")
        return []

    searches = [
        "Search Google for job postings and freelance opportunities posted today with 'hiring' or 'looking for developer'",
        "Search Google for gig opportunities and project requests posted in the last 24 hours"
    ]

    all_opportunities = []

    async with httpx.AsyncClient(timeout=30) as client:
        for query in searches:
            try:
                response = await client.post(
                    f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}',
                    json={
                        'contents': [{
                            'parts': [{
                                'text': f"""{query}

Return ONLY a JSON array of opportunities:
[{{"title": "...", "url": "...", "platform": "...", "description": "..."}}]

No markdown, ONLY JSON array."""
                            }]
                        }],
                        'generationConfig': {
                            'maxOutputTokens': 4000,
                            'temperature': 0.2
                        }
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data['candidates'][0]['content']['parts'][0]['text']

                    opportunities = _parse_gemini_response(content)
                    all_opportunities.extend(opportunities)
                    logger.info(f"Gemini: {len(opportunities)} from '{query[:50]}'")

                else:
                    logger.warning(f"Gemini API error: {response.status_code}")

            except Exception as e:
                logger.error(f"Gemini search failed: {e}")

    return all_opportunities


def _parse_gemini_response(content: str) -> List[Dict]:
    """Parse Gemini's JSON response"""
    try:
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
        return []

    except json.JSONDecodeError as e:
        logger.warning(f"Gemini JSON parse failed: {e}")
        return []


def gemini_normalizer(raw: dict) -> Dict:
    """Normalize Gemini results"""

    title = raw.get('title', '')
    url = raw.get('url', '')
    description = raw.get('description', '')

    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

    return {
        'id': f"gemini_{url_hash}",
        'platform': 'gemini_discovery',
        'url': url,
        'canonical_url': url,
        'title': title[:200],
        'body': description,
        'discovered_at': datetime.now(timezone.utc).isoformat(),
        'value': 800,
        'payment_proximity': 0.5,
        'contactability': 0.6,
        'poster_reputation': 0.6,
        'type': 'opportunity',
        'source': 'api',
        'metadata': {
            'discovered_via': 'gemini_ai'
        }
    }


# Pack registration
GEMINI_PACK = {
    'name': 'gemini_discovery',
    'priority': 90,
    'api_func': gemini_opportunity_search,
    'normalizer': gemini_normalizer,
    'requires_auth': True,
    'has_api': True
}
