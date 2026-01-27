"""
AI-POWERED CONTACT EXTRACTION
==============================
Uses OpenRouter (Claude/GPT-4) and Gemini to extract contact info from text.

Extracts:
- Email addresses
- Phone numbers (normalized to E.164)
- Twitter/X handles
- LinkedIn profiles
- Discord usernames
- Website contact pages

Author: AiGentsy
Updated: January 2026
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional

import httpx

logger = logging.getLogger(__name__)


def normalize_phone_number(phone: str) -> Optional[str]:
    """
    Normalize phone number to E.164 format (+1XXXXXXXXXX).

    Returns None if the number is obviously invalid.
    """
    if not phone:
        return None

    # Remove all non-digit characters except leading +
    digits = re.sub(r'[^\d]', '', phone)

    # Must have at least 10 digits (US number)
    if len(digits) < 10:
        return None

    # Must not be more than 15 digits (international max)
    if len(digits) > 15:
        return None

    # Filter out obviously fake numbers
    fake_patterns = [
        r'^0{5,}',           # All zeros
        r'^1{10,}',          # All ones
        r'^123456',          # Sequential
        r'^555\d{7}$',       # 555 numbers (fictional)
        r'^000',             # Starts with 000
    ]
    for pattern in fake_patterns:
        if re.match(pattern, digits):
            return None

    # Normalize to E.164 (US default)
    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+{digits}"
    else:
        # International number
        return f"+{digits}"


def validate_email(email: str) -> Optional[str]:
    """
    Validate and normalize email address.
    Returns None if invalid.
    """
    if not email:
        return None

    email = email.lower().strip()

    # Basic email pattern
    if not re.match(r'^[\w.+-]+@[\w-]+\.[\w.-]+$', email):
        return None

    # Filter out example/test emails
    invalid_domains = [
        'example.com', 'example.org', 'test.com', 'test.org',
        'email.com', 'domain.com', 'your-email.com', 'youremail.com',
        'placeholder.com', 'sample.com', 'fake.com'
    ]
    domain = email.split('@')[1] if '@' in email else ''
    if domain in invalid_domains:
        return None

    # Filter out noreply addresses
    if any(x in email for x in ['noreply', 'no-reply', 'donotreply', 'do-not-reply']):
        return None

    return email


async def extract_contact_with_openrouter(
    text: str,
    url: str = "",
    model: str = "anthropic/claude-3-haiku"
) -> Dict[str, Any]:
    """
    Use OpenRouter with Claude/GPT to extract contact info from text.

    Args:
        text: The text to analyze (post body, page content, etc.)
        url: Optional URL for context
        model: OpenRouter model to use

    Returns:
        Dict with extracted contact info or empty dict
    """
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        logger.debug("OpenRouter API key not configured")
        return {}

    if not text or len(text.strip()) < 20:
        return {}

    # Truncate to save tokens
    text = text[:3000]

    prompt = f"""Extract ALL contact information from this text.

Text:
{text}

{f'URL: {url}' if url else ''}

Return ONLY a JSON object with any contact info found:
{{
    "email": "actual@email.com or null",
    "phone": "+1XXXXXXXXXX or null",
    "twitter": "@handle or null",
    "linkedin": "linkedin.com/in/profile or null",
    "discord": "username#1234 or null",
    "website": "contact page URL or null"
}}

Rules:
- Only include REAL contact info, not examples or placeholders
- Phone must be a real phone number with area code
- Email must be a real email, not example@example.com
- Twitter must be a real @handle
- Return null for fields not found

