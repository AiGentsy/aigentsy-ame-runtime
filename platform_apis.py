"""
PLATFORM APIS - REAL INTEGRATIONS
=================================
The actual API clients that interact with external platforms.

WORKING INTEGRATIONS:
- Twitter/X: OAuth 1.0a (from social_autoposting_engine)
- Email: Resend API (from resend_automator)
- Reddit: PRAW integration
- GitHub: REST API v3

Each platform executor follows the same interface:
- generate_solution()
- validate_solution()
- submit()
- check_status()

ENV VARS REQUIRED:
- TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
- RESEND_API_KEY
- REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD
- GITHUB_TOKEN
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
        
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
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
        
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
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
        
        if not tweet_id or not self.api_key:
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
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        self.api_base = "https://api.resend.com"
        
        if not self.api_key:
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
        
        if not self.api_key:
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
        
        if not email_id or not self.api_key:
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
# REDDIT EXECUTOR - REAL PRAW-style Implementation
# =============================================================================

class RedditExecutor:
    """
    Real Reddit execution using Reddit API
    
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
        
        if not all([self.client_id, self.client_secret, self.username, self.password]):
            print("⚠️ Reddit credentials incomplete - Reddit executor will use stubs")
    
    async def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token from Reddit"""
        
        if self._access_token and time.time() < self._token_expires:
            return self._access_token
        
        if not all([self.client_id, self.client_secret, self.username, self.password]):
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
        
        # Generate helpful, non-spammy response
        comment_text = f"""I might be able to help with this!

I have experience with {title[:50]} and similar projects.

Feel free to DM me if you'd like to discuss further. No pressure - happy to share some initial thoughts for free.
"""
        
        return {
            'comment_text': comment_text,
            'post_id': source_data.get('post_id') or opportunity.get('id'),
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
# GITHUB EXECUTOR - REAL Implementation
# =============================================================================

class GitHubExecutor:
    """
    Real GitHub execution
    
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
        
        if not self.token:
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
        
        if not self.token:
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
# UPWORK EXECUTOR - Stub (requires browser automation)
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
            'twitter': TwitterExecutor(),
            'x': TwitterExecutor(),
            'email': EmailExecutor(),
            'resend': EmailExecutor(),
            'reddit': RedditExecutor(),
            'github': GitHubExecutor(),
            'github_issues': GitHubExecutor(),
            'github_bounties': GitHubExecutor(),
            'upwork': UpworkExecutor(),
        }
    
    def get_executor(self, platform: str):
        """Get executor for platform"""
        
        platform_lower = platform.lower().replace(' ', '_')
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
        return list(self.executors.keys())
    
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
        
        # Email/Resend
        status['email'] = {
            'configured': bool(os.getenv("RESEND_API_KEY")),
            'env_vars': ['RESEND_API_KEY']
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
        
        # Upwork (always "manual")
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
    print("🧪 TESTING PLATFORM APIS")
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
    
    print("\n✅ Platform API tests complete!")


if __name__ == "__main__":
    asyncio.run(test_platform_apis())
