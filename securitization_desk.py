"""
SECURITIZATION & SECONDARY FLOW DESK
=====================================

Allows qualified LPs to buy tranches of AiGentsy outcome cash flows.
Extends DealGraph with securitization, SPV pooling, and secondary trading.

Tranches:
- Senior (AAA): First claim, lowest yield, OCS >= 80
- Mezzanine (BBB): Second claim, medium yield, OCS >= 60
- Junior (B): Third claim, highest yield, any OCS

Revenue flow:
- Outcome completes → Cash hits pool
- Distribute: Senior first → Mezz → Junior
- 0.15% servicing fee to AiGentsy on all distributions

Usage:
    from securitization_desk import create_spv, issue_tranche, buy_tranche, distribute_cash_flows
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from uuid import uuid4
from collections import defaultdict

def _now():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Tranche definitions
TRANCHES = {
    "senior": {
        "name": "Senior (AAA)",
        "priority": 1,
        "target_yield": 0.06,  # 6% annual
        "min_ocs": 80,
        "coverage_ratio": 1.5,  # 150% overcollateralized
    },
    "mezzanine": {
        "name": "Mezzanine (BBB)",
        "priority": 2,
        "target_yield": 0.12,  # 12% annual
        "min_ocs": 60,
        "coverage_ratio": 1.2,
    },
    "junior": {
        "name": "Junior (B)",
        "priority": 3,
        "target_yield": 0.20,  # 20% annual
        "min_ocs": 0,  # Any quality
        "coverage_ratio": 1.0,
    }
}

# Fee structure
SERVICING_FEE_PCT = 0.0015  # 0.15% on all distributions
ORIGINATION_FEE_PCT = 0.01  # 1% on tranche issuance

# In-memory storage
_SPVs: Dict[str, Dict[str, Any]] = {}
_TRANCHES: Dict[str, Dict[str, Any]] = {}
_TRANCHE_HOLDINGS: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_CASH_POOL: Dict[str, float] = defaultdict(float)
_DISTRIBUTIONS: List[Dict[str, Any]] = []


class SecuritizationDesk:
    """
    Manages outcome securitization and secondary trading.
    """

    def __init__(self):
        self.servicing_fee_pct = SERVICING_FEE_PCT
        self.origination_fee_pct = ORIGINATION_FEE_PCT

    def create_spv(
        self,
        name: str,
        *,
        target_size: float = 100000,
        min_ocs_average: int = 60,
        max_concentration_pct: float = 0.10,
        duration_months: int = 12
    ) -> Dict[str, Any]:
        """
        Create a Special Purpose Vehicle to pool outcome flows.

        Args:
            name: SPV name
            target_size: Target pool size in USD
            min_ocs_average: Minimum weighted-average OCS for pool
            max_concentration_pct: Max single-outcome concentration
            duration_months: Pool duration

        Returns:
            SPV details with ID
        """
        spv_id = f"spv_{uuid4().hex[:8]}"

        spv = {
            "id": spv_id,
            "name": name,
            "status": "OPEN",
            "target_size": target_size,
            "current_size": 0.0,
            "min_ocs_average": min_ocs_average,
            "max_concentration_pct": max_concentration_pct,
            "duration_months": duration_months,
            "created_at": _now(),
            "closes_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat() + "Z",
            "matures_at": (datetime.now(timezone.utc) + timedelta(days=duration_months * 30)).isoformat() + "Z",
            "outcomes": [],
            "weighted_ocs": 0.0,
            "tranches_issued": [],
            "cash_collected": 0.0,
            "cash_distributed": 0.0,
            "events": [{"type": "SPV_CREATED", "at": _now()}]
        }

        _SPVs[spv_id] = spv
        return {"ok": True, "spv_id": spv_id, "spv": spv}

    def add_outcome_to_pool(
        self,
        spv_id: str,
        outcome_id: str,
        expected_value: float,
        ocs: int,
        *,
        connector: str = None,
        entity_id: str = None
    ) -> Dict[str, Any]:
        """
        Add an outcome's expected cash flow to an SPV pool.
        """
        spv = _SPVs.get(spv_id)
        if not spv:
            return {"ok": False, "error": "spv_not_found"}

        if spv["status"] != "OPEN":
            return {"ok": False, "error": f"spv_is_{spv['status'].lower()}"}

        # Check concentration
        new_size = spv["current_size"] + expected_value
        concentration = expected_value / new_size if new_size > 0 else 1.0

        if concentration > spv["max_concentration_pct"]:
            return {"ok": False, "error": "exceeds_concentration_limit", "max_pct": spv["max_concentration_pct"]}

        # Add to pool
        outcome_entry = {
            "outcome_id": outcome_id,
            "expected_value": expected_value,
            "ocs": ocs,
            "connector": connector,
            "entity_id": entity_id,
            "added_at": _now(),
            "cash_received": 0.0,
            "status": "POOLED"
        }

        spv["outcomes"].append(outcome_entry)
        spv["current_size"] = new_size

        # Update weighted OCS
        total_value = sum(o["expected_value"] for o in spv["outcomes"])
        weighted_ocs = sum(o["ocs"] * o["expected_value"] for o in spv["outcomes"]) / total_value
        spv["weighted_ocs"] = round(weighted_ocs, 1)

        spv["events"].append({
            "type": "OUTCOME_ADDED",
            "outcome_id": outcome_id,
            "value": expected_value,
            "ocs": ocs,
            "at": _now()
        })

        return {
            "ok": True,
            "spv_id": spv_id,
            "pool_size": spv["current_size"],
            "weighted_ocs": spv["weighted_ocs"],
            "outcome_count": len(spv["outcomes"])
        }

    def issue_tranche(
        self,
        spv_id: str,
        tranche_type: str,
        amount: float,
        *,
        min_purchase: float = 1000
    ) -> Dict[str, Any]:
        """
        Issue a tranche against an SPV's cash flows.

        Args:
            spv_id: SPV to issue from
            tranche_type: senior, mezzanine, or junior
            amount: Tranche face value
            min_purchase: Minimum purchase amount

        Returns:
            Tranche details
        """
        spv = _SPVs.get(spv_id)
        if not spv:
            return {"ok": False, "error": "spv_not_found"}

        if tranche_type not in TRANCHES:
            return {"ok": False, "error": "invalid_tranche_type"}

        tranche_config = TRANCHES[tranche_type]

        # Check OCS requirement
        if spv["weighted_ocs"] < tranche_config["min_ocs"]:
            return {
                "ok": False,
                "error": "pool_ocs_too_low",
                "pool_ocs": spv["weighted_ocs"],
                "required_ocs": tranche_config["min_ocs"]
            }

        # Check coverage
        total_issued = sum(
            t.get("amount", 0) for t in spv["tranches_issued"]
            if t.get("priority", 99) <= tranche_config["priority"]
        )
        available = spv["current_size"] / tranche_config["coverage_ratio"]

        if total_issued + amount > available:
            return {
                "ok": False,
                "error": "insufficient_coverage",
                "available": round(available - total_issued, 2)
            }

        tranche_id = f"tranche_{spv_id}_{tranche_type}_{uuid4().hex[:6]}"

        # Calculate origination fee
        origination_fee = round(amount * self.origination_fee_pct, 2)

        tranche = {
            "id": tranche_id,
            "spv_id": spv_id,
            "type": tranche_type,
            "name": tranche_config["name"],
            "priority": tranche_config["priority"],
            "amount": amount,
            "outstanding": amount,
            "target_yield": tranche_config["target_yield"],
            "min_purchase": min_purchase,
            "origination_fee": origination_fee,
            "status": "OPEN",
            "created_at": _now(),
            "holders": [],
            "distributions_made": 0.0,
            "events": [{"type": "TRANCHE_ISSUED", "at": _now()}]
        }

        _TRANCHES[tranche_id] = tranche
        spv["tranches_issued"].append({
            "tranche_id": tranche_id,
            "type": tranche_type,
            "priority": tranche_config["priority"],
            "amount": amount
        })

        return {
            "ok": True,
            "tranche_id": tranche_id,
            "tranche": tranche,
            "origination_fee": origination_fee
        }

    def buy_tranche(
        self,
        tranche_id: str,
        buyer_id: str,
        amount: float,
        *,
        accredited: bool = True
    ) -> Dict[str, Any]:
        """
        Purchase a tranche position.
        """
        tranche = _TRANCHES.get(tranche_id)
        if not tranche:
            return {"ok": False, "error": "tranche_not_found"}

        if tranche["status"] != "OPEN":
            return {"ok": False, "error": f"tranche_is_{tranche['status'].lower()}"}

        if not accredited:
            return {"ok": False, "error": "accredited_investor_required"}

        if amount < tranche["min_purchase"]:
            return {"ok": False, "error": "below_minimum_purchase", "min": tranche["min_purchase"]}

        remaining = tranche["amount"] - sum(h["amount"] for h in tranche["holders"])
        if amount > remaining:
            return {"ok": False, "error": "exceeds_available", "available": remaining}

        # Record purchase
        holding = {
            "holding_id": f"hold_{uuid4().hex[:8]}",
            "buyer_id": buyer_id,
            "tranche_id": tranche_id,
            "amount": amount,
            "purchased_at": _now(),
            "distributions_received": 0.0
        }

        tranche["holders"].append(holding)
        _TRANCHE_HOLDINGS[buyer_id].append(holding)

        tranche["events"].append({
            "type": "TRANCHE_PURCHASED",
            "buyer_id": buyer_id,
            "amount": amount,
            "at": _now()
        })

        # Check if fully subscribed
        total_subscribed = sum(h["amount"] for h in tranche["holders"])
        if total_subscribed >= tranche["amount"]:
            tranche["status"] = "SUBSCRIBED"

        return {
            "ok": True,
            "holding": holding,
            "total_subscribed": total_subscribed,
            "remaining": tranche["amount"] - total_subscribed
        }

    def receive_cash_flow(
        self,
        spv_id: str,
        outcome_id: str,
        amount: float,
        *,
        source: str = "outcome_completion"
    ) -> Dict[str, Any]:
        """
        Record cash flow received from an outcome.
        """
        spv = _SPVs.get(spv_id)
        if not spv:
            return {"ok": False, "error": "spv_not_found"}

        # Find outcome in pool
        outcome = None
        for o in spv["outcomes"]:
            if o["outcome_id"] == outcome_id:
                outcome = o
                break

        if not outcome:
            return {"ok": False, "error": "outcome_not_in_pool"}

        # Record cash
        outcome["cash_received"] += amount
        outcome["status"] = "CASH_RECEIVED"
        spv["cash_collected"] += amount
        _CASH_POOL[spv_id] += amount

        spv["events"].append({
            "type": "CASH_RECEIVED",
            "outcome_id": outcome_id,
            "amount": amount,
            "source": source,
            "at": _now()
        })

        return {
            "ok": True,
            "spv_id": spv_id,
            "cash_collected": spv["cash_collected"],
            "pool_balance": _CASH_POOL[spv_id]
        }

    def distribute_cash_flows(self, spv_id: str) -> Dict[str, Any]:
        """
        Distribute accumulated cash to tranche holders in priority order.
        """
        spv = _SPVs.get(spv_id)
        if not spv:
            return {"ok": False, "error": "spv_not_found"}

        available_cash = _CASH_POOL[spv_id]
        if available_cash <= 0:
            return {"ok": False, "error": "no_cash_to_distribute"}

        # Sort tranches by priority
        tranches_ordered = sorted(
            [_TRANCHES[t["tranche_id"]] for t in spv["tranches_issued"] if t["tranche_id"] in _TRANCHES],
            key=lambda t: t["priority"]
        )

        distributions = []
        remaining = available_cash

        for tranche in tranches_ordered:
            if remaining <= 0:
                break

            # Calculate pro-rata distribution to holders
            total_holdings = sum(h["amount"] for h in tranche["holders"])
            if total_holdings <= 0:
                continue

            # Calculate target distribution (proportional to outstanding)
            target_dist = min(remaining, tranche["outstanding"] * tranche["target_yield"] / 12)  # Monthly

            # Deduct servicing fee
            servicing_fee = round(target_dist * self.servicing_fee_pct, 2)
            net_dist = target_dist - servicing_fee

            for holder in tranche["holders"]:
                share = holder["amount"] / total_holdings
                holder_dist = round(net_dist * share, 2)

                if holder_dist > 0:
                    holder["distributions_received"] += holder_dist
                    distributions.append({
                        "tranche_id": tranche["id"],
                        "holder_id": holder["buyer_id"],
                        "amount": holder_dist,
                        "servicing_fee": round(servicing_fee * share, 4),
                        "at": _now()
                    })

            tranche["distributions_made"] += net_dist
            remaining -= target_dist

        # Update pool
        distributed = available_cash - remaining
        _CASH_POOL[spv_id] = remaining
        spv["cash_distributed"] += distributed

        _DISTRIBUTIONS.extend(distributions)

        total_servicing = sum(d.get("servicing_fee", 0) for d in distributions)

        return {
            "ok": True,
            "spv_id": spv_id,
            "distributed": round(distributed, 2),
            "servicing_fees": round(total_servicing, 2),
            "distributions": distributions,
            "remaining_pool": round(remaining, 2)
        }

    def get_spv(self, spv_id: str) -> Optional[Dict[str, Any]]:
        """Get SPV details"""
        return _SPVs.get(spv_id)

    def get_tranche(self, tranche_id: str) -> Optional[Dict[str, Any]]:
        """Get tranche details"""
        return _TRANCHES.get(tranche_id)

    def get_holder_positions(self, holder_id: str) -> List[Dict[str, Any]]:
        """Get all tranche positions for a holder"""
        return _TRANCHE_HOLDINGS.get(holder_id, [])

    def get_stats(self) -> Dict[str, Any]:
        """Get securitization desk statistics"""
        total_pooled = sum(spv["current_size"] for spv in _SPVs.values())
        total_tranches = len(_TRANCHES)
        total_distributed = sum(spv["cash_distributed"] for spv in _SPVs.values())
        total_servicing = sum(d.get("servicing_fee", 0) for d in _DISTRIBUTIONS)

        return {
            "spvs_created": len(_SPVs),
            "tranches_issued": total_tranches,
            "total_pooled": round(total_pooled, 2),
            "total_distributed": round(total_distributed, 2),
            "total_servicing_fees": round(total_servicing, 2),
            "by_tranche_type": {
                t: len([tr for tr in _TRANCHES.values() if tr["type"] == t])
                for t in TRANCHES.keys()
            }
        }


# Module-level singleton
_desk = SecuritizationDesk()


def create_spv(name: str, **kwargs) -> Dict[str, Any]:
    """Create SPV for outcome pooling"""
    return _desk.create_spv(name, **kwargs)


def add_outcome_to_pool(spv_id: str, outcome_id: str, expected_value: float, ocs: int, **kwargs) -> Dict[str, Any]:
    """Add outcome to SPV pool"""
    return _desk.add_outcome_to_pool(spv_id, outcome_id, expected_value, ocs, **kwargs)


def issue_tranche(spv_id: str, tranche_type: str, amount: float, **kwargs) -> Dict[str, Any]:
    """Issue tranche against SPV"""
    return _desk.issue_tranche(spv_id, tranche_type, amount, **kwargs)


def buy_tranche(tranche_id: str, buyer_id: str, amount: float, **kwargs) -> Dict[str, Any]:
    """Purchase tranche position"""
    return _desk.buy_tranche(tranche_id, buyer_id, amount, **kwargs)


def receive_cash_flow(spv_id: str, outcome_id: str, amount: float, **kwargs) -> Dict[str, Any]:
    """Record cash flow from outcome"""
    return _desk.receive_cash_flow(spv_id, outcome_id, amount, **kwargs)


def distribute_cash_flows(spv_id: str) -> Dict[str, Any]:
    """Distribute cash to tranche holders"""
    return _desk.distribute_cash_flows(spv_id)


def get_spv(spv_id: str) -> Optional[Dict[str, Any]]:
    """Get SPV details"""
    return _desk.get_spv(spv_id)


def get_tranche(tranche_id: str) -> Optional[Dict[str, Any]]:
    """Get tranche details"""
    return _desk.get_tranche(tranche_id)


def get_holder_positions(holder_id: str) -> List[Dict[str, Any]]:
    """Get holder's tranche positions"""
    return _desk.get_holder_positions(holder_id)


