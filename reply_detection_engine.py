"""
REPLY DETECTION ENGINE
======================
Detects and processes replies to outreach across all channels.

CHANNELS MONITORED:
- Email (Resend webhooks: delivered, opened, clicked, replied, bounced)
- Twitter DMs (Twitter API inbox check)
- Reddit DMs (Reddit API inbox check)
- LinkedIn Messages (LinkedIn API - limited)

FLOW:
1. Webhooks/polling detect new replies
2. Replies stored in queue with context
3. Conversation engine picks up and responds
4. Track reply rates for optimization

INTEGRATES WITH:
- direct_outreach_engine.py (sent messages)
- conversation_engine.py (handles replies)
- main.py (webhook endpoints)
"""

import asyncio
import os
import json
import hashlib
import hmac
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import httpx


# =============================================================================
# CONFIGURATION
# =============================================================================

class ReplyChannel(Enum):
    EMAIL = "email"
    TWITTER_DM = "twitter_dm"
    REDDIT_DM = "reddit_dm"
    LINKEDIN_MESSAGE = "linkedin_message"
    PLATFORM_COMMENT = "platform_comment"


class ReplyStatus(Enum):
    NEW = "new"
    PROCESSING = "processing"
    RESPONDED = "responded"
    CONVERTED = "converted"
    CLOSED = "closed"


class EmailEvent(Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


@dataclass
class DetectedReply:
    """A reply detected from any channel"""
    reply_id: str
    channel: ReplyChannel
    original_proposal_id: str  # Links back to our outreach
    original_opportunity_id: str
    
    # Sender info
    sender_email: Optional[str] = None
    sender_handle: Optional[str] = None
    sender_name: Optional[str] = None
    
    # Content
    subject: Optional[str] = None
    body: str = ""
    
    # Metadata
    received_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: ReplyStatus = ReplyStatus.NEW
    sentiment: Optional[str] = None  # positive, negative, neutral, interested
    intent: Optional[str] = None  # interested, question, objection, not_interested, spam
    
    # Tracking
    response_time_hours: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reply_id': self.reply_id,
            'channel': self.channel.value,
            'original_proposal_id': self.original_proposal_id,
            'original_opportunity_id': self.original_opportunity_id,
            'sender_email': self.sender_email,
            'sender_handle': self.sender_handle,
            'sender_name': self.sender_name,
            'subject': self.subject,
            'body': self.body,
            'received_at': self.received_at,
            'status': self.status.value,
            'sentiment': self.sentiment,
            'intent': self.intent,
            'response_time_hours': self.response_time_hours
        }


@dataclass
class EmailEventData:
    """Data from Resend webhook"""
    event_type: EmailEvent
    email_id: str
    to_email: str
    from_email: str
    subject: str
    timestamp: str
    
    # Optional based on event type
    reply_body: Optional[str] = None
    click_url: Optional[str] = None
    open_count: int = 0
    
    # Link to our outreach
    proposal_id: Optional[str] = None


# =============================================================================
# REPLY DETECTION ENGINE
# =============================================================================

