"""
CONTENT ENGINE: Proactive Brand Building for Twitter/Instagram

Purpose: Generate and post branded content to build AiGentsy presence
and attract inbound leads (not just respond to discovered opportunities).

Content Types:
1. Portfolio showcases - "Just shipped X in Y minutes"
2. Case studies - Before/after with proof
3. Tech tips - Value-first content
4. Engagement questions - "What's your biggest dev pain point?"
5. Social proof - Reviews, results, metrics

Voice: billionaire-calm
- Short verbs, no exclamation points
- Proof-forward, not hype
- "We'll show you, not sell you"
"""

import os
import logging
import random
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# =============================================================================
# CONTENT TEMPLATES (billionaire-calm voice)
# =============================================================================

PORTFOLIO_TEMPLATES = [
    # Format: (template, requires_data)
    (
        "Just shipped a {project_type} in {time}. Client paid ${price:,}. Market rate: ~${market_rate:,}.\n\nWorld-class quality. Minutes-fast. ~50% under market.\n\nDM \"GO\" if you need {skill} help.",
        ["project_type", "time", "price", "market_rate", "skill"]
    ),
    (
        "{project_type} done.\n\n⏱️ {time}\n💰 ${price:,} (market ~${market_rate:,})\n\nPay only if you love it.\n\n@AiGentsy",
        ["project_type", "time", "price", "market_rate"]
    ),
    (
        "Client needed a {project_type}. Urgent.\n\nFirst preview: {time}\nFinal delivery: same day\nPrice: ~50% under market\n\nWe ship. DM \"GO\"",
        ["project_type", "time"]
    ),
]

CASE_STUDY_TEMPLATES = [
    (
        "Before: {before}\nAfter: {after}\n\nTime: {time}\nCost: ${price:,}\n\nWe don't sell. We show.\n\nDM for your free preview.",
        ["before", "after", "time", "price"]
    ),
    (
        "Case study:\n\n→ Problem: {problem}\n→ Solution: {solution}\n→ Result: {result}\n\nFirst preview free. Pay only if it lands.\n\n@AiGentsy",
        ["problem", "solution", "result"]
    ),
]

TECH_TIP_TEMPLATES = [
    (
        "{tip}\n\nWant us to build it for you? First preview free.\n\n@AiGentsy",
        ["tip"]
    ),
    (
        "Pro tip: {tip}\n\nWe ship these daily. ~50% under market.\n\nDM \"GO\" for a free preview.",
        ["tip"]
    ),
]

ENGAGEMENT_TEMPLATES = [
    (
        "What's the biggest time sink in your {domain} workflow?\n\nWe've automated some wild stuff. Curious what you'd automate first.",
        ["domain"]
    ),
    (
        "Hot take: Most {domain} projects could ship in hours, not weeks.\n\nAgree or disagree?",
        ["domain"]
    ),
    (
        "What {domain} task do you wish you could just hand off?\n\nAsking for... research purposes.",
        ["domain"]
    ),
]

SOCIAL_PROOF_TEMPLATES = [
    (
        "\"{quote}\"\n\n— {attribution}\n\nWe ship world-class work in minutes. DM \"GO\" for a free preview.",
        ["quote", "attribution"]
    ),
    (
        "Another happy client:\n\n\"{quote}\"\n\nFirst preview free. Pay only if you love it.\n\n@AiGentsy",
        ["quote"]
    ),
]

# Sample data for generating content
SAMPLE_PROJECTS = [
    {"project_type": "React dashboard", "time": "47 minutes", "price": 1200, "market_rate": 2400, "skill": "React"},
    {"project_type": "Python automation script", "time": "32 minutes", "price": 800, "market_rate": 1600, "skill": "Python"},
    {"project_type": "landing page", "time": "28 minutes", "price": 600, "market_rate": 1200, "skill": "frontend"},
    {"project_type": "REST API", "time": "51 minutes", "price": 1500, "market_rate": 3000, "skill": "backend"},
    {"project_type": "data pipeline", "time": "43 minutes", "price": 1100, "market_rate": 2200, "skill": "data"},
    {"project_type": "Stripe integration", "time": "38 minutes", "price": 900, "market_rate": 1800, "skill": "payments"},
    {"project_type": "email automation", "time": "25 minutes", "price": 500, "market_rate": 1000, "skill": "automation"},
]

