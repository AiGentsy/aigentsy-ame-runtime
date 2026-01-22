"""
P2P OUTCOME ASSURANCE POOL (OAP)
================================

Peer-to-peer outcome assurance using AIGx credits (non-custodial).
AiGentsy is ONLY a coordinator and fee scheduler - NOT the insurer.

Key Distinctions:
- This is NOT insurance (no policy, no insurer liability)
- Contributors stake AIGx credits (not cash)
- Platform takes coordination fee only
- All fund movement is via PSP at delivery time
- No custody of user funds

Revenue Model:
- Coordination fee: 50 basis points (0.5%) of premium
- Pool management fee: 25 basis points (0.25%) of distributions
- AiGentsy bears NO risk - only coordinates the pool

Usage:
    from assurance.oap_peer import quote_oap, settle_oap

    quote = quote_oap("coi_123", payout_usd=1000, fail_prob=0.08)
    # {"premium_aigx": 144.0, "platform_fee_aigx": 0.72, ...}
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from uuid import uuid4
from collections import defaultdict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


# Fee structure (in basis points)
COORDINATION_FEE_BP = 50   # 0.5% of premium
POOL_MGMT_FEE_BP = 25      # 0.25% of distributions
RISK_MULTIPLIER = Decimal("1.8")  # Risk pricing multiplier


# In-memory pool state (would be DB in production)
_POOL_STATE = {
    "total_staked_aigx": Decimal("0"),
    "total_premiums_collected": Decimal("0"),
    "total_payouts": Decimal("0"),
    "total_coordination_fees": Decimal("0"),
    "active_commitments": {},
    "contributor_balances": defaultdict(Decimal),
    "settlement_history": []
}


class OAPPool:
    """
    Outcome Assurance Pool - P2P assurance coordinator.

    Contributors stake AIGx credits to back outcome delivery.
    On failure, staked credits flow to the buyer.
    On success, contributors keep their stake + share of premiums.
    """

    def __init__(self):
        self.coordination_fee_bp = COORDINATION_FEE_BP
        self.pool_mgmt_fee_bp = POOL_MGMT_FEE_BP
        self.risk_multiplier = RISK_MULTIPLIER

    def quote(
        self,
        coi_id: str,
        payout_usd: float,
        fail_prob: float,
        *,
        outcome_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Quote P2P assurance for an outcome.

        Args:
            coi_id: Contract of Intent ID
            payout_usd: Payout amount if outcome fails (in USD equivalent)
            fail_prob: Estimated failure probability (0.0 to 1.0)
            outcome_type: Type for risk adjustment

        Returns:
            Quote with premium in AIGx credits
        """
        payout = Decimal(str(payout_usd))
        prob = Decimal(str(min(max(fail_prob, 0.01), 0.50)))  # Clamp 1%-50%

        # Calculate premium: payout * fail_prob * risk_multiplier
        raw_premium = payout * prob * self.risk_multiplier

        # Platform coordination fee
        platform_fee = (raw_premium * Decimal(self.coordination_fee_bp)) / Decimal("10000")

        # Net premium to pool
        net_to_pool = raw_premium - platform_fee

        # Required stake from contributors (2x payout for coverage)
        required_stake = payout * Decimal("2")

        return {
            "ok": True,
            "coi_id": coi_id,
            "payout_usd": float(payout),
            "fail_prob": float(prob),
            "premium_aigx": float(raw_premium.quantize(Decimal("0.01"))),
            "platform_fee_aigx": float(platform_fee.quantize(Decimal("0.01"))),
            "net_to_pool_aigx": float(net_to_pool.quantize(Decimal("0.01"))),
            "required_stake_aigx": float(required_stake.quantize(Decimal("0.01"))),
            "risk_multiplier": float(self.risk_multiplier),
            "quoted_at": _now_iso(),
            "valid_for_seconds": 3600,
            "note": "P2P assurance via AIGx stake; AiGentsy is coordinator only, NOT insurer."
        }

    def stake(
        self,
        contributor_id: str,
        coi_id: str,
        stake_aigx: float,
        quote: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Stake AIGx credits to back an outcome.

        Args:
            contributor_id: Contributor identifier
            coi_id: Contract of Intent ID
            stake_aigx: Amount to stake
            quote: Quote from quote() method

        Returns:
            Stake confirmation
        """
        stake = Decimal(str(stake_aigx))
        required = Decimal(str(quote.get("required_stake_aigx", 0)))

        commitment_id = f"oap_{coi_id}_{uuid4().hex[:8]}"

        commitment = {
            "id": commitment_id,
            "coi_id": coi_id,
            "contributor_id": contributor_id,
            "stake_aigx": float(stake),
            "premium_share_aigx": float(Decimal(str(quote.get("net_to_pool_aigx", 0))) * stake / required) if required > 0 else 0,
            "status": "ACTIVE",
            "staked_at": _now_iso(),
            "quote": quote
        }

        _POOL_STATE["active_commitments"][commitment_id] = commitment
        _POOL_STATE["contributor_balances"][contributor_id] += stake
        _POOL_STATE["total_staked_aigx"] += stake
        _POOL_STATE["total_premiums_collected"] += Decimal(str(quote.get("premium_aigx", 0)))
        _POOL_STATE["total_coordination_fees"] += Decimal(str(quote.get("platform_fee_aigx", 0)))

        return {
            "ok": True,
            "commitment_id": commitment_id,
            "commitment": commitment,
            "pool_total_staked": float(_POOL_STATE["total_staked_aigx"])
        }

    def settle(
        self,
        coi_id: str,
        proved_failed: bool,
        payout_usd: float,
        merkle_receipt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Settle assurance based on outcome result.

        Non-custodial: returns split instructions; actual funds move via PSP.

        Args:
            coi_id: Contract of Intent ID
            proved_failed: Whether outcome delivery was proven failed
            payout_usd: Payout amount
            merkle_receipt: Proof receipt from merkle tree

        Returns:
            Settlement instructions (NOT actual fund movement)
        """
        payout = Decimal(str(payout_usd))

        # Find all commitments for this COI
        commitments = [
            c for c in _POOL_STATE["active_commitments"].values()
            if c["coi_id"] == coi_id and c["status"] == "ACTIVE"
        ]

        if not commitments:
            return {"ok": False, "error": "no_active_commitments"}

        settlement_id = f"settle_{coi_id}_{uuid4().hex[:8]}"
        distributions = []

        if proved_failed:
            # Outcome failed: transfer stakes to buyer
            total_stake = sum(Decimal(str(c["stake_aigx"])) for c in commitments)
            payout_share = min(payout, total_stake)

            for c in commitments:
                stake = Decimal(str(c["stake_aigx"]))
                share = (stake / total_stake) * payout_share if total_stake > 0 else Decimal("0")
                distributions.append({
                    "commitment_id": c["id"],
                    "contributor_id": c["contributor_id"],
                    "type": "payout_to_buyer",
                    "aigx_amount": float(share.quantize(Decimal("0.01"))),
                    "original_stake": float(stake)
                })
                c["status"] = "SETTLED_PAYOUT"
                _POOL_STATE["contributor_balances"][c["contributor_id"]] -= stake

            _POOL_STATE["total_payouts"] += payout_share

        else:
            # Outcome succeeded: return stakes + premium share to contributors
            for c in commitments:
                stake = Decimal(str(c["stake_aigx"]))
                premium_share = Decimal(str(c.get("premium_share_aigx", 0)))
                mgmt_fee = (premium_share * Decimal(self.pool_mgmt_fee_bp)) / Decimal("10000")
                net_return = stake + premium_share - mgmt_fee

                distributions.append({
                    "commitment_id": c["id"],
                    "contributor_id": c["contributor_id"],
                    "type": "return_with_premium",
                    "stake_returned": float(stake),
                    "premium_earned": float((premium_share - mgmt_fee).quantize(Decimal("0.01"))),
                    "total_aigx": float(net_return.quantize(Decimal("0.01")))
                })
                c["status"] = "SETTLED_SUCCESS"

        settlement = {
            "id": settlement_id,
            "coi_id": coi_id,
            "proved_failed": proved_failed,
            "payout_due_usd": float(payout) if proved_failed else 0.0,
            "distributions": distributions,
            "merkle_receipt": merkle_receipt,
            "settled_at": _now_iso(),
            "note": "Non-custodial settlement instructions; actual PSP movement separate."
        }

        _POOL_STATE["settlement_history"].append(settlement)

        return {"ok": True, "settlement": settlement}

    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status"""
        active_commitments = [
            c for c in _POOL_STATE["active_commitments"].values()
            if c["status"] == "ACTIVE"
        ]
        return {
            "total_staked_aigx": float(_POOL_STATE["total_staked_aigx"]),
            "total_premiums_collected": float(_POOL_STATE["total_premiums_collected"]),
            "total_payouts": float(_POOL_STATE["total_payouts"]),
            "total_coordination_fees": float(_POOL_STATE["total_coordination_fees"]),
            "active_commitment_count": len(active_commitments),
            "active_coverage_aigx": sum(Decimal(str(c["stake_aigx"])) for c in active_commitments),
            "contributor_count": len(_POOL_STATE["contributor_balances"]),
            "settlement_count": len(_POOL_STATE["settlement_history"])
        }

    def get_contributor_balance(self, contributor_id: str) -> Dict[str, Any]:
        """Get contributor's staked balance and commitments"""
        balance = _POOL_STATE["contributor_balances"].get(contributor_id, Decimal("0"))
        commitments = [
            c for c in _POOL_STATE["active_commitments"].values()
            if c["contributor_id"] == contributor_id
        ]
        return {
            "contributor_id": contributor_id,
            "total_staked_aigx": float(balance),
            "active_commitments": [c for c in commitments if c["status"] == "ACTIVE"],
            "settled_commitments": [c for c in commitments if c["status"].startswith("SETTLED")]
        }


# Module-level singleton
_pool = OAPPool()


def quote_oap(coi_id: str, payout_usd: float, fail_prob: float, **kwargs) -> Dict[str, Any]:
    """Quote P2P outcome assurance"""
    return _pool.quote(coi_id, payout_usd, fail_prob, **kwargs)


def stake_oap(contributor_id: str, coi_id: str, stake_aigx: float, quote: Dict[str, Any]) -> Dict[str, Any]:
    """Stake AIGx credits for assurance"""
    return _pool.stake(contributor_id, coi_id, stake_aigx, quote)


def settle_oap(coi_id: str, proved_failed: bool, payout_usd: float, merkle_receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Settle assurance based on outcome"""
    return _pool.settle(coi_id, proved_failed, payout_usd, merkle_receipt)


def get_pool_status() -> Dict[str, Any]:
    """Get pool status"""
    return _pool.get_pool_status()


def get_contributor_balance(contributor_id: str) -> Dict[str, Any]:
    """Get contributor balance"""
    return _pool.get_contributor_balance(contributor_id)
