"""
COMPLIANCE: Legal and Safety Guards

Modules:
- robots_guard: robots.txt compliance
- rate_limit: Per-host rate limiting
- do_not_touch: Blocked domains registry
"""

from .robots_guard import get_robots_guard, RobotsGuard
from .rate_limit import get_rate_limiter, RateLimiter
from .do_not_touch import get_dnt_registry, DNTRegistry

__all__ = [
    'get_robots_guard', 'RobotsGuard',
    'get_rate_limiter', 'RateLimiter',
    'get_dnt_registry', 'DNTRegistry',
]
