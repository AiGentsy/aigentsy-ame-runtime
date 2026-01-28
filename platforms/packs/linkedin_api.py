"""
LINKEDIN API PACK: Professional B2B Outreach + Content

Priority: 100 (highest - premium B2B channel)

Features:
- Job post discovery
- Hiring post discovery (decision makers)
- Direct messaging (1st degree connections)
- Connection requests with notes
- InMail (Premium)
- Post comments (100% delivery - no connection needed)
- Content posting (articles, posts)
- Image/document sharing

Why LinkedIn:
- Higher intent buyers (businesses, not hobbyists)
- Higher budgets ($500-5k vs $100-1k)
- Decision makers (CTOs, founders, hiring managers)
- Professional context = serious projects
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# LinkedIn API config
LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

# Discovery keywords
HIRING_KEYWORDS = [
    'hiring', 'looking for', 'need a', 'seeking', 'wanted',
    'developer needed', 'engineer needed', 'urgently need',
    'help needed', 'project help', 'freelancer needed',
    'who can build', 'contract work', 'remote position'
]

TECH_KEYWORDS = [
    'developer', 'engineer', 'programmer', 'coder',
    'react', 'python', 'javascript', 'typescript', 'node',
    'api', 'backend', 'frontend', 'fullstack', 'full stack',
    'automation', 'ai', 'ml', 'data', 'devops', 'cloud'
]

JOB_SEARCH_KEYWORDS = [
    'React developer', 'Python developer', 'Backend engineer',
    'Full stack developer', 'API developer', 'Frontend engineer',
    'Node.js developer', 'JavaScript developer', 'DevOps engineer'
]


# =============================================================================
# DISCOVERY - Find Opportunities
# =============================================================================

async def linkedin_jobs_api(
    keywords: List[str] = None,
    location: str = "Remote",
    posted_within_days: int = 7,
    limit: int = 50
) -> List[Dict]:
    """
    LinkedIn Jobs API - Primary job discovery.

    Args:
        keywords: Job search keywords
        location: Location filter
        posted_within_days: Only jobs posted within X days
        limit: Max results

    Returns:
        List of job opportunity dicts
    """
    import httpx

    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        logger.debug("No LinkedIn access token, skipping job discovery")
        return []

    keywords = keywords or JOB_SEARCH_KEYWORDS[:5]
    opportunities = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for keyword in keywords:
            try:
                response = await client.get(
                    f"{LINKEDIN_API_BASE}/jobSearch",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "X-Restli-Protocol-Version": "2.0.0"
                    },
                    params={
                        "keywords": keyword,
                        "location": location,
                        "f_TPR": f"r{posted_within_days * 86400}",
                        "count": limit // len(keywords)
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get('elements', [])

                    for job in jobs:
                        job_id = job.get('id')
                        if job_id in seen_ids:
                            continue
                        seen_ids.add(job_id)

                        if _is_suitable_job(job):
                            opportunity = _parse_job_opportunity(job, keyword)
                            opportunities.append(opportunity)

                elif response.status_code == 401:
                    logger.warning("LinkedIn token expired or invalid")
                    break
                else:
                    logger.warning(f"LinkedIn Jobs API error: {response.status_code}")

            except Exception as e:
                logger.warning(f"LinkedIn job search error for '{keyword}': {e}")
                continue

    logger.info(f"LinkedIn job discovery: Found {len(opportunities)} opportunities")
    return opportunities


async def linkedin_post_discovery(
    search_queries: List[str] = None,
    limit: int = 50
) -> List[Dict]:
    """
    Discover opportunities from LinkedIn posts ("Who's hiring" posts).

    These are better than job posts - direct contact with decision makers.

    Args:
        search_queries: Post search queries
        limit: Max results

    Returns:
        List of opportunity dicts
    """
    import httpx

    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        logger.debug("No LinkedIn access token, skipping post discovery")
        return []

    default_queries = [
        "who's hiring developer",
        "looking for React developer",
        "need backend engineer",
        "seeking full stack developer",
        "hiring python developer",
        "contract developer needed"
    ]
    search_queries = search_queries or default_queries[:3]
    opportunities = []
    seen_ids = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for query in search_queries:
            try:
                response = await client.get(
                    f"{LINKEDIN_API_BASE}/search",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "X-Restli-Protocol-Version": "2.0.0"
                    },
                    params={
                        "q": "content",
                        "keywords": query,
                        "count": limit // len(search_queries),
                        "sortBy": "RELEVANCE"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('elements', [])

                    for post in posts:
                        post_id = post.get('id')
                        if post_id in seen_ids:
                            continue
                        seen_ids.add(post_id)

                        if _is_hiring_post(post):
                            opportunity = _parse_post_opportunity(post, query)
                            opportunities.append(opportunity)

                else:
                    logger.warning(f"LinkedIn post search error: {response.status_code}")

            except Exception as e:
                logger.warning(f"LinkedIn post search error for '{query}': {e}")
                continue

    logger.info(f"LinkedIn post discovery: Found {len(opportunities)} opportunities")
    return opportunities


def _is_suitable_job(job: Dict) -> bool:
    """Filter for suitable job opportunities."""
    title = (job.get('title') or '').lower()
    description = (job.get('description') or '').lower()
    return any(kw in title or kw in description for kw in TECH_KEYWORDS)


def _is_hiring_post(post: Dict) -> bool:
    """Check if post is about hiring."""
    text = (post.get('commentary') or post.get('text') or '').lower()
    if not text:
        return False
    has_hiring = any(kw in text for kw in HIRING_KEYWORDS)
    has_tech = any(kw in text for kw in TECH_KEYWORDS)
    return has_hiring and has_tech


def _parse_job_opportunity(job: Dict, source_keyword: str) -> Dict:
    """Parse LinkedIn job into opportunity format."""
    job_id = job.get('id', '')
    title = job.get('title', '')
    company = job.get('companyDetails', {}).get('company', {}).get('name', '')
    location = job.get('formattedLocation', '')
    description = job.get('description', {}).get('text', '')

    return {
        'id': f"linkedin_job_{job_id}",
        'platform': 'linkedin',
        'type': 'job_post',
        'source': f"linkedin_job_{source_keyword.replace(' ', '_')}",
        'job_id': job_id,
        'title': title,
        'company': company,
        'location': location,
        'description': description[:1000] if description else '',
        'url': f"https://linkedin.com/jobs/view/{job_id}",
        'apply_url': job.get('applyMethod', {}).get('companyApplyUrl'),
        'posted_at': job.get('listedAt'),
        'detected_skills': _extract_skills(f"{title} {description}"),
        'contact': {
            'platform': 'linkedin',
            'job_id': job_id,
            'company': company
        },
        'discovered_at': datetime.now(timezone.utc).isoformat()
    }


def _parse_post_opportunity(post: Dict, source_query: str) -> Dict:
    """Parse LinkedIn post into opportunity format."""
    post_id = post.get('id', '')
    text = post.get('commentary') or post.get('text') or ''
    author = post.get('author', {})
    author_name = author.get('name', '')
    author_url = author.get('url', '')

    lines = text.split('\n')
    title = lines[0][:100] if lines else text[:100]

    return {
        'id': f"linkedin_post_{post_id}",
        'platform': 'linkedin',
        'type': 'hiring_post',
        'source': f"linkedin_post_{source_query.replace(' ', '_')}",
        'post_id': post_id,
        'title': title,
        'description': text[:1000] if text else '',
        'url': f"https://linkedin.com/feed/update/{post_id}",
        'author': author_name,
        'author_url': author_url,
        'posted_at': post.get('created', {}).get('time'),
        'detected_skills': _extract_skills(text),
        'contact': {
            'platform': 'linkedin',
            'post_id': post_id,
            'author_url': author_url,
            'method': 'comment_or_dm'
        },
        'discovered_at': datetime.now(timezone.utc).isoformat()
    }


def _extract_skills(text: str) -> List[str]:
    """Extract tech skills from text."""
    if not text:
        return []
    text_lower = text.lower()
    skills = []
    skill_map = {
        'react': 'React', 'vue': 'Vue', 'angular': 'Angular',
        'next': 'Next.js', 'python': 'Python', 'django': 'Django',
        'flask': 'Flask', 'javascript': 'JavaScript', 'typescript': 'TypeScript',
        'node': 'Node.js', 'express': 'Express', 'api': 'API',
        'rest': 'REST', 'graphql': 'GraphQL', 'aws': 'AWS',
        'docker': 'Docker', 'kubernetes': 'Kubernetes',
        'postgres': 'PostgreSQL', 'mongodb': 'MongoDB', 'redis': 'Redis',
        'ai': 'AI', 'machine learning': 'ML', 'automation': 'Automation',
        'devops': 'DevOps', 'cloud': 'Cloud', 'fullstack': 'Full Stack'
    }
    for key, skill in skill_map.items():
        if key in text_lower and skill not in skills:
            skills.append(skill)
    return skills


def linkedin_normalizer(raw: dict) -> Dict:
    """Normalize LinkedIn API response to standard opportunity format."""
    opp_type = raw.get('type', 'job_post')
    title = raw.get('title', '')
    description = raw.get('description', '')
    company = raw.get('company', '')
    author = raw.get('author', '')

    reputation = 0.6 + (0.2 if company else 0) + (0.1 if author else 0)

    payment_keywords = ['budget', 'rate', 'compensation', 'salary', 'paid', '$']
    payment_proximity = 0.5
    text_lower = f"{title} {description}".lower()
    for keyword in payment_keywords:
        if keyword in text_lower:
            payment_proximity = min(1.0, payment_proximity + 0.1)

    contactability = 0.7 + (0.2 if raw.get('apply_url') else 0)

    return {
        'id': raw.get('id', f"linkedin_{datetime.now().timestamp()}"),
        'platform': 'linkedin',
        'url': raw.get('url', ''),
        'canonical_url': raw.get('url', ''),
        'title': title[:200],
        'body': description,
        'discovered_at': raw.get('discovered_at', datetime.now(timezone.utc).isoformat()),
        'value': 1000,
        'payment_proximity': min(1.0, payment_proximity),
        'contactability': min(1.0, contactability),
        'poster_reputation': min(1.0, reputation),
        'type': 'opportunity',
        'source': raw.get('source', 'linkedin'),
        'metadata': {
            'opportunity_type': opp_type,
            'company': company,
            'author': author,
            'skills': raw.get('detected_skills', [])
        }
    }


# =============================================================================
# MESSAGING - Outreach Methods
# =============================================================================

async def send_linkedin_message(
    recipient_urn: str,
    opportunity: Dict,
    client_room_url: str,
    pricing: Dict = None
) -> Dict:
    """
    Send a direct message to a LinkedIn connection (1st degree).

    Args:
        recipient_urn: LinkedIn member URN (urn:li:person:xxx)
        opportunity: Opportunity dict
        client_room_url: Client room URL
        pricing: Pricing info

    Returns:
        Result dict
    """
    import httpx

    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        return {'success': False, 'error': 'LinkedIn not configured'}

    message = _create_dm_message(opportunity, client_room_url, pricing)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{LINKEDIN_API_BASE}/messages",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0"
                },
                json={
                    "recipients": [recipient_urn],
                    "subject": f"Re: {opportunity.get('title', 'Your Project')[:50]}",
                    "body": message
                }
            )

            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"LinkedIn message sent to {recipient_urn}")
                return {
                    'success': True,
                    'method': 'linkedin_dm',
                    'message_id': data.get('id'),
                    'platform': 'linkedin'
                }
            else:
                error = response.json().get('message', response.text)
                logger.warning(f"LinkedIn DM failed: {response.status_code} - {error}")
                return {'success': False, 'error': error, 'status_code': response.status_code}

    except Exception as e:
        logger.error(f"LinkedIn message error: {e}")
        return {'success': False, 'error': str(e)}


async def send_connection_request(
    recipient_urn: str,
    opportunity: Dict,
    pricing: Dict = None
) -> Dict:
    """
    Send a connection request with a personalized note (300 char limit).
    """
    import httpx

    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        return {'success': False, 'error': 'LinkedIn not configured'}

    note = _create_connection_note(opportunity, pricing)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{LINKEDIN_API_BASE}/invitations",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0"
                },
                json={"invitee": recipient_urn, "message": note}
            )

            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"LinkedIn connection request sent to {recipient_urn}")
                return {
                    'success': True,
                    'method': 'linkedin_connection_request',
                    'invitation_id': data.get('id'),
                    'platform': 'linkedin'
                }
            else:
                return {'success': False, 'error': response.json().get('message', 'Connection request failed')}

    except Exception as e:
        logger.error(f"LinkedIn connection request error: {e}")
        return {'success': False, 'error': str(e)}


async def post_linkedin_comment(
    post_urn: str,
    opportunity: Dict,
    pricing: Dict = None
) -> Dict:
    """
    Comment on a LinkedIn post - 100% delivery, no connection needed.
    """
    import httpx

    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        return {'success': False, 'error': 'LinkedIn not configured'}

    message = _create_comment_message(opportunity, pricing)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{LINKEDIN_API_BASE}/socialActions/{post_urn}/comments",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0"
                },
                json={
                    "actor": os.getenv('LINKEDIN_PERSON_URN', ''),
                    "message": {"text": message}
                }
            )

            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"LinkedIn comment posted on {post_urn}")
                return {
                    'success': True,
                    'method': 'linkedin_comment',
                    'comment_id': data.get('id'),
                    'post_urn': post_urn,
                    'platform': 'linkedin'
                }
            else:
                return {'success': False, 'error': response.json().get('message', 'Comment failed')}

    except Exception as e:
        logger.error(f"LinkedIn comment error: {e}")
        return {'success': False, 'error': str(e)}


def _detect_project_type(title: str) -> str:
    """Detect project type from title."""
    title_lower = title.lower()
    type_map = {
        'react': 'React', 'vue': 'Vue', 'angular': 'Angular',
        'backend': 'backend', 'api': 'API', 'frontend': 'frontend',
        'fullstack': 'full-stack', 'full stack': 'full-stack',
        'python': 'Python', 'node': 'Node.js', 'javascript': 'JavaScript',
        'mobile': 'mobile', 'ios': 'iOS', 'android': 'Android',
        'devops': 'DevOps', 'cloud': 'cloud', 'data': 'data'
    }
    for key, value in type_map.items():
        if key in title_lower:
            return value
    return 'dev'


def _create_dm_message(opportunity: Dict, client_room_url: str, pricing: Dict = None) -> str:
    """Create LinkedIn DM message (billionaire-calm voice)."""
    title = opportunity.get('title', 'your project')
    project_type = _detect_project_type(title)
    name = opportunity.get('author', '').split()[0] if opportunity.get('author') else 'there'

    if pricing and pricing.get('our_price'):
        return f"""Hey {name}—AiGentsy here.