SAMPLE_CASE_STUDIES = [
    {
        "before": "Manual 3-hour data entry process",
        "after": "2-click automation",
        "problem": "Manual data entry eating 3 hours daily",
        "solution": "Python automation with smart validation",
        "result": "90% time saved. Zero errors.",
        "time": "45 minutes",
        "price": 1200
    },
    {
        "before": "Clunky legacy dashboard",
        "after": "Modern React UI",
        "problem": "Slow, outdated internal dashboard",
        "solution": "React rebuild with real-time updates",
        "result": "Team productivity up 40%",
        "time": "2 hours",
        "price": 2400
    },
]

TECH_TIPS = [
    "Use React Query instead of useEffect for data fetching. Trust me.",
    "Your API should return pagination metadata. Every time.",
    "Type your environment variables. Future you will thank present you.",
    "Write tests for the code that scares you most.",
    "Premature optimization is bad. But so is premature abstraction.",
    "If your deploy takes more than 5 minutes, something's wrong.",
    "Rate limiting isn't optional. It's survival.",
]

DOMAINS = ["dev", "startup", "tech", "engineering", "product"]

SAMPLE_QUOTES = [
    {"quote": "Shipped faster than I expected. Quality was excellent.", "attribution": "startup founder"},
    {"quote": "Finally, developers who actually deliver.", "attribution": "agency owner"},
    {"quote": "The preview sold me. No BS, just results.", "attribution": "product manager"},
    {"quote": "50% under my usual agency. Same quality. Faster.", "attribution": "CTO"},
]


# =============================================================================
# CONTENT GENERATION
# =============================================================================

def generate_portfolio_tweet(data: Dict = None) -> str:
    """Generate a portfolio showcase tweet."""
    data = data or random.choice(SAMPLE_PROJECTS)
    template, required = random.choice(PORTFOLIO_TEMPLATES)

    # Check we have required data
    for field in required:
        if field not in data:
            data = random.choice(SAMPLE_PROJECTS)
            break

    return template.format(**data)


def generate_case_study_tweet(data: Dict = None) -> str:
    """Generate a case study tweet."""
    data = data or random.choice(SAMPLE_CASE_STUDIES)
    template, required = random.choice(CASE_STUDY_TEMPLATES)

    for field in required:
        if field not in data:
            data = random.choice(SAMPLE_CASE_STUDIES)
            break

    return template.format(**data)


def generate_tech_tip_tweet() -> str:
    """Generate a tech tip tweet."""
    template, _ = random.choice(TECH_TIP_TEMPLATES)
    tip = random.choice(TECH_TIPS)
    return template.format(tip=tip)


def generate_engagement_tweet() -> str:
    """Generate an engagement question tweet."""
    template, _ = random.choice(ENGAGEMENT_TEMPLATES)
    domain = random.choice(DOMAINS)
    return template.format(domain=domain)


def generate_social_proof_tweet() -> str:
    """Generate a social proof tweet."""
    template, _ = random.choice(SOCIAL_PROOF_TEMPLATES)
    quote_data = random.choice(SAMPLE_QUOTES)
    return template.format(**quote_data)


def generate_content(content_type: str = None, data: Dict = None) -> Dict:
    """
    Generate branded content for posting.

    Args:
        content_type: Type of content (portfolio, case_study, tip, engagement, proof)
        data: Optional custom data for the content

    Returns:
        Dict with content and metadata
    """
    content_types = {
        'portfolio': generate_portfolio_tweet,
        'case_study': generate_case_study_tweet,
        'tip': generate_tech_tip_tweet,
        'engagement': generate_engagement_tweet,
        'proof': generate_social_proof_tweet,
    }

    if content_type and content_type in content_types:
        generator = content_types[content_type]
    else:
        # Random selection with weighted distribution
        weights = [0.35, 0.20, 0.15, 0.15, 0.15]  # More portfolio posts
        content_type = random.choices(list(content_types.keys()), weights=weights)[0]
        generator = content_types[content_type]

    if data:
        content = generator(data)
    else:
        content = generator()

    return {
        'content': content,
        'type': content_type,
        'platform': 'twitter',  # Can extend for Instagram
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'char_count': len(content)
    }


