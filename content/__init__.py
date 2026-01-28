"""
CONTENT MODULE
==============

Universal multi-platform content creation and distribution.

Components:
- UniversalContentOrchestrator: One content → All platforms
- MultiPlatformEngagementBot: Automated engagement across platforms

All content uses billionaire-calm voice:
- Short verbs, proof-forward, no hype
- "We'll show you, not sell you"
"""

from .universal_content_orchestrator import (
    UniversalContentOrchestrator,
    ContentPackage,
    PostingResult,
    get_content_orchestrator,
    generate_and_post_contract_content,
    PLATFORM_CONFIGS
)

from .multi_platform_engagement import (
    MultiPlatformEngagementBot,
    EngagementTarget,
    EngagementResult,
    get_engagement_bot,
    run_daily_engagement,
    ENGAGEMENT_CONFIG
)

__all__ = [
    # Orchestrator
    'UniversalContentOrchestrator',
    'ContentPackage',
    'PostingResult',
    'get_content_orchestrator',
    'generate_and_post_contract_content',
    'PLATFORM_CONFIGS',
    # Engagement
    'MultiPlatformEngagementBot',
    'EngagementTarget',
    'EngagementResult',
    'get_engagement_bot',
    'run_daily_engagement',
    'ENGAGEMENT_CONFIG'
]
