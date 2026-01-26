"""
SCHEMAS: Data Models and Validation

Modules:
- opportunity_v2: Universal opportunity schema
"""

from .opportunity_v2 import (
    OpportunityV2,
    OpportunityType,
    OpportunityStatus,
    ContactInfo,
    PricingInfo,
    EnrichmentData,
    normalize_opportunity,
)

__all__ = [
    'OpportunityV2',
    'OpportunityType',
    'OpportunityStatus',
    'ContactInfo',
    'PricingInfo',
    'EnrichmentData',
    'normalize_opportunity',
]