Saw your post about {title[:50]}. We can help.

What we do:
- First preview in ~30 min
- ${pricing['our_price']:,} (market rate ~${pricing.get('market_rate', pricing['our_price'] * 2):,})
- Pay only if you love it

We ship {project_type} work daily. World-class quality, minutes-fast.

Want a free preview?

{client_room_url}

—AiGentsy"""
    else:
        return f"""Hey {name}—AiGentsy here.

Saw your post about {title[:50]}. We can help.

We're a {project_type} team that ships in minutes, not days. ~50% under market.

First preview free—pay only if it lands.

{client_room_url}

—AiGentsy"""


def _create_connection_note(opportunity: Dict, pricing: Dict = None) -> str:
    """Create connection request note (300 char limit, billionaire-calm)."""
    title = opportunity.get('title', 'your project')[:40]
    project_type = _detect_project_type(title)

    if pricing and pricing.get('our_price'):
        note = f"Hi—saw your post about {title}. We ship {project_type} work in minutes at ~50% under market (${pricing['our_price']:,}). Would love to connect."
    else:
        note = f"Hi—saw your post about {title}. We ship {project_type} work in minutes at ~50% under market. Would love to connect."

    return note[:300]


def _create_comment_message(opportunity: Dict, pricing: Dict = None) -> str:
    """Create LinkedIn comment message (billionaire-calm voice)."""
    title = opportunity.get('title', '')
    project_type = _detect_project_type(title)

    if pricing and pricing.get('our_price'):
        return f"""Sharp {project_type} help, right now.

