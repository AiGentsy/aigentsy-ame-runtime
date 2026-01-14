"""
CONVERSATION AI ENGINE
======================
Multi-turn dialogue system that qualifies leads, handles objections, and closes deals.

CONVERSATION STAGES:
1. INITIAL_REPLY - They responded to outreach
2. QUALIFYING - Gathering budget, timeline, decision maker info
3. HANDLING_OBJECTION - Addressing concerns
4. PROPOSING - Sending formal proposal
5. NEGOTIATING - Price/scope adjustments
6. CLOSING - Getting commitment + deposit
7. CLOSED_WON - Deal done!
8. CLOSED_LOST - Not happening

CAPABILITIES:
- Intent detection from replies
- Smart response generation
- Objection handling playbook
- Dynamic proposal generation
- Automatic stage advancement
- Integration with contract/payment system

PHILOSOPHY:
- Be helpful, not pushy
- Qualify fast (don't waste time on bad fits)
- Address objections directly
- Make it easy to say yes
- Know when to walk away
"""

import os
import json
import hashlib
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import httpx


# =============================================================================
# CONFIGURATION
# =============================================================================

class ConversationStage(Enum):
    INITIAL_REPLY = "initial_reply"
    QUALIFYING = "qualifying"
    HANDLING_OBJECTION = "handling_objection"
    PROPOSING = "proposing"
    NEGOTIATING = "negotiating"
    CLOSING = "closing"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ReplyIntent(Enum):
    INTERESTED = "interested"
    QUESTION = "question"
    OBJECTION = "objection"
    NEGOTIATING = "negotiating"
    READY_TO_BUY = "ready_to_buy"
    NOT_INTERESTED = "not_interested"
    SPAM = "spam"


class ObjectionType(Enum):
    PRICE = "price"
    TIMING = "timing"
    TRUST = "trust"
    NEED_APPROVAL = "need_approval"
    ALREADY_HAVE = "already_have"
    NOT_PRIORITY = "not_priority"
    NEED_MORE_INFO = "need_more_info"


@dataclass
class QualificationData:
    """Data gathered during qualification"""
    budget_confirmed: bool = False
    budget_range: Optional[str] = None  # "500-1000", "1000-5000", etc.
    timeline_confirmed: bool = False
    timeline: Optional[str] = None  # "asap", "this_week", "this_month", "no_rush"
    decision_maker: bool = True  # Assume yes unless told otherwise
    needs_approval_from: Optional[str] = None
    specific_requirements: List[str] = field(default_factory=list)
    pain_points: List[str] = field(default_factory=list)
    
    def is_qualified(self) -> bool:
        """Check if lead is qualified enough to propose"""
        return self.budget_confirmed and self.timeline_confirmed
    
    def qualification_score(self) -> float:
        """Score from 0-1 based on qualification"""
        score = 0.0
        if self.budget_confirmed:
            score += 0.3
        if self.timeline_confirmed:
            score += 0.2
        if self.decision_maker:
            score += 0.2
        if self.specific_requirements:
            score += 0.15
        if self.pain_points:
            score += 0.15
        return min(score, 1.0)
    
    def to_dict(self) -> Dict:
        return {
            'budget_confirmed': self.budget_confirmed,
            'budget_range': self.budget_range,
            'timeline_confirmed': self.timeline_confirmed,
            'timeline': self.timeline,
            'decision_maker': self.decision_maker,
            'needs_approval_from': self.needs_approval_from,
            'specific_requirements': self.specific_requirements,
            'pain_points': self.pain_points,
            'is_qualified': self.is_qualified(),
            'score': self.qualification_score()
        }


