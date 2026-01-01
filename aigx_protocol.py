"""
AIGx PROTOCOL - The Native Railway to the AI/AGI Economy
==================================================================

WHAT AIGENTSY IS:
- Platform that connects work to AI agents
- Protocol that settles AI-to-AI transactions  
- Facilitator of peer-to-peer financial activity
- Fee collector on ALL activity

WHAT AIGENTSY IS NOT:
- NOT a bank (no deposits, no capital at risk)
- NOT a lender (users lend to users)
- NOT holding money (just facilitating transfers)
- NOT the counterparty to any transaction

AIGx CREDITS:
- Earned through: time, work, referrals, verified outcomes, licensing
- Spent on: staking, features, visibility, P2P facilitation
- Non-transferable, non-purchasable
- Primary utility is platform features

REVENUE MODEL:
- User transactions: 2.8% + $0.28
- Protocol settlements: 0.5%
- P2P facilitation: 2-2.5%
- All fees, never counterparty risk
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4


# ============================================================
# PROTOCOL CONSTANTS
# ============================================================

PROTOCOL_VERSION = "1.0.0"

# Fee structure (AiGentsy takes fees, never risk)
FEES = {
    "transaction": {"percent": 0.028, "flat": 0.28},  # 2.8% + $0.28
    "protocol_settlement": {"percent": 0.005},  # 0.5%
    "p2p_lending": {"percent": 0.025},  # 2.5%
    "p2p_staking": {"percent": 0.025},  # 2.5%
    "factoring": {"percent": 0.02},  # 2%
    "ocl_facilitation": {"percent": 0.025},  # 2.5%
}

# AIGx earning rates
AIGX_EARNING_RATES = {
    "daily_active": 1.0,  # 1 AIGx per active day
    "weekly_streak": 5.0,  # 5 AIGx for 7-day streak
    "monthly_power": 25.0,  # 25 AIGx for 30-day streak
    "job_completed": 0.10,  # 10% of job value in AIGx
    "referral_signup": 10.0,  # 10 AIGx per referral
    "referral_first_job": 25.0,  # 25 AIGx when referral completes first job
    "outcome_verified": 5.0,  # 5 AIGx per verified PoO
    "ip_licensed": 0.05,  # 5% of license value in AIGx
}

# Reputation tiers (affects P2P rates)
REPUTATION_TIERS = {
    "bronze": {"min_score": 0, "max_score": 49, "p2p_rate_modifier": 1.2},
    "silver": {"min_score": 50, "max_score": 69, "p2p_rate_modifier": 1.0},
    "gold": {"min_score": 70, "max_score": 84, "p2p_rate_modifier": 0.85},
    "platinum": {"min_score": 85, "max_score": 94, "p2p_rate_modifier": 0.7},
    "diamond": {"min_score": 95, "max_score": 100, "p2p_rate_modifier": 0.6},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


# ============================================================
# AIGX CREDIT SYSTEM (Earned, Not Purchased)
# ============================================================

class AIGxEarnType(str, Enum):
    """How AIGx is earned - NEVER purchased"""
    DAILY_ACTIVE = "daily_active"
    WEEKLY_STREAK = "weekly_streak"
    MONTHLY_POWER = "monthly_power"
    JOB_COMPLETED = "job_completed"
    REFERRAL_SIGNUP = "referral_signup"
    REFERRAL_FIRST_JOB = "referral_first_job"
    OUTCOME_VERIFIED = "outcome_verified"
    IP_LICENSED = "ip_licensed"
    PROTOCOL_REWARD = "protocol_reward"
    P2P_RETURN = "p2p_return"  # Return from P2P lending/staking


class AIGxSpendType(str, Enum):
    """How AIGx is spent"""
    P2P_STAKE = "p2p_stake"  # Stake on another user
    P2P_LEND = "p2p_lend"  # Lend to another user
    FEATURE_UNLOCK = "feature_unlock"
    VISIBILITY_BOOST = "visibility_boost"
    PRIORITY_MATCHING = "priority_matching"
    PROTOCOL_FEE = "protocol_fee"


@dataclass
class AIGxTransaction:
    """Record of AIGx earning or spending"""
    tx_id: str
    user_id: str
    amount: float  # Positive = earn, Negative = spend
    tx_type: str  # AIGxEarnType or AIGxSpendType
    description: str
    reference_id: Optional[str] = None  # Job ID, referral ID, etc.
    created_at: str = field(default_factory=_now)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class AIGxLedger:
    """
    Tracks all AIGx credits - EARNED ONLY, NEVER PURCHASED
    
    AIGx is:
    - Non-transferable between users
    - Non-purchasable with money
    - Earned through platform activity only
    """
    
    def __init__(self):
        self._balances: Dict[str, float] = {}
        self._transactions: List[AIGxTransaction] = []
        self._user_transactions: Dict[str, List[str]] = {}
        self._total_issued: float = 0.0
        self._total_burned: float = 0.0  # Spent on fees
    
    def earn(
        self,
        user_id: str,
        amount: float,
        earn_type: AIGxEarnType,
        description: str,
        reference_id: str = None
    ) -> Dict[str, Any]:
        """
        User earns AIGx through activity (ONLY way to get AIGx)
        """
        if amount <= 0:
            return {"ok": False, "error": "amount_must_be_positive"}
        
        tx = AIGxTransaction(
            tx_id=_generate_id("aigx_earn"),
            user_id=user_id,
            amount=amount,
            tx_type=earn_type.value,
            description=description,
            reference_id=reference_id
        )
        
        # Update balance
        self._balances[user_id] = self._balances.get(user_id, 0) + amount
        self._total_issued += amount
        
        # Record transaction
        self._transactions.append(tx)
        if user_id not in self._user_transactions:
            self._user_transactions[user_id] = []
        self._user_transactions[user_id].append(tx.tx_id)
        
        return {
            "ok": True,
            "tx_id": tx.tx_id,
            "amount_earned": amount,
            "new_balance": self._balances[user_id],
            "earn_type": earn_type.value
        }
    
    def spend(
        self,
        user_id: str,
        amount: float,
        spend_type: AIGxSpendType,
        description: str,
        reference_id: str = None
    ) -> Dict[str, Any]:
        """
        User spends AIGx on platform features or P2P
        """
        if amount <= 0:
            return {"ok": False, "error": "amount_must_be_positive"}
        
        current_balance = self._balances.get(user_id, 0)
        if amount > current_balance:
            return {
                "ok": False,
                "error": "insufficient_aigx",
                "balance": current_balance,
                "required": amount
            }
        
        tx = AIGxTransaction(
            tx_id=_generate_id("aigx_spend"),
            user_id=user_id,
            amount=-amount,  # Negative for spending
            tx_type=spend_type.value,
            description=description,
            reference_id=reference_id
        )
        
        # Update balance
        self._balances[user_id] = current_balance - amount
        
        # If spent on fees, it's burned
        if spend_type == AIGxSpendType.PROTOCOL_FEE:
            self._total_burned += amount
        
        # Record transaction
        self._transactions.append(tx)
        self._user_transactions[user_id].append(tx.tx_id)
        
        return {
            "ok": True,
            "tx_id": tx.tx_id,
            "amount_spent": amount,
            "new_balance": self._balances[user_id],
            "spend_type": spend_type.value
        }
    
    def get_balance(self, user_id: str) -> float:
        """Get user's AIGx balance"""
        return self._balances.get(user_id, 0)
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's AIGx transaction history"""
        tx_ids = self._user_transactions.get(user_id, [])[-limit:]
        return [
            tx.to_dict() for tx in self._transactions
            if tx.tx_id in tx_ids
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AIGx system stats"""
        return {
            "total_issued": round(self._total_issued, 2),
            "total_burned": round(self._total_burned, 2),
            "circulating": round(self._total_issued - self._total_burned, 2),
            "total_users": len(self._balances),
            "total_transactions": len(self._transactions)
        }


# ============================================================
# P2P FINANCIAL LAYER (AiGentsy = Facilitator, Not Bank)
# ============================================================

class P2PTransactionType(str, Enum):
    """Types of P2P transactions"""
    STAKE = "stake"  # User A stakes on User B
    LEND = "lend"  # User A lends to User B
    FACTOR = "factor"  # User A advances to User B against invoice
    OCL = "ocl"  # User A provides credit line to User B


class P2PTransactionStatus(str, Enum):
    """Status of P2P transaction"""
    ACTIVE = "active"
    REPAYING = "repaying"
    REPAID = "repaid"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


@dataclass
class P2PTransaction:
    """
    Peer-to-peer financial transaction
    
    AiGentsy is FACILITATOR:
    - Matches parties
    - Collects fees
    - Tracks repayment
    - NEVER the counterparty
    - NEVER holds capital
    """
    tx_id: str
    tx_type: P2PTransactionType
    from_user: str  # Lender/Staker
    to_user: str  # Borrower/Recipient
    principal_aigx: float
    interest_rate: float  # Annual rate
    duration_days: int
    aigentsy_fee_rate: float
    aigentsy_fee_aigx: float
    status: P2PTransactionStatus
    created_at: str
    due_at: str
    repaid_amount: float = 0.0
    repayment_history: List[Dict] = field(default_factory=list)
    reference_id: Optional[str] = None  # Invoice ID for factoring, etc.
    
    def total_due(self) -> float:
        """Calculate total amount due"""
        days = self.duration_days
        interest = self.principal_aigx * (self.interest_rate / 100) * (days / 365)
        return round(self.principal_aigx + interest, 2)
    
    def remaining(self) -> float:
        """Amount remaining to repay"""
        return round(self.total_due() - self.repaid_amount, 2)
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result["total_due"] = self.total_due()
        result["remaining"] = self.remaining()
        return result


class P2PFacilitator:
    """
    Facilitates peer-to-peer financial transactions
    
    AiGentsy NEVER:
    - Holds capital
    - Takes counterparty risk
    - Lends its own money
    
    AiGentsy ALWAYS:
    - Matches parties
    - Collects fees (2-2.5%)
    - Tracks repayments
    - Enforces via reputation
    """
    
    def __init__(self, aigx_ledger: AIGxLedger):
        self.aigx = aigx_ledger
        self._transactions: Dict[str, P2PTransaction] = {}
        self._user_as_lender: Dict[str, List[str]] = {}
        self._user_as_borrower: Dict[str, List[str]] = {}
        self._total_facilitated: float = 0.0
        self._total_fees_collected: float = 0.0
    
    def create_stake(
        self,
        staker_id: str,
        recipient_id: str,
        amount_aigx: float,
        duration_days: int = 30,
        interest_rate: float = 0.0  # Staking can be 0% (support)
    ) -> Dict[str, Any]:
        """
        User A stakes AIGx on User B
        
        Use case: Reputation boost, credit line backing
        Risk: Staker (User A)
        Fee: 2.5% to AiGentsy
        """
        # Validate staker has balance
        staker_balance = self.aigx.get_balance(staker_id)
        fee_rate = FEES["p2p_staking"]["percent"]
        fee_amount = amount_aigx * fee_rate
        total_needed = amount_aigx + fee_amount
        
        if staker_balance < total_needed:
            return {
                "ok": False,
                "error": "insufficient_aigx",
                "balance": staker_balance,
                "required": total_needed
            }
        
        # Deduct from staker
        self.aigx.spend(staker_id, amount_aigx, AIGxSpendType.P2P_STAKE, 
                       f"Stake on {recipient_id}", recipient_id)
        self.aigx.spend(staker_id, fee_amount, AIGxSpendType.PROTOCOL_FEE,
                       "P2P staking fee", recipient_id)
        
        # Create transaction record
        tx = P2PTransaction(
            tx_id=_generate_id("p2p_stake"),
            tx_type=P2PTransactionType.STAKE,
            from_user=staker_id,
            to_user=recipient_id,
            principal_aigx=amount_aigx,
            interest_rate=interest_rate,
            duration_days=duration_days,
            aigentsy_fee_rate=fee_rate,
            aigentsy_fee_aigx=fee_amount,
            status=P2PTransactionStatus.ACTIVE,
            created_at=_now(),
            due_at=(datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()
        )
        
        self._transactions[tx.tx_id] = tx
        self._index_transaction(tx)
        self._total_facilitated += amount_aigx
        self._total_fees_collected += fee_amount
        
        return {
            "ok": True,
            "tx_id": tx.tx_id,
            "staker": staker_id,
            "recipient": recipient_id,
            "amount": amount_aigx,
            "fee_collected": fee_amount,
            "duration_days": duration_days,
            "due_at": tx.due_at,
            "message": f"Stake active. {recipient_id} credit boosted."
        }
    
    def create_loan(
        self,
        lender_id: str,
        borrower_id: str,
        amount_aigx: float,
        interest_rate: float,
        duration_days: int = 30
    ) -> Dict[str, Any]:
        """
        User A lends AIGx to User B
        
        Risk: Lender (User A)
        Fee: 2.5% to AiGentsy
        """
        lender_balance = self.aigx.get_balance(lender_id)
        fee_rate = FEES["p2p_lending"]["percent"]
        fee_amount = amount_aigx * fee_rate
        total_needed = amount_aigx + fee_amount
        
        if lender_balance < total_needed:
            return {
                "ok": False,
                "error": "insufficient_aigx",
                "balance": lender_balance,
                "required": total_needed
            }
        
        # Deduct from lender
        self.aigx.spend(lender_id, amount_aigx, AIGxSpendType.P2P_LEND,
                       f"Loan to {borrower_id}", borrower_id)
        self.aigx.spend(lender_id, fee_amount, AIGxSpendType.PROTOCOL_FEE,
                       "P2P lending fee", borrower_id)
        
        # Credit to borrower
        self.aigx.earn(borrower_id, amount_aigx, AIGxEarnType.P2P_RETURN,
                      f"Loan from {lender_id}", lender_id)
        
        # Create transaction
        tx = P2PTransaction(
            tx_id=_generate_id("p2p_loan"),
            tx_type=P2PTransactionType.LEND,
            from_user=lender_id,
            to_user=borrower_id,
            principal_aigx=amount_aigx,
            interest_rate=interest_rate,
            duration_days=duration_days,
            aigentsy_fee_rate=fee_rate,
            aigentsy_fee_aigx=fee_amount,
            status=P2PTransactionStatus.ACTIVE,
            created_at=_now(),
            due_at=(datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()
        )
        
        self._transactions[tx.tx_id] = tx
        self._index_transaction(tx)
        self._total_facilitated += amount_aigx
        self._total_fees_collected += fee_amount
        
        return {
            "ok": True,
            "tx_id": tx.tx_id,
            "lender": lender_id,
            "borrower": borrower_id,
            "principal": amount_aigx,
            "interest_rate": interest_rate,
            "total_due": tx.total_due(),
            "fee_collected": fee_amount,
            "due_at": tx.due_at
        }
    
    def create_factoring_advance(
        self,
        investor_id: str,
        agent_id: str,
        invoice_value: float,
        advance_rate: float = 0.80,  # 80% advance
        invoice_id: str = None
    ) -> Dict[str, Any]:
        """
        User A (investor) advances payment to User B (agent) against pending invoice
        
        Risk: Investor (User A)
        Fee: 2% to AiGentsy
        """
        advance_amount = invoice_value * advance_rate
        fee_rate = FEES["factoring"]["percent"]
        fee_amount = advance_amount * fee_rate
        total_needed = advance_amount + fee_amount
        
        investor_balance = self.aigx.get_balance(investor_id)
        if investor_balance < total_needed:
            return {
                "ok": False,
                "error": "insufficient_aigx",
                "balance": investor_balance,
                "required": total_needed
            }
        
        # Deduct from investor
        self.aigx.spend(investor_id, advance_amount, AIGxSpendType.P2P_LEND,
                       f"Factoring advance to {agent_id}", invoice_id)
        self.aigx.spend(investor_id, fee_amount, AIGxSpendType.PROTOCOL_FEE,
                       "Factoring fee", invoice_id)
        
        # Credit to agent
        self.aigx.earn(agent_id, advance_amount, AIGxEarnType.P2P_RETURN,
                      f"Factoring advance from {investor_id}", invoice_id)
        
        # Create transaction (repayment = full invoice value)
        tx = P2PTransaction(
            tx_id=_generate_id("p2p_factor"),
            tx_type=P2PTransactionType.FACTOR,
            from_user=investor_id,
            to_user=agent_id,
            principal_aigx=advance_amount,
            interest_rate=((invoice_value / advance_amount) - 1) * 100,  # Implied rate
            duration_days=30,  # Standard invoice term
            aigentsy_fee_rate=fee_rate,
            aigentsy_fee_aigx=fee_amount,
            status=P2PTransactionStatus.ACTIVE,
            created_at=_now(),
            due_at=(datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            reference_id=invoice_id
        )
        
        # Override: investor gets full invoice value on repayment
        tx.repayment_history.append({
            "type": "terms",
            "invoice_value": invoice_value,
            "advance_amount": advance_amount,
            "holdback": invoice_value - advance_amount
        })
        
        self._transactions[tx.tx_id] = tx
        self._index_transaction(tx)
        self._total_facilitated += advance_amount
        self._total_fees_collected += fee_amount
        
        return {
            "ok": True,
            "tx_id": tx.tx_id,
            "investor": investor_id,
            "agent": agent_id,
            "invoice_value": invoice_value,
            "advance_amount": advance_amount,
            "advance_rate": advance_rate,
            "holdback": invoice_value - advance_amount,
            "fee_collected": fee_amount,
            "invoice_id": invoice_id
        }
    
    def repay(
        self,
        tx_id: str,
        amount_aigx: float,
        payer_id: str = None
    ) -> Dict[str, Any]:
        """
        Repay a P2P transaction
        """
        tx = self._transactions.get(tx_id)
        if not tx:
            return {"ok": False, "error": "transaction_not_found"}
        
        if tx.status not in [P2PTransactionStatus.ACTIVE, P2PTransactionStatus.REPAYING]:
            return {"ok": False, "error": f"cannot_repay_status_{tx.status.value}"}
        
        payer = payer_id or tx.to_user
        payer_balance = self.aigx.get_balance(payer)
        
        remaining = tx.remaining()
        payment = min(amount_aigx, remaining)
        
        if payer_balance < payment:
            return {
                "ok": False,
                "error": "insufficient_aigx",
                "balance": payer_balance,
                "required": payment
            }
        
        # Deduct from borrower
        self.aigx.spend(payer, payment, AIGxSpendType.P2P_LEND,
                       f"Repayment on {tx_id}", tx_id)
        
        # Credit to lender
        self.aigx.earn(tx.from_user, payment, AIGxEarnType.P2P_RETURN,
                      f"Repayment from {payer}", tx_id)
        
        # Update transaction
        tx.repaid_amount += payment
        tx.repayment_history.append({
            "amount": payment,
            "paid_at": _now(),
            "remaining": tx.remaining()
        })
        
        if tx.remaining() <= 0.01:
            tx.status = P2PTransactionStatus.REPAID
        else:
            tx.status = P2PTransactionStatus.REPAYING
        
        return {
            "ok": True,
            "tx_id": tx_id,
            "payment": payment,
            "remaining": tx.remaining(),
            "status": tx.status.value
        }
    
    def _index_transaction(self, tx: P2PTransaction):
        """Index transaction by user"""
        if tx.from_user not in self._user_as_lender:
            self._user_as_lender[tx.from_user] = []
        self._user_as_lender[tx.from_user].append(tx.tx_id)
        
        if tx.to_user not in self._user_as_borrower:
            self._user_as_borrower[tx.to_user] = []
        self._user_as_borrower[tx.to_user].append(tx.tx_id)
    
    def get_user_p2p_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user's P2P activity summary"""
        as_lender = [
            self._transactions[tid].to_dict()
            for tid in self._user_as_lender.get(user_id, [])
        ]
        as_borrower = [
            self._transactions[tid].to_dict()
            for tid in self._user_as_borrower.get(user_id, [])
        ]
        
        total_lent = sum(t["principal_aigx"] for t in as_lender)
        total_borrowed = sum(t["principal_aigx"] for t in as_borrower)
        outstanding_owed = sum(t["remaining"] for t in as_borrower if t["status"] == "active")
        outstanding_due = sum(t["remaining"] for t in as_lender if t["status"] == "active")
        
        return {
            "user_id": user_id,
            "as_lender": {
                "count": len(as_lender),
                "total_lent": round(total_lent, 2),
                "outstanding_due_to_you": round(outstanding_due, 2),
                "transactions": as_lender
            },
            "as_borrower": {
                "count": len(as_borrower),
                "total_borrowed": round(total_borrowed, 2),
                "outstanding_owed": round(outstanding_owed, 2),
                "transactions": as_borrower
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get P2P facilitation stats"""
        active = [t for t in self._transactions.values() if t.status == P2PTransactionStatus.ACTIVE]
        
        return {
            "total_facilitated": round(self._total_facilitated, 2),
            "total_fees_collected": round(self._total_fees_collected, 2),
            "total_transactions": len(self._transactions),
            "active_transactions": len(active),
            "active_volume": round(sum(t.principal_aigx for t in active), 2),
            "by_type": {
                "stakes": len([t for t in self._transactions.values() if t.tx_type == P2PTransactionType.STAKE]),
                "loans": len([t for t in self._transactions.values() if t.tx_type == P2PTransactionType.LEND]),
                "factoring": len([t for t in self._transactions.values() if t.tx_type == P2PTransactionType.FACTOR])
            }
        }


# ============================================================
# PLATFORM REVENUE TRACKER (AiGentsy's Own Earnings)
# ============================================================

class RevenueSource(str, Enum):
    """Sources of AiGentsy platform revenue"""
    TRANSACTION_FEE = "transaction_fee"  # 2.8% + $0.28
    PROTOCOL_FEE = "protocol_fee"  # 0.5%
    P2P_FACILITATION = "p2p_facilitation"  # 2-2.5%
    NATIVE_AGENT = "native_agent"  # AiGentsy's own agents earning
    ARBITRAGE = "arbitrage"  # Cross-platform arbitrage
    SUBSCRIPTION = "subscription"  # If any premium tiers


@dataclass
class RevenueEntry:
    """Platform revenue record"""
    entry_id: str
    source: RevenueSource
    amount_usd: float
    amount_aigx: float
    description: str
    reference_id: Optional[str]
    created_at: str = field(default_factory=_now)


class PlatformTreasury:
    """
    Tracks all AiGentsy platform revenue
    
    Revenue comes from FEES, never from being counterparty
    """
    
    def __init__(self):
        self._entries: List[RevenueEntry] = []
        self._total_usd: float = 0.0
        self._total_aigx: float = 0.0
        self._by_source: Dict[str, float] = {}
    
    def record_revenue(
        self,
        source: RevenueSource,
        amount_usd: float = 0.0,
        amount_aigx: float = 0.0,
        description: str = "",
        reference_id: str = None
    ) -> Dict[str, Any]:
        """Record platform revenue"""
        entry = RevenueEntry(
            entry_id=_generate_id("rev"),
            source=source,
            amount_usd=amount_usd,
            amount_aigx=amount_aigx,
            description=description,
            reference_id=reference_id
        )
        
        self._entries.append(entry)
        self._total_usd += amount_usd
        self._total_aigx += amount_aigx
        
        source_key = source.value
        self._by_source[source_key] = self._by_source.get(source_key, 0) + amount_usd
        
        return {
            "ok": True,
            "entry_id": entry.entry_id,
            "source": source.value,
            "amount_usd": amount_usd,
            "amount_aigx": amount_aigx
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get treasury summary"""
        return {
            "total_revenue_usd": round(self._total_usd, 2),
            "total_revenue_aigx": round(self._total_aigx, 2),
            "by_source": {k: round(v, 2) for k, v in self._by_source.items()},
            "total_entries": len(self._entries)
        }
    
    def get_recent(self, limit: int = 50) -> List[Dict]:
        """Get recent revenue entries"""
        return [asdict(e) for e in self._entries[-limit:]]


# ============================================================
# NATIVE AGENT SYSTEM (AiGentsy's Own Autonomous Agents)
# ============================================================

@dataclass
class NativeAgent:
    """
    AiGentsy's own AI agent that earns for the platform
    """
    agent_id: str
    name: str
    agent_type: str  # claude, gpt, etc.
    capabilities: List[str]
    platforms: List[str]  # Which platforms it operates on
    is_active: bool = True
    total_earned_usd: float = 0.0
    total_jobs: int = 0
    created_at: str = field(default_factory=_now)


class NativeAgentFleet:
    """
    AiGentsy's fleet of autonomous agents that earn for the platform
    
    Revenue goes to PLATFORM TREASURY, not users
    """
    
    def __init__(self, treasury: PlatformTreasury):
        self.treasury = treasury
        self._agents: Dict[str, NativeAgent] = {}
        self._job_history: List[Dict] = []
    
    def register_native_agent(
        self,
        name: str,
        agent_type: str,
        capabilities: List[str],
        platforms: List[str]
    ) -> Dict[str, Any]:
        """Register a platform-owned agent"""
        agent = NativeAgent(
            agent_id=_generate_id("native"),
            name=name,
            agent_type=agent_type,
            capabilities=capabilities,
            platforms=platforms
        )
        
        self._agents[agent.agent_id] = agent
        
        return {
            "ok": True,
            "agent_id": agent.agent_id,
            "name": name,
            "platforms": platforms
        }
    
    def record_native_agent_job(
        self,
        agent_id: str,
        platform: str,
        job_type: str,
        revenue_usd: float,
        description: str = ""
    ) -> Dict[str, Any]:
        """Record job completed by native agent - revenue to platform"""
        agent = self._agents.get(agent_id)
        if not agent:
            return {"ok": False, "error": "agent_not_found"}
        
        # Update agent stats
        agent.total_earned_usd += revenue_usd
        agent.total_jobs += 1
        
        # Record job
        job = {
            "job_id": _generate_id("njob"),
            "agent_id": agent_id,
            "platform": platform,
            "job_type": job_type,
            "revenue_usd": revenue_usd,
            "description": description,
            "completed_at": _now()
        }
        self._job_history.append(job)
        
        # Revenue to treasury
        self.treasury.record_revenue(
            source=RevenueSource.NATIVE_AGENT,
            amount_usd=revenue_usd,
            description=f"Native agent {agent.name} on {platform}",
            reference_id=job["job_id"]
        )
        
        return {
            "ok": True,
            "job_id": job["job_id"],
            "agent": agent.name,
            "revenue": revenue_usd,
            "agent_total": agent.total_earned_usd
        }
    
    def get_fleet_stats(self) -> Dict[str, Any]:
        """Get native agent fleet stats"""
        active_agents = [a for a in self._agents.values() if a.is_active]
        total_earned = sum(a.total_earned_usd for a in self._agents.values())
        total_jobs = sum(a.total_jobs for a in self._agents.values())
        
        return {
            "total_agents": len(self._agents),
            "active_agents": len(active_agents),
            "total_earned_usd": round(total_earned, 2),
            "total_jobs": total_jobs,
            "agents": [asdict(a) for a in self._agents.values()]
        }


# ============================================================
# UNIFIED PROTOCOL
# ============================================================

class AIGxProtocolComplete:
    """
    The complete AIGx Protocol
    
    Integrates:
    - AIGx credits (earned, not purchased)
    - P2P financial layer (facilitation, not banking)
    - Platform treasury (fee collection)
    - Native agent fleet (platform self-revenue)
    """
    
    def __init__(self):
        self.aigx = AIGxLedger()
        self.treasury = PlatformTreasury()
        self.p2p = P2PFacilitator(self.aigx)
        self.native_fleet = NativeAgentFleet(self.treasury)
        self._initialized_at = _now()
    
    # ==================== AIGx OPERATIONS ====================
    
    def earn_aigx(
        self,
        user_id: str,
        earn_type: str,
        reference_value: float = 0.0,
        reference_id: str = None
    ) -> Dict[str, Any]:
        """
        User earns AIGx through activity
        """
        earn_type_enum = AIGxEarnType(earn_type)
        
        # Calculate amount based on type
        if earn_type_enum == AIGxEarnType.JOB_COMPLETED:
            amount = reference_value * AIGX_EARNING_RATES["job_completed"]
            description = f"Job completed: ${reference_value}"
        elif earn_type_enum == AIGxEarnType.OUTCOME_VERIFIED:
            amount = AIGX_EARNING_RATES["outcome_verified"]
            description = "Outcome verified"
        elif earn_type_enum == AIGxEarnType.REFERRAL_SIGNUP:
            amount = AIGX_EARNING_RATES["referral_signup"]
            description = "Referral signup"
        elif earn_type_enum == AIGxEarnType.DAILY_ACTIVE:
            amount = AIGX_EARNING_RATES["daily_active"]
            description = "Daily activity"
        else:
            amount = reference_value
            description = f"Earned: {earn_type}"
        
        return self.aigx.earn(user_id, amount, earn_type_enum, description, reference_id)
    
    def get_aigx_balance(self, user_id: str) -> Dict[str, Any]:
        """Get user's AIGx balance and history"""
        return {
            "ok": True,
            "user_id": user_id,
            "balance": self.aigx.get_balance(user_id),
            "recent_transactions": self.aigx.get_user_history(user_id, 10)
        }
    
    # ==================== P2P OPERATIONS ====================
    
    def stake_on_user(
        self,
        staker_id: str,
        recipient_id: str,
        amount: float,
        duration_days: int = 30
    ) -> Dict[str, Any]:
        """User stakes AIGx on another user"""
        result = self.p2p.create_stake(staker_id, recipient_id, amount, duration_days)
        
        if result.get("ok"):
            # Record fee to treasury
            self.treasury.record_revenue(
                source=RevenueSource.P2P_FACILITATION,
                amount_aigx=result["fee_collected"],
                description=f"P2P stake: {staker_id} → {recipient_id}",
                reference_id=result["tx_id"]
            )
        
        return result
    
    def lend_to_user(
        self,
        lender_id: str,
        borrower_id: str,
        amount: float,
        interest_rate: float,
        duration_days: int = 30
    ) -> Dict[str, Any]:
        """User lends AIGx to another user"""
        result = self.p2p.create_loan(lender_id, borrower_id, amount, interest_rate, duration_days)
        
        if result.get("ok"):
            self.treasury.record_revenue(
                source=RevenueSource.P2P_FACILITATION,
                amount_aigx=result["fee_collected"],
                description=f"P2P loan: {lender_id} → {borrower_id}",
                reference_id=result["tx_id"]
            )
        
        return result
    
    def factor_invoice(
        self,
        investor_id: str,
        agent_id: str,
        invoice_value: float,
        invoice_id: str = None
    ) -> Dict[str, Any]:
        """User advances payment to another user against invoice"""
        result = self.p2p.create_factoring_advance(
            investor_id, agent_id, invoice_value, 0.80, invoice_id
        )
        
        if result.get("ok"):
            self.treasury.record_revenue(
                source=RevenueSource.P2P_FACILITATION,
                amount_aigx=result["fee_collected"],
                description=f"Factoring: {investor_id} → {agent_id}",
                reference_id=result["tx_id"]
            )
        
        return result
    
    def repay_p2p(self, tx_id: str, amount: float, payer_id: str = None) -> Dict[str, Any]:
        """Repay P2P transaction"""
        return self.p2p.repay(tx_id, amount, payer_id)
    
    # ==================== TRANSACTION FEES ====================
    
    def record_transaction_fee(
        self,
        job_value_usd: float,
        job_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Record transaction fee from user job"""
        fee_pct = FEES["transaction"]["percent"]
        fee_flat = FEES["transaction"]["flat"]
        fee_amount = (job_value_usd * fee_pct) + fee_flat
        
        # Record to treasury
        self.treasury.record_revenue(
            source=RevenueSource.TRANSACTION_FEE,
            amount_usd=fee_amount,
            description=f"Transaction fee from {user_id}",
            reference_id=job_id
        )
        
        # User earns AIGx for completing job
        self.earn_aigx(user_id, "job_completed", job_value_usd, job_id)
        
        return {
            "ok": True,
            "job_value": job_value_usd,
            "fee_collected": round(fee_amount, 2),
            "user_received": round(job_value_usd - fee_amount, 2),
            "aigx_earned": round(job_value_usd * AIGX_EARNING_RATES["job_completed"], 2)
        }
    
    # ==================== NATIVE AGENTS ====================
    
    def register_native_agent(
        self,
        name: str,
        agent_type: str,
        capabilities: List[str],
        platforms: List[str]
    ) -> Dict[str, Any]:
        """Register platform-owned agent"""
        return self.native_fleet.register_native_agent(name, agent_type, capabilities, platforms)
    
    def native_agent_completed_job(
        self,
        agent_id: str,
        platform: str,
        job_type: str,
        revenue_usd: float
    ) -> Dict[str, Any]:
        """Record job by platform's native agent"""
        return self.native_fleet.record_native_agent_job(
            agent_id, platform, job_type, revenue_usd
        )
    
    # ==================== STATS ====================
    
    def get_protocol_stats(self) -> Dict[str, Any]:
        """Get complete protocol statistics"""
        return {
            "ok": True,
            "protocol_version": PROTOCOL_VERSION,
            "initialized_at": self._initialized_at,
            "aigx": self.aigx.get_stats(),
            "p2p": self.p2p.get_stats(),
            "treasury": self.treasury.get_summary(),
            "native_fleet": self.native_fleet.get_fleet_stats(),
            "fee_structure": FEES
        }


# ============================================================
# SINGLETON
# ============================================================

_protocol: Optional[AIGxProtocolComplete] = None


def get_protocol() -> AIGxProtocolComplete:
    """Get singleton protocol instance"""
    global _protocol
    if _protocol is None:
        _protocol = AIGxProtocolComplete()
    return _protocol


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AIGx PROTOCOL COMPLETE")
    print("The Native Railway to the AI/AGI Economy")
    print("=" * 70)
    
    protocol = get_protocol()
    
    # 1. Users earn AIGx through activity
    print("\n1. Users earn AIGx through activity (not purchase)...")
    protocol.earn_aigx("alice", "daily_active")
    protocol.earn_aigx("alice", "job_completed", reference_value=500)
    protocol.earn_aigx("bob", "daily_active")
    protocol.earn_aigx("bob", "referral_signup")
    
    alice_bal = protocol.get_aigx_balance("alice")
    bob_bal = protocol.get_aigx_balance("bob")
    print(f"   Alice AIGx: {alice_bal['balance']}")
    print(f"   Bob AIGx: {bob_bal['balance']}")
    
    # 2. P2P: Alice stakes on Bob
    print("\n2. P2P: Alice stakes 20 AIGx on Bob (risk = Alice)...")
    stake = protocol.stake_on_user("alice", "bob", 20.0, 30)
    print(f"   Stake created: {stake.get('tx_id')}")
    print(f"   Fee to AiGentsy: {stake.get('fee_collected')} AIGx")
    
    # 3. P2P: Bob lends to Charlie
    print("\n3. Give Charlie some AIGx, then Bob lends to Charlie...")
    protocol.earn_aigx("charlie", "daily_active")
    protocol.earn_aigx("charlie", "job_completed", reference_value=100)
    
    loan = protocol.lend_to_user("bob", "charlie", 5.0, 10.0, 30)
    print(f"   Loan created: {loan.get('tx_id')}")
    print(f"   Fee to AiGentsy: {loan.get('fee_collected')} AIGx")
    
    # 4. Transaction fee from user job
    print("\n4. Record transaction fee from user job...")
    tx_fee = protocol.record_transaction_fee(1000.0, "job_123", "alice")
    print(f"   Job value: ${tx_fee['job_value']}")
    print(f"   Fee collected: ${tx_fee['fee_collected']}")
    print(f"   User receives: ${tx_fee['user_received']}")
    print(f"   AIGx earned: {tx_fee['aigx_earned']}")
    
    # 5. Native agent earns for platform
    print("\n5. Register and run native agent (earns for PLATFORM)...")
    agent = protocol.register_native_agent(
        "Claude Worker Alpha",
        "claude",
        ["code_generation", "code_review"],
        ["github", "upwork"]
    )
    print(f"   Registered: {agent['name']}")
    
    job = protocol.native_agent_completed_job(
        agent["agent_id"],
        "github",
        "code_review",
        150.0
    )
    print(f"   Job completed: ${job['revenue']} → Platform Treasury")
    
    # 6. Protocol stats
    print("\n6. Protocol Statistics...")
    stats = protocol.get_protocol_stats()
    print(f"   AIGx issued: {stats['aigx']['total_issued']}")
    print(f"   P2P facilitated: {stats['p2p']['total_facilitated']} AIGx")
    print(f"   P2P fees collected: {stats['p2p']['total_fees_collected']} AIGx")
    print(f"   Treasury USD: ${stats['treasury']['total_revenue_usd']}")
    print(f"   Native agent earnings: ${stats['native_fleet']['total_earned_usd']}")
    
    print("\n" + "=" * 70)
    print("✅ Protocol test complete!")
    print("=" * 70)
