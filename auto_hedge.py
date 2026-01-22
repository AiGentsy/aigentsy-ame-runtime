"""
MARKET-NEUTRAL OAA↔IFX AUTO-HEDGE
=================================

Automatically hedges exposure between:
- OAA (Outcome Attribution Asset) - long position on outcomes
- IFX (Intent Futures Exchange) - short/hedge positions

Uses Kelly criterion for position sizing to maximize long-term growth
while maintaining market-neutral exposure.

Flow:
1. Monitor OAA exposure (unhedged outcome positions)
2. Calculate optimal hedge ratio via Kelly
3. Auto-execute IFX hedges when exposure exceeds threshold
4. Rebalance periodically

Revenue:
- Spread capture on hedge execution
- 0.1% rebalance fee

Usage:
    from auto_hedge import get_exposure, execute_hedge, get_kelly_allocation, rebalance
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4
from collections import defaultdict
import math

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Configuration
HEDGE_THRESHOLD_PCT = 0.20  # Hedge when unhedged > 20% of portfolio
REBALANCE_FEE_PCT = 0.001  # 0.1% rebalance fee
MAX_KELLY_FRACTION = 0.25  # Cap at 25% Kelly for safety (half-Kelly)
MIN_HEDGE_AMOUNT = 100  # Minimum hedge amount

# Storage
_OAA_POSITIONS: Dict[str, Dict[str, Any]] = {}  # Long positions
_IFX_HEDGES: Dict[str, Dict[str, Any]] = {}  # Short/hedge positions
_HEDGE_HISTORY: List[Dict[str, Any]] = []
_PORTFOLIO_STATE: Dict[str, Any] = {
    "total_oaa_exposure": 0.0,
    "total_ifx_hedged": 0.0,
    "net_exposure": 0.0,
    "last_rebalance": None
}


class AutoHedge:
    """
    Market-neutral hedging engine using Kelly criterion.
    """

    def __init__(self):
        self.hedge_threshold = HEDGE_THRESHOLD_PCT
        self.rebalance_fee = REBALANCE_FEE_PCT
        self.max_kelly = MAX_KELLY_FRACTION
        self.min_hedge = MIN_HEDGE_AMOUNT

    def record_oaa_position(
        self,
        position_id: str,
        amount: float,
        *,
        outcome_type: str = "general",
        expected_return: float = 0.15,  # Expected 15% return
        volatility: float = 0.30,  # 30% volatility
        entity_id: str = None
    ) -> Dict[str, Any]:
        """
        Record a new OAA (long) position.

        Args:
            position_id: Unique position ID
            amount: Position amount
            outcome_type: Type of outcome
            expected_return: Expected return (annual)
            volatility: Expected volatility (annual)
            entity_id: Entity ID

        Returns:
            Position details and hedge recommendation
        """
        position = {
            "id": position_id,
            "type": "OAA",
            "amount": amount,
            "outcome_type": outcome_type,
            "expected_return": expected_return,
            "volatility": volatility,
            "entity_id": entity_id,
            "hedged_amount": 0.0,
            "hedge_ratio": 0.0,
            "status": "OPEN",
            "created_at": _now()
        }

        _OAA_POSITIONS[position_id] = position

        # Update portfolio state
        _PORTFOLIO_STATE["total_oaa_exposure"] += amount
        _PORTFOLIO_STATE["net_exposure"] = (
            _PORTFOLIO_STATE["total_oaa_exposure"] -
            _PORTFOLIO_STATE["total_ifx_hedged"]
        )

        # Calculate Kelly allocation for this position
        kelly = self._calculate_kelly(expected_return, volatility)

        # Check if hedge needed
        exposure_pct = self._get_exposure_pct()
        needs_hedge = exposure_pct > self.hedge_threshold

        return {
            "ok": True,
            "position": position,
            "kelly_fraction": round(kelly, 4),
            "recommended_hedge": round(amount * (1 - kelly), 2) if needs_hedge else 0,
            "exposure_pct": round(exposure_pct, 4),
            "needs_hedge": needs_hedge
        }

    def _calculate_kelly(self, expected_return: float, volatility: float) -> float:
        """
        Calculate Kelly criterion for position sizing.

        Kelly = (expected_return - risk_free) / volatility^2

        We cap at half-Kelly for safety.
        """
        risk_free = 0.04  # 4% risk-free rate
        if volatility <= 0:
            return self.max_kelly

        kelly = (expected_return - risk_free) / (volatility ** 2)
        kelly = max(0, min(kelly, 1.0))  # Bound to [0, 1]
        kelly = min(kelly, self.max_kelly * 2)  # Allow up to 2x max_kelly

        # Apply half-Kelly for safety
        return kelly * 0.5

    def _get_exposure_pct(self) -> float:
        """Get current unhedged exposure as percentage of total"""
        total = _PORTFOLIO_STATE["total_oaa_exposure"]
        if total <= 0:
            return 0.0
        return _PORTFOLIO_STATE["net_exposure"] / total

    def get_exposure(self) -> Dict[str, Any]:
        """Get current portfolio exposure"""
        exposure_pct = self._get_exposure_pct()

        return {
            "total_oaa_exposure": round(_PORTFOLIO_STATE["total_oaa_exposure"], 2),
            "total_ifx_hedged": round(_PORTFOLIO_STATE["total_ifx_hedged"], 2),
            "net_exposure": round(_PORTFOLIO_STATE["net_exposure"], 2),
            "exposure_pct": round(exposure_pct, 4),
            "hedge_threshold": self.hedge_threshold,
            "needs_rebalance": exposure_pct > self.hedge_threshold,
            "last_rebalance": _PORTFOLIO_STATE["last_rebalance"]
        }

    def execute_hedge(
        self,
        position_id: str = None,
        *,
        hedge_amount: float = None,
        target_exposure_pct: float = None
    ) -> Dict[str, Any]:
        """
        Execute a hedge trade on IFX.

        Args:
            position_id: Specific position to hedge (or portfolio-wide)
            hedge_amount: Specific amount to hedge
            target_exposure_pct: Target exposure percentage

        Returns:
            Hedge execution details
        """
        if position_id:
            # Hedge specific position
            position = _OAA_POSITIONS.get(position_id)
            if not position:
                return {"ok": False, "error": "position_not_found"}

            if hedge_amount is None:
                # Calculate based on Kelly
                kelly = self._calculate_kelly(
                    position["expected_return"],
                    position["volatility"]
                )
                hedge_amount = position["amount"] * (1 - kelly)
        else:
            # Portfolio-wide hedge
            if target_exposure_pct is not None:
                current_exposure = _PORTFOLIO_STATE["net_exposure"]
                target_exposure = _PORTFOLIO_STATE["total_oaa_exposure"] * target_exposure_pct
                hedge_amount = current_exposure - target_exposure
            elif hedge_amount is None:
                # Hedge to threshold
                target_exposure = _PORTFOLIO_STATE["total_oaa_exposure"] * self.hedge_threshold
                hedge_amount = _PORTFOLIO_STATE["net_exposure"] - target_exposure

        if hedge_amount < self.min_hedge:
            return {
                "ok": False,
                "error": "hedge_amount_too_small",
                "min_hedge": self.min_hedge,
                "requested": hedge_amount
            }

        # Calculate fee
        fee = round(hedge_amount * self.rebalance_fee, 2)

        hedge_id = f"hedge_{uuid4().hex[:8]}"

        hedge = {
            "id": hedge_id,
            "type": "IFX_SHORT",
            "amount": hedge_amount,
            "fee": fee,
            "net_amount": hedge_amount - fee,
            "position_id": position_id,
            "executed_at": _now(),
            "status": "EXECUTED"
        }

        _IFX_HEDGES[hedge_id] = hedge
        _HEDGE_HISTORY.append(hedge)

        # Update portfolio state
        _PORTFOLIO_STATE["total_ifx_hedged"] += hedge_amount
        _PORTFOLIO_STATE["net_exposure"] = (
            _PORTFOLIO_STATE["total_oaa_exposure"] -
            _PORTFOLIO_STATE["total_ifx_hedged"]
        )

        # Update position if specific
        if position_id and position_id in _OAA_POSITIONS:
            position = _OAA_POSITIONS[position_id]
            position["hedged_amount"] += hedge_amount
            position["hedge_ratio"] = position["hedged_amount"] / position["amount"]

        # Post fee to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="hedge_fee",
                ref=f"hedge:{hedge_id}",
                debit=0,
                credit=fee,
                meta={
                    "hedge_amount": hedge_amount,
                    "position_id": position_id
                }
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "hedge": hedge,
            "new_exposure": self.get_exposure()
        }

    def get_kelly_allocation(
        self,
        positions: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get Kelly-optimal allocation across positions.

        Args:
            positions: List of positions with expected_return and volatility
                       (uses stored positions if not provided)

        Returns:
            Kelly-optimal allocation
        """
        if positions is None:
            positions = list(_OAA_POSITIONS.values())

        if not positions:
            return {"ok": False, "error": "no_positions"}

        allocations = []
        total_kelly = 0.0

        for pos in positions:
            kelly = self._calculate_kelly(
                pos.get("expected_return", 0.15),
                pos.get("volatility", 0.30)
            )
            allocations.append({
                "position_id": pos.get("id"),
                "amount": pos.get("amount", 0),
                "kelly_fraction": round(kelly, 4),
                "recommended_allocation": round(pos.get("amount", 0) * kelly, 2),
                "recommended_hedge": round(pos.get("amount", 0) * (1 - kelly), 2)
            })
            total_kelly += kelly

        # Normalize if total > 1
        if total_kelly > 1.0:
            scale = 1.0 / total_kelly
            for alloc in allocations:
                alloc["kelly_fraction"] = round(alloc["kelly_fraction"] * scale, 4)
                alloc["recommended_allocation"] = round(alloc["recommended_allocation"] * scale, 2)
                alloc["recommended_hedge"] = round(
                    alloc["amount"] - alloc["recommended_allocation"], 2
                )

        total_recommended = sum(a["recommended_allocation"] for a in allocations)
        total_hedge = sum(a["recommended_hedge"] for a in allocations)

        return {
            "ok": True,
            "allocations": allocations,
            "total_recommended_allocation": round(total_recommended, 2),
            "total_recommended_hedge": round(total_hedge, 2),
            "portfolio_kelly": round(min(total_kelly, 1.0), 4)
        }

    def rebalance(
        self,
        *,
        target_exposure_pct: float = None
    ) -> Dict[str, Any]:
        """
        Rebalance portfolio to target exposure.

        Args:
            target_exposure_pct: Target exposure (default: hedge_threshold)

        Returns:
            Rebalance result
        """
        target = target_exposure_pct if target_exposure_pct is not None else self.hedge_threshold

        current_exposure_pct = self._get_exposure_pct()

        if abs(current_exposure_pct - target) < 0.01:
            return {
                "ok": True,
                "message": "Already at target exposure",
                "current_exposure_pct": round(current_exposure_pct, 4),
                "target_exposure_pct": target,
                "action": "none"
            }

        if current_exposure_pct > target:
            # Need to hedge more
            return self.execute_hedge(target_exposure_pct=target)
        else:
            # Need to unwind hedges
            unwind_amount = (target - current_exposure_pct) * _PORTFOLIO_STATE["total_oaa_exposure"]

            if unwind_amount < self.min_hedge:
                return {
                    "ok": True,
                    "message": "Unwind amount too small",
                    "action": "none"
                }

            # Unwind oldest hedges first
            unwound = 0.0
            fee = round(unwind_amount * self.rebalance_fee, 2)

            for hedge_id, hedge in list(_IFX_HEDGES.items()):
                if unwound >= unwind_amount:
                    break
                if hedge["status"] == "EXECUTED":
                    unwind_this = min(hedge["amount"], unwind_amount - unwound)
                    hedge["amount"] -= unwind_this
                    if hedge["amount"] <= 0:
                        hedge["status"] = "CLOSED"
                    unwound += unwind_this

            # Update portfolio state
            _PORTFOLIO_STATE["total_ifx_hedged"] -= unwound
            _PORTFOLIO_STATE["net_exposure"] = (
                _PORTFOLIO_STATE["total_oaa_exposure"] -
                _PORTFOLIO_STATE["total_ifx_hedged"]
            )
            _PORTFOLIO_STATE["last_rebalance"] = _now()

            return {
                "ok": True,
                "action": "unwind",
                "unwound_amount": round(unwound, 2),
                "fee": fee,
                "new_exposure": self.get_exposure()
            }

    def close_position(self, position_id: str) -> Dict[str, Any]:
        """Close an OAA position and unwind associated hedges"""
        position = _OAA_POSITIONS.get(position_id)
        if not position:
            return {"ok": False, "error": "position_not_found"}

        if position["status"] != "OPEN":
            return {"ok": False, "error": f"position_is_{position['status'].lower()}"}

        # Update portfolio
        _PORTFOLIO_STATE["total_oaa_exposure"] -= position["amount"]
        _PORTFOLIO_STATE["total_ifx_hedged"] -= position["hedged_amount"]
        _PORTFOLIO_STATE["net_exposure"] = (
            _PORTFOLIO_STATE["total_oaa_exposure"] -
            _PORTFOLIO_STATE["total_ifx_hedged"]
        )

        position["status"] = "CLOSED"
        position["closed_at"] = _now()

        return {
            "ok": True,
            "position_id": position_id,
            "closed_amount": position["amount"],
            "hedges_unwound": position["hedged_amount"],
            "new_exposure": self.get_exposure()
        }

    def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get position details"""
        return _OAA_POSITIONS.get(position_id)

    def get_hedge(self, hedge_id: str) -> Optional[Dict[str, Any]]:
        """Get hedge details"""
        return _IFX_HEDGES.get(hedge_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get auto-hedge statistics"""
        total_hedged = sum(h["amount"] for h in _IFX_HEDGES.values() if h["status"] == "EXECUTED")
        total_fees = sum(h["fee"] for h in _HEDGE_HISTORY)

        return {
            "total_oaa_positions": len(_OAA_POSITIONS),
            "open_positions": len([p for p in _OAA_POSITIONS.values() if p["status"] == "OPEN"]),
            "total_oaa_exposure": round(_PORTFOLIO_STATE["total_oaa_exposure"], 2),
            "total_hedges": len(_IFX_HEDGES),
            "total_hedged_amount": round(total_hedged, 2),
            "net_exposure": round(_PORTFOLIO_STATE["net_exposure"], 2),
            "exposure_pct": round(self._get_exposure_pct(), 4),
            "total_hedge_fees_collected": round(total_fees, 2),
            "hedge_transactions": len(_HEDGE_HISTORY),
            "last_rebalance": _PORTFOLIO_STATE["last_rebalance"]
        }