@dataclass
class Conversation:
    """Tracks a full conversation with a prospect"""
    conversation_id: str
    opportunity_id: str
    proposal_id: str
    
    # Contact info
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    contact_handle: Optional[str] = None  # Twitter/Reddit/etc
    channel: str = "email"
    
    # Context from original opportunity
    original_title: str = ""
    original_pain_point: str = ""
    estimated_value: float = 1000
    
    # Conversation state
    stage: ConversationStage = ConversationStage.INITIAL_REPLY
    qualification: QualificationData = field(default_factory=QualificationData)
    
    # Message history
    messages: List[Dict] = field(default_factory=list)  # [{role, content, timestamp}]
    
    # Tracking
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_reply_at: Optional[str] = None
    response_count: int = 0
    
    # Outcome
    final_price: Optional[float] = None
    contract_sent: bool = False
    deposit_paid: bool = False
    
    def add_message(self, role: str, content: str):
        """Add a message to history"""
        self.messages.append({
            'role': role,  # 'prospect' or 'aigentsy'
            'content': content,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        self.updated_at = datetime.now(timezone.utc).isoformat()
        if role == 'prospect':
            self.last_reply_at = datetime.now(timezone.utc).isoformat()
            self.response_count += 1
    
    def get_last_message(self, role: str = None) -> Optional[Dict]:
        """Get most recent message, optionally filtered by role"""
        for msg in reversed(self.messages):
            if role is None or msg['role'] == role:
                return msg
        return None
    
    def to_dict(self) -> Dict:
        return {
            'conversation_id': self.conversation_id,
            'opportunity_id': self.opportunity_id,
            'proposal_id': self.proposal_id,
            'contact_email': self.contact_email,
            'contact_name': self.contact_name,
            'contact_handle': self.contact_handle,
            'channel': self.channel,
            'original_title': self.original_title,
            'original_pain_point': self.original_pain_point,
            'estimated_value': self.estimated_value,
            'stage': self.stage.value,
            'qualification': self.qualification.to_dict(),
            'message_count': len(self.messages),
            'response_count': self.response_count,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_reply_at': self.last_reply_at,
            'final_price': self.final_price,
            'contract_sent': self.contract_sent,
            'deposit_paid': self.deposit_paid
        }


# =============================================================================
# INTENT & OBJECTION DETECTION
# =============================================================================

class IntentDetector:
    """Detects intent and extracts info from prospect messages"""
    
    def __init__(self):
        # Intent patterns
        self.interested_patterns = [
            r'\b(yes|yeah|yep|sure|interested|sounds good|tell me more|let\'s do it)\b',
            r'\b(how (much|do we|can we)|what\'s the (price|cost|rate))\b',
            r'\b(when can you start|how (fast|quickly)|timeline)\b',
            r'\b(send (me|over)|let\'s (talk|chat|discuss))\b',
        ]
        
        self.question_patterns = [
            r'\?',
            r'\b(how|what|when|where|why|who|which|can you|do you|would you|could you)\b',
            r'\b(explain|example|portfolio|previous work|case study)\b',
        ]
        
        self.objection_patterns = [
            r'\b(too (expensive|much|high)|budget|can\'t afford|cheaper)\b',
            r'\b(not (sure|ready|now)|maybe later|need to think|busy)\b',
            r'\b(already (have|using)|competitor|alternative)\b',
            r'\b(check with|ask my|approval|boss|team)\b',
        ]
        
        self.not_interested_patterns = [
            r'\b(no thanks|not interested|unsubscribe|stop|remove)\b',
            r'\b(don\'t (contact|email|message)|spam|go away)\b',
        ]
        
        self.ready_patterns = [
            r'\b(let\'s (start|go|do it)|ready|sign me up|send (contract|invoice))\b',
            r'\b(where do i (pay|sign)|payment|deposit)\b',
        ]
        
        # Budget extraction patterns
        self.budget_patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|K)?',
            r'(\d+(?:,\d{3})*)\s*(?:dollars|usd|USD)',
            r'budget\s*(?:is|of|around)?\s*\$?\s*(\d+(?:,\d{3})*)',
        ]
        
        # Timeline patterns
        self.timeline_patterns = {
            'asap': [r'\b(asap|urgent|immediately|right away|today)\b'],
            'this_week': [r'\b(this week|few days|by friday)\b'],
            'this_month': [r'\b(this month|couple weeks|2-3 weeks)\b'],
            'flexible': [r'\b(no rush|whenever|flexible|no deadline)\b'],
        }
    
    def detect_intent(self, message: str) -> ReplyIntent:
        """Detect the primary intent of a message"""
        message_lower = message.lower()
        
        # Check not interested first (hard no)
        if any(re.search(p, message_lower) for p in self.not_interested_patterns):
            return ReplyIntent.NOT_INTERESTED
        
        # Check ready to buy (best case)
        if any(re.search(p, message_lower) for p in self.ready_patterns):
            return ReplyIntent.READY_TO_BUY
        
        # Check objections
        if any(re.search(p, message_lower) for p in self.objection_patterns):
            return ReplyIntent.OBJECTION
        
        # Check interested
        if any(re.search(p, message_lower) for p in self.interested_patterns):
            return ReplyIntent.INTERESTED
        
        # Check questions
        if any(re.search(p, message_lower) for p in self.question_patterns):
            return ReplyIntent.QUESTION
        
        # Default to question (safest assumption)
        return ReplyIntent.QUESTION
    
    def detect_objection_type(self, message: str) -> Optional[ObjectionType]:
        """Detect specific type of objection"""
        message_lower = message.lower()
        
        if re.search(r'\b(expensive|price|cost|budget|afford|cheaper)\b', message_lower):
            return ObjectionType.PRICE
        
        if re.search(r'\b(busy|time|later|not now|timing)\b', message_lower):
            return ObjectionType.TIMING
        
        if re.search(r'\b(trust|legit|scam|real|verify)\b', message_lower):
            return ObjectionType.TRUST
        
        if re.search(r'\b(boss|manager|team|approval|check with)\b', message_lower):
            return ObjectionType.NEED_APPROVAL
        
        if re.search(r'\b(already|using|have|competitor)\b', message_lower):
            return ObjectionType.ALREADY_HAVE
        
        if re.search(r'\b(priority|urgent|important|focus)\b', message_lower):
            return ObjectionType.NOT_PRIORITY
        
        if re.search(r'\b(more info|details|explain|understand)\b', message_lower):
            return ObjectionType.NEED_MORE_INFO
        
        return None
    
    def extract_budget(self, message: str) -> Optional[str]:
        """Extract budget from message"""
        for pattern in self.budget_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(',', '')
                try:
                    value = float(amount)
                    if 'k' in message.lower() or 'K' in message:
                        value *= 1000
                    return f"${int(value)}"
                except:
                    pass
        return None
    
    def extract_timeline(self, message: str) -> Optional[str]:
        """Extract timeline from message"""
        message_lower = message.lower()
        
        for timeline, patterns in self.timeline_patterns.items():
            if any(re.search(p, message_lower) for p in patterns):
                return timeline
        
        return None
    
    def extract_name(self, message: str) -> Optional[str]:
        """Try to extract name from message"""
        patterns = [
            r"(?:i'm|i am|my name is|this is|call me)\s+([A-Z][a-z]+)",
            r"(?:^|\n)([A-Z][a-z]+)\s+here",
            r"(?:regards|best|thanks),?\s*\n?\s*([A-Z][a-z]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).title()
        
        return None


# =============================================================================
# RESPONSE GENERATOR
# =============================================================================

class ResponseGenerator:
    """Generates contextual responses for different conversation stages"""
    
    def __init__(self):
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
        self.use_ai = bool(self.openrouter_key)
    
    async def generate_response(
        self,
        conversation: Conversation,
        intent: ReplyIntent,
        objection_type: Optional[ObjectionType] = None
    ) -> str:
        """Generate appropriate response based on context"""
        
        # Try AI generation first if available
        if self.use_ai:
            try:
                response = await self._generate_ai_response(conversation, intent, objection_type)
                if response:
                    return response
            except Exception as e:
                print(f"⚠️ AI response generation failed: {e}")
        
        # Fall back to templates
        return self._generate_template_response(conversation, intent, objection_type)
    
    async def _generate_ai_response(
        self,
        conversation: Conversation,
        intent: ReplyIntent,
        objection_type: Optional[ObjectionType]
    ) -> Optional[str]:
        """Generate response using AI"""
        
        # Build context
        context = f"""You are a sales assistant for AiGentsy, a fully autonomous fulfillment company.
        
CONTEXT:
- Original request: {conversation.original_title}
- Pain point: {conversation.original_pain_point}
- Estimated value: ${conversation.estimated_value}
- Current stage: {conversation.stage.value}
- Qualification score: {conversation.qualification.qualification_score():.0%}

CONVERSATION HISTORY:
{self._format_history(conversation)}

PROSPECT'S INTENT: {intent.value}
{f"OBJECTION TYPE: {objection_type.value}" if objection_type else ""}

INSTRUCTIONS:
- Be helpful and conversational, not salesy
- If they have questions, answer directly
- If they have objections, address them honestly
- If they're interested, move toward next step
- Keep responses concise (2-4 sentences)
- End with a clear call to action or question
- Don't use excessive punctuation or emojis

Generate a response:"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-3-haiku",
                        "messages": [{"role": "user", "content": context}],
                        "max_tokens": 300,
                        "temperature": 0.7
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"⚠️ OpenRouter error: {e}")
        
        return None
    
    def _format_history(self, conversation: Conversation) -> str:
        """Format conversation history for AI context"""
        lines = []
        for msg in conversation.messages[-6:]:  # Last 6 messages
            role = "THEM" if msg['role'] == 'prospect' else "US"
            lines.append(f"{role}: {msg['content'][:200]}")
        return "\n".join(lines) if lines else "(No history yet)"
    
    def _generate_template_response(
        self,
        conversation: Conversation,
        intent: ReplyIntent,
        objection_type: Optional[ObjectionType]
    ) -> str:
        """Generate response from templates"""
        
        name = conversation.contact_name or "there"
        
        # Handle by intent
        if intent == ReplyIntent.NOT_INTERESTED:
            return f"No problem at all, {name}! Thanks for letting me know. If things change in the future, feel free to reach out. Best of luck with everything!"
        
        if intent == ReplyIntent.READY_TO_BUY:
            return f"Awesome, {name}! Let's make this happen. I'll send over a quick service agreement with a deposit link. Once that's done, we'll have your project queued up within minutes. Sound good?"
        
        if intent == ReplyIntent.OBJECTION:
            return self._handle_objection(conversation, objection_type, name)
        
        if intent == ReplyIntent.INTERESTED:
            # Move to qualification
            if not conversation.qualification.budget_confirmed:
                return f"Great to hear you're interested, {name}! To make sure we're aligned, what budget range are you working with for this project?"
            elif not conversation.qualification.timeline_confirmed:
                return f"Perfect. And what's your timeline looking like? Do you need this ASAP or is there some flexibility?"
            else:
                return f"Sounds like we're a good fit, {name}. Based on what you've described, I'd estimate this at ${int(conversation.estimated_value)}. Want me to put together a formal proposal?"
        
        if intent == ReplyIntent.QUESTION:
            # Generic helpful response
            return f"Good question, {name}! AiGentsy is essentially your fully-staffed team on demand - we handle {conversation.original_pain_point} end-to-end, delivered in minutes not days. You only pay when you're 100% satisfied. What specific aspect would you like me to elaborate on?"
        
        # Default
        return f"Thanks for getting back to me, {name}! I'd love to learn more about what you're looking for. What's the most important thing you need help with right now?"
    
    def _handle_objection(
        self,
        conversation: Conversation,
        objection_type: Optional[ObjectionType],
        name: str
    ) -> str:
        """Generate objection handling response"""
        
        if objection_type == ObjectionType.PRICE:
            return f"I totally understand budget is a consideration, {name}. The good news is you only pay when you're satisfied with the result. We can also scope this in phases if that helps with cash flow. What range would work better for you?"
        
        if objection_type == ObjectionType.TIMING:
            return f"No rush at all, {name}. When would be a better time to revisit this? I can follow up then, or just ping me whenever you're ready."
        
        if objection_type == ObjectionType.TRUST:
            return f"That's a fair concern, {name}. We work on a satisfaction-guarantee basis - you don't pay until you approve the final deliverable. I can also share some examples of similar work we've done. Would that help?"
        
        if objection_type == ObjectionType.NEED_APPROVAL:
            return f"Makes sense, {name}. Happy to put together a quick overview you can share with your team. What information would be most helpful for them?"
        
        if objection_type == ObjectionType.ALREADY_HAVE:
            return f"Got it, {name}. Curious - what's working well with your current solution, and what could be better? Always good to understand the landscape."
        
        if objection_type == ObjectionType.NOT_PRIORITY:
            return f"Totally understand, {name}. When do you think this might move up in priority? I can check back in then."
        
        if objection_type == ObjectionType.NEED_MORE_INFO:
            return f"Of course, {name}! What would you like to know more about? Happy to explain our process, share examples, or walk through how we'd approach your specific situation."
        
        # Generic objection
        return f"I hear you, {name}. What would need to be different for this to work for you?"


# =============================================================================
# CONVERSATION ENGINE
# =============================================================================

class ConversationEngine:
    """Main engine for managing multi-turn sales conversations"""
    
    def __init__(self):
        self.intent_detector = IntentDetector()
        self.response_generator = ResponseGenerator()
        
        # Active conversations
        self.conversations: Dict[str, Conversation] = {}
        
        # Index by contact for quick lookup
        self.email_to_conversation: Dict[str, str] = {}
        self.handle_to_conversation: Dict[str, str] = {}
        
        # Stats
        self.stats = {
            'conversations_started': 0,
            'responses_sent': 0,
            'qualified_leads': 0,
            'proposals_sent': 0,
            'deals_closed': 0,
            'deals_lost': 0,
            'total_revenue': 0.0
        }
    
    def create_conversation(
        self,
        opportunity_id: str,
        proposal_id: str,
        contact_email: str = None,
        contact_name: str = None,
        contact_handle: str = None,
        channel: str = "email",
        title: str = "",
        pain_point: str = "",
        estimated_value: float = 1000
    ) -> Conversation:
        """Create a new conversation from outreach"""
        
        conv_id = f"conv_{hashlib.md5(f'{opportunity_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        
        conversation = Conversation(
            conversation_id=conv_id,
            opportunity_id=opportunity_id,
            proposal_id=proposal_id,
            contact_email=contact_email,
            contact_name=contact_name,
            contact_handle=contact_handle,
            channel=channel,
            original_title=title,
            original_pain_point=pain_point,
            estimated_value=estimated_value
        )
        
        # Store
        self.conversations[conv_id] = conversation
        
        # Index for lookup
        if contact_email:
            self.email_to_conversation[contact_email.lower()] = conv_id
        if contact_handle:
            self.handle_to_conversation[contact_handle.lower()] = conv_id
        
        self.stats['conversations_started'] += 1
        
        return conversation
    
    def get_conversation_by_email(self, email: str) -> Optional[Conversation]:
        """Find conversation by email"""
        conv_id = self.email_to_conversation.get(email.lower())
        return self.conversations.get(conv_id) if conv_id else None
    
    def get_conversation_by_handle(self, handle: str) -> Optional[Conversation]:
        """Find conversation by social handle"""
        conv_id = self.handle_to_conversation.get(handle.lower())
        return self.conversations.get(conv_id) if conv_id else None
    
    async def process_reply(
        self,
        conversation_id: str = None,
        email: str = None,
        handle: str = None,
        message: str = ""
    ) -> Tuple[Optional[Conversation], Optional[str]]:
        """
        Process an incoming reply and generate response.
        
        Returns: (conversation, response_text)
        """
        # Find conversation
        conversation = None
        
        if conversation_id:
            conversation = self.conversations.get(conversation_id)
        elif email:
            conversation = self.get_conversation_by_email(email)
        elif handle:
            conversation = self.get_conversation_by_handle(handle)
        
        if not conversation:
            return None, None
        
        # Add their message to history
        conversation.add_message('prospect', message)
        
        # Detect intent
        intent = self.intent_detector.detect_intent(message)
        objection_type = None
        
        if intent == ReplyIntent.OBJECTION:
            objection_type = self.intent_detector.detect_objection_type(message)
        
        # Extract any qualification data
        self._extract_qualification_data(conversation, message)
        
        # Update conversation stage
        self._update_stage(conversation, intent)
        
        # Generate response
        response = await self.response_generator.generate_response(
            conversation, intent, objection_type
        )
        
        # Add our response to history
        conversation.add_message('aigentsy', response)
        
        self.stats['responses_sent'] += 1
        
        # Check for qualification milestone
        if conversation.qualification.is_qualified() and not conversation.stage == ConversationStage.CLOSED_WON:
            self.stats['qualified_leads'] += 1
        
        return conversation, response
    
    def _extract_qualification_data(self, conversation: Conversation, message: str):
        """Extract and update qualification data from message"""
        
        # Extract budget
        budget = self.intent_detector.extract_budget(message)
        if budget:
            conversation.qualification.budget_confirmed = True
            conversation.qualification.budget_range = budget
        
        # Extract timeline
        timeline = self.intent_detector.extract_timeline(message)
        if timeline:
            conversation.qualification.timeline_confirmed = True
            conversation.qualification.timeline = timeline
        
        # Extract name
        name = self.intent_detector.extract_name(message)
        if name and not conversation.contact_name:
            conversation.contact_name = name
        
        # Check for approval mention
        if re.search(r'\b(boss|manager|team|approval|check with)\b', message.lower()):
            conversation.qualification.decision_maker = False
    
    def _update_stage(self, conversation: Conversation, intent: ReplyIntent):
        """Update conversation stage based on intent"""
        
        if intent == ReplyIntent.NOT_INTERESTED:
            conversation.stage = ConversationStage.CLOSED_LOST
            self.stats['deals_lost'] += 1
        
        elif intent == ReplyIntent.READY_TO_BUY:
            conversation.stage = ConversationStage.CLOSING
        
        elif intent == ReplyIntent.OBJECTION:
            conversation.stage = ConversationStage.HANDLING_OBJECTION
        
        elif intent == ReplyIntent.INTERESTED:
            if conversation.qualification.is_qualified():
                conversation.stage = ConversationStage.PROPOSING
            else:
                conversation.stage = ConversationStage.QUALIFYING
        
        elif conversation.stage == ConversationStage.INITIAL_REPLY:
            conversation.stage = ConversationStage.QUALIFYING
    
    def mark_proposal_sent(self, conversation_id: str, price: float):
        """Mark that a proposal was sent"""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            conversation.final_price = price
            conversation.stage = ConversationStage.NEGOTIATING
            self.stats['proposals_sent'] += 1
    
    def mark_contract_sent(self, conversation_id: str):
        """Mark that a contract was sent"""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            conversation.contract_sent = True
            conversation.stage = ConversationStage.CLOSING
    
    def mark_deal_closed(self, conversation_id: str, amount: float):
        """Mark deal as closed won"""
        conversation = self.conversations.get(conversation_id)
        if conversation:
            conversation.stage = ConversationStage.CLOSED_WON
            conversation.deposit_paid = True
            conversation.final_price = amount
            self.stats['deals_closed'] += 1
            self.stats['total_revenue'] += amount
    
    def get_conversations_by_stage(self, stage: ConversationStage) -> List[Conversation]:
        """Get all conversations at a specific stage"""
        return [c for c in self.conversations.values() if c.stage == stage]
    
    def get_hot_leads(self) -> List[Conversation]:
        """Get conversations that are close to closing"""
        hot_stages = [
            ConversationStage.PROPOSING,
            ConversationStage.NEGOTIATING,
            ConversationStage.CLOSING
        ]
        return [c for c in self.conversations.values() if c.stage in hot_stages]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversation stats"""
        return {
            **self.stats,
            'active_conversations': len([c for c in self.conversations.values() 
                                        if c.stage not in [ConversationStage.CLOSED_WON, ConversationStage.CLOSED_LOST]]),
            'hot_leads': len(self.get_hot_leads()),
            'qualification_rate': self.stats['qualified_leads'] / self.stats['conversations_started'] 
                                  if self.stats['conversations_started'] > 0 else 0,
            'close_rate': self.stats['deals_closed'] / self.stats['proposals_sent']
                          if self.stats['proposals_sent'] > 0 else 0
        }


# =============================================================================
# SINGLETON
# =============================================================================

_conversation_engine = None

def get_conversation_engine() -> ConversationEngine:
    global _conversation_engine
    if _conversation_engine is None:
        _conversation_engine = ConversationEngine()
    return _conversation_engine
