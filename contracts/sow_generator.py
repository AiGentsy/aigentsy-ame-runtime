"""
SOW GENERATOR: One-Tap Statement of Work Generation
═══════════════════════════════════════════════════════════════════════════════

Generates professional SOWs from runbook plans.

Features:
- Auto-generates scope from plan steps
- Acceptance criteria from QA gates
- Milestone breakdown with timelines
- Redline-ready formatting

Updated: Jan 2026
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import hashlib
import json

logger = logging.getLogger(__name__)


@dataclass
class Milestone:
    """A milestone in the SOW"""
    id: str
    name: str
    description: str
    deliverables: List[str]
    acceptance_criteria: List[str]
    amount_usd: float
    due_date: str
    percentage: float = 0.0


@dataclass
class SOW:
    """Statement of Work"""
    id: str
    opportunity_id: str
    title: str
    scope: str
    deliverables: List[str]
    milestones: List[Milestone]
    total_amount_usd: float
    currency: str = "USD"
    start_date: str = ""
    end_date: str = ""
    terms: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "draft"
    signature_hash: Optional[str] = None


class SOWGenerator:
    """
    Generates Statements of Work from execution plans.

    Flow:
    1. Takes execution plan
    2. Extracts scope from steps
    3. Creates milestones from step groups
    4. Generates acceptance criteria from QA gates
    5. Returns formatted SOW
    """

    def __init__(self):
        self.sows: Dict[str, SOW] = {}
        self.stats = {
            'sows_generated': 0,
            'sows_signed': 0,
            'total_value_usd': 0.0,
        }

    def sow_from_plan(self, opportunity: Dict[str, Any], plan: Dict[str, Any]) -> SOW:
        """
        Generate SOW from opportunity and execution plan.

        Args:
            opportunity: The opportunity dict
            plan: Execution plan dict from orchestrator

        Returns:
            SOW object
        """
        opp_id = opportunity.get('id', 'unknown')

        # Generate SOW ID
        sow_id = f"sow_{hashlib.md5(f'{opp_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"

        # Extract title
        title = opportunity.get('title', 'Professional Services')
        if len(title) > 100:
            title = title[:97] + "..."

        # Calculate pricing
        base_value = opportunity.get('value', 1000)
        enrichment = opportunity.get('enrichment', {})

        # Apply pricing factors
        payment_proximity = enrichment.get('payment_proximity', 0.5)
        contact_score = enrichment.get('contact_score', 0.5)

        # Higher scores = can charge more
        price_multiplier = 0.8 + (payment_proximity * 0.2) + (contact_score * 0.2)
        total_amount = round(base_value * price_multiplier, 2)

        # Generate scope
        scope = self._generate_scope(opportunity, plan)

        # Generate deliverables
        deliverables = self._extract_deliverables(plan)

        # Generate milestones
        milestones = self._generate_milestones(plan, total_amount)

        # Calculate dates
        now = datetime.now(timezone.utc)
        total_sla_minutes = plan.get('total_sla_minutes', 1440)
        end_date = now + timedelta(minutes=total_sla_minutes)

        # Create SOW
        sow = SOW(
            id=sow_id,
            opportunity_id=opp_id,
            title=f"SOW: {title}",
            scope=scope,
            deliverables=deliverables,
            milestones=milestones,
            total_amount_usd=total_amount,
            start_date=now.isoformat(),
            end_date=end_date.isoformat(),
            terms={
                'payment_terms': 'Milestone-based, due upon acceptance',
                'revision_policy': '2 rounds of revisions included',
                'cancellation': '50% kill fee if cancelled after start',
                'ip_transfer': 'Full IP transfer upon final payment',
                'confidentiality': 'NDA terms apply',
            }
        )

        # Store
        self.sows[sow_id] = sow
        self.stats['sows_generated'] += 1
        self.stats['total_value_usd'] += total_amount

        logger.info(f"Generated SOW {sow_id}: ${total_amount} for {opp_id}")

        return sow

    def _generate_scope(self, opportunity: Dict[str, Any], plan: Dict[str, Any]) -> str:
        """Generate scope description"""
        title = opportunity.get('title', 'the requested deliverable')
        body = opportunity.get('body', '')[:500]
        pack = plan.get('offer_pack', 'professional services')

        scope = f"""This Statement of Work covers the delivery of {pack} services for: {title}.

The scope includes all activities necessary to complete the requested work as described in the original opportunity:

{body}

