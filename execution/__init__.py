"""
EXECUTION: Instant Fulfillment System

Fast-path execution for high-intent opportunities.
Same-cycle contact & close.
"""

from .fast_path import FastPath, get_fast_path

__all__ = ['FastPath', 'get_fast_path']
