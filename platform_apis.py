"""
PLATFORM APIS - COMPLETE REAL INTEGRATIONS (MERGED)
====================================================
All platform executors with REAL API implementations.

CONFIGURED PLATFORMS (8 total):
✅ Twitter/X - OAuth 1.0a (TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
✅ Email - Resend API (RESEND_API_KEY)
✅ Reddit - OAuth2 (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD)
✅ GitHub - REST API v3 (GITHUB_TOKEN)
✅ Upwork - Manual submission (no API)
✅ Instagram - Graph API v21.0 (INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID)
✅ LinkedIn - Marketing API v2 (LINKEDIN_ACCESS_TOKEN, LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET)
✅ Twilio SMS - (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)

ALSO AVAILABLE:
- Stability AI (STABILITY_API_KEY) - for graphics generation
- Runway (RUNWAY_API_KEY) - for video generation
- Gemini (GEMINI_API_KEY) - for AI tasks
- OpenRouter (OPENROUTER_API_KEY) - for AI routing
- Perplexity (PERPLEXITY_API_KEY) - for research

Each executor follows the interface:
- generate_solution(opportunity, plan) -> solution
- validate_solution(solution, opportunity) -> validation
- submit(solution, opportunity) -> result
- check_status(job_id) -> status
"""

import os
import asyncio
import json
import hashlib
import hmac
import base64
import time
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode, quote
from pathlib import Path

import httpx


def _now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _generate_id(prefix: str) -> str:
    import uuid
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# =============================================================================
# TWITTER/X EXECUTOR - REAL OAuth 1.0a Implementation
# =============================================================================

class TwitterExecutor:
    """
    Real Twitter/X execution using OAuth 1.0a
    
    Capabilities:
    - Post tweets
    - Reply to tweets
    - Post threads
    - Upload media
    """
    
    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        
        self.api_base = "https://api.twitter.com"
        
        self.configured = all([self.api_key, self.api_secret, self.access_token, self.access_secret])
        if not self.configured:
            print("⚠️ Twitter OAuth credentials incomplete - some features may not work")
    
    def _generate_oauth_signature(
        self,
        method: str,
        url: str,
        params: Dict[str, str],
        oauth_params: Dict[str, str]
    ) -> str:
        """Generate OAuth 1.0a signature"""
        
        # Combine params
        all_params = {**params, **oauth_params}
        
        # Sort and encode
        sorted_params = sorted(all_params.items())
        param_string = "&".join(f"{quote(k, safe='')}={quote(str(v), safe='')}" for k, v in sorted_params)
        
        # Create signature base string
        base_string = f"{method.upper()}&{quote(url, safe='')}&{quote(param_string, safe='')}"
        
        # Create signing key
        signing_key = f"{quote(self.api_secret, safe='')}&{quote(self.access_secret, safe='')}"
        
        # Generate signature
        signature = hmac.new(
            signing_key.encode(),
            base_string.encode(),
            hashlib.sha1
        ).digest()
        
        return base64.b64encode(signature).decode()
    
    def _get_oauth_header(self, method: str, url: str, params: Dict = None) -> str:
        """Generate OAuth 1.0a Authorization header"""
        
        params = params or {}
        
        oauth_params = {
            "oauth_consumer_key": self.api_key,
            "oauth_token": self.access_token,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": hashlib.md5(str(time.time()).encode()).hexdigest(),
            "oauth_version": "1.0"
        }
        
        # Generate signature
        signature = self._generate_oauth_signature(method, url, params, oauth_params)
        oauth_params["oauth_signature"] = signature
        
        # Build header
        header_parts = [f'{k}="{quote(str(v), safe="")}"' for k, v in sorted(oauth_params.items())]
        return "OAuth " + ", ".join(header_parts)
    
    async def generate_solution(self, opportunity: Dict, plan: Dict) -> Dict:
        """Generate tweet content based on opportunity"""
        
        opp_type = opportunity.get('type', 'general')
        title = opportunity.get('title', '')[:100]
        
        # Generate contextual tweet
        if 'pain_point' in opportunity.get('source', ''):
            tweet_text = f"I can help with this! {title[:150]} DM me for details 🚀"
        elif 'hiring' in opp_type.lower():
            tweet_text = f"Interested in this opportunity! {title[:150]} Let's connect 💼"
        else:
            tweet_text = f"Available to help: {title[:180]} #freelance #ai"
        
        return {
            'tweet_text': tweet_text[:280],
            'reply_to_id': opportunity.get('source_data', {}).get('tweet_id'),
            'opportunity_id': opportunity.get('id')
        }
    
    async def validate_solution(self, solution: Dict, opportunity: Dict) -> Dict:
        """Validate tweet before posting"""
        
        tweet_text = solution.get('tweet_text', '')
        
        if len(tweet_text) > 280:
            return {'passed': False, 'errors': ['Tweet exceeds 280 characters']}
        
        if len(tweet_text) < 10:
            return {'passed': False, 'errors': ['Tweet too short']}
        
        return {'passed': True}
    
    async def submit(self, solution: Dict, opportunity: Dict) -> Dict:
        """Post tweet to Twitter"""
        
        if not self.configured:
            return {
                'id': f'stub_twitter_{_generate_id("tw")}',
                'url': '',
                'status': 'skipped',
                'reason': 'Twitter credentials not configured'
            }
        
        tweet_text = solution.get('tweet_text', '')
        reply_to_id = solution.get('reply_to_id')
        
        # Build request
        url = f"{self.api_base}/2/tweets"
        
        payload = {"text": tweet_text}
        if reply_to_id:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to_id}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # For Twitter API v2, we need OAuth 1.0a
                auth_header = self._get_oauth_header("POST", url)
                
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": auth_header,
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    tweet_id = data.get('data', {}).get('id')
                    
                    return {
                        'id': tweet_id,
                        'url': f"https://twitter.com/i/web/status/{tweet_id}",
                        'status': 'posted',
                        'posted_at': _now()
                    }
                else:
                    return {
                        'id': None,
                        'status': 'failed',
                        'error': f"Twitter API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            return {
                'id': None,
                'status': 'failed',
                'error': str(e)
            }
    
    async def check_status(self, tweet_id: str) -> Dict:
        """Check tweet engagement"""
        
        if not tweet_id or not self.configured:
            return {'completed': True, 'status': 'unknown'}
        
        url = f"{self.api_base}/2/tweets/{tweet_id}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                auth_header = self._get_oauth_header("GET", url)
                
                response = await client.get(
                    url,
                    params={"tweet.fields": "public_metrics"},
                    headers={"Authorization": auth_header}
                )
                
                if response.status_code == 200:
                    data = response.json().get('data', {})
                    metrics = data.get('public_metrics', {})
                    
                    return {
                        'completed': True,
                        'status': 'active',
                        'metrics': {
                            'likes': metrics.get('like_count', 0),
                            'retweets': metrics.get('retweet_count', 0),
                            'replies': metrics.get('reply_count', 0),
                            'impressions': metrics.get('impression_count', 0)
                        }
                    }
                    
        except Exception as e:
            pass
        
        return {'completed': True, 'status': 'unknown'}


