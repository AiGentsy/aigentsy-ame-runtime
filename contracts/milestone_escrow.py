"""
MILESTONE ESCROW: PSP Milestone Paylinks with AIGx Micro-Assurance
═══════════════════════════════════════════════════════════════════════════════

Creates milestone-based escrow using payment service provider paylinks.
No custody - funds flow directly through PSP.

Features:
- Milestone-based payment structure
- PSP paylink generation (Stripe, PayPal, etc.)
- AIGx micro-assurance badges per milestone
- Release triggers on QA gate pass

Updated: Jan 2026
"""

import logging
import os
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# PSP Configuration
STRIPE_ENABLED = bool(os.getenv('STRIPE_SECRET_KEY'))
PAYPAL_ENABLED = bool(os.getenv('PAYPAL_CLIENT_ID'))


@dataclass
class PaymentRail:
    """A payment rail option for a milestone"""
    type: str  # 'cash' or 'credit+aigx'
    paylink_url: str
    amount_usd: float
    assurance: Optional[Dict[str, Any]] = None  # AIGx assurance details


@dataclass
class MilestonePaylink:
    """A paylink for a milestone with multiple payment rails"""
    id: str
    milestone_id: str
    amount_usd: float
    currency: str = "USD"
    status: str = "pending"  # pending, funded, released, disputed
    psp: str = "stripe"  # stripe, paypal, crypto
    paylink_url: Optional[str] = None
    funded_at: Optional[str] = None
    released_at: Optional[str] = None
    aigx_badge_id: Optional[str] = None
    aigx_assurance_amount: float = 0.0
    # Two-rail payment options
    rails: List[PaymentRail] = field(default_factory=list)
    selected_rail: Optional[str] = None  # Which rail client chose


@dataclass
class EscrowContract:
    """Escrow contract for all milestones"""
    id: str
    sow_id: str
    opportunity_id: str
    milestones: List[MilestonePaylink] = field(default_factory=list)
    total_amount_usd: float = 0.0
    funded_amount_usd: float = 0.0
    released_amount_usd: float = 0.0
    status: str = "created"  # created, partially_funded, fully_funded, in_progress, completed
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    client_room_url: Optional[str] = None