# Module-level singleton
_auto_hedge = AutoHedge()


def record_oaa_position(position_id: str, amount: float, **kwargs) -> Dict[str, Any]:
    """Record OAA (long) position"""
    return _auto_hedge.record_oaa_position(position_id, amount, **kwargs)


def get_exposure() -> Dict[str, Any]:
    """Get current portfolio exposure"""
    return _auto_hedge.get_exposure()


def execute_hedge(position_id: str = None, **kwargs) -> Dict[str, Any]:
    """Execute hedge trade"""
    return _auto_hedge.execute_hedge(position_id, **kwargs)


def get_kelly_allocation(positions: list = None) -> Dict[str, Any]:
    """Get Kelly-optimal allocation"""
    return _auto_hedge.get_kelly_allocation(positions)


def rebalance(**kwargs) -> Dict[str, Any]:
    """Rebalance portfolio"""
    return _auto_hedge.rebalance(**kwargs)


def close_oaa_position(position_id: str) -> Dict[str, Any]:
    """Close OAA position"""
    return _auto_hedge.close_position(position_id)


def get_oaa_position(position_id: str) -> Optional[Dict[str, Any]]:
    """Get position details"""
    return _auto_hedge.get_position(position_id)


def get_hedge_details(hedge_id: str) -> Optional[Dict[str, Any]]:
    """Get hedge details"""
    return _auto_hedge.get_hedge(hedge_id)


def get_auto_hedge_stats() -> Dict[str, Any]:
    """Get auto-hedge statistics"""
    return _auto_hedge.get_stats()


def get_exposure_summary() -> Dict[str, Any]:
    """Get exposure summary (alias for get_exposure)"""
    return get_exposure()


def get_hedge_portfolio() -> Dict[str, Any]:
    """Get hedge portfolio"""
    return {
        "ok": True,
        "positions": list(_OAA_POSITIONS.values()),
        "hedges": list(_IFX_HEDGES.values()),
        "total_hedged": sum(h.get("amount", 0) for h in _IFX_HEDGES.values() if h.get("status") == "EXECUTED")
    }


def place_hedge(exposure_type: str, amount: float, instrument: str = "put_spread") -> Dict[str, Any]:
    """Place a new hedge"""
    return execute_hedge(amount=amount, hedge_type=instrument)


def rebalance_hedges() -> Dict[str, Any]:
    """Rebalance hedges (alias for rebalance)"""
    return rebalance()
