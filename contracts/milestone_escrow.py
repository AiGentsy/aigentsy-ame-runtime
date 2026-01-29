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
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

# Persistence file path
DATA_DIR = Path(__file__).parent.parent / "data"
CONTRACTS_FILE = DATA_DIR / "escrow_contracts.json"

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
    status: str = "created"  # created, handshake_pending, handshake_accepted, preview_delivered, preview_approved, deposit_pending, funded, in_progress, completed
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    client_room_url: Optional[str] = None

    # Handshake fields
    handshake_status: str = "pending"  # pending, accepted, expired
    handshake_accepted_at: Optional[str] = None
    handshake_expires_at: Optional[str] = None  # 48h from creation
    handshake_ip: Optional[str] = None

    # Preview fields
    preview_status: str = "not_started"  # not_started, in_progress, delivered, approved, expired
    preview_type: Optional[str] = None  # development, design, content, etc.
    preview_artifacts: List[Dict] = field(default_factory=list)  # [{url, type, watermarked}]
    preview_delivered_at: Optional[str] = None
    preview_expires_at: Optional[str] = None  # 48h from delivery

    # Referral field
    referral_code: Optional[str] = None

    # Proof-to-Promo flywheel
    auto_promo_enabled: bool = True


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
        # Load persisted contracts on init
        self._load_contracts()

    def _load_contracts(self):
        """Load contracts from persistent storage"""
        try:
            if CONTRACTS_FILE.exists():
                with open(CONTRACTS_FILE, 'r') as f:
                    data = json.load(f)
                    for contract_id, contract_data in data.get('contracts', {}).items():
                        # Reconstruct MilestonePaylink objects
                        milestones = []
                        for m in contract_data.get('milestones', []):
                            rails = [PaymentRail(**r) for r in m.pop('rails', [])]
                            paylink = MilestonePaylink(**m)
                            paylink.rails = rails
                            milestones.append(paylink)
                        contract_data['milestones'] = milestones
                        self.contracts[contract_id] = EscrowContract(**contract_data)
                    self.stats = data.get('stats', self.stats)
                    logger.info(f"✅ Loaded {len(self.contracts)} contracts from storage")
        except Exception as e:
            logger.warning(f"⚠️ Could not load contracts: {e}")

    def _save_contracts(self):
        """Save contracts to persistent storage"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                'contracts': {cid: self.to_dict(c) for cid, c in self.contracts.items()},
                'stats': self.stats,
                'saved_at': datetime.now(timezone.utc).isoformat()
            }
            with open(CONTRACTS_FILE, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"💾 Saved {len(self.contracts)} contracts to storage")
        except Exception as e:
            logger.error(f"❌ Could not save contracts: {e}")

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

        # Set handshake expiration (48h from creation)
        from datetime import timedelta
        handshake_expires = datetime.now(timezone.utc) + timedelta(hours=48)
        contract.handshake_expires_at = handshake_expires.isoformat()
        contract.status = "handshake_pending"

        # Determine preview type from opportunity
        fulfillment_type = opportunity.get('fulfillment_type') or opportunity.get('category', 'development')
        contract.preview_type = fulfillment_type

        # Generate referral code
        contract.referral_code = hashlib.md5(f"{contract_id}:ref".encode()).hexdigest()[:8].upper()

        # Generate client room URL
        contract.client_room_url = self._generate_client_room_url(contract)

        # Store
        self.contracts[contract_id] = contract
        self.stats['contracts_created'] += 1
        self.stats['total_value_usd'] += total_amount

        # Persist to disk
        self._save_contracts()

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

                self._save_contracts()
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

                    # Trigger proof-to-promo flywheel (non-blocking)
                    if contract.auto_promo_enabled:
                        import asyncio
                        try:
                            asyncio.ensure_future(
                                _trigger_proof_promo_flywheel(contract, self)
                            )
                        except Exception as e:
                            logger.warning(f"Could not schedule proof-promo flywheel: {e}")

                self._save_contracts()
                logger.info(f"Milestone {milestone_id} released: ${milestone.amount_usd}")
                return True

        return False

    def get_contract(self, contract_id: str) -> Optional[EscrowContract]:
        """Get escrow contract"""
        return self.contracts.get(contract_id)

    def accept_handshake(self, contract_id: str, client_ip: str) -> bool:
        """
        Accept handshake terms.

        Args:
            contract_id: Contract ID
            client_ip: Client's IP address for logging

        Returns:
            True if accepted, False otherwise
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            return False

        # Check if already accepted
        if contract.handshake_status == "accepted":
            return True

        # Check if expired
        if contract.handshake_expires_at:
            try:
                expires = datetime.fromisoformat(contract.handshake_expires_at.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > expires:
                    contract.handshake_status = "expired"
                    return False
            except:
                pass

        # Accept handshake
        contract.handshake_status = "accepted"
        contract.handshake_accepted_at = datetime.now(timezone.utc).isoformat()
        contract.handshake_ip = client_ip
        contract.status = "handshake_accepted"

        # Set preview expiration (48h from now)
        from datetime import timedelta
        preview_expires = datetime.now(timezone.utc) + timedelta(hours=48)
        contract.preview_expires_at = preview_expires.isoformat()

        # Start preview generation
        contract.preview_status = "in_progress"

        self._save_contracts()
        logger.info(f"Handshake accepted for {contract_id} from IP {client_ip}")
        return True

    def deliver_preview(self, contract_id: str, artifacts: List[Dict]) -> bool:
        """
        Mark preview as delivered with artifacts.

        Args:
            contract_id: Contract ID
            artifacts: List of artifact dicts [{url, type, watermarked}]

        Returns:
            True if delivered, False otherwise
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            return False

        if contract.handshake_status != "accepted":
            logger.warning(f"Cannot deliver preview for {contract_id}: handshake not accepted")
            return False

        contract.preview_status = "delivered"
        contract.preview_artifacts = artifacts
        contract.preview_delivered_at = datetime.now(timezone.utc).isoformat()
        contract.status = "preview_delivered"

        # Set preview expiration (48h from delivery)
        from datetime import timedelta
        preview_expires = datetime.now(timezone.utc) + timedelta(hours=48)
        contract.preview_expires_at = preview_expires.isoformat()

        self._save_contracts()
        logger.info(f"Preview delivered for {contract_id}: {len(artifacts)} artifacts")
        return True

    def approve_preview(self, contract_id: str) -> bool:
        """
        Approve preview and transition to deposit pending.

        Args:
            contract_id: Contract ID

        Returns:
            True if approved, False otherwise
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            return False

        if contract.preview_status != "delivered":
            logger.warning(f"Cannot approve preview for {contract_id}: not delivered")
            return False

        # Check expiration
        if contract.preview_expires_at:
            try:
                expires = datetime.fromisoformat(contract.preview_expires_at.replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > expires:
                    contract.preview_status = "expired"
                    return False
            except:
                pass

        contract.preview_status = "approved"
        contract.status = "deposit_pending"

        self._save_contracts()
        logger.info(f"Preview approved for {contract_id}")
        return True

    def generate_referral_code(self, contract_id: str) -> Optional[str]:
        """
        Generate unique referral code for a contract.

        Args:
            contract_id: Contract ID

        Returns:
            Referral code string
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            return None

        if contract.referral_code:
            return contract.referral_code

        # Generate short unique code
        code = hashlib.md5(f"{contract_id}:{datetime.now().isoformat()}".encode()).hexdigest()[:8].upper()
        contract.referral_code = code

        logger.info(f"Generated referral code {code} for {contract_id}")
        return code

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
            # Handshake fields
            'handshake_status': contract.handshake_status,
            'handshake_accepted_at': contract.handshake_accepted_at,
            'handshake_expires_at': contract.handshake_expires_at,
            'handshake_ip': contract.handshake_ip,
            # Preview fields
            'preview_status': contract.preview_status,
            'preview_type': contract.preview_type,
            'preview_artifacts': contract.preview_artifacts,
            'preview_delivered_at': contract.preview_delivered_at,
            'preview_expires_at': contract.preview_expires_at,
            # Referral
            'referral_code': contract.referral_code,
            # Proof-to-Promo
            'auto_promo_enabled': getattr(contract, 'auto_promo_enabled', True),
        }


async def _trigger_proof_promo_flywheel(contract: EscrowContract, escrow: 'MilestoneEscrow') -> None:
    """
    Proof-to-Promo Flywheel: on contract completion, mint proof and post success story.

    Steps:
    1. Mint proof via proof_ledger.create_proof()
    2. Post success story to social channels
    3. Log to MetaHive
    All wrapped in try/except - entirely non-blocking.
    """
    contract_id = contract.id
    opp_id = contract.opportunity_id
    total = contract.total_amount_usd

    # 1. Mint proof
    proof_id = None
    try:
        from monetization.proof_ledger import get_proof_ledger
        ledger = get_proof_ledger()
        proof = await ledger.create_proof(
            contract_id=contract_id,
            opportunity_id=opp_id,
            title=f"Completed contract {contract_id}",
            description=f"Successfully delivered ${total:,.0f} contract",
            artifacts=[],
        )
        proof_id = getattr(proof, 'id', None)
        logger.info(f"Proof-to-Promo: minted proof {proof_id} for {contract_id}")
    except Exception as e:
        logger.warning(f"Proof-to-Promo: could not mint proof for {contract_id}: {e}")

    # 2. Post success story to social channels
    try:
        from growth.growth_loops import post_contract_success_story
        await post_contract_success_story(
            contract_id=contract_id,
            total_value=total,
            proof_id=proof_id,
            channels=["twitter", "linkedin", "instagram"],
        )
        logger.info(f"Proof-to-Promo: posted success story for {contract_id}")
    except Exception as e:
        logger.warning(f"Proof-to-Promo: could not post success story for {contract_id}: {e}")

    # 3. Log to MetaHive
    try:
        from metahive import contribute_to_metahive
        await contribute_to_metahive({
            'type': 'proof_promo_flywheel',
            'contract_id': contract_id,
            'proof_id': proof_id,
            'total_value': total,
        })
        logger.info(f"Proof-to-Promo: logged to MetaHive for {contract_id}")
    except Exception as e:
        logger.debug(f"Proof-to-Promo: MetaHive log skipped for {contract_id}: {e}")


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
