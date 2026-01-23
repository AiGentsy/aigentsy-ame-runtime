"""
Financial Manager - OCL P2P Lending + Financial Infrastructure
==============================================================

Systems managed:
1. ocl_p2p_lending.py - AI-to-AI lending marketplace
2. ocl_engine.py - Core OCL functionality
3. ocl_expansion.py - Auto-expand credit 5-25%
4. performance_bonds.py - SLA bonding system
5. securitization_desk.py - Tranche outcome flows
6. outcomes_insurance_oracle.py - Micro-premiums
7. insurance_pool.py - Community insurance
8. agent_factoring.py - Invoice factoring

CRITICAL FEATURE: Internal OCL P2P Lending
- Enables AI agents to lend to each other
- 8-12% APR internal lending rate
- 2.5% facilitation fee on each transaction
- Auto-settles on job completion
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from uuid import uuid4
from dataclasses import dataclass, field
import asyncio
import logging

logger = logging.getLogger("financial_manager")


@dataclass
class InternalLoan:
    """Represents an internal AI-to-AI loan"""
    loan_id: str
    lender_agent: str
    borrower_agent: str
    principal: float
    interest_rate: float  # APR
    created_at: datetime
    due_at: Optional[datetime] = None
    status: str = "active"  # active, repaid, defaulted
    repaid_amount: float = 0.0
    metadata: Dict = field(default_factory=dict)


class FinancialManager:
    """Coordinates financial infrastructure + OCL P2P lending"""

    def __init__(self):
        self._subsystems: Dict[str, bool] = {}
        self._active_loans: List[InternalLoan] = []
        self._agent_capital: Dict[str, float] = {}  # Track agent idle capital
        self._total_facilitation_fees: float = 0.0
        self._init_subsystems()
        self._init_agent_capital()

    def _init_subsystems(self):
        """Initialize all 8 financial subsystems"""

        # 1. OCL P2P Lending
        try:
            from ocl_p2p_lending import (
                create_lending_offer,
                match_lenders_borrowers,
                process_loan_repayment
            )
            self._create_offer = create_lending_offer
            self._match_lenders = match_lenders_borrowers
            self._process_repayment = process_loan_repayment
            self._subsystems["ocl_p2p_lending"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"OCL P2P lending not available: {e}")
            self._subsystems["ocl_p2p_lending"] = False

        # 2. Core OCL Engine
        try:
            from ocl_engine import calculate_ocl_limit, spend_ocl, get_ocl_balance
            self._calc_ocl = calculate_ocl_limit
            self._spend_ocl = spend_ocl
            self._get_balance = get_ocl_balance
            self._subsystems["ocl_engine"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"OCL engine not available: {e}")
            self._subsystems["ocl_engine"] = False

        # 3. OCL Expansion
        try:
            from ocl_expansion import (
                calculate_expansion_rate,
                expand_credit_limit,
                get_expansion_history
            )
            self._calc_expansion = calculate_expansion_rate
            self._expand_credit = expand_credit_limit
            self._subsystems["ocl_expansion"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"OCL expansion not available: {e}")
            self._subsystems["ocl_expansion"] = False

        # 4. Performance Bonds
        try:
            from performance_bonds import (
                calculate_bond_amount,
                stake_bond,
                release_bond
            )
            self._calc_bond = calculate_bond_amount
            self._stake_bond = stake_bond
            self._release_bond = release_bond
            self._subsystems["performance_bonds"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Performance bonds not available: {e}")
            self._subsystems["performance_bonds"] = False

        # 5. Securitization Desk
        try:
            from securitization_desk import (
                create_tranche,
                price_tranche,
                distribute_to_lps
            )
            self._create_tranche = create_tranche
            self._price_tranche = price_tranche
            self._distribute_lps = distribute_to_lps
            self._subsystems["securitization_desk"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Securitization desk not available: {e}")
            self._subsystems["securitization_desk"] = False

        # 6. Outcomes Insurance Oracle
        try:
            from outcomes_insurance_oracle import (
                quote_premium,
                issue_policy,
                settle_insurance
            )
            self._quote_premium = quote_premium
            self._issue_policy = issue_policy
            self._settle_insurance = settle_insurance
            self._subsystems["outcomes_insurance"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Outcomes insurance not available: {e}")
            self._subsystems["outcomes_insurance"] = False

        # 7. Insurance Pool
        try:
            from insurance_pool import (
                contribute_to_pool,
                request_coverage,
                process_pool_claim
            )
            self._pool_contribute = contribute_to_pool
            self._pool_coverage = request_coverage
            self._subsystems["insurance_pool"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Insurance pool not available: {e}")
            self._subsystems["insurance_pool"] = False

        # 8. Agent Factoring
        try:
            from agent_factoring import request_factoring_advance, get_factoring_terms
            self._request_factoring = request_factoring_advance
            self._get_factoring_terms = get_factoring_terms
            self._subsystems["agent_factoring"] = True
        except (ImportError, Exception) as e:
            logger.warning(f"Agent factoring not available: {e}")
            self._subsystems["agent_factoring"] = False

        self._log_status()

    def _init_agent_capital(self):
        """Initialize tracked agent capital pools"""
        # These represent idle capital from various subsystems
        self._agent_capital = {
            "alpha_discovery": 2000.0,
            "ai_router": 1500.0,
            "deal_graph": 500.0,
            "execution_fabric": 1000.0,
            "metahive_brain": 750.0,
            "yield_memory": 250.0,
            "outcome_oracle": 1000.0,
            "spawn_engine": 500.0,
            "revenue_pool": 3000.0,  # Accumulated revenue
            "insurance_reserve": 1500.0  # Insurance pool
        }

    def _log_status(self):
        """Log initialization status"""
        available = sum(1 for v in self._subsystems.values() if v)
        total = len(self._subsystems)
        logger.info(f"FinancialManager: {available}/{total} subsystems loaded")

    async def check_capital_availability(self, amount_needed: float) -> Dict[str, Any]:
        """Check if capital is available for an operation"""
        total_available = sum(self._agent_capital.values())

        # Calculate how much is immediately available vs needs borrowing
        direct_available = min(self._agent_capital.get("revenue_pool", 0), amount_needed)
        needs_borrowing = max(0, amount_needed - direct_available)

        return {
            "ok": True,
            "amount_requested": amount_needed,
            "direct_available": direct_available,
            "needs_borrowing": needs_borrowing,
            "total_pool_available": total_available,
            "can_fulfill": total_available >= amount_needed,
            "agent_pools": self._agent_capital
        }

    async def arrange_internal_lending(self, amount_needed: float) -> Dict[str, Any]:
        """
        CRITICAL: Enable AI agents to lend to each other internally

        This is the OCL P2P feature that allows:
        - Idle agents to earn interest on unused capital
        - Active agents to borrow for opportunity execution
        - Platform to collect 2.5% facilitation fees
        """
        if amount_needed <= 0:
            return {"ok": True, "total_borrowed": 0, "loans": []}

        # Sort agents by idle capital (highest first)
        sorted_agents = sorted(
            [(k, v) for k, v in self._agent_capital.items() if v > 0],
            key=lambda x: x[1],
            reverse=True
        )

        loans = []
        remaining = amount_needed
        facilitation_fee_rate = 0.025  # 2.5%
        internal_apr = 0.10  # 10% APR for internal lending

        for agent_name, available in sorted_agents:
            if remaining <= 0:
                break

            # Don't drain any single agent completely
            max_lend = available * 0.8  # Leave 20% buffer
            loan_amount = min(max_lend, remaining)

            if loan_amount < 10:  # Minimum loan threshold
                continue

            # Create internal loan
            loan = InternalLoan(
                loan_id=f"loan_{uuid4().hex[:8]}",
                lender_agent=agent_name,
                borrower_agent="execution_pool",
                principal=loan_amount,
                interest_rate=internal_apr,
                created_at=datetime.now(timezone.utc),
                status="active"
            )
            self._active_loans.append(loan)

            # Deduct from lender's pool
            self._agent_capital[agent_name] -= loan_amount

            # Calculate facilitation fee
            facilitation_fee = loan_amount * facilitation_fee_rate
            self._total_facilitation_fees += facilitation_fee

            loans.append({
                "loan_id": loan.loan_id,
                "lender": agent_name,
                "amount": loan_amount,
                "interest_rate": internal_apr,
                "facilitation_fee": facilitation_fee
            })

            remaining -= loan_amount

        total_borrowed = amount_needed - remaining

        return {
            "ok": remaining == 0,
            "id": f"lending_pool_{uuid4().hex[:8]}",
            "total_borrowed": total_borrowed,
            "remaining_unfulfilled": remaining,
            "loans": loans,
            "aggregate_rate": internal_apr,
            "total_facilitation_fees": sum(l["facilitation_fee"] for l in loans),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def settle_loan(self, loan_id: str, revenue: float) -> Dict[str, Any]:
        """
        Settle a loan after job completion

        Distributes:
        - Principal back to lender
        - Interest earned to lender
        - Remaining profit to borrower (execution pool)
        """
        # Find all loans in the lending pool
        active_loans = [l for l in self._active_loans if l.status == "active"]

        if not active_loans:
            return {"ok": True, "message": "No active loans to settle", "revenue": revenue}

        settlements = []
        remaining_revenue = revenue

        for loan in active_loans:
            if remaining_revenue <= 0:
                break

            # Calculate interest (simplified - assume 30 day loan period)
            days_active = (datetime.now(timezone.utc) - loan.created_at).days or 1
            interest = loan.principal * (loan.interest_rate * days_active / 365)
            total_owed = loan.principal + interest

            # Attempt to repay
            repayment = min(remaining_revenue, total_owed)
            remaining_revenue -= repayment

            # Update loan status
            loan.repaid_amount += repayment
            if loan.repaid_amount >= total_owed:
                loan.status = "repaid"
                # Return capital to lender
                self._agent_capital[loan.lender_agent] = self._agent_capital.get(loan.lender_agent, 0) + total_owed
            else:
                # Partial repayment
                principal_portion = min(repayment, loan.principal)
                self._agent_capital[loan.lender_agent] = self._agent_capital.get(loan.lender_agent, 0) + principal_portion

            settlements.append({
                "loan_id": loan.loan_id,
                "lender": loan.lender_agent,
                "principal": loan.principal,
                "interest": interest,
                "repaid": repayment,
                "status": loan.status
            })

        # Remaining revenue goes to execution pool
        if remaining_revenue > 0:
            self._agent_capital["revenue_pool"] = self._agent_capital.get("revenue_pool", 0) + remaining_revenue

        return {
            "ok": True,
            "total_revenue": revenue,
            "settlements": settlements,
            "profit_retained": remaining_revenue,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def stake_bond(self, order_value: float, order_id: str) -> Dict[str, Any]:
        """Stake a performance bond for an order"""
        if not self._subsystems.get("performance_bonds"):
            return {"ok": False, "error": "Performance bonds not available"}

        try:
            bond_amount = order_value * 0.1  # 10% bond

            # Try to use external bond system first
            if callable(getattr(self, '_stake_bond', None)):
                result = self._stake_bond(order_id, bond_amount)
                return {"ok": True, "bond_amount": bond_amount, "result": result}

            # Fallback to internal pool
            if self._agent_capital.get("insurance_reserve", 0) >= bond_amount:
                self._agent_capital["insurance_reserve"] -= bond_amount
                return {
                    "ok": True,
                    "bond_amount": bond_amount,
                    "source": "insurance_reserve",
                    "order_id": order_id
                }

            return {"ok": False, "error": "Insufficient bond capital"}

        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def release_bond(self, order_id: str, success: bool) -> Dict[str, Any]:
        """Release a performance bond after order completion"""
        if not self._subsystems.get("performance_bonds"):
            return {"ok": False, "error": "Performance bonds not available"}

        try:
            # Calculate SLA bonus if successful
            bonus_rate = 0.03 if success else 0  # 3% SLA bonus

            return {
                "ok": True,
                "order_id": order_id,
                "success": success,
                "sla_bonus_rate": bonus_rate,
                "status": "released"
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def get_factoring_advance(self, invoice_id: str, amount: float) -> Dict[str, Any]:
        """Get factoring advance on pending revenue"""
        if not self._subsystems.get("agent_factoring"):
            return {"ok": False, "error": "Agent factoring not available"}

        try:
            if callable(self._request_factoring):
                result = await self._request_factoring(invoice_id, amount)
                return {"ok": True, "result": result}

            # Fallback: 85% advance rate
            advance = amount * 0.85
            return {
                "ok": True,
                "invoice_id": invoice_id,
                "requested": amount,
                "advance": advance,
                "advance_rate": 0.85,
                "fee": amount * 0.03  # 3% factoring fee
            }

        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get financial manager status"""
        available = sum(1 for v in self._subsystems.values() if v)
        active_loans = [l for l in self._active_loans if l.status == "active"]

        return {
            "ok": True,
            "subsystems": {
                "available": available,
                "total": len(self._subsystems),
                "percentage": round(available / len(self._subsystems) * 100, 1) if self._subsystems else 0,
                "details": self._subsystems
            },
            "ocl_p2p": {
                "active_loans": len(active_loans),
                "total_principal": sum(l.principal for l in active_loans),
                "total_facilitation_fees": self._total_facilitation_fees,
                "internal_apr": 0.10
            },
            "capital_pools": self._agent_capital,
            "total_capital": sum(self._agent_capital.values()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Singleton instance
_financial_manager: Optional[FinancialManager] = None


def get_financial_manager() -> FinancialManager:
    """Get or create the financial manager singleton"""
    global _financial_manager
    if _financial_manager is None:
        _financial_manager = FinancialManager()
    return _financial_manager
