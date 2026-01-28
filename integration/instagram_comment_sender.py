"""
Instagram Comment Sender - Outreach via public comments
═══════════════════════════════════════════════════════════════════════════════

Post comments on Instagram posts as outreach.

WHY COMMENTS (not DMs):
- No follower restriction (100% delivery)
- Public social proof
- They can DM us back
- API supports automated comments

REQUIREMENTS:
- Instagram Business Account
- INSTAGRAM_ACCESS_TOKEN with instagram_basic, instagram_content_publish

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Instagram Graph API config
INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
INSTAGRAM_BUSINESS_ID = os.getenv('INSTAGRAM_BUSINESS_ID', '')
GRAPH_API_VERSION = 'v18.0'
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramCommentSender:
    """Send outreach comments on Instagram posts"""

    def __init__(self):
        self.access_token = INSTAGRAM_ACCESS_TOKEN
        self.business_id = INSTAGRAM_BUSINESS_ID
        self.available = bool(self.access_token)

        if self.available:
            logger.info("Instagram Comment Sender initialized")
        else:
            logger.warning("Instagram Comment Sender: Missing INSTAGRAM_ACCESS_TOKEN")

    async def send_comment(
        self,
        post_id: str,
        opportunity: Dict,
        client_room_url: str,
        pricing: Dict = None
    ) -> Dict:
        """
        Post a comment on an Instagram post.

        Args:
            post_id: Instagram media ID
            opportunity: Opportunity dict with title, etc.
            client_room_url: Link to client room
            pricing: Optional pricing info

        Returns:
            Result dict with success status
        """
        if not self.available:
            return {
                'success': False,
                'error': 'Instagram not configured (missing INSTAGRAM_ACCESS_TOKEN)'
            }

        # Create comment message
        message = self._create_comment_message(opportunity, client_room_url, pricing)

        try:
            import httpx

            async with httpx.AsyncClient(timeout=30) as client:
                # Post comment via Instagram Graph API
                url = f"{GRAPH_API_BASE}/{post_id}/comments"
                data = {
                    'message': message,
                    'access_token': self.access_token
                }

                response = await client.post(url, data=data)
                result = response.json()

                if result.get('id'):
                    comment_id = result['id']
                    logger.info(f"Instagram comment posted on {post_id}: {comment_id}")
                    return {
                        'success': True,
                        'method': 'instagram_comment',
                        'comment_id': comment_id,
                        'post_id': post_id,
                        'platform': 'instagram'
                    }
                else:
                    error_msg = result.get('error', {}).get('message', 'Unknown error')
                    logger.warning(f"Instagram comment failed: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg,
                        'details': result
                    }

        except Exception as e:
            logger.error(f"Instagram comment error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_comment_message(
        self,
        opportunity: Dict,
        client_room_url: str,
        pricing: Dict = None
    ) -> str:
        """
        Create Instagram comment message.

        Instagram comments allow up to 2,200 characters.
        Keep it concise for better engagement.
        """
        title = opportunity.get('title', '')
        title_lower = title.lower()

        # Detect project type
        if 'react' in title_lower or 'frontend' in title_lower:
            project_type = 'React dev'
        elif 'backend' in title_lower or 'api' in title_lower:
            project_type = 'backend dev'
        elif 'python' in title_lower:
            project_type = 'Python dev'
        elif 'fullstack' in title_lower or 'full stack' in title_lower:
            project_type = 'fullstack dev'
        elif 'design' in title_lower or 'ui' in title_lower:
            project_type = 'design'
        elif 'app' in title_lower or 'mobile' in title_lower:
            project_type = 'app dev'
        else:
            project_type = 'dev'

        # Build message
        if pricing and pricing.get('our_price'):
            message = f"""We team up all the best AI to build your AiGentsy!

Starting at ${pricing['our_price']:,.0f}, delivered within the hour. Free preview first - pay only if perfect.

DM us @AiGentsy to get started!"""
        else:
            message = f"""We team up all the best AI to build your AiGentsy!

Delivered within the hour. Free preview first - pay only if perfect.

DM us @AiGentsy to get started!"""

        return message

    async def reply_to_comment(
        self,
        comment_id: str,
        message: str
    ) -> Dict:
        """Reply to a comment (for conversations)"""
        if not self.available:
            return {'success': False, 'error': 'Instagram not configured'}

        try:
            import httpx

            async with httpx.AsyncClient(timeout=30) as client:
                url = f"{GRAPH_API_BASE}/{comment_id}/replies"
                data = {
                    'message': message,
                    'access_token': self.access_token
                }

                response = await client.post(url, data=data)
                result = response.json()

                if result.get('id'):
                    return {
                        'success': True,
                        'reply_id': result['id'],
                        'parent_comment_id': comment_id
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', {}).get('message', 'Unknown error')
                    }

        except Exception as e:
            logger.error(f"Instagram reply error: {e}")
            return {'success': False, 'error': str(e)}


# Singleton instance
_instagram_sender: Optional[InstagramCommentSender] = None


def get_instagram_sender() -> InstagramCommentSender:
    """Get singleton Instagram Comment Sender instance"""
    global _instagram_sender
    if _instagram_sender is None:
        _instagram_sender = InstagramCommentSender()
    return _instagram_sender


# Convenience function
async def send_instagram_comment(
    post_id: str,
    opportunity: Dict,
    client_room_url: str,
    pricing: Dict = None
) -> Dict:
    """Send Instagram comment outreach"""
    sender = get_instagram_sender()
    return await sender.send_comment(post_id, opportunity, client_room_url, pricing)