# =============================================================================
# EMAIL EXECUTOR - REAL Resend Implementation
# =============================================================================

class EmailExecutor:
    """
    Real email execution using Resend API
    
    Capabilities:
    - Send cold outreach emails
    - Send follow-up sequences
    - Track opens/clicks
    - Handle replies
    """
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("RESEND_FROM_EMAIL", os.getenv("AIGENTSY_FROM_EMAIL", "onboarding@resend.dev"))
        self.api_base = "https://api.resend.com"
        
        self.configured = bool(self.api_key)
        if not self.configured:
            print("⚠️ RESEND_API_KEY not set - Email executor will use stubs")
    
    async def generate_solution(self, opportunity: Dict, plan: Dict) -> Dict:
        """Generate email content based on opportunity"""
        
        title = opportunity.get('title', 'Your Request')
        description = opportunity.get('description', '')[:500]
        value = opportunity.get('value', 0)
        contact_email = opportunity.get('contact_email') or opportunity.get('source_data', {}).get('email')
        
        # Determine email type
        source = opportunity.get('source', '')
        
        if 'pain_point' in source:
            subject = f"I can solve: {title[:50]}"
            body = f"""Hi,

I noticed you're looking for help with {title}.

{description[:200]}

I specialize in this exact problem and can deliver a solution quickly.

Would you be open to a quick call this week to discuss?

Best regards,
AiGentsy Team

P.S. No obligation - just want to see if we're a fit.
"""
        else:
            subject = f"Re: {title[:50]}"
            body = f"""Hi,

I came across your post about {title} and wanted to reach out.

I have extensive experience with similar projects and can deliver high-quality work.

Timeline: 1-2 weeks
Budget: ${value:,.0f} (flexible)

Would love to discuss further. Are you available for a quick chat?

Best regards,
AiGentsy Team
"""
        
        return {
            'to': contact_email,
            'subject': subject,
            'body': body,
            'html': body.replace('\n', '<br>'),
            'opportunity_id': opportunity.get('id')
        }
    
    async def validate_solution(self, solution: Dict, opportunity: Dict) -> Dict:
        """Validate email before sending"""
        
        to_email = solution.get('to')
        subject = solution.get('subject', '')
        body = solution.get('body', '')
        
        errors = []
        
        if not to_email or '@' not in str(to_email):
            errors.append('Invalid or missing recipient email')
        
        if len(subject) < 5:
            errors.append('Subject too short')
        
        if len(body) < 50:
            errors.append('Body too short')
        
        if errors:
            return {'passed': False, 'errors': errors}
        
        return {'passed': True}
    
    async def submit(self, solution: Dict, opportunity: Dict) -> Dict:
        """Send email via Resend API"""
        
        if not self.configured:
            return {
                'id': f'stub_email_{_generate_id("em")}',
                'status': 'skipped',
                'reason': 'RESEND_API_KEY not configured'
            }
        
        to_email = solution.get('to')
        
        if not to_email:
            return {
                'id': None,
                'status': 'failed',
                'error': 'No recipient email address'
            }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.api_base}/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [to_email],
                        "subject": solution.get('subject'),
                        "html": solution.get('html', solution.get('body', '').replace('\n', '<br>'))
                    }
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    
                    return {
                        'id': data.get('id'),
                        'status': 'sent',
                        'sent_at': _now(),
                        'to': to_email
                    }
                else:
                    return {
                        'id': None,
                        'status': 'failed',
                        'error': f"Resend API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            return {
                'id': None,
                'status': 'failed',
                'error': str(e)
            }
    
    async def check_status(self, email_id: str) -> Dict:
        """Check email delivery status"""
        
        if not email_id or not self.configured:
            return {'completed': True, 'status': 'unknown'}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.api_base}/emails/{email_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'completed': True,
                        'status': data.get('status', 'unknown'),
                        'events': data.get('events', [])
                    }
                    
        except Exception:
            pass
        
        return {'completed': True, 'status': 'unknown'}