def get_securitization_stats() -> Dict[str, Any]:
    """Get desk statistics"""
    return _desk.get_stats()


def get_desk_stats() -> Dict[str, Any]:
    """Get desk stats (alias with friendly format)"""
    stats = _desk.get_stats()
    return {
        "ok": True,
        "abs_issued": stats.get("tranches_issued", 0),
        "total_value": stats.get("total_pooled", 0),
        "spvs_created": stats.get("spvs_created", 0),
        "total_distributed": stats.get("total_distributed", 0),
        "servicing_fees": stats.get("total_servicing_fees", 0),
        "by_tranche_type": stats.get("by_tranche_type", {})
    }


def price_abs(face_value: float, tranche_type: str = "senior") -> Dict[str, Any]:
    """Price an asset-backed security"""
    tranche_config = TRANCHES.get(tranche_type)
    if not tranche_config:
        return {"ok": False, "error": "invalid_tranche_type"}

    # Calculate pricing based on tranche characteristics
    origination_fee = round(face_value * ORIGINATION_FEE_PCT, 2)
    annual_yield = tranche_config["target_yield"]
    coverage_ratio = tranche_config["coverage_ratio"]

    # Required pool size to support this tranche
    required_pool = face_value * coverage_ratio

    return {
        "ok": True,
        "tranche_type": tranche_type,
        "face_value": face_value,
        "origination_fee": origination_fee,
        "target_yield": annual_yield,
        "coverage_ratio": coverage_ratio,
        "required_pool_size": required_pool,
        "min_ocs": tranche_config["min_ocs"],
        "monthly_distribution": round(face_value * annual_yield / 12, 2)
    }
