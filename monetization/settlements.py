"""
SETTLEMENTS
===========

Stripe/Bank/Wallet payouts and settlement processing.
Integrates with existing escrow_lite.py Stripe patterns.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import os

# Try to import Stripe
try:
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_AVAILABLE = bool(stripe.api_key)
except ImportError:
    STRIPE_AVAILABLE = False

# Import ledger for balance checks
from .ledger import get_balance, post_entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class Settlements:
    """
    Settlement processor for payouts.

    Supports:
    - Stripe payouts (Stripe Connect)
    - Balance transfers
    - Scheduled settlements
    """

    def __init__(self):
        self._pending: List[Dict[str, Any]] = []
        self._completed: List[Dict[str, Any]] = []
        self.config = {
            "min_payout_threshold": 25.0,
            "transaction_fee_pct": 0.005,
            "transaction_fee_min": 0.50,
            "max_daily_payout": 10000.0
        }

    def pending_count(self) -> int:
        """Count of pending settlements"""
        return len(self._pending)

    def check_payout_eligibility(self, entity: str) -> Dict[str, Any]:
        """Check if entity is eligible for payout"""
        balance = get_balance(entity)
        threshold = self.config["min_payout_threshold"]

        if balance < threshold:
            return {
                "eligible": False,
                "reason": "below_threshold",
                "balance": balance,
                "threshold": threshold,
                "needed": round(threshold - balance, 2)
            }

        return {
            "eligible": True,
            "balance": balance,
            "threshold": threshold
        }

    def calculate_payout(self, entity: str) -> Dict[str, Any]:
        """Calculate payout amount after fees"""
        balance = get_balance(entity)
        threshold = self.config["min_payout_threshold"]

        if balance < threshold:
            return {
                "ok": False,
                "reason": "below_threshold",
                "balance": balance
            }

        # Calculate transaction fee
        fee_pct = self.config["transaction_fee_pct"]
        fee_min = self.config["transaction_fee_min"]
        tx_fee = max(fee_min, round(balance * fee_pct, 2))

        net = round(balance - tx_fee, 2)

        return {
            "ok": True,
            "gross": balance,
            "tx_fee": tx_fee,
            "net": net,
            "fee_rate": round(tx_fee / balance * 100, 2) if balance > 0 else 0
        }

    async def initiate_payout(
        self,
        entity: str,
        *,
        stripe_account_id: str = None,
        method: str = "stripe"
    ) -> Dict[str, Any]:
        """
        Initiate a payout to entity.

        Methods:
        - stripe: Stripe Connect payout
        - balance: Internal balance transfer
        """
        calc = self.calculate_payout(entity)
        if not calc.get("ok"):
            return calc

        gross = calc["gross"]
        tx_fee = calc["tx_fee"]
        net = calc["net"]

        if method == "stripe" and STRIPE_AVAILABLE:
            if not stripe_account_id:
                return {"ok": False, "error": "stripe_account_id_required"}

            try:
                # Create Stripe transfer
                transfer = stripe.Transfer.create(
                    amount=int(net * 100),  # cents
                    currency="usd",
                    destination=stripe_account_id,
                    metadata={
                        "entity": entity,
                        "gross": str(gross),
                        "tx_fee": str(tx_fee),
                        "platform": "aigentsy"
                    }
                )

                # Record in ledger
                post_entry(
                    "payout",
                    f"entity:{entity}",
                    debit=gross,
                    credit=0,
                    meta={
                        "stripe_transfer_id": transfer.id,
                        "net": net,
                        "tx_fee": tx_fee
                    }
                )

                post_entry(
                    "tx_fee",
                    "entity:aigentsy_platform",
                    debit=0,
                    credit=tx_fee,
                    meta={"payout_entity": entity}
                )

                self._completed.append({
                    "entity": entity,
                    "gross": gross,
                    "net": net,
                    "tx_fee": tx_fee,
                    "method": "stripe",
                    "stripe_transfer_id": transfer.id,
                    "completed_at": _now_iso()
                })

                return {
                    "ok": True,
                    "method": "stripe",
                    "stripe_transfer_id": transfer.id,
                    "gross": gross,
                    "net": net,
                    "tx_fee": tx_fee
                }

            except stripe.error.StripeError as e:
                return {"ok": False, "error": str(e)}

        elif method == "balance":
            # Internal balance transfer (mock for now)
            post_entry(
                "payout",
                f"entity:{entity}",
                debit=gross,
                credit=0,
                meta={"method": "balance", "net": net, "tx_fee": tx_fee}
            )

            post_entry(
                "tx_fee",
                "entity:aigentsy_platform",
                debit=0,
                credit=tx_fee,
                meta={"payout_entity": entity}
            )

            self._completed.append({
                "entity": entity,
                "gross": gross,
                "net": net,
                "tx_fee": tx_fee,
                "method": "balance",
                "completed_at": _now_iso()
            })

            return {
                "ok": True,
                "method": "balance",
                "gross": gross,
                "net": net,
                "tx_fee": tx_fee
            }

        return {"ok": False, "error": f"unsupported_method:{method}"}

    def schedule_payout(
        self,
        entity: str,
        schedule_at: str = None
    ) -> Dict[str, Any]:
        """Schedule a payout for later processing"""
        calc = self.calculate_payout(entity)
        if not calc.get("ok"):
            return calc

        self._pending.append({
            "entity": entity,
            "gross": calc["gross"],
            "net": calc["net"],
            "tx_fee": calc["tx_fee"],
            "scheduled_at": schedule_at or _now_iso(),
            "status": "pending"
        })

        return {
            "ok": True,
            "scheduled": True,
            "entity": entity,
            "amount": calc["net"]
        }

    def get_pending_payouts(self) -> List[Dict[str, Any]]:
        """Get list of pending payouts"""
        return list(self._pending)

    def get_completed_payouts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of completed payouts"""
        return list(reversed(self._completed[-limit:]))


