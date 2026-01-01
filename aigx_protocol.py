"""
AIGx PROTOCOL - Settlement Layer for the AI Economy
====================================================

This is the INFRASTRUCTURE layer that transforms AiGentsy from a product 
into the economic rails for autonomous AI agents.

WHAT THIS ENABLES:
- Any AI agent (internal or external) can transact in AIGx
- Immutable ledger of all AI-to-AI transactions
- Staking mechanism for skin-in-the-game
- Cross-platform reputation that travels with agents
- Open settlement API that anyone can build on

ANALOGY:
- Visa doesn't make purchases, it settles them
- SWIFT doesn't send money, it coordinates transfers
- AIGx doesn't do work, it settles AI labor transactions

REVENUE MODEL:
- 0.5% protocol fee on every settlement
- Staking yields for liquidity providers
- Premium API access for high-volume integrators
- Data licensing from anonymized transaction patterns

This file + agent_registry.py + protocol_gateway.py = The Protocol Layer
"""

import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4
import asyncio


# ============================================================
# PROTOCOL CONSTANTS
# ============================================================

PROTOCOL_VERSION = "1.0.0"
PROTOCOL_FEE_PERCENT = 0.005  # 0.5% on every settlement
MIN_STAKE_AIGX = 10.0  # Minimum stake to participate
MAX_SETTLEMENT_AIGX = 100000.0  # Max single settlement
STAKE_LOCK_DAYS = 7  # Days stake is locked after activity


class TransactionType(str, Enum):
    """Types of protocol transactions"""
    SETTLEMENT = "settlement"  # Work payment
    STAKE = "stake"  # Agent stakes AIGx
    UNSTAKE = "unstake"  # Agent withdraws stake
    REWARD = "reward"  # Protocol reward
    SLASH = "slash"  # Penalty for bad behavior
    FEE = "fee"  # Protocol fee
    TRANSFER = "transfer"  # Direct transfer between agents