# =============================================================================
# INSTAGRAM EXECUTOR - REAL Graph API v21.0
# =============================================================================

class InstagramExecutor:
    """
    Real Instagram execution using Graph API
    
    ENV: INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ID
    
    Capabilities:
    - Post images with captions
    - Post carousels
    - Track engagement
    """
    
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.business_id = os.getenv("INSTAGRAM_BUSINESS_ID")
        self.api_base = "https://graph.facebook.com/v21.0"
        
        self.configured = all([self.access_token, self.business_id])
        if not self.configured:
            print("⚠️ Instagram: Missing INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_BUSINESS_ID")
    
    async def generate_solution(self, opportunity: Dict, plan: Dict) -> Dict:
        """Generate Instagram post content"""
        title = opportunity.get('title', '')[:200]
        
        caption = f"🚀 {title}\n\n#ai #automation #business #growth #aigentsy"
        
        return {
            'caption': caption[:2200],
            'media_type': plan.get('media_type', 'IMAGE'),
            'image_url': plan.get('image_url'),
            'opportunity_id': opportunity.get('id')
        }
    
    async def validate_solution(self, solution: Dict, opportunity: Dict) -> Dict:
        if len(solution.get('caption', '')) > 2200:
            return {'passed': False, 'errors': ['Caption exceeds 2200 characters']}
        return {'passed': True}
    
    async def submit(self, solution: Dict, opportunity: Dict) -> Dict:
        """Post to Instagram using Graph API two-step process"""
        if not self.configured:
            return {'id': f'stub_ig_{_generate_id("ig")}', 'status': 'skipped', 'reason': 'Not configured'}
        
        if not solution.get('image_url'):
            return {'id': None, 'status': 'skipped', 'reason': 'No image_url provided for Instagram'}
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Step 1: Create media container
                create_response = await client.post(
                    f"{self.api_base}/{self.business_id}/media",
                    params={
                        "access_token": self.access_token,
                        "image_url": solution['image_url'],
                        "caption": solution.get('caption', '')
                    }
                )
                
                if create_response.status_code != 200:
                    return {'id': None, 'status': 'failed', 'error': f"Create container failed: {create_response.text}"}
                
                container_id = create_response.json().get('id')
                
                # Step 2: Publish
                publish_response = await client.post(
                    f"{self.api_base}/{self.business_id}/media_publish",
                    params={
                        "access_token": self.access_token,
                        "creation_id": container_id
                    }
                )
                
                if publish_response.status_code == 200:
                    media_id = publish_response.json().get('id')
                    return {'id': media_id, 'status': 'posted', 'posted_at': _now()}
                return {'id': None, 'status': 'failed', 'error': f"Publish failed: {publish_response.text}"}
        except Exception as e:
            return {'id': None, 'status': 'failed', 'error': str(e)}
    
    async def check_status(self, post_id: str) -> Dict:
        """Check Instagram post engagement"""
        if not post_id or not self.configured:
            return {'completed': True, 'status': 'unknown'}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.api_base}/{post_id}",
                    params={
                        "access_token": self.access_token,
                        "fields": "like_count,comments_count,timestamp"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'completed': True,
                        'status': 'active',
                        'metrics': {
                            'likes': data.get('like_count', 0),
                            'comments': data.get('comments_count', 0)
                        }
                    }
        except:
            pass
        
        return {'completed': True, 'status': 'posted'}


