"""
GROWTH LOOPS: Automated Upsell & Referral Engine
═══════════════════════════════════════════════════════════════════════════════

Identifies and triggers growth opportunities from completed work.

Features:
- Upsell detection from completed milestones
- Referral tracking and incentives
- Cross-sell based on opportunity patterns
- Automated follow-up sequences

Updated: Jan 2026
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class GrowthOpportunity:
    """A growth opportunity (upsell, cross-sell, referral)"""
    id: str
    type: str  # upsell, cross_sell, referral, repeat
    source_opportunity_id: str
    source_contract_id: Optional[str] = None
    title: str = ""
    description: str = ""
    estimated_value_usd: float = 0.0
    probability: float = 0.5
    status: str = "identified"  # identified, contacted, converted, lost
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    converted_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class ReferralRecord:
    """A referral tracking record"""
    id: str
    referrer_id: str  # Original client
    referred_id: str  # New prospect
    source_contract_id: str
    status: str = "pending"  # pending, contacted, converted
    incentive_usd: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GrowthLoops:
    """
    Manages growth loops for revenue expansion.

    Triggers:
    - Milestone completion → Upsell detection
    - High satisfaction → Referral request
    - Pattern matching → Cross-sell suggestions
    - Time-based → Repeat business outreach
    """

    def __init__(self):
        self.opportunities: Dict[str, GrowthOpportunity] = {}
        self.referrals: Dict[str, ReferralRecord] = {}
        self.stats = {
            'opportunities_identified': 0,
            'opportunities_converted': 0,
            'referrals_received': 0,
            'referrals_converted': 0,
            'upsell_value_usd': 0.0,
            'referral_value_usd': 0.0,
        }

        # Upsell patterns by offer pack
        self.upsell_patterns = {
            'web_dev': [
                {'trigger': 'deploy', 'upsell': 'maintenance', 'value_mult': 0.2, 'prob': 0.4},
                {'trigger': 'mvp', 'upsell': 'full_product', 'value_mult': 3.0, 'prob': 0.3},
                {'trigger': 'feature', 'upsell': 'additional_features', 'value_mult': 0.5, 'prob': 0.5},
            ],
            'mobile_dev': [
                {'trigger': 'ios', 'upsell': 'android', 'value_mult': 0.8, 'prob': 0.6},
                {'trigger': 'android', 'upsell': 'ios', 'value_mult': 0.8, 'prob': 0.6},
                {'trigger': 'launch', 'upsell': 'app_store_optimization', 'value_mult': 0.15, 'prob': 0.5},
            ],
            'data_ml': [
                {'trigger': 'model', 'upsell': 'production_deployment', 'value_mult': 0.5, 'prob': 0.4},
                {'trigger': 'analysis', 'upsell': 'dashboard', 'value_mult': 0.6, 'prob': 0.5},
                {'trigger': 'training', 'upsell': 'monitoring', 'value_mult': 0.3, 'prob': 0.4},
            ],
            'devops': [
                {'trigger': 'infrastructure', 'upsell': 'monitoring', 'value_mult': 0.25, 'prob': 0.6},
                {'trigger': 'ci_cd', 'upsell': 'security_hardening', 'value_mult': 0.4, 'prob': 0.4},
            ],
            'design': [
                {'trigger': 'wireframes', 'upsell': 'high_fidelity', 'value_mult': 2.0, 'prob': 0.7},
                {'trigger': 'ui', 'upsell': 'design_system', 'value_mult': 1.5, 'prob': 0.4},
            ],
            'writing': [
                {'trigger': 'blog', 'upsell': 'content_series', 'value_mult': 4.0, 'prob': 0.3},
                {'trigger': 'copy', 'upsell': 'landing_pages', 'value_mult': 0.5, 'prob': 0.5},
            ],
            'automation': [
                {'trigger': 'script', 'upsell': 'monitoring', 'value_mult': 0.3, 'prob': 0.5},
                {'trigger': 'workflow', 'upsell': 'expansion', 'value_mult': 0.4, 'prob': 0.4},
            ],
        }

    def on_milestone_complete(
        self,
        opportunity: Dict[str, Any],
        contract: Dict[str, Any],
        milestone: Dict[str, Any],
    ) -> List[GrowthOpportunity]:
        """
        Detect growth opportunities when milestone completes.

        Args:
            opportunity: Original opportunity dict
            contract: Contract/escrow dict
            milestone: Completed milestone dict

        Returns:
            List of identified growth opportunities
        """
        identified = []

        opp_id = opportunity.get('id', 'unknown')
        contract_id = contract.get('id', 'unknown')
        offer_pack = opportunity.get('enrichment', {}).get('inventory_scores', {})

        # Determine offer pack
        if offer_pack:
            pack = max(offer_pack.items(), key=lambda x: x[1])[0]
        else:
            pack = 'web_dev'

        # Get base value
        base_value = contract.get('total_amount_usd', 1000)
        milestone_name = milestone.get('name', '').lower()

        # Check upsell patterns
        patterns = self.upsell_patterns.get(pack, [])
        for pattern in patterns:
            if pattern['trigger'] in milestone_name:
                upsell = self._create_growth_opportunity(
                    type='upsell',
                    source_opportunity_id=opp_id,
                    source_contract_id=contract_id,
                    title=f"Upsell: {pattern['upsell'].replace('_', ' ').title()}",
                    description=f"Follow-up opportunity based on {pattern['trigger']} completion",
                    estimated_value=base_value * pattern['value_mult'],
                    probability=pattern['prob'],
                    tags=[pack, pattern['upsell']],
                )
                identified.append(upsell)

        # Check for repeat business opportunity (final milestone)
        if 'final' in milestone_name or 'deliver' in milestone_name:
            repeat = self._create_growth_opportunity(
                type='repeat',
                source_opportunity_id=opp_id,
                source_contract_id=contract_id,
                title="Repeat Business Opportunity",
                description="Client completed project - potential for future work",
                estimated_value=base_value * 0.5,
                probability=0.25,
                tags=[pack, 'repeat'],
            )
            identified.append(repeat)

        logger.info(f"Identified {len(identified)} growth opportunities from milestone completion")

        return identified

    def on_high_satisfaction(
        self,
        opportunity: Dict[str, Any],
        contract: Dict[str, Any],
        satisfaction_score: float,
    ) -> Optional[ReferralRecord]:
        """
        Trigger referral request on high satisfaction.

        Args:
            opportunity: Original opportunity
            contract: Completed contract
            satisfaction_score: 0-1 satisfaction score

        Returns:
            ReferralRecord if request sent
        """
        if satisfaction_score < 0.8:
            return None

        opp_id = opportunity.get('id', 'unknown')
        contract_id = contract.get('id', 'unknown')
        contract_value = contract.get('total_amount_usd', 1000)

        # Create referral tracking
        referral_id = f"ref_{hashlib.md5(f'{contract_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"

        # Calculate incentive (5% of contract value)
        incentive = round(contract_value * 0.05, 2)

        referral = ReferralRecord(
            id=referral_id,
            referrer_id=opp_id,
            referred_id="pending",
            source_contract_id=contract_id,
            incentive_usd=incentive,
        )

        self.referrals[referral_id] = referral
        self.stats['referrals_received'] += 1

        logger.info(f"Created referral request {referral_id} with ${incentive} incentive")

        return referral

    def _create_growth_opportunity(
        self,
        type: str,
        source_opportunity_id: str,
        source_contract_id: str,
        title: str,
        description: str,
        estimated_value: float,
        probability: float,
        tags: List[str],
    ) -> GrowthOpportunity:
        """Create and store growth opportunity"""
        opp_id = f"growth_{hashlib.md5(f'{source_contract_id}_{title}_{datetime.now().isoformat()}'.encode()).hexdigest()[:8]}"

        opp = GrowthOpportunity(
            id=opp_id,
            type=type,
            source_opportunity_id=source_opportunity_id,
            source_contract_id=source_contract_id,
            title=title,
            description=description,
            estimated_value_usd=round(estimated_value, 2),
            probability=probability,
            tags=tags,
        )

        self.opportunities[opp_id] = opp
        self.stats['opportunities_identified'] += 1

        return opp

    def convert_opportunity(self, opportunity_id: str, actual_value: float = None) -> bool:
        """Mark growth opportunity as converted"""
        opp = self.opportunities.get(opportunity_id)
        if not opp:
            return False

        opp.status = "converted"
        opp.converted_at = datetime.now(timezone.utc).isoformat()

        value = actual_value or opp.estimated_value_usd
        self.stats['opportunities_converted'] += 1

        if opp.type == 'upsell':
            self.stats['upsell_value_usd'] += value
        elif opp.type == 'referral':
            self.stats['referral_value_usd'] += value

        logger.info(f"Converted growth opportunity {opportunity_id}: ${value}")

        return True

    def convert_referral(self, referral_id: str, referred_contract_value: float) -> bool:
        """Mark referral as converted and calculate rewards"""
        referral = self.referrals.get(referral_id)
        if not referral:
            return False

        referral.status = "converted"
        self.stats['referrals_converted'] += 1
        self.stats['referral_value_usd'] += referred_contract_value

        logger.info(f"Converted referral {referral_id}: ${referred_contract_value}")

        return True

    def get_pipeline(self) -> Dict[str, Any]:
        """Get growth pipeline summary"""
        by_status = {}
        by_type = {}

        for opp in self.opportunities.values():
            by_status[opp.status] = by_status.get(opp.status, 0) + 1
            by_type[opp.type] = by_type.get(opp.type, 0) + 1

        total_pipeline_value = sum(
            opp.estimated_value_usd * opp.probability
            for opp in self.opportunities.values()
            if opp.status == 'identified'
        )

        return {
            'total_opportunities': len(self.opportunities),
            'by_status': by_status,
            'by_type': by_type,
            'pipeline_value_usd': round(total_pipeline_value, 2),
            'pending_referrals': sum(1 for r in self.referrals.values() if r.status == 'pending'),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get growth loop stats"""
        return {
            **self.stats,
            'pipeline': self.get_pipeline(),
            'conversion_rate': round(
                self.stats['opportunities_converted'] / self.stats['opportunities_identified'] * 100, 1
            ) if self.stats['opportunities_identified'] > 0 else 0,
        }

    def to_dict(self, opp: GrowthOpportunity) -> Dict[str, Any]:
        """Convert growth opportunity to dict"""
        return {
            'id': opp.id,
            'type': opp.type,
            'source_opportunity_id': opp.source_opportunity_id,
            'source_contract_id': opp.source_contract_id,
            'title': opp.title,
            'description': opp.description,
            'estimated_value_usd': opp.estimated_value_usd,
            'probability': opp.probability,
            'status': opp.status,
            'created_at': opp.created_at,
            'converted_at': opp.converted_at,
            'tags': opp.tags,
        }


# Global instance
_growth_loops: Optional[GrowthLoops] = None


def get_growth_loops() -> GrowthLoops:
    """Get or create growth loops singleton"""
    global _growth_loops
    if _growth_loops is None:
        _growth_loops = GrowthLoops()
    return _growth_loops


def on_milestone_complete(opportunity: Dict, contract: Dict, milestone: Dict) -> List[GrowthOpportunity]:
    """Convenience function"""
    return get_growth_loops().on_milestone_complete(opportunity, contract, milestone)
