"""
P2P OUTCOME ASSURANCE
=====================

Peer-to-peer outcome assurance using AIGx credits.
AiGentsy is the coordinator and fee scheduler, NOT the insurer.

This is NOT insurance - it's a P2P assurance pool where contributors
stake AIGx credits to back outcome delivery.

Usage:
    from assurance import quote_oap, stake_oap, settle_oap
"""

from .oap_peer import (
    quote_oap,
    stake_oap,
    settle_oap,
    get_pool_status,
    get_contributor_balance,
    OAPPool
)

__all__ = [
    "quote_oap",
    "stake_oap",
    "settle_oap",
    "get_pool_status",
    "get_contributor_balance",
    "OAPPool"
]
