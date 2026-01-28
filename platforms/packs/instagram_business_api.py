"""
INSTAGRAM BUSINESS API PACK: Business Account Integration

Priority: 100 (highest - premium API access)

Features:
- Media search from business accounts
- Hashtag-based opportunity discovery
- Comment posting for outreach (100% delivery - no DM restrictions)
- Opportunity keyword filtering
- Engagement metrics
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Instagram Graph API config
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


# =============================================================================
# HASHTAG-BASED DISCOVERY
# =============================================================================

async def instagram_hashtag_discovery(
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
    import httpx

    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    business_id = os.getenv('INSTAGRAM_BUSINESS_ID')

    if not access_token or not business_id:
        logger.debug("Instagram hashtag discovery: No credentials")
        return []

    hashtags = hashtags or HIRING_HASHTAGS[:5]  # Limit to avoid rate limits
    opportunities = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for hashtag in hashtags:
            try:
                # Step 1: Get hashtag ID
                search_url = f"{GRAPH_API_BASE}/ig_hashtag_search"
                params = {
                    'user_id': business_id,
                    'q': hashtag,
                    'access_token': access_token
                }

                response = await client.get(search_url, params=params)
                if not response.is_success:
                    logger.warning(f"Hashtag search failed for #{hashtag}: {response.status_code}")
                    continue

                data = response.json()
                if not data.get('data'):
                    continue

                hashtag_id = data['data'][0]['id']

                # Step 2: Get recent media for hashtag
                media_url = f"{GRAPH_API_BASE}/{hashtag_id}/recent_media"
                params = {
                    'user_id': business_id,
                    'fields': 'id,caption,media_type,media_url,permalink,timestamp,children',
                    'access_token': access_token,
                    'limit': limit_per_hashtag
                }

                response = await client.get(media_url, params=params)
                if not response.is_success:
                    logger.warning(f"Media fetch failed for #{hashtag}: {response.status_code}")
                    continue

                posts = response.json().get('data', [])

                for post in posts:
                    if post.get('id') in seen_ids:
                        continue
                    seen_ids.add(post.get('id'))

                    # Filter for hiring-related posts
                    if _is_hiring_post(post):
                        opportunity = _parse_hashtag_opportunity(post, hashtag)
                        opportunities.append(opportunity)
                        logger.debug(f"Found Instagram opportunity: {opportunity.get('title', '')[:50]}")

            except Exception as e:
                logger.warning(f"Error searching hashtag #{hashtag}: {e}")
                continue

    logger.info(f"Instagram hashtag discovery: Found {len(opportunities)} opportunities")
    return opportunities


def _is_hiring_post(post: Dict) -> bool:
    """Check if post is about hiring/looking for help"""
    caption = (post.get('caption') or '').lower()
    if not caption:
        return False

    has_hiring = any(kw in caption for kw in HIRING_KEYWORDS)
    has_tech = any(kw in caption for kw in TECH_KEYWORDS)

    return has_hiring and has_tech


def _parse_hashtag_opportunity(post: Dict, source_hashtag: str) -> Dict:
    """Parse Instagram post into opportunity format"""
    caption = post.get('caption', '')
    post_id = post.get('id')
    permalink = post.get('permalink', f"https://instagram.com/p/{post_id}")

    return {
        'id': f"instagram_{post_id}",
        'platform': 'instagram',
        'post_id': post_id,
        'source': f"instagram_hashtag_{source_hashtag}",
        'title': _extract_title(caption),
        'description': caption[:500] if caption else '',
        'url': permalink,
        'permalink': permalink,
        'timestamp': post.get('timestamp'),
        'media_type': post.get('media_type'),
        'media_url': post.get('media_url'),
        'detected_skills': _extract_skills(caption),
        'contact': {
            'instagram_post_id': post_id,
            'platform': 'instagram'
        },
        'discovered_at': datetime.now(timezone.utc).isoformat()
    }


def _extract_title(caption: str) -> str:
    """Extract a title from the caption"""
    if not caption:
        return "Instagram Opportunity"

    lines = caption.split('\n')
    first_line = lines[0].strip() if lines else caption[:100]
    first_line = first_line.replace('#', '').strip()

    return first_line[:100] if first_line else "Instagram Opportunity"


def _extract_skills(caption: str) -> List[str]:
    """Extract tech skills mentioned in caption"""
    if not caption:
        return []

    caption_lower = caption.lower()
    skills = []

    skill_map = {
        'react': 'React', 'vue': 'Vue', 'angular': 'Angular',
        'next': 'Next.js', 'python': 'Python', 'django': 'Django',
        'flask': 'Flask', 'javascript': 'JavaScript', 'typescript': 'TypeScript',
        'node': 'Node.js', 'express': 'Express', 'api': 'API',
        'rest': 'REST', 'graphql': 'GraphQL', 'aws': 'AWS',
        'docker': 'Docker', 'kubernetes': 'Kubernetes',
        'postgres': 'PostgreSQL', 'mongodb': 'MongoDB', 'redis': 'Redis',
        'ai': 'AI', 'machine learning': 'ML', 'automation': 'Automation'
    }

    for key, skill in skill_map.items():
        if key in caption_lower and skill not in skills:
            skills.append(skill)

    return skills


# =============================================================================
# COMMENT POSTING (Outreach via public comments - 100% delivery)
# =============================================================================

async def post_instagram_comment(
    post_id: str,
    opportunity: Dict,
    client_room_url: str,
    pricing: Dict = None
) -> Dict:
    """
    Post a comment on an Instagram post.

    WHY COMMENTS (not DMs):
    - No follower restriction (100% delivery)
    - Public social proof
    - They can DM us back
    - API supports automated comments

    Args:
        post_id: Instagram media ID
        opportunity: Opportunity dict with title, etc.
        client_room_url: Link to client room
        pricing: Optional pricing info

    Returns:
        Result dict with success status
    """
    import httpx

    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')

    if not access_token:
        return {
            'success': False,
            'error': 'Instagram not configured (missing INSTAGRAM_ACCESS_TOKEN)'
        }

    # Create comment message
    message = _create_comment_message(opportunity, client_room_url, pricing)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{GRAPH_API_BASE}/{post_id}/comments"
            data = {
                'message': message,
                'access_token': access_token
            }

            response = await client.post(url, data=data)
            result = response.json()

            if result.get('id'):
                comment_id = result['id']
                logger.info(f"Instagram comment posted on {post_id}: {comment_id}")
                return {
                    'success': True,
                    'method': 'instagram_comment',
                    'comment_id': comment_id,
                    'post_id': post_id,
                    'platform': 'instagram'
                }
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                logger.warning(f"Instagram comment failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'details': result
                }

    except Exception as e:
        logger.error(f"Instagram comment error: {e}")
        return {'success': False, 'error': str(e)}


def _create_comment_message(
    opportunity: Dict,
    client_room_url: str,
    pricing: Dict = None
) -> str:
    """
    Create Instagram comment message.
    Instagram comments allow up to 2,200 characters.
    Keep it concise for better engagement.
    """
    title = opportunity.get('title', '')
    title_lower = title.lower()

    # Detect project type
    if 'react' in title_lower or 'frontend' in title_lower:
        project_type = 'React dev'
    elif 'backend' in title_lower or 'api' in title_lower:
        project_type = 'backend dev'
    elif 'python' in title_lower:
        project_type = 'Python dev'
    elif 'fullstack' in title_lower or 'full stack' in title_lower:
        project_type = 'fullstack dev'
    elif 'design' in title_lower or 'ui' in title_lower:
        project_type = 'design'
    elif 'app' in title_lower or 'mobile' in title_lower:
        project_type = 'app dev'
    else:
        project_type = 'dev'

    # Build message - professional, value-focused
    if pricing and pricing.get('our_price'):
        message = f"""We can help with this {project_type} work! AI-powered team delivers in hours.