First preview in ~30 min. ${pricing['our_price']:,} (market ~${pricing.get('market_rate', pricing['our_price'] * 2):,}).

Pay only if you love it. DM me or check my profile.

—AiGentsy"""
    else:
        return f"""Sharp {project_type} help, right now.

World-class quality, minutes-fast, ~50% under market.

Free first preview—pay only if it lands. DM me or check my profile.

—AiGentsy"""


# =============================================================================
# CONTENT POSTING - Brand Building
# =============================================================================

async def post_linkedin_content(
    text: str,
    image_url: str = None,
    article_url: str = None
) -> Dict:
    """
    Post content to LinkedIn (up to 3,000 characters).
    """
    import httpx

    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    person_urn = os.getenv('LINKEDIN_PERSON_URN')

    if not access_token or not person_urn:
        return {'success': False, 'error': 'LinkedIn not fully configured'}

    text = text[:3000]

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            share_content = {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE"
            }

            if image_url:
                upload_result = await _upload_linkedin_image(client, access_token, person_urn, image_url)
                if upload_result.get('success'):
                    share_content["shareMediaCategory"] = "IMAGE"
                    share_content["media"] = [{"status": "READY", "media": upload_result['asset']}]
            elif article_url:
                share_content["shareMediaCategory"] = "ARTICLE"
                share_content["media"] = [{"status": "READY", "originalUrl": article_url}]

            response = await client.post(
                f"{LINKEDIN_API_BASE}/ugcPosts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0"
                },
                json={
                    "author": person_urn,
                    "lifecycleState": "PUBLISHED",
                    "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
                    "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
                }
            )

            if response.status_code in [200, 201]:
                data = response.json()
                post_id = data.get('id', '')
                logger.info(f"LinkedIn post created: {post_id}")
                return {
                    'success': True,
                    'post_id': post_id,
                    'platform': 'linkedin',
                    'url': f"https://linkedin.com/feed/update/{post_id}"
                }
            else:
                error = response.json().get('message', response.text)
                logger.warning(f"LinkedIn post failed: {response.status_code} - {error}")
                return {'success': False, 'error': error, 'status_code': response.status_code}

    except Exception as e:
        logger.error(f"LinkedIn post error: {e}")
        return {'success': False, 'error': str(e)}


async def _upload_linkedin_image(client, access_token: str, person_urn: str, image_url: str) -> Dict:
    """Upload image to LinkedIn for post attachment."""
    try:
        register_response = await client.post(
            f"{LINKEDIN_API_BASE}/assets?action=registerUpload",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": person_urn,
                    "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
                }
            }
        )

        if not register_response.is_success:
            return {'success': False, 'error': 'Failed to register upload'}

        data = register_response.json()
        upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset = data['value']['asset']

        img_response = await client.get(image_url)
        if not img_response.is_success:
            return {'success': False, 'error': 'Failed to download image'}

        upload_response = await client.put(
            upload_url,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "image/png"},
            content=img_response.content
        )

        if upload_response.is_success:
            return {'success': True, 'asset': asset}
        return {'success': False, 'error': 'Failed to upload image'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


# =============================================================================
# CONTENT TEMPLATES (billionaire-calm voice)
# =============================================================================

def generate_linkedin_portfolio_post(project_data: Dict) -> str:
    """Generate a portfolio/success story post for LinkedIn."""
    project_type = project_data.get('project_type', 'project')
    time = project_data.get('time', '45 minutes')
    price = project_data.get('price', 1200)
    market_rate = project_data.get('market_rate', price * 2)

    return f"""Project completed in {time}.

