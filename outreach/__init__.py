"""
OUTREACH MODULE
===============

Multi-channel outreach with PUBLIC engagement as primary strategy.

Components:
- PublicEngagementOrchestrator: Public comments/replies on hiring posts
- AutoReplySystem: Monitor and reply to engagement on our content
- SuccessStoryEngine: Generate and post success stories for brand building
- MultilingualOutreach: Multi-language support
- OutreachTracker: Spam prevention

Strategy: PUBLIC comments > DMs (DMs are restricted, public works 100%)

Unified Router: Routes ALL discovery (incl. Perplexity internet-wide search)
to the best channel per opportunity (comment, email, SMS, WhatsApp, DM).
"""
from .multilingual import get_multilingual_outreach, MultilingualOutreach
from .outreach_tracker import get_outreach_tracker, OutreachTracker

# Public Engagement (PRIMARY)
from .public_engagement_orchestrator import (
    PublicEngagementOrchestrator,
    PublicEngagementTarget,
    PublicEngagementResult,
    EngagementPlatform,
    PLATFORM_CONFIGS,
    get_public_engagement_orchestrator,
    run_public_engagement_cycle,
)

# Auto-Reply System
from .auto_reply_system import (
    AutoReplySystem,
    EngagementComment,
    AutoReplyResult,
    get_auto_reply_system,
    run_auto_reply_cycle,
)

# Success Story Engine
from .success_story_engine import (
    SuccessStoryEngine,
    SuccessStory,
    PostResult,
    get_success_story_engine,
    post_contract_success_story,
    run_content_campaign,
)

# Unified Engagement Router (ALL discovery → ALL channels)
from .unified_engagement_router import (
    UnifiedEngagementRouter,
    RoutedEngagement,
    EngagementChannel,
    get_unified_router,
    run_unified_engagement,
)

# Browser Automation (ZERO COST - uses existing accounts)
from .browser_automation import (
    BrowserAutomation,
    BrowserTarget,
    BrowserResult,
    get_browser_automation,
    run_browser_engagement,
)

__all__ = [
    # Multilingual
    'get_multilingual_outreach',
    'MultilingualOutreach',
    # Spam Prevention
    'get_outreach_tracker',
    'OutreachTracker',
    # Public Engagement (PRIMARY)
    'PublicEngagementOrchestrator',
    'PublicEngagementTarget',
    'PublicEngagementResult',
    'EngagementPlatform',
    'PLATFORM_CONFIGS',
    'get_public_engagement_orchestrator',
    'run_public_engagement_cycle',
    # Auto-Reply
    'AutoReplySystem',
    'EngagementComment',
    'AutoReplyResult',
    'get_auto_reply_system',
    'run_auto_reply_cycle',
    # Success Stories
    'SuccessStoryEngine',
    'SuccessStory',
    'PostResult',
    'get_success_story_engine',
    'post_contract_success_story',
    'run_content_campaign',
    # Unified Router (ALL channels)
    'UnifiedEngagementRouter',
    'RoutedEngagement',
    'EngagementChannel',
    'get_unified_router',
    'run_unified_engagement',
    # Browser Automation (ZERO COST)
    'BrowserAutomation',
    'BrowserTarget',
    'BrowserResult',
    'get_browser_automation',
    'run_browser_engagement',
]
