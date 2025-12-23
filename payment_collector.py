"""
PAYMENT COLLECTOR - EXECUTION REVENUE TRACKING
Integrates with your existing Stripe for kit purchases
Extends it to track autonomous execution revenue

This uses your existing STRIPE keys from environment
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx

# Import your existing revenue tracking
try:
    from revenue_flows import calculate_base_fee, calculate_full_fee_with_premium
    from log_to_jsonbin import log_agent_update, get_user
    REVENUE_AVAILABLE = True
except:
    REVENUE_AVAILABLE = False


class PaymentCollector:
    """
    Tracks and reconciles revenue from autonomous executions
    
    Integration:
    - Uses existing Stripe (from kit purchases)
    - Tracks in JSONBin (like your other revenue)
    - Records in outcome_oracle
    - Enables reconciliation
    """
    
    def __init__(self):
        # Check if Stripe is available
        self.stripe_available = bool(os.getenv("STRIPE_SECRET_KEY"))
        
        if self.stripe_available:
            print("✅ Stripe integration available")
        else:
            print("⚠️ Stripe not configured - using tracking only")
    
    
    async def record_execution_revenue(
        self,
        execution_id: str,
        platform: str,
        opportunity_value: float,
        user: Optional[str] = None,
        status: str = "pending"
    ) -> Dict[str, Any]:
        """
        Record revenue from an execution
        
        Status flow:
        - pending: Work submitted, awaiting platform payment
        - confirmed: Platform confirmed payment
        - paid: Money in bank account
        - failed: Execution failed, no payment
        """
        
        # Calculate fees using existing revenue_flows logic
        if REVENUE_AVAILABLE:
            base_fee = calculate_base_fee(opportunity_value)
        else:
            # Fallback calculation
            base_fee = {
                "percent_fee": round(opportunity_value * 0.028, 2),
                "fixed_fee": 0.28,
                "total": round(opportunity_value * 0.028 + 0.28, 2)
            }
        
        # Calculate splits
        if user:
            # User opportunity: user gets 97.2%, AiGentsy gets 2.8%
            user_amount = round(opportunity_value * 0.972, 2)
            aigentsy_amount = base_fee["total"]
        else:
            # AiGentsy opportunity: AiGentsy gets 70% margin
            cost = round(opportunity_value * 0.30, 2)  # 30% cost
            aigentsy_amount = round(opportunity_value - cost, 2)  # 70% profit
            user_amount = 0
        
        # Create revenue record
        revenue_record = {
            "execution_id": execution_id,
            "platform": platform,
            "opportunity_value": opportunity_value,
            "user": user,
            "status": status,
            "fees": base_fee,
            "splits": {
                "user_amount": user_amount,
                "aigentsy_amount": aigentsy_amount,
                "cost": opportunity_value * 0.30 if not user else 0
            },
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "paid_at": None,
            "stripe_charge_id": None,
            "reconciled": False
        }
        
        # Save to JSONBin
        try:
            log_agent_update({
                "type": "execution_revenue",
                "data": revenue_record
            })
        except:
            print(f"⚠️ Could not save to JSONBin")
        
        return revenue_record
    
    
    async def mark_as_paid(
        self,
        execution_id: str,
        stripe_charge_id: Optional[str] = None,
        actual_amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Mark an execution as paid
        
        Called when:
        - Platform confirms payment
        - Stripe charge completes
        - Bank deposit arrives
        """
        
        # Update record in JSONBin
        update = {
            "execution_id": execution_id,
            "status": "paid",
            "paid_at": datetime.now(timezone.utc).isoformat(),
            "stripe_charge_id": stripe_charge_id,
            "actual_amount": actual_amount,
            "reconciled": True
        }
        
        try:
            log_agent_update({
                "type": "execution_payment_confirmed",
                "data": update
            })
        except:
            pass
        
        return update
    
    
    async def reconcile_daily_revenue(self, date: str = None) -> Dict[str, Any]:
        """
        Reconcile all revenue for a given day
        
        Compares:
        - Expected revenue (from executions)
        - Actual revenue (from Stripe/platform payments)
        - Identifies discrepancies
        """
        
        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Get all execution revenue records for this date
        # (This would query JSONBin in production)
        
        reconciliation = {
            "date": date,
            "total_executions": 0,
            "pending_payment": 0,
            "confirmed_payment": 0,
            "paid": 0,
            "failed": 0,
            "expected_revenue": 0.0,
            "actual_revenue": 0.0,
            "discrepancy": 0.0,
            "details": []
        }
        
        # Would populate from actual data
        
        return reconciliation
    
    
    async def get_revenue_stats(self) -> Dict[str, Any]:
        """
        Get current revenue statistics
        
        Returns overview of all execution revenue
        """
        
        # This would query JSONBin for all execution revenue records
        
        stats = {
            "total_revenue_tracked": 0.0,
            "total_paid": 0.0,
            "total_pending": 0.0,
            "by_platform": {},
            "by_status": {
                "pending": 0,
                "confirmed": 0,
                "paid": 0,
                "failed": 0
            },
            "user_earnings": 0.0,
            "aigentsy_earnings": 0.0
        }
        
        return stats


# Singleton instance
_payment_collector = None

def get_payment_collector() -> PaymentCollector:
    """Get singleton payment collector instance"""
    global _payment_collector
    if _payment_collector is None:
        _payment_collector = PaymentCollector()
    return _payment_collector


# Convenience functions for use in universal_executor
async def record_revenue(execution_id: str, platform: str, value: float, user: str = None):
    """Quick helper to record execution revenue"""
    collector = get_payment_collector()
    return await collector.record_execution_revenue(execution_id, platform, value, user)


async def mark_paid(execution_id: str, stripe_charge_id: str = None, amount: float = None):
    """Quick helper to mark execution as paid"""
    collector = get_payment_collector()
    return await collector.mark_as_paid(execution_id, stripe_charge_id, amount)


async def get_revenue_stats():
    """Quick helper to get revenue stats"""
    collector = get_payment_collector()
    return await collector.get_revenue_stats()