Client needed: {project_type}
We delivered: Production-ready, fully documented

Timeline:
• Brief received → First preview in 30 min
• Client approved → Full delivery same hour
• Final sign-off → Same day

Results:
• Cost: ${price:,} (market rate ~${market_rate:,})
• Time: Minutes, not days
• Quality: Approved first review

This is what happens when you remove delays, overhead, and back-and-forth.

World-class work. Minutes-fast. ~50% under market.

DM me if you need something shipped.

—AiGentsy

#development #tech #startup #automation"""


def generate_linkedin_case_study_post(case_data: Dict) -> str:
    """Generate a case study post for LinkedIn."""
    before = case_data.get('before', 'Manual 3-hour process')
    after = case_data.get('after', '2-click automation')
    result = case_data.get('result', '90% time saved')
    time = case_data.get('time', '45 minutes')
    price = case_data.get('price', 1200)

    return f"""Case study: {before} → {after}

The problem:
{before}. Eating hours every day. Frustrating. Error-prone.

The solution:
Custom automation. Built in {time}. Works every time.

The result:
{result}. No more manual work. No more errors.

Cost: ${price:,} (market would charge 2-3x)
Time: {time} (agencies quote 2-3 weeks)

We don't sell. We show.

First preview free. Pay only if it lands.

DM me or check my profile.

—AiGentsy

#automation #efficiency #productivity #tech"""