def generate_thread(topic: str = "portfolio") -> List[str]:
    """
    Generate a Twitter thread (multiple connected tweets).

    Args:
        topic: Thread topic (portfolio, case_study, tips)

    Returns:
        List of tweet texts
    """
    if topic == "portfolio":
        project = random.choice(SAMPLE_PROJECTS)
        return [
            f"Just shipped a {project['project_type']} for a client. Here's the breakdown 🧵",
            f"The ask: Build a {project['project_type']} with specific requirements.\n\nTime to first preview: {project['time']}\nFinal delivery: same day",
            f"The result:\n✓ Production-ready\n✓ Fully documented\n✓ Client approved\n\nPrice: ${project['price']:,} (market rate: ~${project['market_rate']:,})",
            "We don't do proposals. We ship a preview first.\n\nPay only if you love it.\n\nDM \"GO\" for your free preview.\n\n@AiGentsy",
        ]

    elif topic == "case_study":
        case = random.choice(SAMPLE_CASE_STUDIES)
        return [
            f"Case study: How we turned a {case['before'].lower()} into {case['after'].lower()} 🧵",
            f"The problem:\n{case['problem']}\n\nThis was eating hours every day.",
            f"The solution:\n{case['solution']}\n\nTime to build: {case['time']}",
            f"The result:\n{case['result']}\n\nCost: ${case['price']:,} (market would charge 2x)",
            "First preview free. Pay only if it lands.\n\nDM \"GO\" @AiGentsy",
        ]

    elif topic == "tips":
        tips = random.sample(TECH_TIPS, 4)
        return [
            "Quick dev tips from shipping 100+ projects 🧵",
            f"1. {tips[0]}",
            f"2. {tips[1]}",
            f"3. {tips[2]}",
            f"4. {tips[3]}",
            "Want these implemented in your project?\n\nFirst preview free. ~50% under market.\n\nDM \"GO\" @AiGentsy",
        ]

    return []


# =============================================================================
# POSTING FUNCTIONS
# =============================================================================

async def post_brand_content(
    content_type: str = None,
    data: Dict = None,
    platform: str = "twitter"
) -> Dict:
    """
    Generate and post branded content.

    Args:
        content_type: Type of content to generate
        data: Optional custom data
        platform: Target platform (twitter, instagram)

    Returns:
        Result dict with success status
    """
    # Generate content
    generated = generate_content(content_type, data)
    content = generated['content']

    if platform == "twitter":
        from platforms.packs.twitter_v2_api import post_tweet
        result = await post_tweet(content)
        result['content'] = generated
        return result

    elif platform == "instagram":
        # Instagram requires an image - would need image generation
        logger.warning("Instagram content posting requires image URL")
        return {
            'success': False,
            'error': 'Instagram posting requires image_url',
            'content': generated
        }

    return {'success': False, 'error': f'Unknown platform: {platform}'}


async def post_brand_thread(topic: str = "portfolio") -> Dict:
    """
    Generate and post a branded Twitter thread.

    Args:
        topic: Thread topic

    Returns:
        Result dict with all tweet IDs
    """
    from platforms.packs.twitter_v2_api import post_thread

    tweets = generate_thread(topic)
    if not tweets:
        return {'success': False, 'error': f'No thread template for topic: {topic}'}

    result = await post_thread(tweets)
    result['topic'] = topic
    result['content'] = tweets
    return result


# =============================================================================
# INSTAGRAM-SPECIFIC CONTENT (with AI image generation)
# =============================================================================

def generate_instagram_caption(content_type: str = "portfolio", data: Dict = None) -> str:
    """
    Generate an Instagram caption (longer format, with hashtags).

    Args:
        content_type: Type of content
        data: Optional custom data

    Returns:
        Caption text with hashtags
    """
    # Get base content
    generated = generate_content(content_type, data)
    content = generated['content']

    # Add hashtags for Instagram
    hashtags = "\n\n#development #tech #coding #startup #freelance #developer #programming #webdev #software #ai #automation"

    return f"{content}{hashtags}"


