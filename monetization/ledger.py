"""
LEDGER
======

Double-entry accounting for every monetization event.
Integrates with existing append_intent_ledger() from log_to_jsonbin.py.
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timezone
from collections import defaultdict
import json

# Try to import existing DB functions
try:
    from log_to_jsonbin import append_intent_ledger, get_user, log_agent_update
    JSONBIN_AVAILABLE = True
except ImportError:
    JSONBIN_AVAILABLE = False

# MetaHive integration for collective learning
try:
    from metahive_brain import contribute_to_hive
    METAHIVE_AVAILABLE = True
except ImportError:
    METAHIVE_AVAILABLE = False
    async def contribute_to_hive(*args, **kwargs):
        return {"ok": False, "error": "not_available"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


class Ledger:
    """
    Double-entry ledger for monetization tracking.

    Every transaction has:
    - Timestamp
    - Entry type (sale, fee, payout, refund, etc.)
    - Reference (COI ID, contract ID, etc.)
    - Debit amount
    - Credit amount
    - Metadata

    Integrates with JSONBin for persistence.
    """

    def __init__(self):
        self._entries: List[Dict[str, Any]] = []
        self._balances: Dict[str, float] = defaultdict(float)

    def post(
        self,
        entry_type: str,
        ref: str,
        debit: float,
        credit: float,
        meta: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Post a ledger entry.

        Args:
            entry_type: Type of entry (sale, fee, payout, refund, etc.)
            ref: Reference ID (e.g., coi:xxx, entity:user123)
            debit: Debit amount (money out)
            credit: Credit amount (money in)
            meta: Additional metadata
        """
        row = {
            "ts": _now_iso(),
            "type": entry_type,
            "ref": ref,
            "debit": str(Decimal(str(debit)).quantize(Decimal("0.01"))),
            "credit": str(Decimal(str(credit)).quantize(Decimal("0.01"))),
            "meta": meta or {}
        }

        # Store locally
        self._entries.append(row)

        # Update running balance for entity
        if ref.startswith("entity:"):
            entity = ref.split(":", 1)[1]
            self._balances[entity] += credit - debit

        # Persist to JSONBin if available and it's a user entity
        if JSONBIN_AVAILABLE and entry_type in ("entity_credit", "entity_debit", "payout"):
            self._persist_to_jsonbin(row)

        return row

    def _persist_to_jsonbin(self, row: Dict[str, Any]):
        """Persist ledger entry to JSONBin via append_intent_ledger"""
        try:
            ref = row.get("ref", "")
            if ref.startswith("entity:"):
                username = ref.split(":", 1)[1]
                append_intent_ledger(username, {
                    "event": f"monetization_{row['type']}",
                    "debit": row["debit"],
                    "credit": row["credit"],
                    "ref": row["ref"],
                    "meta": row["meta"],
                    "ts": row["ts"]
                })
        except Exception as e:
            # Don't fail on persistence errors
            pass

    def get_balance(self, entity: str) -> float:
        """Get current balance for an entity"""
        return round(self._balances.get(entity, 0), 2)

    def get_balance_from_entries(self, entity: str) -> float:
        """Calculate balance from all entries (slower but accurate)"""
        total = 0.0
        entity_ref = f"entity:{entity}"
        for row in self._entries:
            if row.get("ref") == entity_ref:
                total += float(row["credit"]) - float(row["debit"])
        return round(total, 2)

    def get_entries(
        self,
        entry_type: str = None,
        ref_prefix: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get ledger entries with optional filters"""
        entries = self._entries

        if entry_type:
            entries = [e for e in entries if e["type"] == entry_type]

        if ref_prefix:
            entries = [e for e in entries if e["ref"].startswith(ref_prefix)]

        # Return most recent first
        return list(reversed(entries[-limit:]))

    def get_summary(self, entity: str = None) -> Dict[str, Any]:
        """Get ledger summary"""
        if entity:
            entity_ref = f"entity:{entity}"
            entries = [e for e in self._entries if e.get("ref") == entity_ref]
            total_credits = sum(float(e["credit"]) for e in entries)
            total_debits = sum(float(e["debit"]) for e in entries)
            return {
                "entity": entity,
                "total_credits": round(total_credits, 2),
                "total_debits": round(total_debits, 2),
                "balance": round(total_credits - total_debits, 2),
                "entry_count": len(entries)
            }

        # Global summary
        total_credits = sum(float(e["credit"]) for e in self._entries)
        total_debits = sum(float(e["debit"]) for e in self._entries)
        by_type = defaultdict(float)
        for e in self._entries:
            by_type[e["type"]] += float(e["credit"]) - float(e["debit"])

        return {
            "total_credits": round(total_credits, 2),
            "total_debits": round(total_debits, 2),
            "net": round(total_credits - total_debits, 2),
            "entry_count": len(self._entries),
            "by_type": dict(by_type)
        }

    def record_sale(
        self,
        coi_id: str,
        gross: float,
        splits: Dict[str, Any],
        badge: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Record a complete sale with all splits.

        This is a convenience method that creates multiple ledger entries.
        """
        # Main sale entry
        self.post(
            "sale",
            f"coi:{coi_id}",
            debit=0,
            credit=gross,
            meta={"coi_id": coi_id, "badge": badge}
        )

        # Platform fee
        if splits.get("platform", 0) > 0:
            self.post(
                "entity_credit",
                "entity:aigentsy_platform",
                debit=0,
                credit=splits["platform"],
                meta={"coi_id": coi_id, "type": "platform_fee"}
            )

        # User credit
        if splits.get("user", 0) > 0:
            username = splits.get("username", "unknown")
            self.post(
                "entity_credit",
                f"entity:{username}",
                debit=0,
                credit=splits["user"],
                meta={"coi_id": coi_id, "type": "user_revenue"}
            )

        # Pool credit
        if splits.get("pool", 0) > 0:
            self.post(
                "entity_credit",
                "entity:metahive_pool",
                debit=0,
                credit=splits["pool"],
                meta={"coi_id": coi_id, "type": "pool_contribution"}
            )

        # Partner credit
        if splits.get("partner", 0) > 0:
            partner = splits.get("partner_id", "partner_pool")
            self.post(
                "entity_credit",
                f"entity:{partner}",
                debit=0,
                credit=splits["partner"],
                meta={"coi_id": coi_id, "type": "partner_share"}
            )

        # Referral credits
        if splits.get("referrals"):
            for ref_id, ref_amt in splits["referrals"].items():
                self.post(
                    "entity_credit",
                    f"entity:{ref_id}",
                    debit=0,
                    credit=ref_amt,
                    meta={"coi_id": coi_id, "type": "referral"}
                )

        # Contribute successful pattern to MetaHive for collective learning
        if METAHIVE_AVAILABLE and gross > 0:
            try:
                import asyncio
                margin_pct = (gross - splits.get("platform", 0)) / gross if gross > 0 else 0

                asyncio.create_task(contribute_to_hive(
                    username=splits.get("username", "system"),
                    pattern_type="monetization_strategy",
                    context={
                        "coi_id": coi_id,
                        "gross": gross,
                        "splits": splits,
                        "badge": badge
                    },
                    action={
                        "type": "coi_sale",
                        "platform_fee_pct": splits.get("platform", 0) / gross if gross > 0 else 0,
                        "has_referrals": bool(splits.get("referrals")),
                        "has_badge": bool(badge and badge.get("badge_id"))
                    },
                    outcome={
                        "roas": 1 + margin_pct,  # Return on ad spend proxy
                        "quality_score": 0.8 if badge else 0.6,
                        "revenue": gross
                    },
                    anonymize=True
                ))
            except Exception:
                pass  # Don't fail sale recording on hive contribution error

        return {"ok": True, "coi_id": coi_id, "entries_created": True}


# Module-level singleton
_default_ledger = Ledger()


def post_entry(entry_type: str, ref: str, debit: float, credit: float, meta: Dict = None) -> Dict:
    """Post entry to default ledger"""
    return _default_ledger.post(entry_type, ref, debit, credit, meta)


def get_balance(entity: str) -> float:
    """Get balance from default ledger"""
    return _default_ledger.get_balance(entity)


def get_ledger_summary(entity: str = None) -> Dict[str, Any]:
    """Get ledger summary"""
    return _default_ledger.get_summary(entity)


def get_entity_balance(entity: str) -> Dict[str, Any]:
    """Get entity balance with summary"""
    return {
        "ok": True,
        "entity": entity,
        "balance": _default_ledger.get_balance(entity),
        "summary": _default_ledger.get_summary(entity)
    }


def get_entity_ledger(entity: str, limit: int = 100) -> Dict[str, Any]:
    """Get entity ledger history"""
    entries = _default_ledger.get_entries(ref_prefix=f"entity:{entity}", limit=limit)
    return {
        "ok": True,
        "entity": entity,
        "entries": entries,
        "count": len(entries)
    }


def get_ledger_stats() -> Dict[str, Any]:
    """Get global ledger statistics"""
    summary = _default_ledger.get_summary()
    return {
        "ok": True,
        **summary
    }


def record_sale(coi_id: str, gross: float, splits: Dict[str, Any], badge: Dict[str, Any] = None) -> Dict[str, Any]:
    """Record a complete sale"""
    return _default_ledger.record_sale(coi_id, gross, splits, badge)
