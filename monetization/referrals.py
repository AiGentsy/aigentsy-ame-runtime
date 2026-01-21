"""
REFERRALS
=========

Multi-hop attribution with geometric decay.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .fee_schedule import get_fee
from .ledger import post_entry


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class Referrals:
    """
    Referral attribution engine with multi-hop decay.

    Features:
    - Multi-hop referral chains (up to 5 levels)
    - Geometric decay per hop (60% retention per level)
    - Lifetime attribution tracking
    - Auto-payout on threshold
    """

    def __init__(self):
        self.config = {
            "default_pct": 0.12,     # 12% default referral share
            "decay_factor": 0.6,     # 60% retained per hop
            "max_hops": 5,           # Max chain length
            "min_payout": 1.00       # Min payout per referrer
        }
        self._chains: Dict[str, List[str]] = {}  # user -> referral chain
        self._earnings: Dict[str, float] = {}    # referrer -> total earnings

    def register_chain(self, user: str, chain: List[str]) -> Dict[str, Any]:
        """Register a referral chain for a user"""
        if not chain:
            return {"ok": True, "chain": []}

        # Limit chain length
        chain = chain[:self.config["max_hops"]]
        self._chains[user] = chain

        return {
            "ok": True,
            "user": user,
            "chain": chain,
            "hops": len(chain)
        }

    def get_chain(self, user: str) -> List[str]:
        """Get referral chain for a user"""
        return self._chains.get(user, [])

    def allocate(
        self,
        gross: float,
        chain: List[str],
        base_pct: float = None
    ) -> Dict[str, Any]:
        """
        Allocate referral revenue across chain with decay.

        Args:
            gross: Gross revenue amount
            chain: Referral chain (first = direct referrer)
            base_pct: Base referral percentage (default 12%)

        Returns:
            Dict with splits per referrer and remainder
        """
        if not chain:
            return {"splits": {}, "remainder": gross, "total_allocated": 0}

        pct = base_pct or get_fee("referral_default_pct", self.config["default_pct"])
        decay = get_fee("referral_decay_factor", self.config["decay_factor"])
        min_payout = self.config["min_payout"]

        splits = {}
        total_allocated = 0.0

        for i, referrer in enumerate(chain[:self.config["max_hops"]]):
            # Geometric decay: base_pct * decay^i
            hop_pct = pct * (decay ** i)
            amount = round(gross * hop_pct, 2)

            if amount < min_payout:
                continue

            splits[referrer] = amount
            total_allocated += amount

            # Track earnings
            self._earnings[referrer] = self._earnings.get(referrer, 0) + amount

        remainder = round(gross - total_allocated, 2)

        return {
            "splits": splits,
            "remainder": remainder,
            "total_allocated": round(total_allocated, 2),
            "chain_length": len(chain),
            "active_hops": len(splits)
        }

    def record_attribution(
        self,
        user: str,
        gross: float,
        source: str = "purchase"
    ) -> Dict[str, Any]:
        """
        Record attribution for a user's revenue event.

        Looks up chain and allocates referral splits.
        """
        chain = self.get_chain(user)
        if not chain:
            return {"ok": True, "referrals": {}, "no_chain": True}

        alloc = self.allocate(gross, chain)

        # Record ledger entries
        for referrer, amount in alloc["splits"].items():
            post_entry(
                "referral_credit",
                f"entity:{referrer}",
                debit=0,
                credit=amount,
                meta={"source_user": user, "source": source, "gross": gross}
            )

        return {
            "ok": True,
            "user": user,
            "gross": gross,
            "referrals": alloc["splits"],
            "total_referral_payout": alloc["total_allocated"]
        }

    def get_earnings(self, referrer: str) -> Dict[str, Any]:
        """Get referrer's total earnings"""
        return {
            "referrer": referrer,
            "total_earnings": round(self._earnings.get(referrer, 0), 2)
        }

    def get_top_referrers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top referrers by earnings"""
        sorted_referrers = sorted(
            self._earnings.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {"referrer": r, "earnings": round(e, 2)}
            for r, e in sorted_referrers[:limit]
        ]

    def simulate_chain(
        self,
        gross: float,
        chain_length: int
    ) -> Dict[str, Any]:
        """Simulate referral allocation for a chain length"""
        fake_chain = [f"referrer_{i}" for i in range(chain_length)]
        return self.allocate(gross, fake_chain)


# Module-level singleton
_default_referrals = Referrals()


def allocate_referrals(gross: float, chain: List[str], **kwargs) -> Dict[str, Any]:
    """Allocate referrals using default engine"""
    return _default_referrals.allocate(gross, chain, **kwargs)


def register_chain(user: str, chain: List[str]) -> Dict[str, Any]:
    """Register referral chain"""
    return _default_referrals.register_chain(user, chain)


def record_attribution(user: str, gross: float, **kwargs) -> Dict[str, Any]:
    """Record attribution"""
    return _default_referrals.record_attribution(user, gross, **kwargs)
