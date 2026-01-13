"""
DIRECT OUTREACH ENGINE
======================
Sends proposals via DM/email instead of posting to restricted platforms.

OUTREACH CHANNELS:
1. Email (via Resend API) - highest conversion
2. Twitter DM - quick engagement
3. LinkedIn Message - professional B2B
4. Reddit DM - community-sourced leads
5. GitHub Discussion - open source contacts

PHILOSOPHY:
- NEVER post to Fiverr/Upwork (violates ToS)
- Direct contact = higher conversion
- Personalized proposals based on extracted pain points
- Quality control on all outreach
- Track responses and optimize templates

INTEGRATES WITH:
- internet_discovery_expansion (receives contacts)
- opportunity_engagement (extends existing)
- platform_apis (uses Twitter, Email executors)
- quality_control (apex QC on proposals)
"""

import asyncio
import aiohttp
import os
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# CONFIGURATION
# =============================================================================

class OutreachChannel(Enum):
    EMAIL = "email"
    TWITTER_DM = "twitter_dm"
    LINKEDIN_MESSAGE = "linkedin_message"
    REDDIT_DM = "reddit_dm"
    GITHUB_DISCUSSION = "github_discussion"
    DISCORD_DM = "discord_dm"


class OutreachStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    REPLIED = "replied"
    CONVERTED = "converted"
    REJECTED = "rejected"
    BOUNCED = "bounced"


@dataclass
class OutreachProposal:
    """A proposal to send to a prospect"""
    proposal_id: str
    opportunity_id: str
    channel: OutreachChannel
    recipient: str  # email, @handle, username
    subject: str
    body: str
    personalization: Dict[str, str]
    value_proposition: str
    call_to_action: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sent_at: Optional[str] = None
    status: OutreachStatus = OutreachStatus.PENDING


@dataclass
class OutreachResult:
    """Result of an outreach attempt"""
    proposal_id: str
    channel: OutreachChannel
    status: OutreachStatus
    sent_at: str
    response: Optional[str] = None
    error: Optional[str] = None
    tracking_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# PROPOSAL GENERATOR
# =============================================================================