class ReplyDetectionEngine:
    """
    Monitors all channels for replies to outreach.
    Queues replies for conversation engine.
    """
    
    def __init__(self):
        # API Keys
        self.resend_webhook_secret = os.getenv("RESEND_WEBHOOK_SECRET", "")
        self.twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN", "")
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID", "")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
        self.reddit_refresh_token = os.getenv("REDDIT_REFRESH_TOKEN", "")
        
        # Reply queue
        self.reply_queue: List[DetectedReply] = []
        self.processed_replies: Dict[str, DetectedReply] = {}
        
        # Email event tracking (for opens, clicks before reply)
        self.email_events: Dict[str, List[EmailEventData]] = {}  # email_id -> events
        
        # Proposal tracking (to link replies back to outreach)
        self.sent_proposals: Dict[str, Dict] = {}  # proposal_id -> proposal data
        self.email_to_proposal: Dict[str, str] = {}  # recipient_email -> proposal_id
        
        # Stats
        self.stats = {
            'emails_sent': 0,
            'emails_delivered': 0,
            'emails_opened': 0,
            'emails_clicked': 0,
            'emails_replied': 0,
            'emails_bounced': 0,
            'twitter_dms_sent': 0,
            'twitter_dms_replied': 0,
            'reddit_dms_sent': 0,
            'reddit_dms_replied': 0,
            'total_replies': 0,
            'replies_converted': 0,
        }
    
    # =========================================================================
    # PROPOSAL TRACKING
    # =========================================================================
    
    def track_sent_proposal(self, proposal_id: str, proposal_data: Dict):
        """Track a sent proposal so we can link replies back"""
        self.sent_proposals[proposal_id] = {
            **proposal_data,
            'sent_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Map email to proposal for quick lookup
        if proposal_data.get('recipient_email'):
            self.email_to_proposal[proposal_data['recipient_email'].lower()] = proposal_id
        
        # Update stats
        channel = proposal_data.get('channel', 'email')
        if channel == 'email':
            self.stats['emails_sent'] += 1
        elif channel == 'twitter_dm':
            self.stats['twitter_dms_sent'] += 1
        elif channel == 'reddit_dm':
            self.stats['reddit_dms_sent'] += 1
    
    def get_proposal_for_email(self, email: str) -> Optional[Dict]:
        """Get proposal data for an email recipient"""
        proposal_id = self.email_to_proposal.get(email.lower())
        if proposal_id:
            return self.sent_proposals.get(proposal_id)
        return None
    
    # =========================================================================
    # RESEND WEBHOOK PROCESSING
    # =========================================================================
    
    def verify_resend_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Resend webhook signature"""
        if not self.resend_webhook_secret:
            return True  # Skip verification if no secret configured
        
        expected = hmac.new(
            self.resend_webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    async def process_resend_webhook(self, event_data: Dict) -> Optional[DetectedReply]:
        """
        Process incoming Resend webhook event.
        
        Event types:
        - email.sent
        - email.delivered
        - email.opened
        - email.clicked
        - email.bounced
        - email.complained
        - email.delivery_delayed
        
        Note: Resend doesn't have a direct "replied" event.
        We detect replies by monitoring inbox or using email forwarding.
        """
        event_type = event_data.get('type', '')
        data = event_data.get('data', {})
        
        email_id = data.get('email_id', '')
        to_email = data.get('to', [''])[0] if isinstance(data.get('to'), list) else data.get('to', '')
        from_email = data.get('from', '')
        subject = data.get('subject', '')
        
        # Map to our enum
        event_map = {
            'email.sent': EmailEvent.SENT,
            'email.delivered': EmailEvent.DELIVERED,
            'email.opened': EmailEvent.OPENED,
            'email.clicked': EmailEvent.CLICKED,
            'email.bounced': EmailEvent.BOUNCED,
            'email.complained': EmailEvent.COMPLAINED,
        }
        
        event_enum = event_map.get(event_type)
        if not event_enum:
            return None
        
        # Create event record
        email_event = EmailEventData(
            event_type=event_enum,
            email_id=email_id,
            to_email=to_email,
            from_email=from_email,
            subject=subject,
            timestamp=datetime.now(timezone.utc).isoformat(),
            click_url=data.get('click', {}).get('url') if event_type == 'email.clicked' else None,
        )
        
        # Store event
        if email_id not in self.email_events:
            self.email_events[email_id] = []
        self.email_events[email_id].append(email_event)
        
        # Update stats
        if event_enum == EmailEvent.DELIVERED:
            self.stats['emails_delivered'] += 1
        elif event_enum == EmailEvent.OPENED:
            self.stats['emails_opened'] += 1
        elif event_enum == EmailEvent.CLICKED:
            self.stats['emails_clicked'] += 1
        elif event_enum == EmailEvent.BOUNCED:
            self.stats['emails_bounced'] += 1
        
        # For opens/clicks, we might want to prioritize follow-up
        if event_enum in [EmailEvent.OPENED, EmailEvent.CLICKED]:
            proposal = self.get_proposal_for_email(to_email)
            if proposal:
                print(f"📬 Email {event_enum.value}: {to_email} (proposal: {proposal.get('proposal_id')})")
        
        return None  # No reply detected from these events
    
    async def process_email_reply(self, reply_data: Dict) -> DetectedReply:
        """
        Process an email reply (from inbox monitoring or forwarding).
        
        reply_data:
        - from_email: sender's email
        - to_email: our email (that received reply)
        - subject: email subject
        - body: email body text
        - received_at: timestamp
        """
        from_email = reply_data.get('from_email', '')
        subject = reply_data.get('subject', '')
        body = reply_data.get('body', '')
        
        # Find the original proposal
        proposal = self.get_proposal_for_email(from_email)
        proposal_id = proposal.get('proposal_id', 'unknown') if proposal else 'unknown'
        opportunity_id = proposal.get('opportunity_id', 'unknown') if proposal else 'unknown'
        
        # Calculate response time
        response_time = None
        if proposal and proposal.get('sent_at'):
            sent_at = datetime.fromisoformat(proposal['sent_at'].replace('Z', '+00:00'))
            received_at = datetime.now(timezone.utc)
            response_time = (received_at - sent_at).total_seconds() / 3600  # hours
        
        # Analyze intent
        intent = self._analyze_reply_intent(body)
        sentiment = self._analyze_sentiment(body)
        
        # Create reply record
        reply = DetectedReply(
            reply_id=f"reply_{hashlib.md5(f'{from_email}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}",
            channel=ReplyChannel.EMAIL,
            original_proposal_id=proposal_id,
            original_opportunity_id=opportunity_id,
            sender_email=from_email,
            sender_name=reply_data.get('from_name', ''),
            subject=subject,
            body=body,
            received_at=datetime.now(timezone.utc).isoformat(),
            status=ReplyStatus.NEW,
            sentiment=sentiment,
            intent=intent,
            response_time_hours=response_time
        )
        
        # Add to queue
        self.reply_queue.append(reply)
        self.stats['emails_replied'] += 1
        self.stats['total_replies'] += 1
        
        print(f"📩 New email reply from {from_email} - Intent: {intent}, Sentiment: {sentiment}")
        
        return reply
    
    # =========================================================================
    # TWITTER DM MONITORING
    # =========================================================================
    
    async def check_twitter_dms(self) -> List[DetectedReply]:
        """
        Check Twitter DMs for replies.
        Requires Twitter API v2 with DM read access.
        """
        if not self.twitter_bearer:
            return []
        
        replies = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Get DM events (last 24 hours)
                url = "https://api.twitter.com/2/dm_events"
                headers = {"Authorization": f"Bearer {self.twitter_bearer}"}
                params = {
                    "dm_event.fields": "id,text,sender_id,created_at",
                    "max_results": 100
                }
                
                response = await client.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get('data', [])
                    
                    for event in events:
                        # Check if this is a reply to our DM (not from us)
                        sender_id = event.get('sender_id', '')
                        
                        # Skip our own messages
                        # You'd need to store your own Twitter user ID to filter
                        
                        event_id = event.get('id', '')
                        
                        # Check if already processed
                        if event_id in self.processed_replies:
                            continue
                        
                        # Create reply
                        reply = DetectedReply(
                            reply_id=f"twitter_{event_id}",
                            channel=ReplyChannel.TWITTER_DM,
                            original_proposal_id='',  # Need to link from sender
                            original_opportunity_id='',
                            sender_handle=sender_id,  # Would need to resolve to handle
                            body=event.get('text', ''),
                            received_at=event.get('created_at', datetime.now(timezone.utc).isoformat()),
                            status=ReplyStatus.NEW,
                            intent=self._analyze_reply_intent(event.get('text', '')),
                            sentiment=self._analyze_sentiment(event.get('text', ''))
                        )
                        
                        replies.append(reply)
                        self.reply_queue.append(reply)
                        self.processed_replies[event_id] = reply
                        
                        self.stats['twitter_dms_replied'] += 1
                        self.stats['total_replies'] += 1
                
                elif response.status_code == 429:
                    print("⚠️ Twitter API rate limited")
                else:
                    print(f"⚠️ Twitter DM check failed: {response.status_code}")
                    
        except Exception as e:
            print(f"⚠️ Twitter DM check error: {e}")
        
        return replies
    
    # =========================================================================
    # REDDIT DM MONITORING
    # =========================================================================
    
    async def check_reddit_dms(self) -> List[DetectedReply]:
        """
        Check Reddit inbox for replies.
        Requires Reddit API OAuth.
        """
        if not all([self.reddit_client_id, self.reddit_client_secret]):
            return []
        
        replies = []
        
        try:
            async with httpx.AsyncClient() as client:
                # Get access token
                auth = (self.reddit_client_id, self.reddit_client_secret)
                token_url = "https://www.reddit.com/api/v1/access_token"
                token_data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self.reddit_refresh_token
                }
                
                token_response = await client.post(
                    token_url, 
                    auth=auth, 
                    data=token_data,
                    headers={"User-Agent": "AiGentsy/1.0"},
                    timeout=30
                )
                
                if token_response.status_code != 200:
                    print(f"⚠️ Reddit token refresh failed: {token_response.status_code}")
                    return []
                
                access_token = token_response.json().get('access_token')
                
                # Get inbox messages
                inbox_url = "https://oauth.reddit.com/message/inbox"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "User-Agent": "AiGentsy/1.0"
                }
                
                response = await client.get(inbox_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    messages = data.get('data', {}).get('children', [])
                    
                    for msg in messages:
                        msg_data = msg.get('data', {})
                        msg_id = msg_data.get('id', '')
                        
                        # Check if already processed
                        if msg_id in self.processed_replies:
                            continue
                        
                        # Only process unread messages
                        if msg_data.get('new', False):
                            reply = DetectedReply(
                                reply_id=f"reddit_{msg_id}",
                                channel=ReplyChannel.REDDIT_DM,
                                original_proposal_id='',
                                original_opportunity_id='',
                                sender_handle=msg_data.get('author', ''),
                                subject=msg_data.get('subject', ''),
                                body=msg_data.get('body', ''),
                                received_at=datetime.fromtimestamp(
                                    msg_data.get('created_utc', 0), 
                                    timezone.utc
                                ).isoformat(),
                                status=ReplyStatus.NEW,
                                intent=self._analyze_reply_intent(msg_data.get('body', '')),
                                sentiment=self._analyze_sentiment(msg_data.get('body', ''))
                            )
                            
                            replies.append(reply)
                            self.reply_queue.append(reply)
                            self.processed_replies[msg_id] = reply
                            
                            self.stats['reddit_dms_replied'] += 1
                            self.stats['total_replies'] += 1
                            
        except Exception as e:
            print(f"⚠️ Reddit DM check error: {e}")
        
        return replies
    
    # =========================================================================
    # INTENT & SENTIMENT ANALYSIS
    # =========================================================================
    
    def _analyze_reply_intent(self, text: str) -> str:
        """
        Analyze reply to determine intent.
        Returns: interested, question, objection, not_interested, spam
        """
        text_lower = text.lower()
        
        # Interested signals
        interested_keywords = [
            'yes', 'interested', 'tell me more', 'sounds good', 'let\'s talk',
            'schedule', 'available', 'pricing', 'cost', 'how much', 'get started',
            'love to', 'would like', 'sign me up', 'let\'s do it', 'i\'m in'
        ]
        
        # Question signals
        question_keywords = [
            'how does', 'what is', 'can you', 'do you', 'would you', 'could you',
            '?', 'explain', 'example', 'portfolio', 'previous work', 'references'
        ]
        
        # Objection signals
        objection_keywords = [
            'too expensive', 'budget', 'not sure', 'need to think', 'check with',
            'maybe later', 'not right now', 'busy', 'already have', 'using'
        ]
        
        # Not interested signals
        not_interested_keywords = [
            'no thanks', 'not interested', 'unsubscribe', 'stop', 'remove',
            'don\'t contact', 'spam', 'go away', 'leave me alone'
        ]
        
        # Score each intent
        if any(kw in text_lower for kw in not_interested_keywords):
            return 'not_interested'
        
        if any(kw in text_lower for kw in interested_keywords):
            return 'interested'
        
        if any(kw in text_lower for kw in objection_keywords):
            return 'objection'
        
        if any(kw in text_lower for kw in question_keywords) or '?' in text:
            return 'question'
        
        # Default to question if we can't tell
        return 'question'
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        Basic sentiment analysis.
        Returns: positive, negative, neutral
        """
        text_lower = text.lower()
        
        positive_words = [
            'great', 'awesome', 'excellent', 'love', 'perfect', 'amazing',
            'thanks', 'thank you', 'appreciate', 'helpful', 'good', 'nice',
            'excited', 'looking forward', 'fantastic', 'wonderful'
        ]
        
        negative_words = [
            'no', 'not', 'don\'t', 'spam', 'stop', 'terrible', 'awful',
            'hate', 'annoying', 'waste', 'scam', 'bad', 'worst', 'horrible'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    # =========================================================================
    # QUEUE MANAGEMENT
    # =========================================================================
    
    def get_pending_replies(self, limit: int = 20) -> List[DetectedReply]:
        """Get replies waiting to be processed"""
        pending = [r for r in self.reply_queue if r.status == ReplyStatus.NEW]
        return pending[:limit]
    
    def get_high_priority_replies(self) -> List[DetectedReply]:
        """Get high-priority replies (interested intent)"""
        return [
            r for r in self.reply_queue 
            if r.status == ReplyStatus.NEW and r.intent == 'interested'
        ]
    
    def mark_reply_processing(self, reply_id: str):
        """Mark a reply as being processed"""
        for reply in self.reply_queue:
            if reply.reply_id == reply_id:
                reply.status = ReplyStatus.PROCESSING
                break
    
    def mark_reply_responded(self, reply_id: str):
        """Mark a reply as responded to"""
        for reply in self.reply_queue:
            if reply.reply_id == reply_id:
                reply.status = ReplyStatus.RESPONDED
                break
    
    def mark_reply_converted(self, reply_id: str):
        """Mark a reply as converted to deal"""
        for reply in self.reply_queue:
            if reply.reply_id == reply_id:
                reply.status = ReplyStatus.CONVERTED
                self.stats['replies_converted'] += 1
                break
    
    # =========================================================================
    # BATCH OPERATIONS
    # =========================================================================
    
    async def check_all_channels(self) -> Dict[str, List[DetectedReply]]:
        """Check all channels for new replies"""
        results = {
            'twitter': [],
            'reddit': [],
            'email': []  # Email replies come via webhook, not polling
        }
        
        # Check Twitter DMs
        results['twitter'] = await self.check_twitter_dms()
        
        # Check Reddit DMs
        results['reddit'] = await self.check_reddit_dms()
        
        total = len(results['twitter']) + len(results['reddit'])
        if total > 0:
            print(f"📬 Found {total} new replies across channels")
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reply detection stats"""
        # Calculate rates
        open_rate = (
            self.stats['emails_opened'] / self.stats['emails_delivered'] 
            if self.stats['emails_delivered'] > 0 else 0
        )
        reply_rate = (
            self.stats['total_replies'] / self.stats['emails_sent']
            if self.stats['emails_sent'] > 0 else 0
        )
        conversion_rate = (
            self.stats['replies_converted'] / self.stats['total_replies']
            if self.stats['total_replies'] > 0 else 0
        )
        
        return {
            **self.stats,
            'open_rate': round(open_rate * 100, 1),
            'reply_rate': round(reply_rate * 100, 1),
            'conversion_rate': round(conversion_rate * 100, 1),
            'pending_replies': len([r for r in self.reply_queue if r.status == ReplyStatus.NEW]),
            'high_priority': len(self.get_high_priority_replies())
        }


# =============================================================================
# SINGLETON
# =============================================================================

_reply_engine_instance = None

def get_reply_engine() -> ReplyDetectionEngine:
    global _reply_engine_instance
    if _reply_engine_instance is None:
        _reply_engine_instance = ReplyDetectionEngine()
    return _reply_engine_instance
