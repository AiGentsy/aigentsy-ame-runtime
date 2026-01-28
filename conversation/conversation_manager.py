"""
CONVERSATION MANAGER: Autonomous AI Conversations
=================================================

Monitors for replies to outreach and responds autonomously.
Uses Claude for intelligent, contextual responses.

Flow:
1. Check for new replies (Twitter DMs, emails)
2. Load conversation history and contract context
3. Generate AI response using Claude
4. Send response back via same channel
5. Continue until handshake acceptance or decline
"""

import os
import json
import logging
import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# Persistence
DATA_DIR = Path(__file__).parent.parent / "data"
CONVERSATIONS_FILE = DATA_DIR / "conversations.json"


class ConversationState(Enum):
    INITIAL_SENT = "initial_sent"
    IN_CONVERSATION = "in_conversation"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    HANDSHAKE_ACCEPTED = "accepted"
    DECLINED = "declined"
    STALE = "stale"


@dataclass
class ConversationMessage:
    """A single message in a conversation"""
    from_us: bool
    text: str
    timestamp: str
    platform: str = "twitter"
    message_id: Optional[str] = None


@dataclass
class Conversation:
    """A conversation with a potential client"""
    id: str
    platform: str  # twitter, email
    user_id: str
    username: str
    contract_id: str
    opportunity_id: str
    state: str = "initial_sent"
    messages: List[Dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    our_twitter_id: Optional[str] = None


class ConversationManager:
    """
    Manages autonomous conversations across platforms.

    Monitors for replies and generates AI responses.
    """

    def __init__(self):
        self.conversations: Dict[str, Conversation] = {}
        self.twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
        self.twitter_access = os.getenv('TWITTER_ACCESS_TOKEN')
        self.twitter_access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.twitter_api_secret = os.getenv('TWITTER_API_SECRET')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.our_twitter_id = os.getenv('TWITTER_USER_ID')  # Our account's Twitter ID
        self.last_dm_check = datetime.now(timezone.utc) - timedelta(minutes=5)

        # Load persisted conversations
        self._load_conversations()

        logger.info(f"ConversationManager initialized with {len(self.conversations)} conversations")

    def _load_conversations(self):
        """Load conversations from persistent storage"""
        try:
            if CONVERSATIONS_FILE.exists():
                with open(CONVERSATIONS_FILE, 'r') as f:
                    data = json.load(f)
                    for conv_id, conv_data in data.get('conversations', {}).items():
                        self.conversations[conv_id] = Conversation(**conv_data)
                    logger.info(f"Loaded {len(self.conversations)} conversations")
        except Exception as e:
            logger.warning(f"Could not load conversations: {e}")

    def _save_conversations(self):
        """Save conversations to persistent storage"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                'conversations': {cid: asdict(c) for cid, c in self.conversations.items()},
                'saved_at': datetime.now(timezone.utc).isoformat()
            }
            with open(CONVERSATIONS_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save conversations: {e}")

    def register_outreach(
        self,
        platform: str,
        user_id: str,
        username: str,
        contract_id: str,
        opportunity_id: str,
        initial_message: str,
        message_id: Optional[str] = None
    ) -> str:
        """
        Register an outreach message so we can track replies.

        Call this after sending a DM/email.
        """
        conv_id = f"{platform}_{user_id}_{contract_id}"

        conversation = Conversation(
            id=conv_id,
            platform=platform,
            user_id=user_id,
            username=username,
            contract_id=contract_id,
            opportunity_id=opportunity_id,
            state="initial_sent",
            messages=[{
                'from_us': True,
                'text': initial_message,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'platform': platform,
                'message_id': message_id
            }]
        )

        self.conversations[conv_id] = conversation
        self._save_conversations()

        logger.info(f"Registered outreach conversation: {conv_id}")
        return conv_id

    async def check_for_replies(self) -> List[Dict]:
        """
        Check all platforms for new replies.

        Returns list of reply dicts with conversation context.
        """
        replies = []

        # Check Twitter DMs
        if self.twitter_bearer and self.twitter_access:
            twitter_replies = await self._check_twitter_dms()
            replies.extend(twitter_replies)

        # Check Twitter mentions (for public reply responses)
        if self.twitter_bearer and self.twitter_access:
            mention_replies = await self._check_twitter_mentions()
            replies.extend(mention_replies)

        # Check emails (via webhook queue - Resend sends webhooks)
        # email_replies = await self._check_email_replies()
        # replies.extend(email_replies)

        return replies

    async def _check_twitter_dms(self) -> List[Dict]:
        """Check for new Twitter DM replies - including orphaned conversations from before registration"""
        replies = []

        try:
            # Get DM conversations using OAuth 1.0a
            from requests_oauthlib import OAuth1
            import requests
            import re

            auth = OAuth1(
                self.twitter_api_key,
                client_secret=self.twitter_api_secret,
                resource_owner_key=self.twitter_access,
                resource_owner_secret=self.twitter_access_secret
            )

            # First, get our user ID if we don't have it
            if not self.our_twitter_id:
                me_resp = requests.get(
                    "https://api.twitter.com/2/users/me",
                    auth=auth
                )
                if me_resp.status_code == 200:
                    self.our_twitter_id = me_resp.json().get('data', {}).get('id')
                    logger.info(f"Got our Twitter ID: {self.our_twitter_id}")

            if not self.our_twitter_id:
                logger.warning("Could not get Twitter user ID")
                return replies

            # Get DM events
            dm_resp = requests.get(
                "https://api.twitter.com/2/dm_events",
                params={
                    "dm_event.fields": "id,text,created_at,sender_id,dm_conversation_id,participant_ids",
                    "event_types": "MessageCreate",
                    "max_results": 50
                },
                auth=auth
            )

            if dm_resp.status_code != 200:
                logger.warning(f"Twitter DM check failed: {dm_resp.status_code} - {dm_resp.text}")
                return replies

            dm_data = dm_resp.json()
            events = dm_data.get('data', [])

            logger.info(f"Checking {len(events)} DM events")

            # Track which message IDs we've already processed this run
            processed_this_run = set()

            for event in events:
                sender_id = event.get('sender_id')
                msg_id = event.get('id')
                msg_text = event.get('text', '')
                dm_conv_id = event.get('dm_conversation_id')

                # Skip our own messages
                if sender_id == self.our_twitter_id:
                    continue

                # Skip if already processed this run
                if msg_id in processed_this_run:
                    continue
                processed_this_run.add(msg_id)

                # Check if this is from a known conversation
                conv = self._find_conversation_by_user('twitter', sender_id)

                if conv:
                    # Known conversation - check if message is new
                    msg_id = event.get('id')
                    if any(m.get('message_id') == msg_id for m in conv.messages):
                        continue  # Already processed this message

                    # Check if message is new (after last activity)
                    msg_time = event.get('created_at', '')
                    if msg_time and conv.last_activity:
                        try:
                            msg_dt = datetime.fromisoformat(msg_time.replace('Z', '+00:00'))
                            last_dt = datetime.fromisoformat(conv.last_activity.replace('Z', '+00:00'))
                            if msg_dt <= last_dt:
                                continue  # Already processed
                        except:
                            pass

                    replies.append({
                        'platform': 'twitter',
                        'conversation_id': conv.id,
                        'user_id': sender_id,
                        'username': conv.username,
                        'message': msg_text,
                        'message_id': msg_id,
                        'contract_id': conv.contract_id,
                        'opportunity_id': conv.opportunity_id,
                        'dm_conversation_id': dm_conv_id
                    })
                    logger.info(f"Found reply from known @{conv.username}: {msg_text[:50]}...")

                else:
                    # Unknown conversation - check if we sent them a DM first (orphaned outreach)
                    # Look for our messages in this DM conversation
                    our_msg = await self._find_our_message_in_conversation(dm_conv_id, auth)

                    if our_msg:
                        # We did reach out to this person - auto-create conversation
                        username = await self._get_twitter_username(sender_id, auth)

                        # Try to extract contract_id from our original message
                        contract_id = self._extract_contract_id(our_msg)

                        # Create new conversation on-the-fly
                        conv_id = f"twitter_{sender_id}_orphan_{msg_id[:8]}"
                        new_conv = Conversation(
                            id=conv_id,
                            platform='twitter',
                            user_id=sender_id,
                            username=username or f"user_{sender_id}",
                            contract_id=contract_id or 'unknown',
                            opportunity_id='orphan',
                            state='in_conversation',
                            messages=[
                                {
                                    'from_us': True,
                                    'text': our_msg,
                                    'timestamp': datetime.now(timezone.utc).isoformat(),
                                    'platform': 'twitter'
                                }
                            ]
                        )
                        self.conversations[conv_id] = new_conv
                        self._save_conversations()

                        logger.info(f"Auto-created conversation for orphan DM from @{username}")

                        replies.append({
                            'platform': 'twitter',
                            'conversation_id': conv_id,
                            'user_id': sender_id,
                            'username': username or f"user_{sender_id}",
                            'message': msg_text,
                            'message_id': msg_id,
                            'contract_id': contract_id or 'unknown',
                            'opportunity_id': 'orphan',
                            'dm_conversation_id': dm_conv_id
                        })

        except Exception as e:
            logger.error(f"Error checking Twitter DMs: {e}", exc_info=True)

        return replies

    async def _check_twitter_mentions(self) -> List[Dict]:
        """
        Check for Twitter mentions (public replies to our tweets).

        When we send a public reply to someone's tweet, they may reply back
        by mentioning us. This catches those responses.
        """
        replies = []

        try:
            from requests_oauthlib import OAuth1
            import requests
            import re

            auth = OAuth1(
                self.twitter_api_key,
                client_secret=self.twitter_api_secret,
                resource_owner_key=self.twitter_access,
                resource_owner_secret=self.twitter_access_secret
            )

            # First, get our user ID if we don't have it
            if not self.our_twitter_id:
                me_resp = requests.get(
                    "https://api.twitter.com/2/users/me",
                    auth=auth
                )
                if me_resp.status_code == 200:
                    self.our_twitter_id = me_resp.json().get('data', {}).get('id')
                    logger.info(f"Got our Twitter ID: {self.our_twitter_id}")

            if not self.our_twitter_id:
                return replies

            # Get recent mentions
            mentions_resp = requests.get(
                f"https://api.twitter.com/2/users/{self.our_twitter_id}/mentions",
                params={
                    "tweet.fields": "created_at,author_id,conversation_id,in_reply_to_user_id,text",
                    "expansions": "author_id",
                    "user.fields": "username",
                    "max_results": 20
                },
                auth=auth
            )

            if mentions_resp.status_code != 200:
                logger.warning(f"Twitter mentions check failed: {mentions_resp.status_code}")
                return replies

            data = mentions_resp.json()
            mentions = data.get('data', [])
            users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

            logger.info(f"Checking {len(mentions)} Twitter mentions")

            for mention in mentions:
                author_id = mention.get('author_id')
                tweet_id = mention.get('id')
                text = mention.get('text', '')
                conversation_id = mention.get('conversation_id')

                # Skip our own tweets
                if author_id == self.our_twitter_id:
                    continue

                # Get username
                user = users.get(author_id, {})
                username = user.get('username', f'user_{author_id}')

                # Check if we have a conversation with this user
                conv = self._find_conversation_by_user('twitter', author_id)

                # Also check by username (public replies may not have user_id registered)
                if not conv:
                    conv = self._find_conversation_by_username('twitter', username)

                if conv:
                    # Check if we already processed this tweet
                    if any(m.get('message_id') == tweet_id for m in conv.messages):
                        continue

                    replies.append({
                        'platform': 'twitter_mention',
                        'conversation_id': conv.id,
                        'user_id': author_id,
                        'username': username,
                        'message': text,
                        'message_id': tweet_id,
                        'contract_id': conv.contract_id,
                        'opportunity_id': conv.opportunity_id,
                        'tweet_id': tweet_id,
                        'conversation_thread_id': conversation_id
                    })
                    logger.info(f"Found mention reply from @{username}: {text[:50]}...")

                else:
                    # Unknown user mentioning us - might be responding to our public reply
                    # Check if this is a reply in a thread we started
                    if conversation_id:
                        # Create orphan conversation for tracking
                        conv_id = f"twitter_mention_{author_id}_{tweet_id[:8]}"
                        new_conv = Conversation(
                            id=conv_id,
                            platform='twitter',
                            user_id=author_id,
                            username=username,
                            contract_id='unknown',
                            opportunity_id='mention',
                            state='in_conversation',
                            messages=[]
                        )
                        self.conversations[conv_id] = new_conv
                        self._save_conversations()

                        replies.append({
                            'platform': 'twitter_mention',
                            'conversation_id': conv_id,
                            'user_id': author_id,
                            'username': username,
                            'message': text,
                            'message_id': tweet_id,
                            'contract_id': 'unknown',
                            'opportunity_id': 'mention',
                            'tweet_id': tweet_id,
                            'conversation_thread_id': conversation_id
                        })
                        logger.info(f"New mention from @{username}: {text[:50]}...")

        except Exception as e:
            logger.error(f"Error checking Twitter mentions: {e}", exc_info=True)

        return replies

    def _find_conversation_by_username(self, platform: str, username: str) -> Optional[Conversation]:
        """Find conversation by platform and username"""
        for conv in self.conversations.values():
            if conv.platform == platform and conv.username.lower() == username.lower():
                return conv
        return None

    async def _find_our_message_in_conversation(self, dm_conv_id: str, auth) -> Optional[str]:
        """Find if we sent a message in this DM conversation (outreach detection)"""
        try:
            import requests

            # Get messages in this specific conversation
            resp = requests.get(
                f"https://api.twitter.com/2/dm_conversations/{dm_conv_id}/dm_events",
                params={
                    "dm_event.fields": "id,text,sender_id,created_at",
                    "max_results": 20
                },
                auth=auth
            )

            if resp.status_code == 200:
                events = resp.json().get('data', [])
                for event in events:
                    if event.get('sender_id') == self.our_twitter_id:
                        # Found our message - this was outreach
                        return event.get('text', '')

        except Exception as e:
            logger.warning(f"Could not check conversation history: {e}")

        return None

    async def _get_twitter_username(self, user_id: str, auth) -> Optional[str]:
        """Get Twitter username from user ID"""
        try:
            import requests

            resp = requests.get(
                f"https://api.twitter.com/2/users/{user_id}",
                auth=auth
            )

            if resp.status_code == 200:
                return resp.json().get('data', {}).get('username')

        except Exception as e:
            logger.warning(f"Could not get username for {user_id}: {e}")

        return None

    def _extract_contract_id(self, message: str) -> Optional[str]:
        """Extract contract ID from a message containing client-room URL"""
        import re

        # Look for client-room/esc_xxxx pattern
        match = re.search(r'client-room/(esc_[a-f0-9]+)', message)
        if match:
            return match.group(1)

        # Also try t.co shortened URLs - we can't expand them, but log it
        if 't.co/' in message:
            logger.info("Message contains shortened URL - contract ID extraction may fail")

        return None

    def _find_conversation_by_user(self, platform: str, user_id: str) -> Optional[Conversation]:
        """Find conversation by platform and user ID"""
        for conv in self.conversations.values():
            if conv.platform == platform and conv.user_id == user_id:
                return conv
        return None

    async def process_reply(self, reply: Dict) -> Optional[str]:
        """
        Process a reply and generate AI response.

        Returns the response sent, or None if failed.
        """
        conv = self.conversations.get(reply['conversation_id'])
        if not conv:
            logger.warning(f"Conversation not found: {reply['conversation_id']}")
            return None

        user_message = reply['message']

        # Add user message to history
        conv.messages.append({
            'from_us': False,
            'text': user_message,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'platform': reply['platform'],
            'message_id': reply.get('message_id')
        })
        conv.last_activity = datetime.now(timezone.utc).isoformat()

        # Update state based on message content
        conv.state = self._determine_state(user_message, conv.state)

        # Check for explicit decline or acceptance
        if self._is_decline(user_message):
            conv.state = ConversationState.DECLINED.value
            self._save_conversations()
            logger.info(f"Conversation {conv.id} declined")
            return None  # Don't respond to explicit declines

        if self._is_acceptance(user_message):
            conv.state = ConversationState.HANDSHAKE_ACCEPTED.value

        # Generate AI response
        response = await self._generate_response(conv, user_message)

        if not response:
            logger.error(f"Failed to generate response for {conv.id}")
            return None

        # Send response
        sent = await self._send_response(reply['platform'], reply, response)

        if sent:
            # Add our response to history
            conv.messages.append({
                'from_us': True,
                'text': response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'platform': reply['platform']
            })
            conv.last_activity = datetime.now(timezone.utc).isoformat()
            self._save_conversations()

            logger.info(f"Sent response to @{conv.username}: {response[:50]}...")
            return response

        return None

    def _determine_state(self, message: str, current_state: str) -> str:
        """Determine conversation state from message content"""
        msg_lower = message.lower()

        # Check for interest signals
        if any(word in msg_lower for word in ['interested', 'tell me more', 'sounds good', 'how does', 'what if']):
            return ConversationState.CLOSING.value

        # Check for objections
        if any(word in msg_lower for word in ['but', 'however', 'concerned', 'worried', 'expensive', 'too much', 'not sure']):
            return ConversationState.OBJECTION_HANDLING.value

        # Check for questions
        if '?' in message:
            return ConversationState.IN_CONVERSATION.value

        return ConversationState.IN_CONVERSATION.value

    def _is_decline(self, message: str) -> bool:
        """Check if message is an explicit decline"""
        msg_lower = message.lower()
        decline_phrases = [
            'not interested', 'no thanks', 'no thank you', 'don\'t contact',
            'stop messaging', 'leave me alone', 'unsubscribe', 'spam',
            'don\'t need', 'already have', 'not looking'
        ]
        return any(phrase in msg_lower for phrase in decline_phrases)

    def _is_acceptance(self, message: str) -> bool:
        """Check if message signals acceptance"""
        msg_lower = message.lower()
        accept_phrases = [
            'let\'s do it', 'i\'m in', 'sign me up', 'sounds great',
            'let\'s go', 'ok deal', 'deal', 'yes please'
        ]
        return any(phrase in msg_lower for phrase in accept_phrases)

    async def _generate_response(self, conv: Conversation, user_message: str) -> Optional[str]:
        """Generate AI response using Claude"""
        if not self.anthropic_key:
            logger.error("ANTHROPIC_API_KEY not set")
            return None

        try:
            # Load contract data for context (may be None for orphan conversations)
            contract_data = await self._load_contract_data(conv.contract_id)

            # Build conversation history
            history_text = self._build_history_text(conv.messages)

            # Try to detect project type from conversation history if no contract
            title_for_type = contract_data.get('title', '')
            if not title_for_type and conv.messages:
                # Use our first message to detect type
                first_msg = conv.messages[0].get('text', '') if conv.messages else ''
                title_for_type = first_msg

            # Determine project type for personalization
            try:
                from direct_outreach_engine import detect_project_type
                project_type = detect_project_type(title_for_type)
            except:
                project_type = 'default'

            type_labels = {
                'development': 'dev', 'backend': 'backend dev', 'frontend': 'frontend dev',
                'automation': 'automation', 'design': 'designer', 'content': 'content writer',
                'data': 'data analyst', 'marketing': 'marketing', 'default': 'AI'
            }
            type_label = type_labels.get(project_type, 'AI')

            # Build system prompt
            has_contract = conv.contract_id and conv.contract_id != 'unknown'
            client_room_url = contract_data.get('client_room_url', '')

            if has_contract and client_room_url:
                opportunity_context = f"""THE OPPORTUNITY:
Title: {contract_data.get('title', 'their project')}
Market rate: ${contract_data.get('market_rate', 2000):,}
Your price: ${contract_data.get('our_price', 1200):,}
Client room: {client_room_url}"""
            else:
                opportunity_context = """THE OPPORTUNITY:
You reached out about helping with their project. The link to their proposal was in your first message."""

            system_prompt = f"""You are AiGentsy, an autonomous AI that actually does the work (not just chat about it).

YOUR IDENTITY:
- You're their autonomous {type_label} AiGentsy
- Think ChatGPT, but instead of chatting, you actually do the work
- You work 24/7, no breaks, no mistakes
- You deliver within the hour, for half the typical cost

YOUR GOAL:
Guide them toward checking out the proposal link. Don't be pushy - just helpful, friendly, and conversational.

{opportunity_context}

CONVERSATION STATE: {conv.state}

YOUR TONE:
- Conversational and friendly (like chatting with a cool friend who can code/design/etc)
- Confident but not arrogant
- Answer questions directly
- NOT salesy or pushy
- Keep it SHORT (under 280 characters for Twitter DMs)

CONVERSATION HISTORY:
{history_text}

USER'S LATEST MESSAGE:
{user_message}

Generate a natural response. If they seem interested, reference the link in the first message. If they have questions, answer them. Be warm and human. Keep it under 280 characters."""

            # Call Claude
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 300,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": user_message}
                        ]
                    }
                )

                if resp.is_success:
                    data = resp.json()
                    response = data['content'][0]['text']

                    # Ensure under 280 chars for Twitter
                    if len(response) > 280:
                        response = response[:277] + "..."

                    return response
                else:
                    logger.error(f"Claude API error: {resp.status_code} - {resp.text}")
                    return None

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None

    def _build_history_text(self, messages: List[Dict]) -> str:
        """Build conversation history text for context"""
        lines = []
        for msg in messages[-5:]:  # Last 5 messages
            speaker = "You (AiGentsy)" if msg['from_us'] else "Them"
            lines.append(f"{speaker}: {msg['text']}")
        return "\n".join(lines)

    async def _load_contract_data(self, contract_id: str) -> Dict:
        """Load contract data for response context"""
        try:
            from contracts.milestone_escrow import get_milestone_escrow
            escrow = get_milestone_escrow()
            contract = escrow.get_contract(contract_id)

            if contract:
                contract_dict = escrow.to_dict(contract)

                # Get pricing
                from pricing_calculator import calculate_full_pricing
                pricing = calculate_full_pricing({'title': contract_dict.get('title', ''), 'value': contract_dict.get('total_amount_usd', 0)})

                return {
                    'title': contract_dict.get('title', 'your project'),
                    'market_rate': pricing.market_rate,
                    'our_price': pricing.our_price,
                    'client_room_url': contract_dict.get('client_room_url', '')
                }
        except Exception as e:
            logger.warning(f"Could not load contract data: {e}")

        return {
            'title': 'your project',
            'market_rate': 2000,
            'our_price': 1200,
            'client_room_url': ''
        }

    async def _send_response(self, platform: str, reply: Dict, response: str) -> bool:
        """Send response via appropriate platform"""
        if platform == 'twitter':
            return await self._send_twitter_dm(reply, response)
        elif platform == 'twitter_mention':
            return await self._send_twitter_reply(reply, response)
        elif platform == 'email':
            return await self._send_email_reply(reply, response)
        return False

    async def _send_twitter_dm(self, reply: Dict, response: str) -> bool:
        """Send Twitter DM response"""
        try:
            from requests_oauthlib import OAuth1
            import requests

            auth = OAuth1(
                self.twitter_api_key,
                client_secret=self.twitter_api_secret,
                resource_owner_key=self.twitter_access,
                resource_owner_secret=self.twitter_access_secret
            )

            # Use dm_conversation_id if available, otherwise send to user
            dm_conv_id = reply.get('dm_conversation_id')

            if dm_conv_id:
                # Reply in existing conversation
                dm_resp = requests.post(
                    f"https://api.twitter.com/2/dm_conversations/{dm_conv_id}/messages",
                    json={"text": response},
                    auth=auth
                )
            else:
                # Send new DM
                dm_resp = requests.post(
                    f"https://api.twitter.com/2/dm_conversations/with/{reply['user_id']}/messages",
                    json={"text": response},
                    auth=auth
                )

            if dm_resp.status_code in [200, 201]:
                return True
            else:
                logger.error(f"Failed to send Twitter DM: {dm_resp.status_code} - {dm_resp.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending Twitter DM: {e}")
            return False

    async def _send_twitter_reply(self, reply: Dict, response: str) -> bool:
        """Send public Twitter reply (to a mention)"""
        try:
            from requests_oauthlib import OAuth1
            import requests

            auth = OAuth1(
                self.twitter_api_key,
                client_secret=self.twitter_api_secret,
                resource_owner_key=self.twitter_access,
                resource_owner_secret=self.twitter_access_secret
            )

            # Include @mention in reply
            username = reply.get('username', '')
            tweet_id = reply.get('tweet_id')

            if not tweet_id:
                logger.error("No tweet_id for public reply")
                return False

            # Format reply with @mention
            reply_text = f"@{username} {response}"

            # Ensure under 280 chars
            if len(reply_text) > 280:
                reply_text = reply_text[:277] + "..."

            # Post reply tweet
            tweet_resp = requests.post(
                "https://api.twitter.com/2/tweets",
                json={
                    "text": reply_text,
                    "reply": {
                        "in_reply_to_tweet_id": str(tweet_id)
                    }
                },
                auth=auth
            )

            if tweet_resp.status_code in [200, 201]:
                logger.info(f"Posted public reply to @{username}")
                return True
            else:
                logger.error(f"Failed to post reply: {tweet_resp.status_code} - {tweet_resp.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending Twitter reply: {e}")
            return False

    async def _send_email_reply(self, reply: Dict, response: str) -> bool:
        """Send email reply via Resend"""
        # TODO: Implement email replies
        return False

    async def run_monitor_loop(self):
        """
        Main monitoring loop - check for replies and respond.

        Run this on a schedule (every 2-5 minutes).
        """
        logger.info("Checking for conversation replies...")

        try:
            # Check for new replies
            replies = await self.check_for_replies()

            logger.info(f"Found {len(replies)} new replies")

            # Process each reply
            for reply in replies:
                response = await self.process_reply(reply)
                if response:
                    logger.info(f"Responded to {reply.get('username')}")

                # Small delay between responses to avoid rate limits
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")

    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        states = {}
        for conv in self.conversations.values():
            states[conv.state] = states.get(conv.state, 0) + 1

        return {
            'total_conversations': len(self.conversations),
            'by_state': states,
            'platforms': {
                'twitter': len([c for c in self.conversations.values() if c.platform == 'twitter']),
                'email': len([c for c in self.conversations.values() if c.platform == 'email'])
            }
        }


# Singleton instance
_conversation_manager = None


def get_conversation_manager() -> ConversationManager:
    """Get singleton conversation manager instance"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
