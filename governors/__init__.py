"""
GOVERNORS - Risk & Spend Control System
=======================================

Hard caps, automatic degradation, and ND-JSON event emission
for autonomous operation within safe boundaries.

Usage:
    from governors import guard_spend, get_spend_status, reset_daily_caps
"""

from .governor_runtime import (
    guard_spend,
    get_spend_status,
    reset_daily_caps,
    emit_governor_event,
    get_degradation_level,
    check_module_cap,
    GovernorState
)

__all__ = [
    "guard_spend",
    "get_spend_status",
    "reset_daily_caps",
    "emit_governor_event",
    "get_degradation_level",
    "check_module_cap",
    "GovernorState"
]