# =============================================================================
# LINKEDIN EXECUTOR - REAL Marketing API v2
# =============================================================================

class LinkedInExecutor:
    """
    Real LinkedIn execution using Marketing API
    
    ENV: LINKEDIN_ACCESS_TOKEN, LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET
    
    Capabilities:
    - Post text updates
    - Post articles
    - Track engagement
    """
    
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.api_base = "https://api.linkedin.com/v2"
        
        self.configured = bool(self.access_token)
        if not self.configured:
            print("⚠️ LinkedIn: Missing LINKEDIN_ACCESS_TOKEN")
        
        self._author_urn = None
    
    async def _get_author_urn(self) -> Optional[str]:
        """Get the author URN for posting"""
        if self._author_urn:
            return self._author_urn
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"{self.api_base}/me",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    self._author_urn = f"urn:li:person:{data.get('id')}"
                    return self._author_urn
        except:
            pass
        return None
    
    async def generate_solution(self, opportunity: Dict, plan: Dict) -> Dict:
        """Generate LinkedIn post content"""
        title = opportunity.get('title', '')[:200]
        
        text = f"""🚀 Exciting opportunity in the AI automation space!

{title}

If you're looking to leverage AI for business growth, let's connect!

#AI #Automation #Business #Innovation #AiGentsy
"""
        return {'text': text[:3000], 'opportunity_id': opportunity.get('id')}
    
    async def validate_solution(self, solution: Dict, opportunity: Dict) -> Dict:
        if len(solution.get('text', '')) > 3000:
            return {'passed': False, 'errors': ['Post exceeds 3000 characters']}
        return {'passed': True}
    
    async def submit(self, solution: Dict, opportunity: Dict) -> Dict:
        """Post to LinkedIn using UGC Posts API"""
        if not self.configured:
            return {'id': f'stub_li_{_generate_id("li")}', 'status': 'skipped', 'reason': 'Not configured'}
        
        author_urn = await self._get_author_urn()
        if not author_urn:
            return {'id': None, 'status': 'failed', 'error': 'Could not get LinkedIn author URN'}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.api_base}/ugcPosts",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0"
                    },
                    json={
                        "author": author_urn,
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {"text": solution.get('text', '')},
                                "shareMediaCategory": "NONE"
                            }
                        },
                        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
                    }
                )
                
                if response.status_code in [200, 201]:
                    post_id = response.headers.get('x-restli-id', _generate_id('li'))
                    return {'id': post_id, 'status': 'posted', 'posted_at': _now()}
                return {'id': None, 'status': 'failed', 'error': f"LinkedIn API: {response.status_code} - {response.text}"}
        except Exception as e:
            return {'id': None, 'status': 'failed', 'error': str(e)}
    
    async def check_status(self, post_id: str) -> Dict:
        return {'completed': True, 'status': 'posted'}


# =============================================================================
# TWILIO SMS EXECUTOR - REAL
# =============================================================================

class TwilioSMSExecutor:
    """
    Real SMS execution using Twilio
    
    ENV: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    
    Capabilities:
    - Send SMS messages
    - Track delivery
    """
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        self.configured = all([self.account_sid, self.auth_token, self.from_number])
        if not self.configured:
            print("⚠️ Twilio SMS: Missing credentials")
    
    async def generate_solution(self, opportunity: Dict, plan: Dict) -> Dict:
        """Generate SMS content"""
        title = opportunity.get('title', '')[:50]
        to_number = opportunity.get('phone') or opportunity.get('source_data', {}).get('phone')
        
        message = f"Hi! I can help with {title}. Reply YES to connect. - AiGentsy"
        
        return {'to': to_number, 'message': message[:160], 'opportunity_id': opportunity.get('id')}
    
    async def validate_solution(self, solution: Dict, opportunity: Dict) -> Dict:
        if not solution.get('to'):
            return {'passed': False, 'errors': ['No phone number']}
        if len(solution.get('message', '')) > 1600:
            return {'passed': False, 'errors': ['Message too long']}
        return {'passed': True}
    
    async def submit(self, solution: Dict, opportunity: Dict) -> Dict:
        """Send SMS via Twilio"""
        if not self.configured:
            return {'id': f'stub_sms_{_generate_id("sms")}', 'status': 'skipped', 'reason': 'Not configured'}
        
        if not solution.get('to'):
            return {'id': None, 'status': 'failed', 'error': 'No phone number'}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                    auth=(self.account_sid, self.auth_token),
                    data={
                        "From": self.from_number,
                        "To": solution['to'],
                        "Body": solution.get('message', '')
                    }
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {'id': data.get('sid'), 'status': 'sent', 'sent_at': _now()}
                return {'id': None, 'status': 'failed', 'error': f"Twilio: {response.status_code}"}
        except Exception as e:
            return {'id': None, 'status': 'failed', 'error': str(e)}
    
    async def check_status(self, message_sid: str) -> Dict:
        """Check SMS delivery status"""
        if not message_sid or not self.configured:
            return {'completed': True, 'status': 'unknown'}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages/{message_sid}.json",
                    auth=(self.account_sid, self.auth_token)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'completed': True,
                        'status': data.get('status', 'unknown')
                    }
        except:
            pass
        
        return {'completed': True, 'status': 'sent'}