All work will be performed according to industry best practices and will include quality assurance checks at each milestone."""

        return scope

    def _extract_deliverables(self, plan: Dict[str, Any]) -> List[str]:
        """Extract deliverables from plan steps"""
        deliverables = []

        for step in plan.get('steps', []):
            step_name = step.get('name', '')
            if 'deliver' in step_name.lower():
                deliverables.append(f"Final {step.get('description', step_name)}")
            elif step.get('artifacts'):
                for artifact in step.get('artifacts', []):
                    deliverables.append(artifact)

        if not deliverables:
            # Default deliverables based on pack
            pack = plan.get('offer_pack', 'web_dev')
            default_deliverables = {
                'web_dev': ['Source code repository', 'Documentation', 'Deployment guide'],
                'mobile_dev': ['App source code', 'Build files', 'App store assets'],
                'data_ml': ['Trained model', 'Evaluation report', 'Integration code'],
                'devops': ['Infrastructure code', 'CI/CD pipeline', 'Runbook'],
                'design': ['Design files (Figma/Sketch)', 'Asset exports', 'Style guide'],
                'writing': ['Final document', 'Source files', 'Revision history'],
                'automation': ['Script files', 'Documentation', 'Test results'],
            }
            deliverables = default_deliverables.get(pack, ['Completed deliverable'])

        return deliverables

    def _generate_milestones(self, plan: Dict[str, Any], total_amount: float) -> List[Milestone]:
        """Generate milestones from plan steps"""
        milestones = []
        steps = plan.get('steps', [])

        if not steps:
            # Single milestone
            return [Milestone(
                id='m1',
                name='Project Completion',
                description='Full project delivery',
                deliverables=['All deliverables'],
                acceptance_criteria=['Client approval'],
                amount_usd=total_amount,
                due_date=(datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                percentage=100.0,
            )]

        # Group steps into milestones (roughly 2-4 milestones)
        num_milestones = min(4, max(2, len(steps) // 2))
        steps_per_milestone = len(steps) // num_milestones

        now = datetime.now(timezone.utc)
        cumulative_minutes = 0

        for i in range(num_milestones):
            start_idx = i * steps_per_milestone
            end_idx = start_idx + steps_per_milestone if i < num_milestones - 1 else len(steps)
            milestone_steps = steps[start_idx:end_idx]

            # Calculate milestone values
            milestone_sla = sum(s.get('sla_minutes', 60) for s in milestone_steps)
            cumulative_minutes += milestone_sla

            # Milestone percentage (front-loaded for lower risk)
            if i == 0:
                percentage = 30.0
            elif i == num_milestones - 1:
                percentage = 40.0
            else:
                percentage = 30.0 / (num_milestones - 2) if num_milestones > 2 else 30.0

            amount = round(total_amount * (percentage / 100), 2)

            # Extract acceptance criteria from QA gates
            acceptance_criteria = []
            for step in milestone_steps:
                if step.get('qa_gate'):
                    acceptance_criteria.append(f"Pass {step['qa_gate']} check")
            if not acceptance_criteria:
                acceptance_criteria = ['Client review and approval']

            milestone = Milestone(
                id=f'm{i+1}',
                name=f"Milestone {i+1}: {milestone_steps[0].get('name', 'Deliverable')}",
                description=', '.join(s.get('name', '') for s in milestone_steps),
                deliverables=[s.get('name', '') for s in milestone_steps],
                acceptance_criteria=acceptance_criteria,
                amount_usd=amount,
                due_date=(now + timedelta(minutes=cumulative_minutes)).isoformat(),
                percentage=percentage,
            )
            milestones.append(milestone)

        return milestones

    def sign_sow(self, sow_id: str, signature_data: Dict[str, Any]) -> Optional[SOW]:
        """Sign/accept a SOW"""
        sow = self.sows.get(sow_id)
        if not sow:
            return None

        # Generate signature hash
        sig_content = json.dumps({
            'sow_id': sow_id,
            'total': sow.total_amount_usd,
            'signed_at': datetime.now(timezone.utc).isoformat(),
            'signer': signature_data.get('signer', 'client'),
        }, sort_keys=True)

        sow.signature_hash = hashlib.sha256(sig_content.encode()).hexdigest()
        sow.status = 'signed'
        self.stats['sows_signed'] += 1

        logger.info(f"SOW {sow_id} signed: {sow.signature_hash[:16]}...")

        return sow

    def get_sow(self, sow_id: str) -> Optional[SOW]:
        """Get SOW by ID"""
        return self.sows.get(sow_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get generator stats"""
        return {
            **self.stats,
            'active_sows': len(self.sows),
        }

    def to_dict(self, sow: SOW) -> Dict[str, Any]:
        """Convert SOW to dict"""
        return {
            'id': sow.id,
            'opportunity_id': sow.opportunity_id,
            'title': sow.title,
            'scope': sow.scope,
            'deliverables': sow.deliverables,
            'milestones': [
                {
                    'id': m.id,
                    'name': m.name,
                    'description': m.description,
                    'deliverables': m.deliverables,
                    'acceptance_criteria': m.acceptance_criteria,
                    'amount_usd': m.amount_usd,
                    'due_date': m.due_date,
                    'percentage': m.percentage,
                }
                for m in sow.milestones
            ],
            'total_amount_usd': sow.total_amount_usd,
            'currency': sow.currency,
            'start_date': sow.start_date,
            'end_date': sow.end_date,
            'terms': sow.terms,
            'created_at': sow.created_at,
            'status': sow.status,
            'signature_hash': sow.signature_hash,
        }


# Global instance
_generator: Optional[SOWGenerator] = None


def get_sow_generator() -> SOWGenerator:
    """Get or create SOW generator singleton"""
    global _generator
    if _generator is None:
        _generator = SOWGenerator()
    return _generator


def sow_from_plan(opportunity: Dict[str, Any], plan: Dict[str, Any]) -> SOW:
    """Convenience function"""
    return get_sow_generator().sow_from_plan(opportunity, plan)