Starting at ${pricing['our_price']:,.0f} - free preview first, pay only if you love it.

DM us to get started!"""
    else:
        message = f"""We can help with this {project_type} work! AI-powered team delivers in hours.

Free preview first - pay only if you're happy with the results.

DM us to get started!"""

    return message


async def reply_to_instagram_comment(comment_id: str, message: str) -> Dict:
    """Reply to a comment (for conversations)"""
    import httpx

    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')

    if not access_token:
        return {'success': False, 'error': 'Instagram not configured'}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{GRAPH_API_BASE}/{comment_id}/replies"
            data = {
                'message': message,
                'access_token': access_token
            }

            response = await client.post(url, data=data)
            result = response.json()

            if result.get('id'):
                return {
                    'success': True,
                    'reply_id': result['id'],
                    'parent_comment_id': comment_id
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', {}).get('message', 'Unknown error')
                }

    except Exception as e:
        logger.error(f"Instagram reply error: {e}")
        return {'success': False, 'error': str(e)}


# Pack registration
INSTAGRAM_PACK = {
    'name': 'instagram_business_api',
    'priority': 100,
    'api_func': instagram_business_search,
    'normalizer': instagram_normalizer,
    'requires_auth': True,
    'has_api': True,
    'hashtag_discovery': instagram_hashtag_discovery,
    'post_comment': post_instagram_comment,
    'reply_to_comment': reply_to_instagram_comment
}