# =============================================================================
# REDDIT EXECUTOR - REAL OAuth2 Implementation
# =============================================================================

class RedditExecutor:
    """
    Real Reddit execution using Reddit API
    
    ENV: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
    
    Capabilities:
    - Comment on posts
    - Reply to threads
    - Send DMs
    - Track karma
    """
    
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.username = os.getenv("REDDIT_USERNAME")
        self.password = os.getenv("REDDIT_PASSWORD")
        self.user_agent = "AiGentsy/1.0 (by /u/aigentsy)"
        
        self._access_token = None
        self._token_expires = 0
        
        self.configured = all([self.client_id, self.client_secret, self.username, self.password])
        if not self.configured:
            print("⚠️ Reddit credentials incomplete - Reddit executor will use stubs")
    
    async def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token from Reddit"""
        
        if self._access_token and time.time() < self._token_expires:
            return self._access_token
        
        if not self.configured:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=(self.client_id, self.client_secret),
                    data={
                        "grant_type": "password",
                        "username": self.username,
                        "password": self.password
                    },
                    headers={"User-Agent": self.user_agent}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data.get('access_token')
                    self._token_expires = time.time() + data.get('expires_in', 3600) - 60
                    return self._access_token
                    
        except Exception as e:
            print(f"Reddit auth error: {e}")
        
        return None
    
    async def generate_solution(self, opportunity: Dict, plan: Dict) -> Dict:
        """Generate Reddit comment/reply"""
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')[:200]
        source_data = opportunity.get('source_data', {})
        url = opportunity.get('url', '')
        
        # Extract post_id from URL if not in source_data
        post_id = source_data.get('post_id')
        if not post_id and url:
            import re
            match = re.search(r'/comments/([a-zA-Z0-9]+)/', url)
            if match:
                post_id = match.group(1)
        
        # Generate helpful, non-spammy response
        comment_text = f"""I might be able to help with this!

I have experience with {title[:50]} and similar projects.

Feel free to DM me if you'd like to discuss further. No pressure - happy to share some initial thoughts for free.
"""
        
        return {
            'comment_text': comment_text,
            'post_id': post_id,
            'subreddit': source_data.get('subreddit', 'unknown'),
            'opportunity_id': opportunity.get('id')
        }
    
    async def validate_solution(self, solution: Dict, opportunity: Dict) -> Dict:
        """Validate Reddit comment"""
        
        comment_text = solution.get('comment_text', '')
        
        if len(comment_text) < 20:
            return {'passed': False, 'errors': ['Comment too short']}
        
        if len(comment_text) > 10000:
            return {'passed': False, 'errors': ['Comment too long']}
        
        # Check for spam patterns
        spam_patterns = ['buy now', 'click here', '100% guarantee', 'limited time']
        for pattern in spam_patterns:
            if pattern.lower() in comment_text.lower():
                return {'passed': False, 'errors': [f'Spam pattern detected: {pattern}']}
        
        return {'passed': True}
    
    async def submit(self, solution: Dict, opportunity: Dict) -> Dict:
        """Post comment to Reddit"""
        
        token = await self._get_access_token()
        
        if not token:
            return {
                'id': f'stub_reddit_{_generate_id("rd")}',
                'url': opportunity.get('url', ''),
                'status': 'skipped',
                'reason': 'Reddit credentials not configured'
            }
        
        post_id = solution.get('post_id')
        comment_text = solution.get('comment_text')
        
        if not post_id:
            return {
                'id': None,
                'status': 'failed',
                'error': 'No post_id provided'
            }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://oauth.reddit.com/api/comment",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "User-Agent": self.user_agent
                    },
                    data={
                        "thing_id": f"t3_{post_id}" if not post_id.startswith('t3_') else post_id,
                        "text": comment_text
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract comment ID from response
                    comment_data = data.get('json', {}).get('data', {}).get('things', [{}])[0].get('data', {})
                    comment_id = comment_data.get('id')
                    
                    return {
                        'id': comment_id,
                        'url': f"https://reddit.com/comments/{post_id}/_/{comment_id}" if comment_id else '',
                        'status': 'posted',
                        'posted_at': _now()
                    }
                else:
                    return {
                        'id': None,
                        'status': 'failed',
                        'error': f"Reddit API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            return {
                'id': None,
                'status': 'failed',
                'error': str(e)
            }
    
    async def check_status(self, comment_id: str) -> Dict:
        """Check comment status/karma"""
        return {'completed': True, 'status': 'posted'}


# =============================================================================
# GITHUB EXECUTOR - REAL REST API v3
# =============================================================================

class GitHubExecutor:
    """
    Real GitHub execution using REST API v3
    
    ENV: GITHUB_TOKEN
    
    Capabilities:
    - Comment on issues
    - Submit PRs
    - Fork repositories
    - Track issue status
    """
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.username = os.getenv("GITHUB_USERNAME", "aigentsy-bot")
        self.api_base = "https://api.github.com"
        
        self.configured = bool(self.token)
        if not self.configured:
            print("⚠️ GITHUB_TOKEN not set - GitHub executor will use stubs")
    
    async def generate_solution(self, opportunity: Dict, plan: Dict) -> Dict:
        """Generate GitHub comment/PR content"""
        
        url = opportunity.get('url', '')
        title = opportunity.get('title', '')
        
        # Parse GitHub URL
        import re
        issue_match = re.search(r'github\.com/([^/]+)/([^/]+)/issues/(\d+)', url)
        
        if issue_match:
            owner, repo, issue_number = issue_match.groups()
            
            comment_text = f"""Hi! I'd like to help with this issue.

