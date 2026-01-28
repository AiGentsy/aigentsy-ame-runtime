"""
AUTONOMOUS CONVERSATION SYSTEM
==============================

Monitors for replies to outreach messages and responds autonomously using AI.

Components:
- ReplyMonitor: Check Twitter DMs, emails for replies
- AIResponder: Generate contextual AI responses
- ConversationManager: Orchestrate conversation flow
"""

from .conversation_manager import ConversationManager, get_conversation_manager

__all__ = ['ConversationManager', 'get_conversation_manager']