async def generate_and_post_instagram(
    content_type: str = "portfolio",
    data: Dict = None,
    generate_image: bool = True
) -> Dict:
    """
    Generate content + image and post to Instagram.

    Uses Stability AI or Runway to generate branded images.

    Args:
        content_type: Type of content (portfolio, case_study, tip)
        data: Optional custom data
        generate_image: Whether to generate AI image

    Returns:
        Result dict with post details
    """
    from integration.image_generation import (
        generate_portfolio_image,
        generate_case_study_image,
        generate_tech_tip_image,
        save_image_to_storage
    )
    from platforms.packs.instagram_business_api import post_instagram_content

    # Generate caption
    caption = generate_instagram_caption(content_type, data)

    # Generate image based on content type
    image_result = None
    if generate_image:
        if content_type == "portfolio":
            project = data or random.choice(SAMPLE_PROJECTS)
            image_result = await generate_portfolio_image(
                project.get('project_type', 'software'),
                style="dashboard"
            )
        elif content_type == "case_study":
            case = data or random.choice(SAMPLE_CASE_STUDIES)
            image_result = await generate_case_study_image(
                case.get('before', 'manual process'),
                case.get('after', 'automated solution')
            )
        elif content_type == "tip":
            tip = random.choice(TECH_TIPS)
            image_result = await generate_tech_tip_image(tip[:50])
        else:
            # Default to portfolio style
            image_result = await generate_portfolio_image("software development")

        if not image_result.get('success'):
            logger.warning(f"Image generation failed: {image_result.get('error')}")
            return {
                'success': False,
                'error': f"Image generation failed: {image_result.get('error')}",
                'caption': caption
            }

        # Save/upload image to get public URL
        storage_result = await save_image_to_storage(image_result)
        if not storage_result.get('success'):
            return {
                'success': False,
                'error': 'Failed to store image',
                'image_result': image_result
            }

        image_url = storage_result.get('url')

        # Note: Instagram Graph API requires publicly accessible URLs
        # Data URIs won't work - need cloud storage (S3, GCS, etc.)
        if image_url.startswith('data:'):
            return {
                'success': False,
                'error': 'Instagram requires public image URL. Need cloud storage configured.',
                'caption': caption,
                'image_generated': True,
                'note': 'Set up S3/GCS upload in save_image_to_storage()'
            }

        # Post to Instagram
        result = await post_instagram_content(image_url, caption)
        result['image_url'] = image_url
        result['content_type'] = content_type
        return result

    return {
        'success': False,
        'error': 'No image URL provided and generate_image=False',
        'caption': caption
    }


async def post_instagram_portfolio(image_url: str, project_data: Dict = None) -> Dict:
    """
    Post a portfolio showcase to Instagram with existing image URL.

    Args:
        image_url: Public URL to portfolio image/screenshot
        project_data: Optional project data

    Returns:
        Result dict
    """
    from platforms.packs.instagram_business_api import post_instagram_content

    caption = generate_instagram_caption("portfolio", project_data)
    return await post_instagram_content(image_url, caption)


# =============================================================================
# CONTENT SCHEDULING (simple implementation)
# =============================================================================

# Content queue for scheduled posts
_content_queue: List[Dict] = []