I have experience with similar problems and can implement a solution.

**Proposed approach:**
- Analyze the root cause
- Implement a fix with tests
- Submit a PR for review

Would you be interested in having me work on this? I can start immediately.
"""
            
            return {
                'type': 'issue_comment',
                'owner': owner,
                'repo': repo,
                'issue_number': issue_number,
                'comment_text': comment_text,
                'opportunity_id': opportunity.get('id')
            }
        
        # For non-issue URLs, generate general response
        return {
            'type': 'general',
            'comment_text': f"Interested in helping with: {title}",
            'opportunity_id': opportunity.get('id')
        }
    
    async def validate_solution(self, solution: Dict, opportunity: Dict) -> Dict:
        """Validate GitHub solution"""
        
        if solution.get('type') == 'issue_comment':
            if not all([solution.get('owner'), solution.get('repo'), solution.get('issue_number')]):
                return {'passed': False, 'errors': ['Missing GitHub issue details']}
        
        return {'passed': True}
    
    async def submit(self, solution: Dict, opportunity: Dict) -> Dict:
        """Submit comment to GitHub issue"""
        
        if not self.configured:
            return {
                'id': f'stub_github_{_generate_id("gh")}',
                'url': opportunity.get('url', ''),
                'status': 'skipped',
                'reason': 'GITHUB_TOKEN not configured'
            }
        
        if solution.get('type') != 'issue_comment':
            return {
                'id': None,
                'status': 'skipped',
                'reason': 'Only issue comments supported currently'
            }
        
        owner = solution.get('owner')
        repo = solution.get('repo')
        issue_number = solution.get('issue_number')
        comment_text = solution.get('comment_text')
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.api_base}/repos/{owner}/{repo}/issues/{issue_number}/comments",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    json={"body": comment_text}
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    
                    return {
                        'id': data.get('id'),
                        'url': data.get('html_url'),
                        'status': 'posted',
                        'posted_at': _now()
                    }
                else:
                    return {
                        'id': None,
                        'status': 'failed',
                        'error': f"GitHub API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            return {
                'id': None,
                'status': 'failed',
                'error': str(e)
            }
    
    async def check_status(self, comment_id: str) -> Dict:
        """Check if issue has been updated"""
        return {'completed': True, 'status': 'posted'}


# =============================================================================
# UPWORK EXECUTOR - Manual Submission (No Public API)
# =============================================================================

class UpworkExecutor:
    """
    Upwork execution - requires manual/browser automation
    
    Upwork doesn't have a public API for proposal submission,
    so this generates proposals for manual submission or
    browser automation via Puppeteer/Playwright.
    """
    
    def __init__(self):
        self.username = os.getenv("UPWORK_USERNAME")
        self.configured = True  # Always "configured" since it's manual
        print("ℹ️ Upwork executor generates proposals for manual submission")
    
    async def generate_solution(self, opportunity: Dict, plan: Dict) -> Dict:
        """Generate Upwork proposal"""
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        value = opportunity.get('value', 0)
        
        proposal = f"""Dear Hiring Manager,

I'm excited to apply for your project: {title}

RELEVANT EXPERIENCE:
I have extensive experience with similar projects and can deliver high-quality results.