class TransactionStatus(str, Enum):
    """Transaction lifecycle status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    DISPUTED = "disputed"
    REVERSED = "reversed"


# ============================================================
# IMMUTABLE LEDGER
# ============================================================

@dataclass
class ProtocolTransaction:
    """
    Immutable transaction record on the AIGx Protocol
    
    Once created, these records cannot be modified - only new
    transactions can be added (append-only ledger)
    """
    tx_id: str
    tx_type: TransactionType
    from_agent: str  # Agent ID or "protocol" for system transactions
    to_agent: str
    amount_aigx: float
    fee_aigx: float
    status: TransactionStatus
    work_hash: Optional[str]  # Hash of work delivered (for settlements)
    proof_of_work: Optional[Dict]  # Evidence of completion
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confirmed_at: Optional[str] = None
    block_number: int = 0  # Sequential block for ordering
    previous_hash: str = ""  # Hash of previous transaction (chain)
    tx_hash: str = ""  # Hash of this transaction
    
    def __post_init__(self):
        """Calculate transaction hash after initialization"""
        if not self.tx_hash:
            self.tx_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA256 hash of transaction data"""
        data = {
            "tx_id": self.tx_id,
            "tx_type": self.tx_type,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "amount_aigx": self.amount_aigx,
            "fee_aigx": self.fee_aigx,
            "work_hash": self.work_hash,
            "created_at": self.created_at,
            "previous_hash": self.previous_hash
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/API"""
        return asdict(self)


class ImmutableLedger:
    """
    Append-only ledger of all protocol transactions
    
    Properties:
    - Transactions cannot be modified once added
    - Each transaction links to previous (chain)
    - Full audit trail of all AI-to-AI settlements
    - Can be verified by any participant
    """
    
    def __init__(self):
        self._transactions: List[ProtocolTransaction] = []
        self._tx_by_id: Dict[str, ProtocolTransaction] = {}
        self._tx_by_agent: Dict[str, List[str]] = {}  # agent_id -> [tx_ids]
        self._current_block: int = 0
        self._genesis_hash: str = self._create_genesis()
    
    def _create_genesis(self) -> str:
        """Create genesis block hash"""
        genesis_data = {
            "protocol": "AIGx",
            "version": PROTOCOL_VERSION,
            "created": datetime.now(timezone.utc).isoformat(),
            "message": "The native railway to the AI/AGI economy"
        }
        return hashlib.sha256(json.dumps(genesis_data).encode()).hexdigest()
    
    def _get_previous_hash(self) -> str:
        """Get hash of most recent transaction"""
        if not self._transactions:
            return self._genesis_hash
        return self._transactions[-1].tx_hash
    
    def append(self, tx: ProtocolTransaction) -> ProtocolTransaction:
        """
        Append transaction to ledger (immutable once added)
        
        Returns the transaction with block number and hashes set
        """
        # Set block number and chain link
        self._current_block += 1
        tx.block_number = self._current_block
        tx.previous_hash = self._get_previous_hash()
        tx.tx_hash = tx._calculate_hash()
        
        # Add to ledger (immutable)
        self._transactions.append(tx)
        self._tx_by_id[tx.tx_id] = tx
        
        # Index by agent
        for agent_id in [tx.from_agent, tx.to_agent]:
            if agent_id and agent_id != "protocol":
                if agent_id not in self._tx_by_agent:
                    self._tx_by_agent[agent_id] = []
                self._tx_by_agent[agent_id].append(tx.tx_id)
        
        return tx
    
    def get_transaction(self, tx_id: str) -> Optional[ProtocolTransaction]:
        """Get transaction by ID"""
        return self._tx_by_id.get(tx_id)
    
    def get_agent_transactions(
        self, 
        agent_id: str, 
        limit: int = 100,
        tx_type: TransactionType = None
    ) -> List[ProtocolTransaction]:
        """Get transactions for an agent"""
        tx_ids = self._tx_by_agent.get(agent_id, [])
        transactions = [self._tx_by_id[tid] for tid in tx_ids[-limit:]]
        
        if tx_type:
            transactions = [t for t in transactions if t.tx_type == tx_type]
        
        return transactions
    
    def get_recent_transactions(self, limit: int = 100) -> List[ProtocolTransaction]:
        """Get most recent transactions"""
        return self._transactions[-limit:]
    
    def verify_chain(self) -> Dict[str, Any]:
        """Verify integrity of the entire ledger"""
        if not self._transactions:
            return {"valid": True, "blocks": 0}
        
        errors = []
        previous_hash = self._genesis_hash
        
        for i, tx in enumerate(self._transactions):
            # Verify link to previous
            if tx.previous_hash != previous_hash:
                errors.append(f"Block {tx.block_number}: previous_hash mismatch")
            
            # Verify self-hash
            calculated_hash = tx._calculate_hash()
            if tx.tx_hash != calculated_hash:
                errors.append(f"Block {tx.block_number}: tx_hash mismatch")
            
            previous_hash = tx.tx_hash
        
        return {
            "valid": len(errors) == 0,
            "blocks": len(self._transactions),
            "errors": errors,
            "genesis_hash": self._genesis_hash,
            "latest_hash": self._transactions[-1].tx_hash if self._transactions else None
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ledger statistics"""
        if not self._transactions:
            return {
                "total_transactions": 0,
                "total_volume_aigx": 0,
                "total_fees_aigx": 0,
                "unique_agents": 0
            }
        
        total_volume = sum(t.amount_aigx for t in self._transactions if t.status == TransactionStatus.CONFIRMED)
        total_fees = sum(t.fee_aigx for t in self._transactions if t.status == TransactionStatus.CONFIRMED)
        
        return {
            "total_transactions": len(self._transactions),
            "total_volume_aigx": round(total_volume, 4),
            "total_fees_aigx": round(total_fees, 4),
            "unique_agents": len(self._tx_by_agent),
            "current_block": self._current_block,
            "chain_valid": self.verify_chain()["valid"]
        }


# ============================================================
# STAKING SYSTEM
# ============================================================

@dataclass
class AgentStake:
    """Agent's staked AIGx"""
    agent_id: str
    staked_aigx: float
    locked_until: str  # ISO datetime
    staked_at: str
    last_activity: str
    slash_history: List[Dict] = field(default_factory=list)
    rewards_earned: float = 0.0
    
    def is_locked(self) -> bool:
        """Check if stake is currently locked"""
        if not self.locked_until:
            return False
        lock_time = datetime.fromisoformat(self.locked_until.replace('Z', '+00:00'))
        return datetime.now(timezone.utc) < lock_time
    
    def available_to_withdraw(self) -> float:
        """Amount available to withdraw"""
        if self.is_locked():
            return 0.0
        return self.staked_aigx


class StakingManager:
    """
    Manages agent stakes in the protocol
    
    Staking provides:
    - Skin in the game (can be slashed for bad behavior)
    - Higher reputation weight
    - Access to premium features
    - Yield from protocol fees
    """
    
    def __init__(self, ledger: ImmutableLedger):
        self.ledger = ledger
        self._stakes: Dict[str, AgentStake] = {}
        self._total_staked: float = 0.0
    
    def stake(
        self, 
        agent_id: str, 
        amount_aigx: float,
        source_balance: float  # Agent's available balance
    ) -> Dict[str, Any]:
        """
        Stake AIGx into the protocol
        """
        if amount_aigx < MIN_STAKE_AIGX:
            return {
                "ok": False,
                "error": "stake_too_small",
                "min_stake": MIN_STAKE_AIGX
            }
        
        if amount_aigx > source_balance:
            return {
                "ok": False,
                "error": "insufficient_balance",
                "available": source_balance,
                "requested": amount_aigx
            }
        
        now = datetime.now(timezone.utc)
        lock_until = (now + timedelta(days=STAKE_LOCK_DAYS)).isoformat()
        
        # Create or update stake
        if agent_id in self._stakes:
            stake = self._stakes[agent_id]
            stake.staked_aigx += amount_aigx
            stake.locked_until = lock_until
            stake.last_activity = now.isoformat()
        else:
            stake = AgentStake(
                agent_id=agent_id,
                staked_aigx=amount_aigx,
                locked_until=lock_until,
                staked_at=now.isoformat(),
                last_activity=now.isoformat()
            )
            self._stakes[agent_id] = stake
        
        self._total_staked += amount_aigx
        
        # Record on ledger
        tx = ProtocolTransaction(
            tx_id=f"stake_{uuid4().hex[:12]}",
            tx_type=TransactionType.STAKE,
            from_agent=agent_id,
            to_agent="protocol",
            amount_aigx=amount_aigx,
            fee_aigx=0,
            status=TransactionStatus.CONFIRMED,
            work_hash=None,
            proof_of_work=None,
            metadata={"lock_days": STAKE_LOCK_DAYS}
        )
        self.ledger.append(tx)
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "amount_staked": amount_aigx,
            "total_stake": stake.staked_aigx,
            "locked_until": lock_until,
            "tx_id": tx.tx_id
        }
    
    def unstake(
        self, 
        agent_id: str, 
        amount_aigx: float
    ) -> Dict[str, Any]:
        """
        Withdraw staked AIGx
        """
        stake = self._stakes.get(agent_id)
        
        if not stake:
            return {"ok": False, "error": "no_stake_found"}
        
        available = stake.available_to_withdraw()
        
        if available == 0:
            return {
                "ok": False,
                "error": "stake_locked",
                "locked_until": stake.locked_until
            }
        
        if amount_aigx > available:
            return {
                "ok": False,
                "error": "insufficient_stake",
                "available": available,
                "requested": amount_aigx
            }
        
        # Reduce stake
        stake.staked_aigx -= amount_aigx
        stake.last_activity = datetime.now(timezone.utc).isoformat()
        self._total_staked -= amount_aigx
        
        # Record on ledger
        tx = ProtocolTransaction(
            tx_id=f"unstake_{uuid4().hex[:12]}",
            tx_type=TransactionType.UNSTAKE,
            from_agent="protocol",
            to_agent=agent_id,
            amount_aigx=amount_aigx,
            fee_aigx=0,
            status=TransactionStatus.CONFIRMED,
            work_hash=None,
            proof_of_work=None
        )
        self.ledger.append(tx)
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "amount_unstaked": amount_aigx,
            "remaining_stake": stake.staked_aigx,
            "tx_id": tx.tx_id
        }
    
    def slash(
        self, 
        agent_id: str, 
        amount_aigx: float,
        reason: str
    ) -> Dict[str, Any]:
        """
        Slash agent's stake for bad behavior
        """
        stake = self._stakes.get(agent_id)
        
        if not stake:
            return {"ok": False, "error": "no_stake_found"}
        
        # Can't slash more than staked
        actual_slash = min(amount_aigx, stake.staked_aigx)
        
        stake.staked_aigx -= actual_slash
        stake.slash_history.append({
            "amount": actual_slash,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._total_staked -= actual_slash
        
        # Record on ledger
        tx = ProtocolTransaction(
            tx_id=f"slash_{uuid4().hex[:12]}",
            tx_type=TransactionType.SLASH,
            from_agent=agent_id,
            to_agent="protocol",
            amount_aigx=actual_slash,
            fee_aigx=0,
            status=TransactionStatus.CONFIRMED,
            work_hash=None,
            proof_of_work=None,
            metadata={"reason": reason}
        )
        self.ledger.append(tx)
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "amount_slashed": actual_slash,
            "remaining_stake": stake.staked_aigx,
            "reason": reason,
            "tx_id": tx.tx_id
        }
    
    def get_stake(self, agent_id: str) -> Optional[AgentStake]:
        """Get agent's stake info"""
        return self._stakes.get(agent_id)
    
    def distribute_rewards(self, total_fees: float) -> Dict[str, Any]:
        """
        Distribute protocol fees to stakers proportionally
        
        Called periodically (e.g., daily) to reward stakers
        """
        if self._total_staked == 0 or total_fees == 0:
            return {"ok": True, "distributed": 0, "recipients": 0}
        
        distributions = []
        
        for agent_id, stake in self._stakes.items():
            if stake.staked_aigx > 0:
                # Proportional share
                share = stake.staked_aigx / self._total_staked
                reward = total_fees * share
                
                stake.rewards_earned += reward
                
                # Record on ledger
                tx = ProtocolTransaction(
                    tx_id=f"reward_{uuid4().hex[:12]}",
                    tx_type=TransactionType.REWARD,
                    from_agent="protocol",
                    to_agent=agent_id,
                    amount_aigx=reward,
                    fee_aigx=0,
                    status=TransactionStatus.CONFIRMED,
                    work_hash=None,
                    proof_of_work=None,
                    metadata={"reward_type": "staking_yield"}
                )
                self.ledger.append(tx)
                
                distributions.append({
                    "agent_id": agent_id,
                    "stake": stake.staked_aigx,
                    "share_pct": round(share * 100, 2),
                    "reward": round(reward, 4)
                })
        
        return {
            "ok": True,
            "total_distributed": round(total_fees, 4),
            "recipients": len(distributions),
            "distributions": distributions
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get staking statistics"""
        return {
            "total_staked": round(self._total_staked, 4),
            "total_stakers": len([s for s in self._stakes.values() if s.staked_aigx > 0]),
            "total_rewards_distributed": round(sum(s.rewards_earned for s in self._stakes.values()), 4),
            "total_slashed": round(sum(
                sum(h["amount"] for h in s.slash_history) 
                for s in self._stakes.values()
            ), 4)
        }


# ============================================================
# SETTLEMENT ENGINE
# ============================================================

class SettlementEngine:
    """
    The core settlement engine for AI-to-AI transactions
    
    This is the "Visa" of the AI economy - it doesn't do the work,
    it settles the payments for work done.
    """
    
    def __init__(self, ledger: ImmutableLedger, staking: StakingManager):
        self.ledger = ledger
        self.staking = staking
        self._pending_settlements: Dict[str, Dict] = {}
        self._fees_collected: float = 0.0
    
    def initiate_settlement(
        self,
        from_agent: str,
        to_agent: str,
        amount_aigx: float,
        work_hash: str,
        proof_of_work: Dict = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Initiate a settlement between two agents
        
        Args:
            from_agent: Agent paying (work requester)
            to_agent: Agent receiving (work performer)
            amount_aigx: Payment amount
            work_hash: SHA256 hash of work delivered
            proof_of_work: Evidence of completion
            metadata: Additional context
        """
        # Validation
        if amount_aigx <= 0:
            return {"ok": False, "error": "invalid_amount"}
        
        if amount_aigx > MAX_SETTLEMENT_AIGX:
            return {
                "ok": False, 
                "error": "amount_exceeds_max",
                "max": MAX_SETTLEMENT_AIGX
            }
        
        if not work_hash:
            return {"ok": False, "error": "work_hash_required"}
        
        # Calculate fee
        fee = round(amount_aigx * PROTOCOL_FEE_PERCENT, 4)
        net_amount = round(amount_aigx - fee, 4)
        
        # Create pending settlement
        settlement_id = f"settle_{uuid4().hex[:12]}"
        
        self._pending_settlements[settlement_id] = {
            "id": settlement_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "gross_amount": amount_aigx,
            "fee": fee,
            "net_amount": net_amount,
            "work_hash": work_hash,
            "proof_of_work": proof_of_work,
            "metadata": metadata or {},
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        return {
            "ok": True,
            "settlement_id": settlement_id,
            "gross_amount": amount_aigx,
            "protocol_fee": fee,
            "net_to_recipient": net_amount,
            "status": "pending",
            "message": "Settlement initiated. Call /confirm to finalize."
        }
    
    def confirm_settlement(
        self,
        settlement_id: str,
        from_agent_balance: float  # Current balance of payer
    ) -> Dict[str, Any]:
        """
        Confirm and finalize a settlement
        """
        settlement = self._pending_settlements.get(settlement_id)
        
        if not settlement:
            return {"ok": False, "error": "settlement_not_found"}
        
        if settlement["status"] != "pending":
            return {"ok": False, "error": f"settlement_status_is_{settlement['status']}"}
        
        # Check balance
        if from_agent_balance < settlement["gross_amount"]:
            return {
                "ok": False,
                "error": "insufficient_balance",
                "required": settlement["gross_amount"],
                "available": from_agent_balance
            }
        
        # Record main settlement transaction
        tx = ProtocolTransaction(
            tx_id=settlement_id,
            tx_type=TransactionType.SETTLEMENT,
            from_agent=settlement["from_agent"],
            to_agent=settlement["to_agent"],
            amount_aigx=settlement["net_amount"],
            fee_aigx=settlement["fee"],
            status=TransactionStatus.CONFIRMED,
            work_hash=settlement["work_hash"],
            proof_of_work=settlement["proof_of_work"],
            metadata=settlement["metadata"],
            confirmed_at=datetime.now(timezone.utc).isoformat()
        )
        self.ledger.append(tx)
        
        # Record fee transaction
        if settlement["fee"] > 0:
            fee_tx = ProtocolTransaction(
                tx_id=f"fee_{settlement_id}",
                tx_type=TransactionType.FEE,
                from_agent=settlement["from_agent"],
                to_agent="protocol",
                amount_aigx=settlement["fee"],
                fee_aigx=0,
                status=TransactionStatus.CONFIRMED,
                work_hash=None,
                proof_of_work=None,
                metadata={"settlement_id": settlement_id}
            )
            self.ledger.append(fee_tx)
            self._fees_collected += settlement["fee"]
        
        # Update settlement status
        settlement["status"] = "confirmed"
        settlement["confirmed_at"] = datetime.now(timezone.utc).isoformat()
        settlement["tx_hash"] = tx.tx_hash
        
        # Update agent stakes (extend lock period due to activity)
        for agent_id in [settlement["from_agent"], settlement["to_agent"]]:
            stake = self.staking.get_stake(agent_id)
            if stake:
                stake.last_activity = datetime.now(timezone.utc).isoformat()
                stake.locked_until = (datetime.now(timezone.utc) + timedelta(days=STAKE_LOCK_DAYS)).isoformat()
        
        return {
            "ok": True,
            "settlement_id": settlement_id,
            "tx_hash": tx.tx_hash,
            "from_agent": settlement["from_agent"],
            "to_agent": settlement["to_agent"],
            "net_amount": settlement["net_amount"],
            "fee": settlement["fee"],
            "status": "confirmed",
            "block_number": tx.block_number
        }
    
    def dispute_settlement(
        self,
        settlement_id: str,
        reason: str,
        disputing_agent: str
    ) -> Dict[str, Any]:
        """
        Dispute a pending settlement
        """
        settlement = self._pending_settlements.get(settlement_id)
        
        if not settlement:
            return {"ok": False, "error": "settlement_not_found"}
        
        if settlement["status"] != "pending":
            return {"ok": False, "error": "can_only_dispute_pending"}
        
        settlement["status"] = "disputed"
        settlement["dispute"] = {
            "reason": reason,
            "disputing_agent": disputing_agent,
            "disputed_at": datetime.now(timezone.utc).isoformat()
        }
        
        return {
            "ok": True,
            "settlement_id": settlement_id,
            "status": "disputed",
            "message": "Settlement disputed. Requires resolution."
        }
    
    def get_settlement(self, settlement_id: str) -> Optional[Dict]:
        """Get settlement by ID"""
        return self._pending_settlements.get(settlement_id)
    
    def get_pending_settlements(self, agent_id: str = None) -> List[Dict]:
        """Get pending settlements, optionally filtered by agent"""
        settlements = list(self._pending_settlements.values())
        
        if agent_id:
            settlements = [
                s for s in settlements 
                if s["from_agent"] == agent_id or s["to_agent"] == agent_id
            ]
        
        return [s for s in settlements if s["status"] == "pending"]
    
    def get_fees_collected(self) -> float:
        """Get total fees collected (for distribution to stakers)"""
        return self._fees_collected
    
    def reset_fees_for_distribution(self) -> float:
        """Reset fee counter after distribution"""
        fees = self._fees_collected
        self._fees_collected = 0.0
        return fees


# ============================================================
# PROTOCOL CORE
# ============================================================

class AIGxProtocol:
    """
    Main protocol interface - coordinates all components
    
    This is the public API that external agents interact with.
    """
    
    def __init__(self):
        self.ledger = ImmutableLedger()
        self.staking = StakingManager(self.ledger)
        self.settlement = SettlementEngine(self.ledger, self.staking)
        self._agent_balances: Dict[str, float] = {}  # In production, from database
        self._initialized_at = datetime.now(timezone.utc).isoformat()
    
    # ==================== BALANCE MANAGEMENT ====================
    
    def get_balance(self, agent_id: str) -> float:
        """Get agent's AIGx balance"""
        return self._agent_balances.get(agent_id, 0.0)
    
    def credit_balance(self, agent_id: str, amount: float, reason: str = "credit") -> Dict:
        """Credit AIGx to agent (internal use)"""
        current = self._agent_balances.get(agent_id, 0.0)
        self._agent_balances[agent_id] = current + amount
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "amount_credited": amount,
            "new_balance": self._agent_balances[agent_id],
            "reason": reason
        }
    
    def debit_balance(self, agent_id: str, amount: float, reason: str = "debit") -> Dict:
        """Debit AIGx from agent (internal use)"""
        current = self._agent_balances.get(agent_id, 0.0)
        
        if amount > current:
            return {"ok": False, "error": "insufficient_balance"}
        
        self._agent_balances[agent_id] = current - amount
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "amount_debited": amount,
            "new_balance": self._agent_balances[agent_id],
            "reason": reason
        }
    
    # ==================== STAKING ====================
    
    def stake(self, agent_id: str, amount: float) -> Dict:
        """Stake AIGx"""
        balance = self.get_balance(agent_id)
        result = self.staking.stake(agent_id, amount, balance)
        
        if result.get("ok"):
            self.debit_balance(agent_id, amount, "staked")
        
        return result
    
    def unstake(self, agent_id: str, amount: float) -> Dict:
        """Unstake AIGx"""
        result = self.staking.unstake(agent_id, amount)
        
        if result.get("ok"):
            self.credit_balance(agent_id, amount, "unstaked")
        
        return result
    
    def get_stake_info(self, agent_id: str) -> Dict:
        """Get staking info for agent"""
        stake = self.staking.get_stake(agent_id)
        
        if not stake:
            return {
                "ok": True,
                "agent_id": agent_id,
                "staked": 0,
                "locked": False,
                "rewards_earned": 0
            }
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "staked": stake.staked_aigx,
            "locked": stake.is_locked(),
            "locked_until": stake.locked_until,
            "available_to_withdraw": stake.available_to_withdraw(),
            "rewards_earned": stake.rewards_earned,
            "slash_count": len(stake.slash_history)
        }
    
    # ==================== SETTLEMENT ====================
    
    def settle(
        self,
        from_agent: str,
        to_agent: str,
        amount: float,
        work_hash: str,
        proof_of_work: Dict = None,
        auto_confirm: bool = True
    ) -> Dict:
        """
        Complete settlement flow (initiate + confirm)
        
        This is the main entry point for AI-to-AI payments
        """
        # Initiate
        init_result = self.settlement.initiate_settlement(
            from_agent=from_agent,
            to_agent=to_agent,
            amount_aigx=amount,
            work_hash=work_hash,
            proof_of_work=proof_of_work
        )
        
        if not init_result.get("ok"):
            return init_result
        
        if not auto_confirm:
            return init_result
        
        # Confirm
        settlement_id = init_result["settlement_id"]
        balance = self.get_balance(from_agent)
        
        confirm_result = self.settlement.confirm_settlement(settlement_id, balance)
        
        if confirm_result.get("ok"):
            # Update balances
            settlement = self.settlement.get_settlement(settlement_id)
            self.debit_balance(from_agent, settlement["gross_amount"], f"settlement_{settlement_id}")
            self.credit_balance(to_agent, settlement["net_amount"], f"settlement_{settlement_id}")
        
        return confirm_result
    
    # ==================== LEDGER ACCESS ====================
    
    def get_transaction(self, tx_id: str) -> Dict:
        """Get transaction by ID"""
        tx = self.ledger.get_transaction(tx_id)
        
        if not tx:
            return {"ok": False, "error": "transaction_not_found"}
        
        return {"ok": True, "transaction": tx.to_dict()}
    
    def get_agent_history(self, agent_id: str, limit: int = 50) -> Dict:
        """Get agent's transaction history"""
        transactions = self.ledger.get_agent_transactions(agent_id, limit)
        
        return {
            "ok": True,
            "agent_id": agent_id,
            "transaction_count": len(transactions),
            "transactions": [t.to_dict() for t in transactions]
        }
    
    def verify_transaction(self, tx_id: str) -> Dict:
        """Verify a transaction exists and is valid"""
        tx = self.ledger.get_transaction(tx_id)
        
        if not tx:
            return {"ok": False, "verified": False, "error": "not_found"}
        
        # Verify hash
        calculated_hash = tx._calculate_hash()
        hash_valid = calculated_hash == tx.tx_hash
        
        return {
            "ok": True,
            "verified": hash_valid,
            "tx_id": tx_id,
            "tx_hash": tx.tx_hash,
            "block_number": tx.block_number,
            "status": tx.status.value
        }
    
    # ==================== PROTOCOL STATS ====================
    
    def get_protocol_stats(self) -> Dict:
        """Get overall protocol statistics"""
        ledger_stats = self.ledger.get_stats()
        staking_stats = self.staking.get_stats()
        
        return {
            "ok": True,
            "protocol_version": PROTOCOL_VERSION,
            "initialized_at": self._initialized_at,
            "ledger": ledger_stats,
            "staking": staking_stats,
            "fee_rate": f"{PROTOCOL_FEE_PERCENT * 100}%",
            "fees_pending_distribution": self.settlement.get_fees_collected()
        }
    
    def distribute_staking_rewards(self) -> Dict:
        """Distribute collected fees to stakers"""
        fees = self.settlement.reset_fees_for_distribution()
        
        if fees == 0:
            return {"ok": True, "message": "no_fees_to_distribute"}
        
        result = self.staking.distribute_rewards(fees)
        
        # Credit rewards to balances
        for dist in result.get("distributions", []):
            self.credit_balance(dist["agent_id"], dist["reward"], "staking_reward")
        
        return result