# Module-level singleton
_default_settlements = Settlements()


async def payout(entity: str, **kwargs) -> Dict[str, Any]:
    """Initiate payout using default settlements"""
    return await _default_settlements.initiate_payout(entity, **kwargs)


def calculate_payout(entity: str) -> Dict[str, Any]:
    """Calculate payout for entity"""
    return _default_settlements.calculate_payout(entity)


def check_eligibility(entity: str) -> Dict[str, Any]:
    """Check payout eligibility"""
    return _default_settlements.check_payout_eligibility(entity)


def queue_settlement(entity: str, stripe_account_id: str = None, method: str = "stripe") -> Dict[str, Any]:
    """Queue a settlement/payout"""
    return _default_settlements.schedule_payout(entity)


def get_pending_settlements() -> Dict[str, Any]:
    """Get pending settlements"""
    pending = _default_settlements.get_pending_payouts()
    return {
        "ok": True,
        "pending": pending,
        "count": len(pending)
    }


async def process_settlements() -> Dict[str, Any]:
    """Process all pending settlements"""
    pending = _default_settlements.get_pending_payouts()
    results = []

    for p in pending:
        try:
            result = await _default_settlements.initiate_payout(p["entity"], method="balance")
            results.append({
                "entity": p["entity"],
                "success": result.get("ok", False),
                "result": result
            })
        except Exception as e:
            results.append({
                "entity": p["entity"],
                "success": False,
                "error": str(e)
            })

    # Clear processed
    _default_settlements._pending = [p for p in pending if not any(r["entity"] == p["entity"] and r["success"] for r in results)]

    return {
        "ok": True,
        "processed": len(results),
        "successful": sum(1 for r in results if r["success"]),
        "results": results
    }


async def initiate_payout(entity: str, **kwargs) -> Dict[str, Any]:
    """Initiate a payout"""
    return await _default_settlements.initiate_payout(entity, **kwargs)