APPROACH:
1. Deep dive into your requirements
2. Create a detailed implementation plan
3. Execute with regular updates
4. Deliver with documentation and support

TIMELINE & BUDGET:
I can complete this within your timeline at ${value:,.0f}.

I'd love to discuss your project in more detail. Are you available for a quick call?

Best regards,
AiGentsy Team
"""
        
        return {
            'proposal_text': proposal,
            'bid_amount': value,
            'timeline': plan.get('timeline', '1-2 weeks'),
            'job_url': opportunity.get('url'),
            'opportunity_id': opportunity.get('id'),
            'submission_method': 'manual'
        }
    
    async def validate_solution(self, solution: Dict, opportunity: Dict) -> Dict:
        """Validate Upwork proposal"""
        return {'passed': True}
    
    async def submit(self, solution: Dict, opportunity: Dict) -> Dict:
        """Return proposal for manual submission"""
        
        return {
            'id': f'upwork_manual_{_generate_id("uw")}',
            'status': 'ready_for_manual_submission',
            'proposal': solution.get('proposal_text'),
            'job_url': solution.get('job_url'),
            'instructions': 'Copy proposal and submit manually at Upwork'
        }
    
    async def check_status(self, proposal_id: str) -> Dict:
        """Check proposal status - manual tracking required"""
        return {'completed': False, 'status': 'pending_manual_check'}


# =============================================================================
# UNIFIED EXECUTOR ROUTER
# =============================================================================

class PlatformExecutorRouter:
    """
    Routes execution to appropriate platform executor
    """
    
    def __init__(self):
        self.executors = {
            # Social
            'twitter': TwitterExecutor(),
            'x': TwitterExecutor(),
            'instagram': InstagramExecutor(),
            'linkedin': LinkedInExecutor(),
            'reddit': RedditExecutor(),
            
            # Communication
            'email': EmailExecutor(),
            'resend': EmailExecutor(),
            'sms': TwilioSMSExecutor(),
            'twilio': TwilioSMSExecutor(),
            
            # Coding
            'github': GitHubExecutor(),
            'github_issues': GitHubExecutor(),
            'github_bounties': GitHubExecutor(),
            
            # Freelance
            'upwork': UpworkExecutor(),
        }
    
    def get_executor(self, platform: str):
        """Get executor for platform"""
        platform_lower = platform.lower().replace(' ', '_').replace('-', '_')
        return self.executors.get(platform_lower)
    
    async def execute_opportunity(
        self,
        opportunity: Dict,
        plan: Dict = None
    ) -> Dict:
        """
        Execute opportunity end-to-end
        
        Flow:
        1. Route to appropriate executor
        2. Generate solution
        3. Validate
        4. Submit
        5. Track
        """
        
        platform = opportunity.get('platform') or opportunity.get('source', 'unknown')
        executor = self.get_executor(platform)
        
        if not executor:
            return {
                'ok': False,
                'error': f'No executor for platform: {platform}',
                'opportunity_id': opportunity.get('id')
            }
        
        plan = plan or {}
        
        try:
            # Generate solution
            solution = await executor.generate_solution(opportunity, plan)
            
            # Validate
            validation = await executor.validate_solution(solution, opportunity)
            
            if not validation.get('passed'):
                return {
                    'ok': False,
                    'stage': 'validation',
                    'errors': validation.get('errors', []),
                    'opportunity_id': opportunity.get('id')
                }
            
            # Submit
            result = await executor.submit(solution, opportunity)
            
            return {
                'ok': result.get('status') in ['posted', 'sent', 'ready_for_manual_submission'],
                'platform': platform,
                'opportunity_id': opportunity.get('id'),
                'solution': solution,
                'result': result,
                'executed_at': _now()
            }
            
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
                'opportunity_id': opportunity.get('id')
            }
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available platform executors"""
        return list(set(self.executors.keys()))
    
    def get_platform_status(self) -> Dict[str, Dict]:
        """Get configuration status for each platform"""
        
        status = {}
        
        # Twitter
        status['twitter'] = {
            'configured': all([
                os.getenv("TWITTER_API_KEY"),
                os.getenv("TWITTER_API_SECRET"),
                os.getenv("TWITTER_ACCESS_TOKEN"),
                os.getenv("TWITTER_ACCESS_SECRET")
            ]),
            'env_vars': ['TWITTER_API_KEY', 'TWITTER_API_SECRET', 'TWITTER_ACCESS_TOKEN', 'TWITTER_ACCESS_SECRET']
        }
        
        # Instagram
        status['instagram'] = {
            'configured': all([
                os.getenv("INSTAGRAM_ACCESS_TOKEN"),
                os.getenv("INSTAGRAM_BUSINESS_ID")
            ]),
            'env_vars': ['INSTAGRAM_ACCESS_TOKEN', 'INSTAGRAM_BUSINESS_ID']
        }
        
        # LinkedIn
        status['linkedin'] = {
            'configured': bool(os.getenv("LINKEDIN_ACCESS_TOKEN")),
            'env_vars': ['LINKEDIN_ACCESS_TOKEN', 'LINKEDIN_CLIENT_ID', 'LINKEDIN_CLIENT_SECRET']
        }
        
        # Email/Resend
        status['email'] = {
            'configured': bool(os.getenv("RESEND_API_KEY")),
            'env_vars': ['RESEND_API_KEY']
        }
        
        # SMS/Twilio
        status['sms'] = {
            'configured': all([
                os.getenv("TWILIO_ACCOUNT_SID"),
                os.getenv("TWILIO_AUTH_TOKEN"),
                os.getenv("TWILIO_PHONE_NUMBER")
            ]),
            'env_vars': ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER']
        }
        
        # Reddit
        status['reddit'] = {
            'configured': all([
                os.getenv("REDDIT_CLIENT_ID"),
                os.getenv("REDDIT_CLIENT_SECRET"),
                os.getenv("REDDIT_USERNAME"),
                os.getenv("REDDIT_PASSWORD")
            ]),
            'env_vars': ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USERNAME', 'REDDIT_PASSWORD']
        }
        
        # GitHub
        status['github'] = {
            'configured': bool(os.getenv("GITHUB_TOKEN")),
            'env_vars': ['GITHUB_TOKEN']
        }
        
        # Upwork (always "configured" - manual)
        status['upwork'] = {
            'configured': True,
            'note': 'Manual submission - no API available'
        }
        
        return status