class MilestoneEscrow:
    """
    Creates and manages milestone-based escrow contracts.

    Flow:
    1. Create escrow from SOW milestones
    2. Generate paylinks for each milestone
    3. Attach AIGx micro-assurance badges
    4. Release funds on milestone completion
    """

    def __init__(self):
        self.contracts: Dict[str, EscrowContract] = {}
        self.stats = {
            'contracts_created': 0,
            'milestones_funded': 0,
            'milestones_released': 0,
            'total_value_usd': 0.0,
            'total_released_usd': 0.0,
        }

    async def create_milestones(self, opportunity: Dict[str, Any], sow: Dict[str, Any]) -> EscrowContract:
        """
        Create escrow contract from SOW.

        Args:
            opportunity: The opportunity dict
            sow: SOW dict from generator

        Returns:
            EscrowContract with paylinks
        """
        opp_id = opportunity.get('id', 'unknown')
        sow_id = sow.get('id', 'unknown')

        # Generate contract ID
        contract_id = f"esc_{hashlib.md5(f'{sow_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"

        # Create milestone paylinks
        milestones = []
        total_amount = 0.0

        for milestone in sow.get('milestones', []):
            amount = milestone.get('amount_usd', 0)
            total_amount += amount

            milestone_id = milestone.get('id', '')
            paylink_id_str = f"{contract_id}_{milestone_id}"
            paylink = MilestonePaylink(
                id=f"pay_{hashlib.md5(paylink_id_str.encode()).hexdigest()[:8]}",
                milestone_id=milestone_id,
                amount_usd=amount,
                psp=self._select_psp(amount),
            )

            # Generate paylink URL (cash rail)
            cash_link = await self._generate_paylink(paylink, opportunity)
            paylink.paylink_url = cash_link

            # Attach AIGx micro-assurance
            paylink.aigx_badge_id, paylink.aigx_assurance_amount = self._attach_aigx_badge(amount)

            # Generate two-rail payment options
            paylink.rails = await self._generate_payment_rails(
                paylink, opportunity, cash_link
            )

            milestones.append(paylink)

        # Create contract
        contract = EscrowContract(
            id=contract_id,
            sow_id=sow_id,
            opportunity_id=opp_id,
            milestones=milestones,
            total_amount_usd=total_amount,
        )

        # Generate client room URL
        contract.client_room_url = self._generate_client_room_url(contract)

        # Store
        self.contracts[contract_id] = contract
        self.stats['contracts_created'] += 1
        self.stats['total_value_usd'] += total_amount

        logger.info(f"Created escrow {contract_id}: ${total_amount} across {len(milestones)} milestones")

        return contract

    def _select_psp(self, amount: float) -> str:
        """Select best PSP for amount"""
        if STRIPE_ENABLED:
            return "stripe"
        elif PAYPAL_ENABLED:
            return "paypal"
        else:
            return "manual"

    async def _generate_paylink(self, paylink: MilestonePaylink, opportunity: Dict[str, Any]) -> str:
        """Generate PSP paylink"""
        if paylink.psp == "stripe" and STRIPE_ENABLED:
            try:
                import stripe
                stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

                # Create payment link
                link = stripe.PaymentLink.create(
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"Milestone {paylink.milestone_id}",
                                'description': opportunity.get('title', 'Service milestone'),
                            },
                            'unit_amount': int(paylink.amount_usd * 100),
                        },
                        'quantity': 1,
                    }],
                    metadata={
                        'milestone_id': paylink.milestone_id,
                        'paylink_id': paylink.id,
                        'opportunity_id': opportunity.get('id', ''),
                    }
                )
                return link.url

            except Exception as e:
                logger.warning(f"Stripe paylink failed: {e}")

        # Fallback: generate placeholder URL
        return f"https://pay.aigentsy.com/{paylink.id}?amount={paylink.amount_usd}"

    def _attach_aigx_badge(self, amount: float) -> tuple:
        """Attach AIGx micro-assurance badge"""
        # AIGx assurance = 2% of milestone value
        assurance_amount = round(amount * 0.02, 2)
        badge_id = f"aigx_{hashlib.md5(f'{amount}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"

        return badge_id, assurance_amount

    async def _generate_payment_rails(
        self,
        paylink: MilestonePaylink,
        opportunity: Dict[str, Any],
        cash_link: str,
    ) -> List[PaymentRail]:
        """
        Generate two-rail payment options.

        Rails:
        1. Cash: Standard payment
        2. Credit+AIGx: Outcome credits with micro-assurance (slightly higher)
        """
        rails = []

        # Rail 1: Cash (standard)
        rails.append(PaymentRail(
            type='cash',
            paylink_url=cash_link,
            amount_usd=paylink.amount_usd,
            assurance=None,
        ))

        # Rail 2: Credit+AIGx (5% premium for assurance)
        credit_amount = round(paylink.amount_usd * 1.05, 2)
        credit_link = f"https://pay.aigentsy.com/{paylink.id}?type=credit&amount={credit_amount}"

        rails.append(PaymentRail(
            type='credit+aigx',
            paylink_url=credit_link,
            amount_usd=credit_amount,
            assurance={
                'token': 'AIGx',
                'coverage': 'micro',
                'fee': 0.02,
                'badge_id': paylink.aigx_badge_id,
                'assurance_amount': paylink.aigx_assurance_amount,
            },
        ))

        return rails

    def _generate_client_room_url(self, contract: EscrowContract) -> str:
        """Generate signed client room URL"""
        # Create signed token
        token = hashlib.sha256(
            f"{contract.id}:{contract.sow_id}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:32]

        return f"https://room.aigentsy.com/{contract.id}?token={token}"

    async def fund_milestone(self, contract_id: str, milestone_id: str) -> bool:
        """Mark milestone as funded"""
        contract = self.contracts.get(contract_id)
        if not contract:
            return False

        for milestone in contract.milestones:
            if milestone.milestone_id == milestone_id:
                milestone.status = "funded"
                milestone.funded_at = datetime.now(timezone.utc).isoformat()
                contract.funded_amount_usd += milestone.amount_usd
                self.stats['milestones_funded'] += 1

                # Update contract status
                if contract.funded_amount_usd >= contract.total_amount_usd:
                    contract.status = "fully_funded"
                else:
                    contract.status = "partially_funded"

                logger.info(f"Milestone {milestone_id} funded: ${milestone.amount_usd}")
                return True

        return False

    async def release_milestone(self, contract_id: str, milestone_id: str, qa_passed: bool = True) -> bool:
        """Release milestone funds"""
        if not qa_passed:
            logger.warning(f"Cannot release {milestone_id}: QA not passed")
            return False

        contract = self.contracts.get(contract_id)
        if not contract:
            return False

        for milestone in contract.milestones:
            if milestone.milestone_id == milestone_id and milestone.status == "funded":
                milestone.status = "released"
                milestone.released_at = datetime.now(timezone.utc).isoformat()
                contract.released_amount_usd += milestone.amount_usd
                self.stats['milestones_released'] += 1
                self.stats['total_released_usd'] += milestone.amount_usd

                # Check if contract complete
                if contract.released_amount_usd >= contract.total_amount_usd:
                    contract.status = "completed"

                logger.info(f"Milestone {milestone_id} released: ${milestone.amount_usd}")
                return True

        return False

    def get_contract(self, contract_id: str) -> Optional[EscrowContract]:
        """Get escrow contract"""
        return self.contracts.get(contract_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get escrow stats"""
        return {
            **self.stats,
            'active_contracts': len(self.contracts),
        }

    def to_dict(self, contract: EscrowContract) -> Dict[str, Any]:
        """Convert contract to dict"""
        return {
            'id': contract.id,
            'sow_id': contract.sow_id,
            'opportunity_id': contract.opportunity_id,
            'milestones': [
                {
                    'id': m.id,
                    'milestone_id': m.milestone_id,
                    'amount_usd': m.amount_usd,
                    'currency': m.currency,
                    'status': m.status,
                    'psp': m.psp,
                    'paylink_url': m.paylink_url,
                    'funded_at': m.funded_at,
                    'released_at': m.released_at,
                    'aigx_badge_id': m.aigx_badge_id,
                    'aigx_assurance_amount': m.aigx_assurance_amount,
                }
                for m in contract.milestones
            ],
            'total_amount_usd': contract.total_amount_usd,
            'funded_amount_usd': contract.funded_amount_usd,
            'released_amount_usd': contract.released_amount_usd,
            'status': contract.status,
            'created_at': contract.created_at,
            'client_room_url': contract.client_room_url,
        }


# Global instance
_escrow: Optional[MilestoneEscrow] = None


def get_milestone_escrow() -> MilestoneEscrow:
    """Get or create escrow singleton"""
    global _escrow
    if _escrow is None:
        _escrow = MilestoneEscrow()
    return _escrow


async def create_milestones(opportunity: Dict[str, Any], sow: Dict[str, Any]) -> EscrowContract:
    """Convenience function"""
    return await get_milestone_escrow().create_milestones(opportunity, sow)
