"""
REVENUE RECONCILIATION ENGINE
==============================

Unified cross-platform revenue tracking with discrepancy detection.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
from collections import defaultdict
import hashlib
import json


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _parse_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except:
        return datetime.now(timezone.utc)


class RevenueSource(str, Enum):
    STRIPE = "stripe"
    UPWORK = "upwork"
    FIVERR = "fiverr"
    FREELANCER = "freelancer"
    TOPTAL = "toptal"
    GITHUB = "github"
    AFFILIATE = "affiliate"
    SUBSCRIPTION = "subscription"
    AIGX_CONVERSION = "aigx_conversion"
    PARTNER_NETWORK = "partner_network"
    SHOPIFY = "shopify"
    MANUAL = "manual"
    OTHER = "other"


class ReconciliationStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    DISCREPANCY = "discrepancy"
    RESOLVED = "resolved"
    WRITTEN_OFF = "written_off"


class EntryType(str, Enum):
    REVENUE = "revenue"
    FEE = "fee"
    PAYOUT = "payout"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"


PLATFORM_FEES = {
    RevenueSource.STRIPE: {"percent": 0.029, "fixed": 0.30},
    RevenueSource.UPWORK: {"percent": 0.10, "fixed": 0},
    RevenueSource.FIVERR: {"percent": 0.20, "fixed": 0},
    RevenueSource.FREELANCER: {"percent": 0.10, "fixed": 0},
    RevenueSource.TOPTAL: {"percent": 0.0, "fixed": 0},
    RevenueSource.SHOPIFY: {"percent": 0.029, "fixed": 0.30},
}

AIGENTSY_FEE = {"percent": 0.028, "fixed": 0.28}

RECONCILIATION_CONFIG = {
    "tolerance_percent": 0.02,
    "tolerance_fixed": 1.00,
    "auto_resolve_below": 5.00,
}


@dataclass
class LedgerEntry:
    entry_id: str
    user_id: str
    source: RevenueSource
    entry_type: EntryType
    gross_amount: float
    fees: float
    net_amount: float
    currency: str
    reference_id: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)
    reconciled: bool = False
    reconciliation_status: ReconciliationStatus = ReconciliationStatus.PENDING
    matched_entry_id: Optional[str] = None
    discrepancy_amount: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "entry_id": self.entry_id,
            "user_id": self.user_id,
            "source": self.source.value,
            "entry_type": self.entry_type.value,
            "gross_amount": self.gross_amount,
            "fees": self.fees,
            "net_amount": self.net_amount,
            "currency": self.currency,
            "reference_id": self.reference_id,
            "description": self.description,
            "created_at": self.created_at,
            "reconciled": self.reconciled,
            "reconciliation_status": self.reconciliation_status.value,
        }


@dataclass
class Discrepancy:
    discrepancy_id: str
    entry_id: str
    user_id: str
    expected_amount: float
    actual_amount: float
    difference: float
    difference_percent: float
    source: RevenueSource
    reason: Optional[str] = None
    status: ReconciliationStatus = ReconciliationStatus.DISCREPANCY
    detected_at: str = field(default_factory=_now)
    resolved_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "discrepancy_id": self.discrepancy_id,
            "entry_id": self.entry_id,
            "user_id": self.user_id,
            "expected_amount": self.expected_amount,
            "actual_amount": self.actual_amount,
            "difference": self.difference,
            "source": self.source.value,
            "reason": self.reason,
            "status": self.status.value,
        }


class RevenueReconciliationEngine:
    
    def __init__(self):
        self.ledger: List[LedgerEntry] = []
        self.discrepancies: List[Discrepancy] = []
        self.pending_payouts: Dict[str, Dict] = {}
        self._entries_by_user: Dict[str, List[LedgerEntry]] = defaultdict(list)
        self._entries_by_reference: Dict[str, LedgerEntry] = {}
        
        print("\n" + "="*60)
        print("💵 REVENUE RECONCILIATION ENGINE INITIALIZED")
        print("="*60 + "\n")
    
    
    def record_revenue(
        self,
        user_id: str,
        source: RevenueSource,
        gross_amount: float,
        reference_id: str,
        description: str,
        currency: str = "USD",
        metadata: Dict = None
    ) -> LedgerEntry:
        
        platform_fee_config = PLATFORM_FEES.get(source, {"percent": 0, "fixed": 0})
        platform_fee = gross_amount * platform_fee_config["percent"] + platform_fee_config["fixed"]
        aigentsy_fee = gross_amount * AIGENTSY_FEE["percent"] + AIGENTSY_FEE["fixed"]
        total_fees = platform_fee + aigentsy_fee
        net_amount = gross_amount - total_fees
        
        entry = LedgerEntry(
            entry_id=_generate_id("led"),
            user_id=user_id,
            source=source,
            entry_type=EntryType.REVENUE,
            gross_amount=round(gross_amount, 2),
            fees=round(total_fees, 2),
            net_amount=round(net_amount, 2),
            currency=currency,
            reference_id=reference_id,
            description=description,
            metadata=metadata or {},
        )
        
        self._add_entry(entry)
        
        self.pending_payouts[reference_id] = {
            "entry_id": entry.entry_id,
            "user_id": user_id,
            "expected_net": net_amount,
            "source": source,
        }
        
        return entry
    
    
    def record_payout(
        self,
        user_id: str,
        source: RevenueSource,
        amount: float,
        reference_id: str,
        description: str,
        currency: str = "USD",
    ) -> Tuple[LedgerEntry, Optional[Discrepancy]]:
        
        entry = LedgerEntry(
            entry_id=_generate_id("led"),
            user_id=user_id,
            source=source,
            entry_type=EntryType.PAYOUT,
            gross_amount=amount,
            fees=0,
            net_amount=amount,
            currency=currency,
            reference_id=reference_id,
            description=description,
        )
        
        self._add_entry(entry)
        discrepancy = self._reconcile_payout(entry, reference_id)
        
        return entry, discrepancy
    
    
    def _add_entry(self, entry: LedgerEntry):
        self.ledger.append(entry)
        self._entries_by_user[entry.user_id].append(entry)
        self._entries_by_reference[entry.reference_id] = entry
    
    
    def _reconcile_payout(self, payout_entry: LedgerEntry, reference_id: str) -> Optional[Discrepancy]:
        pending = self.pending_payouts.get(reference_id)
        
        if not pending:
            payout_entry.reconciliation_status = ReconciliationStatus.PENDING
            return None
        
        expected = pending["expected_net"]
        actual = payout_entry.net_amount
        
        diff = abs(expected - actual)
        diff_percent = diff / expected if expected > 0 else 0
        
        if diff <= RECONCILIATION_CONFIG["tolerance_fixed"] or diff_percent <= RECONCILIATION_CONFIG["tolerance_percent"]:
            payout_entry.reconciled = True
            payout_entry.reconciliation_status = ReconciliationStatus.MATCHED
            payout_entry.matched_entry_id = pending["entry_id"]
            del self.pending_payouts[reference_id]
            return None
        
        discrepancy = Discrepancy(
            discrepancy_id=_generate_id("disc"),
            entry_id=payout_entry.entry_id,
            user_id=payout_entry.user_id,
            expected_amount=expected,
            actual_amount=actual,
            difference=round(expected - actual, 2),
            difference_percent=round(diff_percent * 100, 2),
            source=payout_entry.source,
            reason="Fee difference" if diff < 20 else "Significant variance",
        )
        
        self.discrepancies.append(discrepancy)
        payout_entry.reconciliation_status = ReconciliationStatus.DISCREPANCY
        payout_entry.discrepancy_amount = discrepancy.difference
        
        if abs(discrepancy.difference) < RECONCILIATION_CONFIG["auto_resolve_below"]:
            discrepancy.status = ReconciliationStatus.RESOLVED
            discrepancy.resolved_at = _now()
            discrepancy.resolution_notes = "Auto-resolved: below threshold"
        
        return discrepancy
    
    
    def generate_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        
        entries = self.ledger
        
        if start_date:
            entries = [e for e in entries if e.created_at >= start_date]
        if end_date:
            entries = [e for e in entries if e.created_at <= end_date]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        
        revenue_entries = [e for e in entries if e.entry_type == EntryType.REVENUE]
        
        total_gross = sum(e.gross_amount for e in revenue_entries)
        total_fees = sum(e.fees for e in revenue_entries)
        total_net = sum(e.net_amount for e in revenue_entries)
        
        matched = sum(1 for e in entries if e.reconciliation_status == ReconciliationStatus.MATCHED)
        pending = sum(1 for e in entries if e.reconciliation_status == ReconciliationStatus.PENDING)
        
        by_source = {}
        for source in RevenueSource:
            source_entries = [e for e in revenue_entries if e.source == source]
            if source_entries:
                by_source[source.value] = {
                    "count": len(source_entries),
                    "gross": round(sum(e.gross_amount for e in source_entries), 2),
                    "net": round(sum(e.net_amount for e in source_entries), 2),
                }
        
        return {
            "total_entries": len(entries),
            "matched_entries": matched,
            "pending_entries": pending,
            "total_gross_revenue": round(total_gross, 2),
            "total_fees": round(total_fees, 2),
            "total_net_revenue": round(total_net, 2),
            "by_source": by_source,
            "unresolved_discrepancies": [
                d.to_dict() for d in self.discrepancies 
                if d.status == ReconciliationStatus.DISCREPANCY
            ][:10],
        }
    
    
    def get_user_ledger(self, user_id: str, limit: int = 100) -> Dict[str, Any]:
        entries = self._entries_by_user.get(user_id, [])
        entries = sorted(entries, key=lambda e: e.created_at, reverse=True)[:limit]
        
        revenue_entries = [e for e in entries if e.entry_type == EntryType.REVENUE]
        
        return {
            "user_id": user_id,
            "entry_count": len(entries),
            "total_gross_revenue": round(sum(e.gross_amount for e in revenue_entries), 2),
            "total_net": round(sum(e.net_amount for e in entries), 2),
            "entries": [e.to_dict() for e in entries],
        }
    
    
    def export_for_audit(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        report = self.generate_report(start_date, end_date)
        
        entries = self.ledger
        if start_date:
            entries = [e for e in entries if e.created_at >= start_date]
        if end_date:
            entries = [e for e in entries if e.created_at <= end_date]
        
        entry_data = json.dumps([e.to_dict() for e in entries], sort_keys=True)
        verification_hash = hashlib.sha256(entry_data.encode()).hexdigest()
        
        return {
            "export_id": _generate_id("exp"),
            "exported_at": _now(),
            "summary": report,
            "verification_hash": verification_hash,
            "entries": [e.to_dict() for e in entries],
        }
    
    
    def get_reconciliation_stats(self) -> Dict[str, Any]:
        if not self.ledger:
            return {"total_entries": 0}
        
        total = len(self.ledger)
        matched = sum(1 for e in self.ledger if e.reconciliation_status == ReconciliationStatus.MATCHED)
        
        revenue_entries = [e for e in self.ledger if e.entry_type == EntryType.REVENUE]
        
        return {
            "total_entries": total,
            "matched_entries": matched,
            "reconciliation_rate": round(matched / total * 100, 1) if total > 0 else 0,
            "total_gross_revenue": round(sum(e.gross_amount for e in revenue_entries), 2),
            "total_net_revenue": round(sum(e.net_amount for e in revenue_entries), 2),
            "unresolved_discrepancies": sum(1 for d in self.discrepancies if d.status == ReconciliationStatus.DISCREPANCY),
            "pending_payouts": len(self.pending_payouts),
        }


_RECONCILIATION_ENGINE: Optional[RevenueReconciliationEngine] = None


def get_reconciliation_engine() -> RevenueReconciliationEngine:
    global _RECONCILIATION_ENGINE
    if _RECONCILIATION_ENGINE is None:
        _RECONCILIATION_ENGINE = RevenueReconciliationEngine()
    return _RECONCILIATION_ENGINE


async def record_platform_revenue(
    user_id: str,
    platform: str,
    amount: float,
    reference_id: str,
    description: str = "Platform revenue"
) -> Dict[str, Any]:
    engine = get_reconciliation_engine()
    
    try:
        source = RevenueSource(platform.lower())
    except ValueError:
        source = RevenueSource.OTHER
    
    entry = engine.record_revenue(user_id, source, amount, reference_id, description)
    
    return {
        "ok": True,
        "entry_id": entry.entry_id,
        "gross_amount": entry.gross_amount,
        "fees": entry.fees,
        "net_amount": entry.net_amount,
    }


async def record_platform_payout(
    user_id: str,
    platform: str,
    amount: float,
    reference_id: str,
    description: str = "Platform payout"
) -> Dict[str, Any]:
    engine = get_reconciliation_engine()
    
    try:
        source = RevenueSource(platform.lower())
    except ValueError:
        source = RevenueSource.OTHER
    
    entry, discrepancy = engine.record_payout(user_id, source, amount, reference_id, description)
    
    result = {
        "ok": True,
        "entry_id": entry.entry_id,
        "amount": entry.net_amount,
        "reconciliation_status": entry.reconciliation_status.value,
    }
    
    if discrepancy:
        result["discrepancy"] = discrepancy.to_dict()
    
    return result


async def _test_reconciliation_engine():
    print("\n" + "="*60)
    print("🧪 TESTING REVENUE RECONCILIATION ENGINE")
    print("="*60)
    
    engine = get_reconciliation_engine()
    
    print("\n💰 Test 1: Recording revenue...")
    entry1 = engine.record_revenue("alice", RevenueSource.UPWORK, 500, "upwork_001", "Website project")
    print(f"   Gross: ${entry1.gross_amount}, Fees: ${entry1.fees}, Net: ${entry1.net_amount}")
    
    entry2 = engine.record_revenue("alice", RevenueSource.STRIPE, 200, "stripe_001", "Direct payment")
    print(f"   Gross: ${entry2.gross_amount} (Stripe)")
    
    entry3 = engine.record_revenue("bob", RevenueSource.FIVERR, 100, "fiverr_001", "Logo design")
    print(f"   Gross: ${entry3.gross_amount} (Fiverr)")
    
    print("\n✅ Test 2: Matching payout...")
    payout1, disc1 = engine.record_payout("alice", RevenueSource.UPWORK, entry1.net_amount, "upwork_001", "Payout")
    print(f"   Status: {payout1.reconciliation_status.value}")
    
    print("\n⚠️ Test 3: Payout with discrepancy...")
    payout2, disc2 = engine.record_payout("alice", RevenueSource.STRIPE, entry2.net_amount - 15, "stripe_001", "Payout")
    if disc2:
        print(f"   Discrepancy: ${disc2.difference}")
    
    print("\n📊 Test 4: Report...")
    report = engine.generate_report()
    print(f"   Gross: ${report['total_gross_revenue']}")
    print(f"   Net: ${report['total_net_revenue']}")
    print(f"   Matched: {report['matched_entries']}/{report['total_entries']}")
    
    print("\n📋 Test 5: Audit export...")
    export = engine.export_for_audit()
    print(f"   Hash: {export['verification_hash'][:20]}...")
    
    print("\n📈 Stats:", engine.get_reconciliation_stats())
    print("\n✅ Reconciliation engine tests completed!")


if __name__ == "__main__":
    asyncio.run(_test_reconciliation_engine())
