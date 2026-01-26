"""
INFRA: Pipeline Infrastructure for Production SLOs

- Ultra-fast queuing with idempotency
- Backpressure management
- SLO enforcement
"""

from .pipeline import Pipeline, SLOGuard, get_pipeline

__all__ = ['Pipeline', 'SLOGuard', 'get_pipeline']
