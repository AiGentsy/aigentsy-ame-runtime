"""
PLATFORMS: Platform Pack System

A unified interface for scraping different platforms with:
- API > Flow > Selectors priority
- Self-healing selectors
- Rate limit compliance
- OAuth integration
"""

from .pack_interface import PlatformPack, PackPriority
from .pack_registry import get_pack_registry, PackRegistry

__all__ = [
    'PlatformPack', 'PackPriority',
    'get_pack_registry', 'PackRegistry',
]