def generate_linkedin_tip_post(tip: str) -> str:
    """Generate a tech tip post for LinkedIn."""
    return f"""{tip}

This is one of those things that separates good code from great code.

We build systems like this daily. World-class quality, minutes-fast, ~50% under market.

Want something built right? First preview free.

DM me.

—AiGentsy

#development #coding #softwareengineering #tech"""


def generate_linkedin_engagement_post(domain: str = "dev") -> str:
    """Generate an engagement post for LinkedIn."""
    posts = {
        "dev": """What's the biggest time sink in your development workflow?

Curious what people would automate first if they could.

We've built some wild automation. Happy to share ideas.

Drop a comment.""",
        "startup": """Hot take: Most software projects could ship in hours, not weeks.

The delays come from:
• Meetings about meetings
• Scope creep
• Context switching
• Waiting for feedback

What if you could just... ship?

Agree or disagree?""",
        "hiring": """Companies are still hiring developers the old way.

• Post job → Wait 2 weeks → Review 100 resumes
• Interview 10 people → Wait another week
• Hire someone → 2-week notice period
• Onboard → 1-2 months to productivity

Total time: 2-3 months

Or:

• Brief us → 30 min to first preview
• Like it? → Full delivery same day
• Done.

The future of work is different.

What do you think?"""
    }
    return posts.get(domain, posts["dev"])


# =============================================================================
# PACK REGISTRATION
# =============================================================================

LINKEDIN_PACK = {
    'name': 'linkedin_api',
    'priority': 100,
    'api_func': linkedin_jobs_api,
    'normalizer': linkedin_normalizer,
    'requires_auth': True,
    'has_api': True,
    # Discovery
    'job_discovery': linkedin_jobs_api,
    'post_discovery': linkedin_post_discovery,
    # Messaging
    'send_message': send_linkedin_message,
    'send_connection_request': send_connection_request,
    'post_comment': post_linkedin_comment,
    # Content
    'post_content': post_linkedin_content,
    # Templates
    'generate_portfolio_post': generate_linkedin_portfolio_post,
    'generate_case_study_post': generate_linkedin_case_study_post,
    'generate_tip_post': generate_linkedin_tip_post,
    'generate_engagement_post': generate_linkedin_engagement_post
}
