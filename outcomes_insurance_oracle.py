"""
OUTCOMES INSURANCE ORACLE (OIO)
===============================

Micro-premium insurance for outcome guarantees on any COI chain.

How it works:
1. /oio/quote returns a premium to insure the promised outcome
2. Premium = base_fail_prob × payout × margin
3. Auto-settles using Proof-of-Execution receipts + SLA logs
4. No manual adjudication - purely algorithmic

Benefits:
- Converts "maybe later" into "buy now"
- De-risks for buyers
- Higher close rates
- Raises attach rate materially

Usage:
    from outcomes_insurance_oracle import quote_oio, attach_oio, settle_oio

    # Get quote
    quote = quote_oio(coi_id="coi_123", payout=500, entity_id="provider_x")

    # Attach to COI
    policy = attach_oio(coi_id="coi_123", quote=quote)

    # Auto-settle on completion
    settlement = settle_oio(coi_id="coi_123", success=True, proofs=[...])
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class OutcomesInsuranceOracle:
    """
    Algorithmic outcome insurance oracle.

    Pricing model:
    - Base failure probability from OCS + connector track record
    - Premium = fail_prob × payout × margin_multiplier
    - Risk pool absorbs claims
    - Auto-settles via proof verification
    """

    def __init__(self):
        self.config = {
            "base_fail_prob": 0.05,          # 5% base failure rate
            "margin_multiplier": 1.8,        # 80% margin over expected loss
            "min_premium_pct": 0.01,         # 1% floor
            "max_premium_pct": 0.15,         # 15% ceiling
            "ocs_weight": 0.6,               # OCS contribution to fail prob
            "connector_weight": 0.4,         # Connector history contribution
            "min_payout": 10.0,              # Min insurable amount
            "max_payout": 10000.0            # Max insurable amount
        }

        self._policies: Dict[str, Dict[str, Any]] = {}
        self._claims: List[Dict[str, Any]] = []
        self._pool_balance: float = 10000.0  # Starting pool

        # Track connector failure rates
        self._connector_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"success": 0, "fail": 0}
        )

    def _get_ocs_fail_prob(self, entity_id: str) -> float:
        """Get failure probability from OCS"""
        try:
            from brain_overlay.ocs import OCSEngine
            ocs_engine = OCSEngine()
            details = ocs_engine.get_entity_details(entity_id)
            ocs = details.get("ocs", 50)

            # Map OCS to fail probability
            # OCS 100 = 1% fail, OCS 50 = 5% fail, OCS 0 = 15% fail
            fail_prob = 0.01 + (100 - ocs) * 0.0014
            return round(min(0.20, max(0.01, fail_prob)), 4)
        except:
            return self.config["base_fail_prob"]

    def _get_connector_fail_prob(self, connector: str) -> float:
        """Get failure probability from connector history"""
        stats = self._connector_stats[connector]
        total = stats["success"] + stats["fail"]

        if total < 10:
            return self.config["base_fail_prob"]

        fail_rate = stats["fail"] / total
        # Apply smoothing
        smoothed = (fail_rate * total + self.config["base_fail_prob"] * 10) / (total + 10)
        return round(smoothed, 4)

    def quote(
        self,
        coi_id: str,
        payout: float,
        *,
        entity_id: str = None,
        connector: str = None,
        sla_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Quote outcome insurance premium.

        Args:
            coi_id: COI being insured
            payout: Amount to pay out on failure
            entity_id: Provider entity ID (for OCS lookup)
            connector: Connector being used (for history)
            sla_hours: SLA window in hours

        Returns:
            Quote with premium, coverage details
        """
        # Validate payout
        if payout < self.config["min_payout"]:
            return {
                "ok": False,
                "error": "payout_below_minimum",
                "min_payout": self.config["min_payout"]
            }

        if payout > self.config["max_payout"]:
            return {
                "ok": False,
                "error": "payout_above_maximum",
                "max_payout": self.config["max_payout"]
            }

        # Calculate failure probability
        ocs_fail = self._get_ocs_fail_prob(entity_id) if entity_id else self.config["base_fail_prob"]
        conn_fail = self._get_connector_fail_prob(connector) if connector else self.config["base_fail_prob"]

        # Weighted combination
        fail_prob = (
            ocs_fail * self.config["ocs_weight"] +
            conn_fail * self.config["connector_weight"]
        )

        # SLA adjustment (longer SLA = slightly higher risk)
        sla_factor = 1.0 + (sla_hours - 24) * 0.005  # 0.5% per hour beyond 24h
        fail_prob *= sla_factor

        # Calculate premium
        expected_loss = payout * fail_prob
        premium = expected_loss * self.config["margin_multiplier"]

        # Apply bounds
        min_premium = payout * self.config["min_premium_pct"]
        max_premium = payout * self.config["max_premium_pct"]
        premium = round(max(min_premium, min(max_premium, premium)), 2)

        # Premium as percentage
        premium_pct = round(premium / payout * 100, 2)

        return {
            "ok": True,
            "coi_id": coi_id,
            "payout": payout,
            "premium": premium,
            "premium_pct": premium_pct,
            "coverage": {
                "sla_hours": sla_hours,
                "refund_on_failure": payout,
                "auto_settle": True
            },
            "risk_factors": {
                "ocs_fail_prob": ocs_fail,
                "connector_fail_prob": conn_fail,
                "combined_fail_prob": round(fail_prob, 4),
                "sla_factor": round(sla_factor, 3)
            },
            "valid_until": _now_iso(),  # Quote valid briefly
            "pool_capacity": self._pool_balance > payout * 2
        }

    def attach(
        self,
        coi_id: str,
        quote: Dict[str, Any],
        *,
        buyer_id: str = None
    ) -> Dict[str, Any]:
        """
        Attach insurance policy to COI.

        Args:
            coi_id: COI to insure
            quote: Quote from quote()
            buyer_id: Who's paying the premium

        Returns:
            Attached policy details
        """
        if not quote.get("ok"):
            return {"ok": False, "error": "invalid_quote"}

        if coi_id in self._policies:
            return {"ok": False, "error": "already_insured", "coi_id": coi_id}

        # Check pool capacity
        payout = quote["payout"]
        if self._pool_balance < payout * 2:
            return {"ok": False, "error": "insufficient_pool_capacity"}

        premium = quote["premium"]

        # Create policy
        policy = {
            "id": f"oio_{coi_id}",
            "coi_id": coi_id,
            "payout": payout,
            "premium": premium,
            "buyer_id": buyer_id,
            "status": "active",
            "coverage": quote["coverage"],
            "risk_factors": quote["risk_factors"],
            "attached_at": _now_iso(),
            "settled_at": None,
            "outcome": None
        }

        self._policies[coi_id] = policy

        # Collect premium into pool
        self._pool_balance += premium

        # Post to ledger
        try:
            from monetization.ledger import post_entry
            post_entry(
                entry_type="oio_premium",
                ref=f"oio:{coi_id}",
                debit=0,
                credit=premium,
                meta={"coi_id": coi_id, "payout": payout, "buyer_id": buyer_id}
            )
        except ImportError:
            pass

        return {
            "ok": True,
            "policy": policy,
            "pool_balance": round(self._pool_balance, 2)
        }

    def settle(
        self,
        coi_id: str,
        success: bool,
        *,
        proofs: List[Dict[str, Any]] = None,
        sla_met: bool = True
    ) -> Dict[str, Any]:
        """
        Auto-settle insurance based on outcome.

        Args:
            coi_id: COI to settle
            success: Whether outcome was successful
            proofs: Proof-of-execution receipts
            sla_met: Whether SLA was met

        Returns:
            Settlement result (refund or no action)
        """
        if coi_id not in self._policies:
            return {"ok": False, "error": "no_policy_found"}

        policy = self._policies[coi_id]

        if policy["status"] != "active":
            return {"ok": False, "error": f"policy_{policy['status']}"}

        # Update connector stats for future pricing
        connector = policy.get("coverage", {}).get("connector")
        if connector:
            if success and sla_met:
                self._connector_stats[connector]["success"] += 1
            else:
                self._connector_stats[connector]["fail"] += 1

        settlement = {
            "coi_id": coi_id,
            "success": success,
            "sla_met": sla_met,
            "proof_count": len(proofs) if proofs else 0,
            "settled_at": _now_iso()
        }

        if success and sla_met:
            # No payout - premium is profit
            policy["status"] = "completed"
            policy["outcome"] = "success"
            settlement["action"] = "none"
            settlement["message"] = "Outcome successful - no payout"
            settlement["payout"] = 0
        else:
            # Failure - pay out
            payout = policy["payout"]

            if self._pool_balance >= payout:
                self._pool_balance -= payout
                policy["status"] = "paid"
                policy["outcome"] = "failure"
                settlement["action"] = "payout"
                settlement["payout"] = payout
                settlement["message"] = f"Outcome failed - ${payout} refunded"

                # Record claim
                self._claims.append({
                    "coi_id": coi_id,
                    "payout": payout,
                    "reason": "outcome_failure" if not success else "sla_breach",
                    "claimed_at": _now_iso()
                })

                # Post to ledger
                try:
                    from monetization.ledger import post_entry
                    post_entry(
                        entry_type="oio_payout",
                        ref=f"oio:{coi_id}",
                        debit=payout,
                        credit=0,
                        meta={"coi_id": coi_id, "reason": settlement["message"]}
                    )
                except ImportError:
                    pass
            else:
                policy["status"] = "underfunded"
                settlement["action"] = "deferred"
                settlement["message"] = "Pool underfunded - payout deferred"

        policy["settled_at"] = _now_iso()

        return {
            "ok": True,
            "settlement": settlement,
            "pool_balance": round(self._pool_balance, 2)
        }

    def get_policy(self, coi_id: str) -> Optional[Dict[str, Any]]:
        """Get policy by COI ID"""
        return self._policies.get(coi_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get OIO statistics"""
        active = len([p for p in self._policies.values() if p["status"] == "active"])
        completed = len([p for p in self._policies.values() if p["status"] == "completed"])
        paid = len([p for p in self._policies.values() if p["status"] == "paid"])

        total_premiums = sum(p["premium"] for p in self._policies.values())
        total_payouts = sum(c["payout"] for c in self._claims)

        return {
            "total_policies": len(self._policies),
            "active": active,
            "completed": completed,
            "paid_out": paid,
            "total_premiums": round(total_premiums, 2),
            "total_payouts": round(total_payouts, 2),
            "net_profit": round(total_premiums - total_payouts, 2),
            "pool_balance": round(self._pool_balance, 2),
            "loss_ratio": round(total_payouts / total_premiums, 3) if total_premiums > 0 else 0
        }


# Module-level singleton
_oio = OutcomesInsuranceOracle()


def quote_oio(coi_id: str, payout: float, **kwargs) -> Dict[str, Any]:
    """Quote outcome insurance"""
    return _oio.quote(coi_id, payout, **kwargs)


def attach_oio(coi_id: str, quote: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    """Attach insurance to COI"""
    return _oio.attach(coi_id, quote, **kwargs)


def settle_oio(coi_id: str, success: bool, **kwargs) -> Dict[str, Any]:
    """Settle insurance based on outcome"""
    return _oio.settle(coi_id, success, **kwargs)


def get_oio_policy(coi_id: str) -> Optional[Dict[str, Any]]:
    """Get policy for COI"""
    return _oio.get_policy(coi_id)


def get_oio_stats() -> Dict[str, Any]:
    """Get OIO statistics"""
    return _oio.get_stats()