class ProposalGenerator:
    """
    Generates personalized proposals based on opportunity data.
    Uses AI conductor for high-quality personalization.
    """
    
    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        # Channel-specific templates
        self.templates = {
            OutreachChannel.EMAIL: self._email_template,
            OutreachChannel.TWITTER_DM: self._twitter_dm_template,
            OutreachChannel.LINKEDIN_MESSAGE: self._linkedin_template,
            OutreachChannel.REDDIT_DM: self._reddit_dm_template,
            OutreachChannel.GITHUB_DISCUSSION: self._github_template,
        }
        
        # Value propositions by category - AiGentsy: Your fully staffed autonomous company
        self.value_props = {
            'development': "AiGentsy becomes your fully staffed dev team — from spec to shipped, handled",
            'automation': "AiGentsy is your automation department — we build it, deploy it, maintain it",
            'design': "AiGentsy is your creative studio — best-in-class design, delivered instantly",
            'content': "AiGentsy is your content team — highest quality, end-to-end production",
            'data': "AiGentsy is your analytics department — raw data to actionable insights, handled",
            'marketing': "AiGentsy is your marketing team — strategy to execution, fully autonomous",
            'default': "AiGentsy is your fully staffed team for this — end-to-end, handled"
        }
    
    async def generate_proposal(
        self,
        opportunity: Dict[str, Any],
        contact: Dict[str, Any],
        channel: OutreachChannel
    ) -> OutreachProposal:
        """Generate a personalized proposal for an opportunity"""
        
        # Extract key info
        opp_id = opportunity.get('opportunity_id', 'unknown')
        title = opportunity.get('title', '')
        pain_point = opportunity.get('pain_point', '')
        estimated_value = opportunity.get('estimated_value', 1000)
        
        # Determine value proposition
        category = self._categorize_opportunity(title, pain_point)
        value_prop = self.value_props.get(category, self.value_props['default'])
        
        # Get recipient based on channel
        recipient = self._get_recipient(contact, channel)
        
        # Generate using template
        template_fn = self.templates.get(channel, self._email_template)
        subject, body = template_fn(
            name=contact.get('name', 'there'),
            title=title,
            pain_point=pain_point,
            value_prop=value_prop,
            estimated_value=estimated_value
        )
        
        # Create proposal
        proposal = OutreachProposal(
            proposal_id=f"prop_{hashlib.md5(f'{opp_id}_{channel.value}'.encode()).hexdigest()[:12]}",
            opportunity_id=opp_id,
            channel=channel,
            recipient=recipient,
            subject=subject,
            body=body,
            personalization={
                'name': contact.get('name', ''),
                'company': contact.get('company', ''),
                'pain_point': pain_point,
            },
            value_proposition=value_prop,
            call_to_action="Reply to discuss" if channel != OutreachChannel.TWITTER_DM else "DM me!"
        )
        
        return proposal
    
    def _categorize_opportunity(self, title: str, pain_point: str) -> str:
        """Categorize the opportunity for value prop selection"""
        text = (title + ' ' + pain_point).lower()
        
        if any(kw in text for kw in ['develop', 'code', 'build', 'app', 'software', 'api']):
            return 'development'
        elif any(kw in text for kw in ['automat', 'bot', 'script', 'workflow']):
            return 'automation'
        elif any(kw in text for kw in ['design', 'ui', 'ux', 'graphic', 'logo']):
            return 'design'
        elif any(kw in text for kw in ['content', 'write', 'blog', 'copy', 'article']):
            return 'content'
        elif any(kw in text for kw in ['data', 'analyt', 'dashboard', 'report']):
            return 'data'
        else:
            return 'default'
    
    def _get_recipient(self, contact: Dict, channel: OutreachChannel) -> str:
        """Get recipient identifier for channel"""
        if channel == OutreachChannel.EMAIL:
            return contact.get('email', '')
        elif channel == OutreachChannel.TWITTER_DM:
            return contact.get('twitter_handle', '')
        elif channel == OutreachChannel.LINKEDIN_MESSAGE:
            return contact.get('linkedin_url', '')
        elif channel == OutreachChannel.REDDIT_DM:
            return contact.get('reddit_username', '')
        elif channel == OutreachChannel.GITHUB_DISCUSSION:
            return contact.get('github_username', '')
        return ''
    
    # Template methods
    
    def _email_template(self, name: str, title: str, pain_point: str, value_prop: str, estimated_value: float) -> tuple:
        """Generate email proposal - AiGentsy: Your fully staffed autonomous company"""
        subject = f"Re: {title[:50]}"
        
        body = f"""Hi {name},

Saw your post about "{title}" — this is exactly what we built AiGentsy for.

We're the first fully autonomous fulfillment company. Think of us as your on-demand {pain_point[:40]} team — a complete staff working for you, from brief to delivery.

No freelancers. No waiting. No back-and-forth.

Here's how it works:

→ You tell us what you need
→ Your AiGentsy team delivers (usually within minutes)
→ You review, request changes, we iterate until it's right
→ You only pay when you approve

We've handled thousands of projects like this. Best-in-class quality, first-of-its-kind speed.

Investment: ${int(estimated_value * 0.7)} — and you don't pay a cent until you're happy with the result.

Want to see it in action? Just reply and I'll get your project queued up.

— The AiGentsy Team

P.S. If timing isn't right, no worries. We'll be here.
"""
        
        return subject, body
    
    def _twitter_dm_template(self, name: str, title: str, pain_point: str, value_prop: str, estimated_value: float) -> tuple:
        """Generate Twitter DM - Confident, effortless"""
        subject = ""  # No subject for DMs
        
        body = f"""Hey {name} 👋

Saw you need help with {title[:25]}...

AiGentsy is basically a fully staffed company that works for you — end-to-end delivery in minutes.

First of its kind. Want me to show you?"""
        
        return subject, body
    
    def _linkedin_template(self, name: str, title: str, pain_point: str, value_prop: str, estimated_value: float) -> tuple:
        """Generate LinkedIn message - Professional, confident"""
        subject = f"Re: {title[:40]}"
        
        body = f"""Hi {name},

Came across your post about {title} — wanted to introduce you to something we've built.

AiGentsy is the first fully autonomous fulfillment company. We're essentially your on-demand {pain_point[:50]} team — a complete staff working for you, end-to-end.

What makes us different:

• Delivery in minutes, not days or weeks
• Iterate with your team until it's exactly right
• Pay only when you approve the final result

We've handled thousands of similar projects with best-in-class results.

Would you be open to a quick demo? No pitch — just want to show you what's possible now.

— AiGentsy Team"""
        
        return subject, body
    
    def _reddit_dm_template(self, name: str, title: str, pain_point: str, value_prop: str, estimated_value: float) -> tuple:
        """Generate Reddit DM - Casual but confident"""
        subject = f"Re: {title[:50]}"
        
        body = f"""Hey u/{name},

Saw your post about {title}. 

We built AiGentsy for exactly this — it's basically a fully staffed company that works for you. You describe what you need, your team delivers it (usually in minutes), you iterate until it's perfect, then you pay.

First of its kind. No freelancers, no waiting around.

Happy to show you how it works if you're curious. No pressure either way.

Cheers"""
        
        return subject, body
    
    def _github_template(self, name: str, title: str, pain_point: str, value_prop: str, estimated_value: float) -> tuple:
        """Generate GitHub discussion/issue comment - Dev-friendly, confident"""
        subject = f"Can help with: {title[:50]}"
        
        body = f"""Hi @{name},

Noticed this issue — this is actually what we built AiGentsy for.

**AiGentsy** is the first fully autonomous fulfillment company. For {pain_point[:50]}:

- Your dedicated team delivers in minutes
- You review, iterate, approve when ready
- Pay only after you're satisfied

We've shipped thousands of similar projects. Best-in-class quality, first-of-its-kind speed.

Want me to queue this up? No obligation — takes about 2 minutes to get started."""
        
        return subject, body


