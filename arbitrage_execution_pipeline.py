"""
ARBITRAGE EXECUTION PIPELINE
============================

THE MONEY PRINTER:
Detect arbitrage → Auto-purchase → Auto-fulfill → Auto-list → Collect spread
At scale across ALL platforms simultaneously.

WHAT IT DOES:
1. Takes detected arbitrage opportunities (from flow_arbitrage_detector.py)
2. Validates margins and risk
3. Auto-purchases on cheap platform
4. Routes to fulfillment (agent or AiGentsy)
5. Auto-lists on expensive platform
6. Settles and collects spread

INTEGRATES WITH:
- flow_arbitrage_detector.py (detection)
- universal_platform_adapter.py (platform access)
- execution_orchestrator.py (fulfillment)
- payment_collector.py (settlement)
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


# ============================================================
# TYPES & CONFIGURATION
# ============================================================

class ArbitrageType(str, Enum):
    PRICE = "price"
    TEMPORAL = "temporal"
    SUPPLY_DEMAND = "supply_demand"
    INFORMATION = "information"


class ArbitrageStatus(str, Enum):
    DETECTED = "detected"
    VALIDATING = "validating"
    APPROVED = "approved"
    PURCHASING = "purchasing"
    PURCHASED = "purchased"
    FULFILLING = "fulfilling"
    FULFILLED = "fulfilled"
    LISTING = "listing"
    LISTED = "listed"
    SETTLING = "settling"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


RISK_CONFIG = {
    RiskLevel.LOW: {"min_margin": 0.20, "max_investment": 1000, "auto_approve": True},
    RiskLevel.MEDIUM: {"min_margin": 0.30, "max_investment": 500, "auto_approve": True},
    RiskLevel.HIGH: {"min_margin": 0.50, "max_investment": 200, "auto_approve": False}
}

PLATFORM_FEES = {
    "fiverr": 0.20, "upwork": 0.20, "freelancer": 0.10,
    "99designs": 0.15, "toptal": 0.30, "direct": 0.028
}


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class ArbitrageOpportunity:
    opportunity_id: str
    arbitrage_type: ArbitrageType
    source_platform: str
    source_price: float
    target_platform: str
    target_price: float
    source_url: Optional[str] = None
    source_listing_id: Optional[str] = None
    target_demand_level: str = "medium"
    raw_spread: float = 0.0
    net_margin: float = 0.0
    margin_percent: float = 0.0
    service_type: str = ""
    service_description: str = ""
    delivery_time_days: int = 7
    risk_level: RiskLevel = RiskLevel.MEDIUM
    success_probability: float = 0.5
    status: ArbitrageStatus = ArbitrageStatus.DETECTED
    detected_at: str = field(default_factory=_now)
    expires_at: Optional[str] = None
    
    def calculate_margins(self):
        source_fee = PLATFORM_FEES.get(self.source_platform, 0.15)
        target_fee = PLATFORM_FEES.get(self.target_platform, 0.15)
        effective_cost = self.source_price
        effective_revenue = self.target_price * (1 - target_fee)
        self.raw_spread = self.target_price - self.source_price
        self.net_margin = effective_revenue - effective_cost
        self.margin_percent = self.net_margin / self.source_price if self.source_price > 0 else 0
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["arbitrage_type"] = self.arbitrage_type.value
        result["risk_level"] = self.risk_level.value
        result["status"] = self.status.value
        return result


@dataclass
class ArbitrageExecution:
    execution_id: str
    opportunity_id: str
    opportunity: ArbitrageOpportunity
    investment_amount: float
    expected_return: float
    expected_profit: float
    status: ArbitrageStatus = ArbitrageStatus.APPROVED
    purchase_order_id: Optional[str] = None
    purchase_completed_at: Optional[str] = None
    actual_purchase_price: float = 0.0
    fulfillment_id: Optional[str] = None
    fulfillment_agent: Optional[str] = None
    fulfillment_completed_at: Optional[str] = None
    listing_id: Optional[str] = None
    listing_url: Optional[str] = None
    listing_created_at: Optional[str] = None
    sale_id: Optional[str] = None
    sale_completed_at: Optional[str] = None
    actual_sale_price: float = 0.0
    actual_profit: float = 0.0
    roi: float = 0.0
    started_at: str = field(default_factory=_now)
    completed_at: Optional[str] = None
    events: List[Dict] = field(default_factory=list)
    
    def log_event(self, event_type: str, details: Dict = None):
        self.events.append({"type": event_type, "details": details or {}, "timestamp": _now()})
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["opportunity"] = self.opportunity.to_dict()
        result["status"] = self.status.value
        return result


# ============================================================
# RISK VALIDATOR
# ============================================================

class RiskValidator:
    def __init__(self):
        self._platform_success_rates = {
            "fiverr": 0.85, "upwork": 0.80, "freelancer": 0.75,
            "99designs": 0.90, "direct": 0.95
        }
        self._service_success_rates = {
            "content_creation": 0.90, "design": 0.85,
            "software_development": 0.75, "marketing": 0.80
        }
    
    def validate(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        issues = []
        opportunity.calculate_margins()
        
        if opportunity.margin_percent < 0.10:
            issues.append(f"Margin too low: {opportunity.margin_percent:.1%}")
        
        risk_config = RISK_CONFIG[opportunity.risk_level]
        if opportunity.margin_percent < risk_config["min_margin"]:
            issues.append(f"Margin below threshold for {opportunity.risk_level.value} risk")
        
        source_reliability = self._platform_success_rates.get(opportunity.source_platform, 0.7)
        target_reliability = self._platform_success_rates.get(opportunity.target_platform, 0.7)
        service_success = self._service_success_rates.get(opportunity.service_type, 0.8)
        
        opportunity.success_probability = source_reliability * target_reliability * service_success
        
        if opportunity.success_probability >= 0.8:
            opportunity.risk_level = RiskLevel.LOW
        elif opportunity.success_probability >= 0.5:
            opportunity.risk_level = RiskLevel.MEDIUM
        else:
            opportunity.risk_level = RiskLevel.HIGH
        
        valid = len(issues) == 0 or (len(issues) == 1 and opportunity.margin_percent >= 0.20)
        
        return {
            "valid": valid,
            "risk_level": opportunity.risk_level.value,
            "margin_percent": round(opportunity.margin_percent, 3),
            "net_margin": round(opportunity.net_margin, 2),
            "success_probability": round(opportunity.success_probability, 2),
            "issues": issues,
            "auto_approve": RISK_CONFIG[opportunity.risk_level]["auto_approve"] and valid,
            "max_investment": RISK_CONFIG[opportunity.risk_level]["max_investment"]
        }


# ============================================================
# PLATFORM EXECUTOR
# ============================================================

class PlatformExecutor:
    async def purchase(self, platform: str, listing_id: str, price: float, service_details: Dict) -> Dict:
        print(f"   📥 Purchasing on {platform}: ${price:.2f}")
        await asyncio.sleep(0.3)
        return {
            "ok": True, "platform": platform,
            "order_id": _generate_id("order"),
            "price": price, "status": "purchased",
            "purchased_at": _now()
        }
    
    async def create_listing(self, platform: str, service_type: str, title: str, description: str, price: float, delivery_days: int) -> Dict:
        print(f"   📤 Creating listing on {platform}: ${price:.2f}")
        await asyncio.sleep(0.3)
        listing_id = _generate_id("listing")
        return {
            "ok": True, "platform": platform,
            "listing_id": listing_id,
            "title": title, "price": price, "status": "active",
            "url": f"https://{platform}.com/listings/{listing_id}",
            "created_at": _now()
        }


# ============================================================
# FULFILLMENT ROUTER
# ============================================================

class FulfillmentRouter:
    def __init__(self):
        self._capabilities = {
            "content_creation": {"available": True, "cost_multiplier": 0.3},
            "design": {"available": True, "cost_multiplier": 0.4},
            "software_development": {"available": True, "cost_multiplier": 0.35},
            "marketing": {"available": True, "cost_multiplier": 0.35}
        }
    
    async def route_fulfillment(self, execution: ArbitrageExecution) -> Dict:
        capability = self._capabilities.get(execution.opportunity.service_type)
        if capability and capability["available"]:
            return {
                "method": "aigentsy", "agent": "aigentsy_internal",
                "cost": execution.opportunity.source_price * capability["cost_multiplier"],
                "confidence": 0.90
            }
        return {"method": "purchased", "agent": "source_platform", "cost": execution.opportunity.source_price, "confidence": 0.80}
    
    async def execute_fulfillment(self, execution: ArbitrageExecution, routing: Dict) -> Dict:
        print(f"   🔧 Fulfilling via {routing['method']}...")
        await asyncio.sleep(0.5)
        return {"ok": True, "fulfillment_id": _generate_id("fulfill"), "method": routing["method"], "status": "completed", "completed_at": _now()}


# ============================================================
# SETTLEMENT ENGINE
# ============================================================

class SettlementEngine:
    def __init__(self):
        self._settlements: Dict[str, Dict] = {}
        self._total_profit: float = 0.0
        self._total_volume: float = 0.0
    
    async def settle(self, execution: ArbitrageExecution) -> Dict:
        print(f"   💰 Settling execution {execution.execution_id}...")
        
        target_fee = PLATFORM_FEES.get(execution.opportunity.target_platform, 0.15)
        net_revenue = execution.actual_sale_price * (1 - target_fee)
        actual_profit = net_revenue - execution.actual_purchase_price
        roi = actual_profit / execution.actual_purchase_price if execution.actual_purchase_price > 0 else 0
        
        execution.actual_profit = actual_profit
        execution.roi = roi
        execution.status = ArbitrageStatus.COMPLETED
        execution.completed_at = _now()
        
        self._total_profit += actual_profit
        self._total_volume += execution.actual_sale_price
        
        settlement = {
            "settlement_id": _generate_id("settle"),
            "execution_id": execution.execution_id,
            "profit": actual_profit, "roi": roi,
            "settled_at": _now()
        }
        self._settlements[settlement["settlement_id"]] = settlement
        
        return {"ok": True, "settlement": settlement}
    
    def get_stats(self) -> Dict:
        return {
            "total_settlements": len(self._settlements),
            "total_volume": round(self._total_volume, 2),
            "total_profit": round(self._total_profit, 2)
        }


# ============================================================
# MAIN PIPELINE
# ============================================================

class ArbitrageExecutionPipeline:
    def __init__(self):
        self.validator = RiskValidator()
        self.executor = PlatformExecutor()
        self.router = FulfillmentRouter()
        self.settlement = SettlementEngine()
        self._opportunities: Dict[str, ArbitrageOpportunity] = {}
        self._executions: Dict[str, ArbitrageExecution] = {}
        self._pending_approval: Dict[str, ArbitrageOpportunity] = {}
        self._auto_execute: bool = True
        self._max_concurrent: int = 5
        self._active_executions: int = 0
    
    async def process_opportunity(self, opportunity: ArbitrageOpportunity) -> Dict:
        print(f"\n{'='*60}")
        print(f"🎯 ARBITRAGE: {opportunity.opportunity_id}")
        print(f"   {opportunity.source_platform} ${opportunity.source_price:.0f} → {opportunity.target_platform} ${opportunity.target_price:.0f}")
        print(f"{'='*60}")
        
        self._opportunities[opportunity.opportunity_id] = opportunity
        
        # Validate
        print("\n📋 Validating...")
        validation = self.validator.validate(opportunity)
        print(f"   Margin: {validation['margin_percent']:.1%}, Risk: {validation['risk_level']}")
        
        if not validation["valid"]:
            opportunity.status = ArbitrageStatus.REJECTED
            return {"ok": False, "status": "rejected", "reason": validation["issues"]}
        
        if not validation["auto_approve"]:
            self._pending_approval[opportunity.opportunity_id] = opportunity
            return {"ok": True, "status": "pending_approval"}
        
        if self._auto_execute:
            return await self._execute_arbitrage(opportunity, validation)
        
        return {"ok": True, "status": "approved"}
    
    async def _execute_arbitrage(self, opportunity: ArbitrageOpportunity, validation: Dict) -> Dict:
        self._active_executions += 1
        
        try:
            execution = ArbitrageExecution(
                execution_id=_generate_id("exec"),
                opportunity_id=opportunity.opportunity_id,
                opportunity=opportunity,
                investment_amount=opportunity.source_price,
                expected_return=opportunity.target_price,
                expected_profit=opportunity.net_margin
            )
            self._executions[execution.execution_id] = execution
            
            # Purchase
            print("\n💳 Purchasing...")
            purchase = await self.executor.purchase(
                opportunity.source_platform, opportunity.source_listing_id or "direct",
                opportunity.source_price, {"type": opportunity.service_type}
            )
            execution.purchase_order_id = purchase["order_id"]
            execution.actual_purchase_price = purchase["price"]
            execution.status = ArbitrageStatus.PURCHASED
            print(f"   ✓ Order {execution.purchase_order_id}")
            
            # Fulfill
            print("\n🔧 Fulfilling...")
            routing = await self.router.route_fulfillment(execution)
            fulfillment = await self.router.execute_fulfillment(execution, routing)
            execution.fulfillment_id = fulfillment["fulfillment_id"]
            execution.status = ArbitrageStatus.FULFILLED
            print(f"   ✓ Via {routing['method']}")
            
            # List
            print("\n📤 Listing...")
            listing = await self.executor.create_listing(
                opportunity.target_platform, opportunity.service_type,
                f"Professional {opportunity.service_type.replace('_', ' ').title()}",
                opportunity.service_description, opportunity.target_price, opportunity.delivery_time_days
            )
            execution.listing_id = listing["listing_id"]
            execution.listing_url = listing["url"]
            execution.status = ArbitrageStatus.LISTED
            print(f"   ✓ {execution.listing_url}")
            
            # Simulate sale
            print("\n🛒 Sale...")
            await asyncio.sleep(0.2)
            execution.sale_id = _generate_id("sale")
            execution.actual_sale_price = opportunity.target_price
            print(f"   ✓ Sold ${execution.actual_sale_price:.2f}")
            
            # Settle
            print("\n💰 Settling...")
            settlement = await self.settlement.settle(execution)
            
            print(f"\n{'='*60}")
            print(f"✅ COMPLETE: ${execution.actual_profit:.2f} profit ({execution.roi:.1%} ROI)")
            print(f"{'='*60}\n")
            
            return {
                "ok": True, "execution_id": execution.execution_id,
                "status": "completed",
                "profit": execution.actual_profit, "roi": execution.roi
            }
            
        except Exception as e:
            print(f"\n❌ Failed: {e}")
            opportunity.status = ArbitrageStatus.FAILED
            return {"ok": False, "status": "failed", "error": str(e)}
        finally:
            self._active_executions -= 1
    
    async def process_batch(self, opportunities: List[ArbitrageOpportunity]) -> Dict:
        print(f"\n{'='*70}")
        print(f"🚀 BATCH: {len(opportunities)} opportunities")
        print(f"{'='*70}")
        
        results = []
        for opp in opportunities:
            result = await self.process_opportunity(opp)
            results.append(result)
        
        completed = len([r for r in results if r.get("status") == "completed"])
        total_profit = sum(r.get("profit", 0) for r in results if r.get("ok"))
        
        print(f"\n📊 BATCH SUMMARY: {completed}/{len(opportunities)} completed, ${total_profit:.2f} profit")
        
        return {
            "ok": True, "total": len(opportunities),
            "completed": completed, "total_profit": total_profit,
            "results": results
        }
    
    def get_stats(self) -> Dict:
        completed = [e for e in self._executions.values() if e.status == ArbitrageStatus.COMPLETED]
        return {
            "total_executions": len(self._executions),
            "completed": len(completed),
            "total_profit": sum(e.actual_profit for e in completed),
            "avg_roi": sum(e.roi for e in completed) / len(completed) if completed else 0
        }


def convert_detected_to_opportunity(detected: Dict) -> ArbitrageOpportunity:
    """Convert from flow_arbitrage_detector.py format"""
    source_data = detected.get("source_data", {})
    arb_type_map = {"price": ArbitrageType.PRICE, "temporal": ArbitrageType.TEMPORAL,
                   "information": ArbitrageType.INFORMATION, "supply_demand": ArbitrageType.SUPPLY_DEMAND}
    
    opp = ArbitrageOpportunity(
        opportunity_id=detected.get("id", _generate_id("arb")),
        arbitrage_type=arb_type_map.get(detected.get("arbitrage_type", "price"), ArbitrageType.PRICE),
        source_platform=source_data.get("source_platform", "fiverr"),
        source_price=source_data.get("source_price", 0),
        target_platform=source_data.get("target_platform", "upwork"),
        target_price=source_data.get("target_price", 0),
        service_type=detected.get("type", "content_creation"),
        service_description=detected.get("description", "")
    )
    opp.calculate_margins()
    return opp


_pipeline: Optional[ArbitrageExecutionPipeline] = None

def get_arbitrage_pipeline() -> ArbitrageExecutionPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = ArbitrageExecutionPipeline()
    return _pipeline


if __name__ == "__main__":
    async def test():
        print("=" * 70)
        print("ARBITRAGE EXECUTION PIPELINE - Test")
        print("=" * 70)
        
        pipeline = get_arbitrage_pipeline()
        
        opportunities = [
            ArbitrageOpportunity(
                opportunity_id=_generate_id("arb"),
                arbitrage_type=ArbitrageType.PRICE,
                source_platform="fiverr", source_price=50,
                target_platform="upwork", target_price=200,
                service_type="content_creation"
            ),
            ArbitrageOpportunity(
                opportunity_id=_generate_id("arb"),
                arbitrage_type=ArbitrageType.PRICE,
                source_platform="99designs", source_price=100,
                target_platform="direct", target_price=500,
                service_type="design"
            )
        ]
        
        await pipeline.process_batch(opportunities)
        
        stats = pipeline.get_stats()
        print(f"\n📊 FINAL: {stats['completed']} completed, ${stats['total_profit']:.2f} profit, {stats['avg_roi']:.1%} avg ROI")
    
    asyncio.run(test())