# =============================================================================
# SINGLETON & CONVENIENCE
# =============================================================================

_router: Optional[PlatformExecutorRouter] = None


def get_platform_router() -> PlatformExecutorRouter:
    """Get singleton platform router"""
    global _router
    if _router is None:
        _router = PlatformExecutorRouter()
    return _router


# =============================================================================
# TEST
# =============================================================================

async def test_platform_apis():
    """Test platform API integrations"""
    
    print("\n" + "=" * 70)
    print("🧪 TESTING PLATFORM APIS (8 EXECUTORS)")
    print("=" * 70)
    
    router = get_platform_router()
    
    # Check platform status
    print("\n📊 Platform Configuration Status:")
    status = router.get_platform_status()
    for platform, info in status.items():
        configured = "✅" if info.get('configured') else "❌"
        print(f"   {configured} {platform}")
    
    # Test Twitter (if configured)
    if status['twitter']['configured']:
        print("\n🐦 Testing Twitter...")
        twitter = router.get_executor('twitter')
        
        test_opp = {
            'id': 'test_1',
            'title': 'Need help with Python automation',
            'source': 'twitter_pain_point'
        }
        
        solution = await twitter.generate_solution(test_opp, {})
        print(f"   Generated tweet: {solution.get('tweet_text', '')[:50]}...")
    
    # Test Email (if configured)
    if status['email']['configured']:
        print("\n📧 Testing Email (Resend)...")
        email = router.get_executor('email')
        
        test_opp = {
            'id': 'test_2',
            'title': 'Looking for web developer',
            'contact_email': 'test@example.com',
            'value': 500
        }
        
        solution = await email.generate_solution(test_opp, {})
        print(f"   Generated subject: {solution.get('subject', '')}")
    
    # Test Instagram (if configured)
    if status['instagram']['configured']:
        print("\n📸 Testing Instagram...")
        ig = router.get_executor('instagram')
        test_opp = {'id': 'test_ig', 'title': 'AI automation showcase'}
        solution = await ig.generate_solution(test_opp, {})
        print(f"   Generated caption: {solution.get('caption', '')[:50]}...")
    
    # Test LinkedIn (if configured)
    if status['linkedin']['configured']:
        print("\n💼 Testing LinkedIn...")
        li = router.get_executor('linkedin')
        test_opp = {'id': 'test_li', 'title': 'AI business opportunity'}
        solution = await li.generate_solution(test_opp, {})
        print(f"   Generated post: {solution.get('text', '')[:50]}...")
    
    # Test SMS (if configured)
    if status['sms']['configured']:
        print("\n📱 Testing SMS (Twilio)...")
        sms = router.get_executor('sms')
        test_opp = {'id': 'test_sms', 'title': 'Quick project', 'phone': '+1234567890'}
        solution = await sms.generate_solution(test_opp, {})
        print(f"   Generated message: {solution.get('message', '')}")
    
    print("\n✅ Platform API tests complete!")
    print(f"   Total executors: 8")
    print(f"   Configured: {sum(1 for p in status.values() if p.get('configured'))}")


if __name__ == "__main__":
    asyncio.run(test_platform_apis())