# =============================================================================
# CHANNEL EXECUTORS
# =============================================================================

class EmailOutreach:
    """Send outreach emails via Resend API"""
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "hello@aigentsy.com")
        self.configured = bool(self.api_key)
    
    async def send(self, proposal: OutreachProposal) -> OutreachResult:
        """Send email proposal"""
        
        if not self.configured:
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.EMAIL,
                status=OutreachStatus.BOUNCED,
                sent_at=datetime.now(timezone.utc).isoformat(),
                error="Email not configured - missing RESEND_API_KEY"
            )
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [proposal.recipient],
                        "subject": proposal.subject,
                        "text": proposal.body
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return OutreachResult(
                            proposal_id=proposal.proposal_id,
                            channel=OutreachChannel.EMAIL,
                            status=OutreachStatus.SENT,
                            sent_at=datetime.now(timezone.utc).isoformat(),
                            tracking_id=data.get('id'),
                            metadata={'resend_response': data}
                        )
                    else:
                        error = await resp.text()
                        return OutreachResult(
                            proposal_id=proposal.proposal_id,
                            channel=OutreachChannel.EMAIL,
                            status=OutreachStatus.BOUNCED,
                            sent_at=datetime.now(timezone.utc).isoformat(),
                            error=f"Resend error: {error}"
                        )
        
        except Exception as e:
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.EMAIL,
                status=OutreachStatus.BOUNCED,
                sent_at=datetime.now(timezone.utc).isoformat(),
                error=str(e)
            )


class TwitterDMOutreach:
    """Send Twitter DMs via Twitter API v2"""
    
    def __init__(self):
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        self.configured = all([self.api_key, self.api_secret, self.access_token, self.access_secret])
    
    async def send(self, proposal: OutreachProposal) -> OutreachResult:
        """Send Twitter DM"""
        
        if not self.configured:
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.TWITTER_DM,
                status=OutreachStatus.BOUNCED,
                sent_at=datetime.now(timezone.utc).isoformat(),
                error="Twitter not configured"
            )
        
        # First, get user ID from handle
        handle = proposal.recipient.lstrip('@')
        user_id = await self._get_user_id(handle)
        
        if not user_id:
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.TWITTER_DM,
                status=OutreachStatus.BOUNCED,
                sent_at=datetime.now(timezone.utc).isoformat(),
                error=f"Could not find Twitter user: {handle}"
            )
        
        # Send DM using Twitter API v2
        try:
            # Note: Full OAuth implementation needed here
            # This is a simplified version
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.TWITTER_DM,
                status=OutreachStatus.PENDING,
                sent_at=datetime.now(timezone.utc).isoformat(),
                metadata={'user_id': user_id, 'message': proposal.body}
            )
        
        except Exception as e:
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.TWITTER_DM,
                status=OutreachStatus.BOUNCED,
                sent_at=datetime.now(timezone.utc).isoformat(),
                error=str(e)
            )
    
    async def _get_user_id(self, handle: str) -> Optional[str]:
        """Get Twitter user ID from handle"""
        if not self.bearer_token:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.twitter.com/2/users/by/username/{handle}",
                    headers={"Authorization": f"Bearer {self.bearer_token}"}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('data', {}).get('id')
        except:
            pass
        
        return None