def queue_content(content: Dict, scheduled_for: str = None) -> Dict:
    """
    Add content to the posting queue.

    Args:
        content: Content dict with 'content' and 'platform'
        scheduled_for: Optional ISO timestamp for scheduling

    Returns:
        Queue entry
    """
    entry = {
        'id': f"content_{len(_content_queue)}_{datetime.now().timestamp()}",
        'content': content,
        'scheduled_for': scheduled_for or datetime.now(timezone.utc).isoformat(),
        'status': 'queued',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    _content_queue.append(entry)
    return entry


def get_content_queue() -> List[Dict]:
    """Get all queued content."""
    return _content_queue


async def process_content_queue() -> Dict:
    """
    Process and post all due content in the queue.

    Returns:
        Results dict
    """
    now = datetime.now(timezone.utc)
    results = []

    for entry in _content_queue:
        if entry['status'] != 'queued':
            continue

        scheduled = datetime.fromisoformat(entry['scheduled_for'].replace('Z', '+00:00'))
        if scheduled > now:
            continue

        # Post the content
        content_data = entry['content']
        result = await post_brand_content(
            content_type=content_data.get('type'),
            data=content_data.get('data'),
            platform=content_data.get('platform', 'twitter')
        )

        entry['status'] = 'posted' if result.get('success') else 'failed'
        entry['result'] = result
        entry['posted_at'] = datetime.now(timezone.utc).isoformat()
        results.append(entry)

    return {
        'processed': len(results),
        'results': results
    }


# =============================================================================
# ENGAGEMENT HELPERS
# =============================================================================

async def engage_with_mention(
    tweet_id: str,
    username: str,
    mention_text: str
) -> Dict:
    """
    Engage with a Twitter mention proactively.

    Args:
        tweet_id: ID of the mention tweet
        username: Username who mentioned us
        mention_text: Text of the mention

    Returns:
        Result dict
    """
    from platforms.packs.twitter_v2_api import post_tweet

    # Generate contextual response
    text_lower = mention_text.lower()

    if any(word in text_lower for word in ['thanks', 'thank', 'awesome', 'great', 'love']):
        response = f"@{username} Glad to help. Let us know if you need anything else."
    elif any(word in text_lower for word in ['help', 'need', 'looking', 'want']):
        response = f"@{username} We can ship a preview in ~30 min. DM \"GO\" and we'll get started."
    elif any(word in text_lower for word in ['price', 'cost', 'how much', 'rate']):
        response = f"@{username} ~50% under market. First preview is free—pay only if you love it. DM \"GO\" to start."
    else:
        response = f"@{username} We're here. DM \"GO\" if you need anything shipped."

    return await post_tweet(response, reply_to=tweet_id)


# =============================================================================
# LINKEDIN-SPECIFIC CONTENT
# =============================================================================

def generate_linkedin_post(content_type: str = "portfolio", data: Dict = None) -> str:
    """
    Generate a LinkedIn post (longer format, professional tone).

    Args:
        content_type: Type of content (portfolio, case_study, tip, engagement)
        data: Optional custom data

    Returns:
        Post text
    """
    from platforms.packs.linkedin_api import (
        generate_linkedin_portfolio_post,
        generate_linkedin_case_study_post,
        generate_linkedin_tip_post,
        generate_linkedin_engagement_post
    )

    if content_type == "portfolio":
        project = data or random.choice(SAMPLE_PROJECTS)
        return generate_linkedin_portfolio_post(project)

    elif content_type == "case_study":
        case = data or random.choice(SAMPLE_CASE_STUDIES)
        return generate_linkedin_case_study_post(case)

    elif content_type == "tip":
        tip = random.choice(TECH_TIPS)
        return generate_linkedin_tip_post(tip)

    elif content_type == "engagement":
        domain = random.choice(DOMAINS)
        return generate_linkedin_engagement_post(domain)

    else:
        # Default to portfolio
        project = random.choice(SAMPLE_PROJECTS)
        return generate_linkedin_portfolio_post(project)


async def post_linkedin_brand_content(
    content_type: str = "portfolio",
    data: Dict = None,
    image_url: str = None
) -> Dict:
    """
    Generate and post branded content to LinkedIn.

    Args:
        content_type: Type of content
        data: Optional custom data
        image_url: Optional image URL to attach

    Returns:
        Result dict
    """
    from platforms.packs.linkedin_pack import post_linkedin_content

    text = generate_linkedin_post(content_type, data)

    result = await post_linkedin_content(text, image_url=image_url)
    result['content_type'] = content_type
    result['text'] = text
    return result


async def post_brand_content_all_platforms(
    content_type: str = "portfolio",
    data: Dict = None
) -> Dict:
    """
    Post branded content to all platforms (Twitter, Instagram, LinkedIn).

    Args:
        content_type: Type of content
        data: Optional custom data

    Returns:
        Results dict with status per platform
    """
    results = {
        'twitter': None,
        'instagram': None,
        'linkedin': None
    }

    # Twitter
    try:
        results['twitter'] = await post_brand_content(content_type, data, platform='twitter')
    except Exception as e:
        results['twitter'] = {'success': False, 'error': str(e)}

    # LinkedIn (longer format)
    try:
        results['linkedin'] = await post_linkedin_brand_content(content_type, data)
    except Exception as e:
        results['linkedin'] = {'success': False, 'error': str(e)}

    # Instagram (requires image - skip if no image generation)
    # Note: Would need image generation for Instagram
    results['instagram'] = {
        'success': False,
        'skipped': True,
        'reason': 'Instagram requires image - use generate_and_post_instagram()'
    }

    return {
        'success': any(r.get('success') for r in results.values() if r),
        'results': results
    }


# Export for use in other modules
__all__ = [
    'generate_content',
    'generate_thread',
    'post_brand_content',
    'post_brand_thread',
    'generate_instagram_caption',
    'post_instagram_portfolio',
    'generate_and_post_instagram',
    'queue_content',
    'get_content_queue',
    'process_content_queue',
    'engage_with_mention',
    # LinkedIn
    'generate_linkedin_post',
    'post_linkedin_brand_content',
    'post_brand_content_all_platforms',
]