JSON only:"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://aigentsy.com",
                    "X-Title": "AiGentsy Contact Extraction"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                    "max_tokens": 300
                }
            )

            if response.status_code != 200:
                logger.debug(f"OpenRouter error: {response.status_code}")
                return {}

            data = response.json()
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

            # Parse JSON from response
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if not json_match:
                return {}

            try:
                contact_data = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                return {}

            # Build structured contact
            contact = {}

            # Email (highest priority)
            email = validate_email(contact_data.get('email'))
            if email:
                contact['email'] = email
                contact['preferred_outreach'] = 'email'

            # Phone
            phone = normalize_phone_number(contact_data.get('phone', ''))
            if phone:
                contact['phone'] = phone
                if 'preferred_outreach' not in contact:
                    contact['preferred_outreach'] = 'sms'

            # Twitter
            twitter = contact_data.get('twitter')
            if twitter and twitter != 'null':
                handle = str(twitter).lstrip('@').lower()
                if handle and handle not in ['twitter', 'x', 'com', 'null', 'none']:
                    contact['twitter_handle'] = handle
                    if 'preferred_outreach' not in contact:
                        contact['preferred_outreach'] = 'twitter_dm'

            # LinkedIn
            linkedin = contact_data.get('linkedin')
            if linkedin and linkedin != 'null' and 'linkedin.com' in str(linkedin):
                # Extract profile ID
                match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', str(linkedin))
                if match:
                    contact['linkedin_id'] = match.group(1)
                    if 'preferred_outreach' not in contact:
                        contact['preferred_outreach'] = 'linkedin_message'

            # Discord
            discord = contact_data.get('discord')
            if discord and discord != 'null' and '#' in str(discord):
                contact['discord'] = str(discord)

            if contact:
                contact['extraction_source'] = 'ai_openrouter'
                logger.info(f"AI extracted: {list(contact.keys())}")

            return contact

    except httpx.TimeoutException:
        logger.debug("OpenRouter request timed out")
        return {}
    except Exception as e:
        logger.debug(f"OpenRouter extraction error: {e}")
        return {}


async def extract_contact_with_gemini(
    text: str,
    url: str = ""
) -> Dict[str, Any]:
    """
    Use Gemini to extract contact info from text.

    Falls back option when OpenRouter is unavailable.
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.debug("Gemini API key not configured")
        return {}

    if not text or len(text.strip()) < 20:
        return {}

    # Truncate to save tokens
    text = text[:3000]

    prompt = f"""Extract contact information from this text and return as JSON.

Text:
{text}

Return JSON with: email, phone, twitter, linkedin (or null if not found).
Only include REAL contact info, not examples."""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0,
                        "maxOutputTokens": 300
                    }
                }
            )

            if response.status_code != 200:
                logger.debug(f"Gemini error: {response.status_code}")
                return {}

            data = response.json()
            content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')

            # Parse JSON
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if not json_match:
                return {}

            try:
                contact_data = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                return {}

            # Build structured contact (same as OpenRouter)
            contact = {}

            email = validate_email(contact_data.get('email'))
            if email:
                contact['email'] = email
                contact['preferred_outreach'] = 'email'

            phone = normalize_phone_number(contact_data.get('phone', ''))
            if phone:
                contact['phone'] = phone
                if 'preferred_outreach' not in contact:
                    contact['preferred_outreach'] = 'sms'

            twitter = contact_data.get('twitter')
            if twitter and twitter != 'null':
                handle = str(twitter).lstrip('@').lower()
                if handle and handle not in ['twitter', 'x', 'com', 'null', 'none']:
                    contact['twitter_handle'] = handle
                    if 'preferred_outreach' not in contact:
                        contact['preferred_outreach'] = 'twitter_dm'

            if contact:
                contact['extraction_source'] = 'ai_gemini'
                logger.info(f"Gemini extracted: {list(contact.keys())}")

            return contact

    except Exception as e:
        logger.debug(f"Gemini extraction error: {e}")
        return {}


async def extract_contact_with_ai(
    text: str,
    url: str = ""
) -> Dict[str, Any]:
    """
    Extract contact using best available AI.

    Tries OpenRouter first (Claude), then Gemini as fallback.

    Args:
        text: Text to analyze
        url: Optional URL for context

    Returns:
        Dict with extracted contact info
    """
    # Try OpenRouter first (Claude is better at extraction)
    contact = await extract_contact_with_openrouter(text, url)
    if contact:
        return contact

    # Fallback to Gemini
    contact = await extract_contact_with_gemini(text, url)
    return contact


# Export for use in discovery
__all__ = [
    'extract_contact_with_ai',
    'extract_contact_with_openrouter',
    'extract_contact_with_gemini',
    'normalize_phone_number',
    'validate_email'
]