class LinkedInOutreach:
    """Send LinkedIn messages via LinkedIn API"""
    
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.configured = bool(self.access_token)
    
    async def send(self, proposal: OutreachProposal) -> OutreachResult:
        """Send LinkedIn message"""
        
        if not self.configured:
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.LINKEDIN_MESSAGE,
                status=OutreachStatus.BOUNCED,
                sent_at=datetime.now(timezone.utc).isoformat(),
                error="LinkedIn not configured"
            )
        
        # LinkedIn messaging requires connection first
        # This would use LinkedIn Messaging API
        return OutreachResult(
            proposal_id=proposal.proposal_id,
            channel=OutreachChannel.LINKEDIN_MESSAGE,
            status=OutreachStatus.PENDING,
            sent_at=datetime.now(timezone.utc).isoformat(),
            metadata={'linkedin_url': proposal.recipient, 'message': proposal.body}
        )


class RedditDMOutreach:
    """Send Reddit DMs via Reddit API"""
    
    def __init__(self):
        self.client_id = os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.username = os.getenv("REDDIT_USERNAME")
        self.password = os.getenv("REDDIT_PASSWORD")
        
        self.configured = all([self.client_id, self.client_secret, self.username, self.password])
        self.access_token = None
    
    async def _get_token(self) -> Optional[str]:
        """Get Reddit OAuth token"""
        if self.access_token:
            return self.access_token
        
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
                async with session.post(
                    "https://www.reddit.com/api/v1/access_token",
                    auth=auth,
                    data={
                        "grant_type": "password",
                        "username": self.username,
                        "password": self.password
                    },
                    headers={"User-Agent": "AiGentsy/1.0"}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.access_token = data.get('access_token')
                        return self.access_token
        except:
            pass
        
        return None
    
    async def send(self, proposal: OutreachProposal) -> OutreachResult:
        """Send Reddit DM"""
        
        if not self.configured:
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.REDDIT_DM,
                status=OutreachStatus.BOUNCED,
                sent_at=datetime.now(timezone.utc).isoformat(),
                error="Reddit not configured"
            )
        
        token = await self._get_token()
        if not token:
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.REDDIT_DM,
                status=OutreachStatus.BOUNCED,
                sent_at=datetime.now(timezone.utc).isoformat(),
                error="Failed to get Reddit token"
            )
        
        recipient = proposal.recipient.lstrip('u/')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://oauth.reddit.com/api/compose",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "User-Agent": "AiGentsy/1.0"
                    },
                    data={
                        "to": recipient,
                        "subject": proposal.subject,
                        "text": proposal.body
                    }
                ) as resp:
                    if resp.status == 200:
                        return OutreachResult(
                            proposal_id=proposal.proposal_id,
                            channel=OutreachChannel.REDDIT_DM,
                            status=OutreachStatus.SENT,
                            sent_at=datetime.now(timezone.utc).isoformat()
                        )
                    else:
                        error = await resp.text()
                        return OutreachResult(
                            proposal_id=proposal.proposal_id,
                            channel=OutreachChannel.REDDIT_DM,
                            status=OutreachStatus.BOUNCED,
                            sent_at=datetime.now(timezone.utc).isoformat(),
                            error=f"Reddit API error: {error}"
                        )
        
        except Exception as e:
            return OutreachResult(
                proposal_id=proposal.proposal_id,
                channel=OutreachChannel.REDDIT_DM,
                status=OutreachStatus.BOUNCED,
                sent_at=datetime.now(timezone.utc).isoformat(),
                error=str(e)
            )


# =============================================================================
# MAIN DIRECT OUTREACH ENGINE
# =============================================================================

