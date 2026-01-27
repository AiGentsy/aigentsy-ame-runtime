"""
EXECUTION: Instant Fulfillment System

Fast-path execution for high-intent opportunities.
Same-cycle contact & close.

Includes:
- Fast Path: Same-cycle contact & close
- Dual Track: Parallel PoC + outreach lanes
"""

from .fast_path import FastPath, get_fast_path
from .dual_track import get_dual_track_executor, DualTrackExecutor

__all__ = ['FastPath', 'get_fast_path', 'get_dual_track_executor', 'DualTrackExecutor']
