"""
Managers Package - Coordinates 60+ Subsystems
=============================================

Manager Pattern for clean orchestration:
- RevenueManager: 11 revenue-generating systems
- FinancialManager: 8 financial/OCL P2P systems
- ExecutionManager: 10 execution/verification systems
- DiscoveryManager: 15 discovery sources
- IntelligenceManager: 10 scoring/learning systems
"""

from .revenue_manager import RevenueManager, get_revenue_manager
from .financial_manager import FinancialManager, get_financial_manager
from .execution_manager import ExecutionManager, get_execution_manager
from .discovery_manager import DiscoveryManager, get_discovery_manager
from .intelligence_manager import IntelligenceManager, get_intelligence_manager

__all__ = [
    "RevenueManager", "get_revenue_manager",
    "FinancialManager", "get_financial_manager",
    "ExecutionManager", "get_execution_manager",
    "DiscoveryManager", "get_discovery_manager",
    "IntelligenceManager", "get_intelligence_manager"
]