class DirectOutreachEngine:
    """
    Main engine that orchestrates direct outreach via DM/email.
    
    Flow:
    1. Receive opportunity with contact info
    2. Generate personalized proposal
    3. Select best outreach channel
    4. Send via appropriate executor
    5. Track response and optimize
    """
    
    def __init__(self):
        self.proposal_generator = ProposalGenerator()
        
        # Channel executors
        self.executors = {
            OutreachChannel.EMAIL: EmailOutreach(),
            OutreachChannel.TWITTER_DM: TwitterDMOutreach(),
            OutreachChannel.LINKEDIN_MESSAGE: LinkedInOutreach(),
            OutreachChannel.REDDIT_DM: RedditDMOutreach(),
        }
        
        # Outreach history
        self.history: List[OutreachResult] = []
        
        # Quality control thresholds
        self.min_contact_confidence = 0.3
        self.max_daily_outreach = 50
        self.daily_count = 0
        self.last_reset = datetime.now(timezone.utc).date()
    
    async def process_opportunity(
        self,
        opportunity: Dict[str, Any],
        contact: Dict[str, Any]
    ) -> Optional[OutreachResult]:
        """
        Process a single opportunity for outreach.
        
        Args:
            opportunity: From discovery engine
            contact: Extracted contact info
        
        Returns:
            OutreachResult if sent, None if filtered
        """
        
        # Reset daily counter
        today = datetime.now(timezone.utc).date()
        if today != self.last_reset:
            self.daily_count = 0
            self.last_reset = today
        
        # Check rate limit
        if self.daily_count >= self.max_daily_outreach:
            print(f"⚠️ Daily outreach limit reached ({self.max_daily_outreach})")
            return None
        
        # Check contact confidence
        confidence = contact.get('extraction_confidence', 0)
        if confidence < self.min_contact_confidence:
            print(f"⚠️ Contact confidence too low: {confidence}")
            return None
        
        # Determine best channel
        channel = self._select_channel(contact)
        if not channel:
            print(f"⚠️ No valid outreach channel for contact")
            return None
        
        # Generate proposal
        proposal = await self.proposal_generator.generate_proposal(
            opportunity, contact, channel
        )
        
        # Quality check
        if not self._quality_check(proposal):
            print(f"⚠️ Proposal failed quality check")
            return None
        
        # Send
        executor = self.executors.get(channel)
        if not executor:
            print(f"⚠️ No executor for channel: {channel}")
            return None
        
        result = await executor.send(proposal)
        
        # Track
        self.history.append(result)
        if result.status == OutreachStatus.SENT:
            self.daily_count += 1
        
        return result
    
    async def process_batch(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> List[OutreachResult]:
        """Process a batch of opportunities"""
        
        results = []
        
        for opp in opportunities:
            contact = opp.get('contact')
            if not contact:
                continue
            
            # Convert contact dataclass to dict if needed
            if hasattr(contact, '__dict__'):
                contact = {
                    'email': getattr(contact, 'email', None),
                    'twitter_handle': getattr(contact, 'twitter_handle', None),
                    'linkedin_url': getattr(contact, 'linkedin_url', None),
                    'reddit_username': getattr(contact, 'reddit_username', None),
                    'github_username': getattr(contact, 'github_username', None),
                    'name': getattr(contact, 'name', None),
                    'company': getattr(contact, 'company', None),
                    'extraction_confidence': getattr(contact, 'extraction_confidence', 0),
                    'preferred_outreach': getattr(contact, 'preferred_outreach', None),
                }
            
            result = await self.process_opportunity(opp, contact)
            if result:
                results.append(result)
            
            # Rate limit between sends
            await asyncio.sleep(2)
        
        return results
    
    def _select_channel(self, contact: Dict) -> Optional[OutreachChannel]:
        """Select best outreach channel based on available contact info"""
        
        # Check preferred
        preferred = contact.get('preferred_outreach')
        if preferred:
            channel_map = {
                'email': OutreachChannel.EMAIL,
                'twitter_dm': OutreachChannel.TWITTER_DM,
                'linkedin_message': OutreachChannel.LINKEDIN_MESSAGE,
                'reddit_dm': OutreachChannel.REDDIT_DM,
            }
            if preferred in channel_map:
                executor = self.executors.get(channel_map[preferred])
                if executor and executor.configured:
                    return channel_map[preferred]
        
        # Fallback priority: Email > Twitter > LinkedIn > Reddit
        if contact.get('email') and self.executors[OutreachChannel.EMAIL].configured:
            return OutreachChannel.EMAIL
        
        if contact.get('twitter_handle') and self.executors[OutreachChannel.TWITTER_DM].configured:
            return OutreachChannel.TWITTER_DM
        
        if contact.get('linkedin_url') and self.executors[OutreachChannel.LINKEDIN_MESSAGE].configured:
            return OutreachChannel.LINKEDIN_MESSAGE
        
        if contact.get('reddit_username') and self.executors[OutreachChannel.REDDIT_DM].configured:
            return OutreachChannel.REDDIT_DM
        
        return None
    
    def _quality_check(self, proposal: OutreachProposal) -> bool:
        """Quality check on proposal before sending"""
        
        # Basic checks
        if not proposal.recipient:
            return False
        
        if len(proposal.body) < 50:
            return False
        
        if len(proposal.body) > 5000:
            return False
        
        # Check for spam indicators
        spam_words = ['limited time', 'act now', 'click here', 'buy now', 'free money']
        body_lower = proposal.body.lower()
        if any(word in body_lower for word in spam_words):
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get outreach statistics"""
        
        total = len(self.history)
        sent = sum(1 for r in self.history if r.status == OutreachStatus.SENT)
        bounced = sum(1 for r in self.history if r.status == OutreachStatus.BOUNCED)
        replied = sum(1 for r in self.history if r.status == OutreachStatus.REPLIED)
        converted = sum(1 for r in self.history if r.status == OutreachStatus.CONVERTED)
        
        return {
            'total_attempts': total,
            'sent': sent,
            'bounced': bounced,
            'replied': replied,
            'converted': converted,
            'send_rate': sent / total if total > 0 else 0,
            'reply_rate': replied / sent if sent > 0 else 0,
            'conversion_rate': converted / replied if replied > 0 else 0,
            'daily_count': self.daily_count,
            'daily_limit': self.max_daily_outreach,
            'channels_configured': {
                channel.value: executor.configured
                for channel, executor in self.executors.items()
            }
        }


# =============================================================================
# INTEGRATION FUNCTIONS
# =============================================================================

# Singleton instance
_outreach_engine = None

def get_outreach_engine() -> DirectOutreachEngine:
    """Get singleton outreach engine instance"""
    global _outreach_engine
    if _outreach_engine is None:
        _outreach_engine = DirectOutreachEngine()
    return _outreach_engine


async def send_direct_outreach(
    opportunity: Dict[str, Any],
    contact: Dict[str, Any]
) -> Optional[OutreachResult]:
    """
    Send direct outreach for an opportunity.
    Integrates with opportunity_engagement.
    """
    engine = get_outreach_engine()
    return await engine.process_opportunity(opportunity, contact)


# =============================================================================
# STANDALONE TEST
# =============================================================================

async def test_direct_outreach():
    """Test the direct outreach engine"""
    
    print("\n" + "=" * 70)
    print("🧪 TESTING DIRECT OUTREACH ENGINE")
    print("=" * 70)
    
    engine = DirectOutreachEngine()
    
    # Check configured channels
    print("\n📱 Channel Configuration:")
    stats = engine.get_stats()
    for channel, configured in stats['channels_configured'].items():
        status = "✅" if configured else "❌"
        print(f"   {status} {channel}")
    
    # Test proposal generation
    print("\n📝 Testing proposal generation...")
    generator = ProposalGenerator()
    
    test_opp = {
        'opportunity_id': 'test_123',
        'title': 'Need help building a Python automation script',
        'pain_point': 'Manual data entry taking too long',
        'estimated_value': 2000
    }
    
    test_contact = {
        'email': 'test@example.com',
        'name': 'John',
        'extraction_confidence': 0.8,
        'preferred_outreach': 'email'
    }
    
    proposal = await generator.generate_proposal(
        test_opp, test_contact, OutreachChannel.EMAIL
    )
    
    print(f"   Subject: {proposal.subject}")
    print(f"   Body preview: {proposal.body[:100]}...")
    print(f"   Channel: {proposal.channel.value}")
    print(f"   Recipient: {proposal.recipient}")
    
    # Test Twitter DM template (shorter)
    twitter_proposal = await generator.generate_proposal(
        test_opp, {'twitter_handle': 'johndoe', 'name': 'John'}, OutreachChannel.TWITTER_DM
    )
    print(f"\n   Twitter DM ({len(twitter_proposal.body)} chars):")
    print(f"   {twitter_proposal.body}")
    
    print("\n✅ Direct outreach engine test complete!")
    print(f"   Daily limit: {engine.max_daily_outreach}")
    print(f"   Min confidence: {engine.min_contact_confidence}")


if __name__ == "__main__":
    asyncio.run(test_direct_outreach())