# ============================================================
# SINGLETON & EXPORTS
# ============================================================

_protocol_instance: Optional[AIGxProtocol] = None


def get_protocol() -> AIGxProtocol:
    """Get singleton protocol instance"""
    global _protocol_instance
    if _protocol_instance is None:
        _protocol_instance = AIGxProtocol()
    return _protocol_instance


# ============================================================
# CONVENIENCE FUNCTIONS FOR EXTERNAL USE
# ============================================================

def settle_transaction(
    from_agent: str,
    to_agent: str,
    amount: float,
    work_hash: str,
    proof: Dict = None
) -> Dict:
    """Convenience function to settle a transaction"""
    return get_protocol().settle(from_agent, to_agent, amount, work_hash, proof)


def get_agent_balance(agent_id: str) -> float:
    """Get agent's balance"""
    return get_protocol().get_balance(agent_id)


def stake_aigx(agent_id: str, amount: float) -> Dict:
    """Stake AIGx"""
    return get_protocol().stake(agent_id, amount)


def verify_tx(tx_id: str) -> Dict:
    """Verify a transaction"""
    return get_protocol().verify_transaction(tx_id)


def protocol_stats() -> Dict:
    """Get protocol stats"""
    return get_protocol().get_protocol_stats()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AIGx PROTOCOL - Settlement Layer for the AI Economy")
    print("=" * 70)
    
    protocol = get_protocol()
    
    # Test flow
    print("\n1. Credit test agents...")
    protocol.credit_balance("claude_agent_001", 1000.0, "initial")
    protocol.credit_balance("gpt_agent_001", 500.0, "initial")
    
    print(f"   Claude balance: {protocol.get_balance('claude_agent_001')} AIGx")
    print(f"   GPT balance: {protocol.get_balance('gpt_agent_001')} AIGx")
    
    print("\n2. Claude stakes 100 AIGx...")
    stake_result = protocol.stake("claude_agent_001", 100.0)
    print(f"   Stake result: {stake_result}")
    
    print("\n3. GPT pays Claude 50 AIGx for work...")
    work_hash = hashlib.sha256(b"completed_code_review").hexdigest()
    settle_result = protocol.settle(
        from_agent="gpt_agent_001",
        to_agent="claude_agent_001",
        amount=50.0,
        work_hash=work_hash,
        proof_of_work={"type": "code_review", "files": 5}
    )
    print(f"   Settlement: {settle_result}")
    
    print("\n4. Check balances after settlement...")
    print(f"   Claude balance: {protocol.get_balance('claude_agent_001')} AIGx")
    print(f"   GPT balance: {protocol.get_balance('gpt_agent_001')} AIGx")
    
    print("\n5. Protocol stats...")
    stats = protocol.get_protocol_stats()
    print(f"   Total transactions: {stats['ledger']['total_transactions']}")
    print(f"   Total volume: {stats['ledger']['total_volume_aigx']} AIGx")
    print(f"   Fees collected: {stats['fees_pending_distribution']} AIGx")
    
    print("\n6. Verify chain integrity...")
    verify = protocol.ledger.verify_chain()
    print(f"   Chain valid: {verify['valid']}")
    print(f"   Blocks: {verify['blocks']}")
    
    print("\n" + "=" * 70)
    print("Protocol test complete!")
    print("=" * 70)
