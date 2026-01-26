"""
ROUTING: Opportunity Routing and Scoring

Uses existing AttentionRouter for Thompson Sampling
Adds inventory fit scoring and conversion optimization
Integrates with existing systems via AccessPanelAdapter
"""

from .inventory_fit import get_inventory_scorer, InventoryFitScorer
from .conversion_router import get_conversion_router, ConversionRouter
from .access_panel_adapter import get_access_panel_adapter, AccessPanelAdapter

__all__ = [
    'get_inventory_scorer', 'InventoryFitScorer',
    'get_conversion_router', 'ConversionRouter',
    'get_access_panel_adapter', 'AccessPanelAdapter',
]
