"""
Financial Manager - OCL P2P Lending + Financial Infrastructure
==============================================================

Systems managed (with ACTUAL function imports):
1. ocl_p2p_lending.py - create_loan_offer, match_loan_offers, accept_loan_offer
2. ocl_engine.py - calculate_ocl_limit, spend_ocl, get_ocl_balance
3. ocl_expansion.py - expand_ocl_limit, process_job_completion_expansion
4. performance_bonds.py - stake_bond, return_bond, award_sla_bonus
5. securitization_desk.py - create_spv, issue_tranche, distribute_cash_flows
6. outcomes_insurance_oracle.py - quote_oio, attach_oio, settle_oio
7. insurance_pool.py - collect_insurance, payout_from_pool
8. agent_factoring.py - request_factoring_advance, calculate_factoring_tier
9. batch_payments.py - create_batch_payment, execute_batch_payment
10. builder_risk_tranches.py - register_builder, issue_tranche
11. dark_pool.py - create_dark_pool_auction, submit_dark_pool_bid

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
        self._agent_capital: Dict[str, float] = {}
        self._total_facilitation_fees: float = 0.0
        self._init_subsystems()
        self._init_agent_capital()

    def _init_subsystems(self):
        """Initialize all 11 financial subsystems with CORRECT imports"""

        # 1. OCL P2P Lending
        try:
            from ocl_p2p_lending import (
                create_loan_offer,
                create_loan_request,
                match_loan_offers,
                accept_loan_offer,
                make_loan_payment,
                auto_repay_from_earnings,
                get_active_loans,
                get_loan_history,
                list_available_offers,
                calculate_credit_score
            )
            self._create_offer = create_loan_offer
            self._create_request = create_loan_request
            self._match_lenders = match_loan_offers
            self._accept_offer = accept_loan_offer
            self._make_payment = make_loan_payment
            self._auto_repay = auto_repay_from_earnings
            self._get_loans = get_active_loans
            self._loan_history = get_loan_history
            self._list_offers = list_available_offers
            self._credit_score = calculate_credit_score
            self._subsystems["ocl_p2p_lending"] = True
            logger.info("OCL P2P Lending loaded successfully")
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
            logger.info("OCL Engine loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"OCL engine not available: {e}")
            self._subsystems["ocl_engine"] = False

        # 3. OCL Expansion
        try:
            from ocl_expansion import (
                calculate_ocl_expansion,
                check_expansion_eligibility,
                expand_ocl_limit,
                process_job_completion_expansion,
                trigger_r3_reallocation,
                get_expansion_stats
            )
            self._calc_expansion = calculate_ocl_expansion
            self._check_eligibility = check_expansion_eligibility
            self._expand_credit = expand_ocl_limit
            self._job_expansion = process_job_completion_expansion
            self._r3_realloc = trigger_r3_reallocation
            self._expansion_stats = get_expansion_stats
            self._subsystems["ocl_expansion"] = True
            logger.info("OCL Expansion loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"OCL expansion not available: {e}")
            self._subsystems["ocl_expansion"] = False

        # 4. Performance Bonds
        try:
            from performance_bonds import (
                calculate_bond_amount,
                stake_bond,
                return_bond,
                calculate_sla_bonus,
                award_sla_bonus,
                slash_bond
            )
            self._calc_bond = calculate_bond_amount
            self._stake_bond = stake_bond
            self._return_bond = return_bond
            self._calc_sla = calculate_sla_bonus
            self._award_sla = award_sla_bonus
            self._slash_bond = slash_bond
            self._subsystems["performance_bonds"] = True
            logger.info("Performance Bonds loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Performance bonds not available: {e}")
            self._subsystems["performance_bonds"] = False

        # 5. Securitization Desk
        try:
            from securitization_desk import (
                SecuritizationDesk,
                create_spv,
                add_outcome_to_pool,
                issue_tranche,
                buy_tranche,
                receive_cash_flow,
                distribute_cash_flows,
                get_spv,
                get_tranche,
                get_holder_positions,
                get_securitization_stats,
                get_desk_stats,
                price_abs
            )
            self._desk_class = SecuritizationDesk
            self._create_spv = create_spv
            self._add_to_pool = add_outcome_to_pool
            self._issue_tranche = issue_tranche
            self._buy_tranche = buy_tranche
            self._receive_cash = receive_cash_flow
            self._distribute_cash = distribute_cash_flows
            self._get_spv = get_spv
            self._get_tranche = get_tranche
            self._holder_positions = get_holder_positions
            self._sec_stats = get_securitization_stats
            self._desk_stats = get_desk_stats
            self._price_abs = price_abs
            self._subsystems["securitization_desk"] = True
            logger.info("Securitization Desk loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Securitization desk not available: {e}")
            self._subsystems["securitization_desk"] = False

        # 6. Outcomes Insurance Oracle
        try:
            from outcomes_insurance_oracle import (
                OutcomesInsuranceOracle,
                quote_oio,
                attach_oio,
                settle_oio,
                get_oio_policy,
                get_oio_stats,
                calculate_premium
            )
            self._oio_class = OutcomesInsuranceOracle
            self._quote_oio = quote_oio
            self._attach_oio = attach_oio
            self._settle_oio = settle_oio
            self._get_policy = get_oio_policy
            self._oio_stats = get_oio_stats
            self._calc_premium = calculate_premium
            self._subsystems["outcomes_insurance"] = True
            logger.info("Outcomes Insurance Oracle loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Outcomes insurance not available: {e}")
            self._subsystems["outcomes_insurance"] = False

        # 7. Insurance Pool
        try:
            from insurance_pool import (
                calculate_insurance_fee,
                collect_insurance,
                get_pool_balance,
                payout_from_pool,
                calculate_dispute_rate,
                calculate_annual_refund,
                issue_annual_refund
            )
            self._calc_fee = calculate_insurance_fee
            self._collect_insurance = collect_insurance
            self._pool_balance = get_pool_balance
            self._pool_payout = payout_from_pool
            self._dispute_rate = calculate_dispute_rate
            self._annual_refund = calculate_annual_refund
            self._issue_refund = issue_annual_refund
            self._subsystems["insurance_pool"] = True
            logger.info("Insurance Pool loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Insurance pool not available: {e}")
            self._subsystems["insurance_pool"] = False

        # 8. Agent Factoring
        try:
            from agent_factoring import (
                calculate_factoring_tier,
                calculate_outstanding_factoring,
                request_factoring_advance,
                settle_factoring,
                calculate_factoring_eligibility
            )
            self._factoring_tier = calculate_factoring_tier
            self._outstanding_factoring = calculate_outstanding_factoring
            self._request_factoring = request_factoring_advance
            self._settle_factoring = settle_factoring
            self._factoring_eligibility = calculate_factoring_eligibility
            self._subsystems["agent_factoring"] = True
            logger.info("Agent Factoring loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Agent factoring not available: {e}")
            self._subsystems["agent_factoring"] = False

        # 9. Batch Payments
        try:
            from batch_payments import (
                create_batch_payment,
                execute_batch_payment,
                generate_bulk_invoices,
                batch_revenue_recognition,
                schedule_recurring_payment,
                generate_payment_report,
                retry_failed_payments
            )
            self._create_batch = create_batch_payment
            self._execute_batch = execute_batch_payment
            self._bulk_invoices = generate_bulk_invoices
            self._revenue_recognition = batch_revenue_recognition
            self._recurring_payment = schedule_recurring_payment
            self._payment_report = generate_payment_report
            self._retry_payments = retry_failed_payments
            self._subsystems["batch_payments"] = True
            logger.info("Batch Payments loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Batch payments not available: {e}")
            self._subsystems["batch_payments"] = False

        # 10. Builder Risk Tranches
        try:
            from builder_risk_tranches import (
                BuilderRiskTranches,
                register_builder,
                record_builder_transaction,
                file_builder_claim,
                upgrade_builder_tier,
                get_builder,
                get_builder_coverage,
                get_brt_stats,
                get_tranche_portfolio,
                issue_tranche as brt_issue_tranche,
                price_tranche as brt_price_tranche
            )
            self._brt_class = BuilderRiskTranches
            self._register_builder = register_builder
            self._builder_transaction = record_builder_transaction
            self._file_claim = file_builder_claim
            self._upgrade_tier = upgrade_builder_tier
            self._get_builder = get_builder
            self._builder_coverage = get_builder_coverage
            self._brt_stats = get_brt_stats
            self._tranche_portfolio = get_tranche_portfolio
            self._brt_issue = brt_issue_tranche
            self._brt_price = brt_price_tranche
            self._subsystems["builder_tranches"] = True
            logger.info("Builder Risk Tranches loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Builder risk tranches not available: {e}")
            self._subsystems["builder_tranches"] = False

        # 11. Dark Pool
        try:
            from dark_pool import (
                create_dark_pool_auction,
                submit_dark_pool_bid,
                calculate_bid_score,
                close_dark_pool_auction,
                reveal_agent_identity,
                calculate_dark_pool_metrics,
                get_agent_dark_pool_history,
                check_dark_pool_access,
                qualify_for_dark_pool_intent,
                create_premium_dark_pool_auction,
                submit_premium_dark_pool_bid,
                get_dark_pool_leaderboard
            )
            self._create_auction = create_dark_pool_auction
            self._submit_bid = submit_dark_pool_bid
            self._bid_score = calculate_bid_score
            self._close_auction = close_dark_pool_auction
            self._reveal_identity = reveal_agent_identity
            self._dark_metrics = calculate_dark_pool_metrics
            self._dark_history = get_agent_dark_pool_history
            self._dark_access = check_dark_pool_access
            self._qualify_intent = qualify_for_dark_pool_intent
            self._premium_auction = create_premium_dark_pool_auction
            self._premium_bid = submit_premium_dark_pool_bid
            self._dark_leaderboard = get_dark_pool_leaderboard
            self._subsystems["dark_pool"] = True
            logger.info("Dark Pool loaded successfully")
        except (ImportError, Exception) as e:
            logger.warning(f"Dark pool not available: {e}")
            self._subsystems["dark_pool"] = False

        self._log_status()

    def _init_agent_capital(self):
        """Initialize tracked agent capital pools"""
        self._agent_capital = {
            "alpha_discovery": 2000.0,
            "ai_router": 1500.0,
            "deal_graph": 500.0,
            "execution_fabric": 1000.0,
            "metahive_brain": 750.0,
            "yield_memory": 250.0,
            "outcome_oracle": 1000.0,
            "spawn_engine": 500.0,
            "revenue_pool": 3000.0,
            "insurance_reserve": 1500.0
        }

    def _log_status(self):
        """Log initialization status"""
        available = sum(1 for v in self._subsystems.values() if v)
        total = len(self._subsystems)
        logger.info(f"FinancialManager: {available}/{total} subsystems loaded")

    async def check_capital_availability(self, amount_needed: float) -> Dict[str, Any]:
        """Check if capital is available for an operation"""
        total_available = sum(self._agent_capital.values())
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

        - Idle agents earn interest on unused capital
        - Active agents borrow for opportunity execution
        - Platform collects 2.5% facilitation fees
        """
        if amount_needed <= 0:
            return {"ok": True, "total_borrowed": 0, "loans": []}

        sorted_agents = sorted(
            [(k, v) for k, v in self._agent_capital.items() if v > 0],
            key=lambda x: x[1],
            reverse=True
        )

        loans = []
        remaining = amount_needed
        facilitation_fee_rate = 0.025
        internal_apr = 0.10

        for agent_name, available in sorted_agents:
            if remaining <= 0:
                break

            max_lend = available * 0.8
            loan_amount = min(max_lend, remaining)

            if loan_amount < 10:
                continue

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
            self._agent_capital[agent_name] -= loan_amount

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
        """Settle a loan after job completion"""
        active_loans = [l for l in self._active_loans if l.status == "active"]

        if not active_loans:
            return {"ok": True, "message": "No active loans to settle", "revenue": revenue}

        settlements = []
        remaining_revenue = revenue

        for loan in active_loans:
            if remaining_revenue <= 0:
                break

            days_active = (datetime.now(timezone.utc) - loan.created_at).days or 1
            interest = loan.principal * (loan.interest_rate * days_active / 365)
            total_owed = loan.principal + interest

            repayment = min(remaining_revenue, total_owed)
            remaining_revenue -= repayment

            loan.repaid_amount += repayment
            if loan.repaid_amount >= total_owed:
                loan.status = "repaid"
                self._agent_capital[loan.lender_agent] = self._agent_capital.get(loan.lender_agent, 0) + total_owed
            else:
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

        if remaining_revenue > 0:
            self._agent_capital["revenue_pool"] = self._agent_capital.get("revenue_pool", 0) + remaining_revenue

        return {
            "ok": True,
            "total_revenue": revenue,
            "settlements": settlements,
            "profit_retained": remaining_revenue,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def stake_bond(self, user: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Stake a performance bond for an order"""
        if not self._subsystems.get("performance_bonds"):
            return {"ok": False, "error": "Performance bonds not available"}

        try:
            order_value = intent.get("value", 100)
            bond_info = self._calc_bond(order_value) if callable(self._calc_bond) else {"bond_amount": order_value * 0.1}
            result = await self._stake_bond(user, intent) if callable(self._stake_bond) else {"staked": True}
            return {"ok": True, "bond_amount": bond_info, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def release_bond(self, user: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """Release a performance bond after order completion"""
        if not self._subsystems.get("performance_bonds"):
            return {"ok": False, "error": "Performance bonds not available"}

        try:
            result = await self._return_bond(user, intent) if callable(self._return_bond) else {"released": True}
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def get_factoring_advance(self, user: Dict[str, Any], amount: float) -> Dict[str, Any]:
        """Get factoring advance on pending revenue"""
        if not self._subsystems.get("agent_factoring"):
            return {"ok": False, "error": "Agent factoring not available"}

        try:
            if callable(self._request_factoring):
                result = await self._request_factoring(user, amount)
                return {"ok": True, "result": result}

            advance = amount * 0.85
            return {
                "ok": True,
                "requested": amount,
                "advance": advance,
                "advance_rate": 0.85,
                "fee": amount * 0.03
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def create_dark_pool_auction(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Create a dark pool auction for high-value intents"""
        if not self._subsystems.get("dark_pool"):
            return {"ok": False, "error": "Dark pool not available"}

        try:
            if callable(self._create_auction):
                result = self._create_auction(intent)
                return {"ok": True, "auction": result}
            return {"ok": False, "error": "Create auction not callable"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def execute_batch_payment(self, payments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a batch of payments"""
        if not self._subsystems.get("batch_payments"):
            return {"ok": False, "error": "Batch payments not available"}

        try:
            if callable(self._create_batch):
                batch = await self._create_batch(payments)
                if callable(self._execute_batch):
                    result = await self._execute_batch(batch.get("batch_id", ""))
                    return {"ok": True, "result": result}
            return {"ok": False, "error": "Batch execution failed"}
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
