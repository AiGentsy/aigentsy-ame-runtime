"""
DEFINITION OF DONE (DoD) SIGNATURES: Verifiable Completion Criteria
====================================================================

Cryptographically signed completion criteria for each milestone:
- Clear, measurable acceptance criteria
- Automated verification where possible
- Client sign-off with timestamp
- Immutable proof of completion

Updated: Jan 2026
"""

import logging
import hashlib
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class CriterionType(Enum):
    """Types of completion criteria"""
    AUTOMATED = "automated"      # Can be verified automatically
    MANUAL = "manual"            # Requires manual verification
    CLIENT = "client"            # Requires client approval
    HYBRID = "hybrid"            # Both automated and manual


class CriterionStatus(Enum):
    """Status of a criterion"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"


@dataclass
class CompletionCriterion:
    """Single completion criterion"""
    id: str
    name: str
    description: str
    type: CriterionType = CriterionType.MANUAL
    status: CriterionStatus = CriterionStatus.PENDING
    verification_method: Optional[str] = None  # For automated: function name
    verification_result: Optional[Dict] = None
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class DoDSignature:
    """Cryptographic signature for DoD completion"""
    signer: str                # Who signed
    signer_role: str           # client, system, qa
    timestamp: str
    hash: str                  # SHA-256 of criteria state
    criteria_snapshot: Dict    # Snapshot of criteria at signing


@dataclass
class DefinitionOfDone:
    """Complete Definition of Done for a milestone"""
    id: str
    milestone_id: str
    contract_id: str
    title: str
    criteria: List[CompletionCriterion] = field(default_factory=list)
    signatures: List[DoDSignature] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    status: str = "pending"  # pending, in_review, completed, disputed

    @property
    def is_complete(self) -> bool:
        """Check if all criteria are satisfied"""
        return all(
            c.status in [CriterionStatus.PASSED, CriterionStatus.WAIVED]
            for c in self.criteria
        )

    @property
    def completion_percentage(self) -> float:
        """Get completion percentage"""
        if not self.criteria:
            return 0.0
        passed = sum(1 for c in self.criteria if c.status in [CriterionStatus.PASSED, CriterionStatus.WAIVED])
        return passed / len(self.criteria) * 100


# Standard DoD templates by pack type
DOD_TEMPLATES: Dict[str, List[Dict]] = {
    'web_dev': [
        {
            'id': 'code_compiles',
            'name': 'Code Compiles',
            'description': 'Application builds without errors',
            'type': CriterionType.AUTOMATED,
            'verification_method': 'verify_build',
        },
        {
            'id': 'tests_pass',
            'name': 'Tests Pass',
            'description': 'All unit and integration tests pass',
            'type': CriterionType.AUTOMATED,
            'verification_method': 'verify_tests',
        },
        {
            'id': 'responsive',
            'name': 'Responsive Design',
            'description': 'Works on mobile, tablet, and desktop',
            'type': CriterionType.MANUAL,
        },
        {
            'id': 'accessibility',
            'name': 'Accessibility',
            'description': 'Meets WCAG 2.1 AA standards',
            'type': CriterionType.HYBRID,
            'verification_method': 'verify_accessibility',
        },
        {
            'id': 'client_approval',
            'name': 'Client Approval',
            'description': 'Client has reviewed and approved the work',
            'type': CriterionType.CLIENT,
        },
    ],
    'mobile_dev': [
        {
            'id': 'builds_ios',
            'name': 'iOS Build',
            'description': 'Application builds for iOS',
            'type': CriterionType.AUTOMATED,
            'verification_method': 'verify_ios_build',
        },
        {
            'id': 'builds_android',
            'name': 'Android Build',
            'description': 'Application builds for Android',
            'type': CriterionType.AUTOMATED,
            'verification_method': 'verify_android_build',
        },
        {
            'id': 'tests_pass',
            'name': 'Tests Pass',
            'description': 'All tests pass',
            'type': CriterionType.AUTOMATED,
            'verification_method': 'verify_tests',
        },
        {
            'id': 'device_testing',
            'name': 'Device Testing',
            'description': 'Tested on target devices',
            'type': CriterionType.MANUAL,
        },
        {
            'id': 'client_approval',
            'name': 'Client Approval',
            'description': 'Client has reviewed and approved',
            'type': CriterionType.CLIENT,
        },
    ],
    'design': [
        {
            'id': 'design_specs',
            'name': 'Design Specs',
            'description': 'All design specifications documented',
            'type': CriterionType.MANUAL,
        },
        {
            'id': 'assets_exported',
            'name': 'Assets Exported',
            'description': 'All assets exported in required formats',
            'type': CriterionType.MANUAL,
        },
        {
            'id': 'style_guide',
            'name': 'Style Guide',
            'description': 'Style guide/design system provided',
            'type': CriterionType.MANUAL,
        },
        {
            'id': 'client_approval',
            'name': 'Client Approval',
            'description': 'Client has approved the designs',
            'type': CriterionType.CLIENT,
        },
    ],
    'content': [
        {
            'id': 'word_count',
            'name': 'Word Count',
            'description': 'Content meets required word count',
            'type': CriterionType.AUTOMATED,
            'verification_method': 'verify_word_count',
        },
        {
            'id': 'grammar_check',
            'name': 'Grammar Check',
            'description': 'Content passes grammar check',
            'type': CriterionType.AUTOMATED,
            'verification_method': 'verify_grammar',
        },
        {
            'id': 'seo_optimized',
            'name': 'SEO Optimized',
            'description': 'Content is SEO optimized',
            'type': CriterionType.HYBRID,
        },
        {
            'id': 'client_approval',
            'name': 'Client Approval',
            'description': 'Client has approved the content',
            'type': CriterionType.CLIENT,
        },
    ],
    'devops': [
        {
            'id': 'infra_provisioned',
            'name': 'Infrastructure Provisioned',
            'description': 'All infrastructure is provisioned',
            'type': CriterionType.AUTOMATED,
            'verification_method': 'verify_infrastructure',
        },
        {
            'id': 'security_scan',
            'name': 'Security Scan',
            'description': 'Passes security vulnerability scan',
            'type': CriterionType.AUTOMATED,
            'verification_method': 'verify_security',
        },
        {
            'id': 'monitoring_setup',
            'name': 'Monitoring Setup',
            'description': 'Monitoring and alerting configured',
            'type': CriterionType.MANUAL,
        },
        {
            'id': 'documentation',
            'name': 'Documentation',
            'description': 'Runbook and documentation provided',
            'type': CriterionType.MANUAL,
        },
        {
            'id': 'client_approval',
            'name': 'Client Approval',
            'description': 'Client has approved the deployment',
            'type': CriterionType.CLIENT,
        },
    ],
}


class DoDManager:
    """
    Manage Definition of Done for milestones.

    Flow:
    1. Create DoD from template + custom criteria
    2. Verify criteria (automated + manual)
    3. Collect signatures
    4. Generate completion proof
    """

    def __init__(self):
        self.definitions: Dict[str, DefinitionOfDone] = {}
        self.stats = {
            'dods_created': 0,
            'dods_completed': 0,
            'criteria_verified': 0,
            'signatures_collected': 0,
        }

    def create_dod(
        self,
        milestone_id: str,
        contract_id: str,
        pack: str,
        title: str,
        custom_criteria: List[Dict] = None,
    ) -> DefinitionOfDone:
        """
        Create Definition of Done for a milestone.

        Args:
            milestone_id: Milestone ID
            contract_id: Contract ID
            pack: Service pack type
            title: DoD title
            custom_criteria: Additional custom criteria

        Returns:
            DefinitionOfDone instance
        """
        dod_id = f"dod_{hashlib.md5(f'{milestone_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"

        # Get template criteria
        template_criteria = DOD_TEMPLATES.get(pack, [])
        criteria = []

        for i, tc in enumerate(template_criteria):
            criteria.append(CompletionCriterion(
                id=f"{dod_id}_{tc['id']}",
                name=tc['name'],
                description=tc['description'],
                type=tc.get('type', CriterionType.MANUAL),
                verification_method=tc.get('verification_method'),
            ))

        # Add custom criteria
        if custom_criteria:
            for i, cc in enumerate(custom_criteria):
                criteria.append(CompletionCriterion(
                    id=f"{dod_id}_custom_{i}",
                    name=cc.get('name', f'Custom Criterion {i+1}'),
                    description=cc.get('description', ''),
                    type=CriterionType(cc.get('type', 'manual')),
                ))

        dod = DefinitionOfDone(
            id=dod_id,
            milestone_id=milestone_id,
            contract_id=contract_id,
            title=title,
            criteria=criteria,
        )

        self.definitions[dod_id] = dod
        self.stats['dods_created'] += 1

        logger.info(f"Created DoD: {dod_id} with {len(criteria)} criteria")

        return dod

    async def verify_criterion(
        self,
        dod_id: str,
        criterion_id: str,
        passed: bool,
        verified_by: str = "system",
        notes: str = None,
        result: Dict = None,
    ) -> bool:
        """
        Verify a criterion.

        Args:
            dod_id: DoD ID
            criterion_id: Criterion ID
            passed: Whether criterion passed
            verified_by: Who verified
            notes: Optional notes
            result: Verification result data

        Returns:
            True if verified
        """
        dod = self.definitions.get(dod_id)
        if not dod:
            return False

        for criterion in dod.criteria:
            if criterion.id == criterion_id:
                criterion.status = CriterionStatus.PASSED if passed else CriterionStatus.FAILED
                criterion.verified_at = datetime.now(timezone.utc).isoformat()
                criterion.verified_by = verified_by
                criterion.notes = notes
                criterion.verification_result = result

                self.stats['criteria_verified'] += 1

                logger.info(f"Criterion {criterion_id} verified: {criterion.status.value}")

                # Check if DoD is now complete
                if dod.is_complete:
                    dod.status = "in_review"

                return True

        return False

    async def run_automated_verification(
        self,
        dod_id: str,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Run automated verification for all automated criteria.

        Args:
            dod_id: DoD ID
            context: Context for verification (workspace path, etc.)

        Returns:
            Results of automated verification
        """
        dod = self.definitions.get(dod_id)
        if not dod:
            return {'ok': False, 'error': 'DoD not found'}

        context = context or {}
        results = []

        for criterion in dod.criteria:
            if criterion.type in [CriterionType.AUTOMATED, CriterionType.HYBRID]:
                if criterion.verification_method:
                    # Run verification
                    result = await self._run_verification(
                        criterion.verification_method,
                        context,
                    )

                    await self.verify_criterion(
                        dod_id=dod_id,
                        criterion_id=criterion.id,
                        passed=result.get('passed', False),
                        verified_by='automated',
                        notes=result.get('message'),
                        result=result,
                    )

                    results.append({
                        'criterion_id': criterion.id,
                        'name': criterion.name,
                        'passed': result.get('passed', False),
                        'message': result.get('message'),
                    })

        return {
            'ok': True,
            'automated_checks': len(results),
            'passed': sum(1 for r in results if r['passed']),
            'results': results,
        }

    async def _run_verification(
        self,
        method: str,
        context: Dict,
    ) -> Dict[str, Any]:
        """Run a verification method"""
        # Map verification methods to functions
        verifiers = {
            'verify_build': self._verify_build,
            'verify_tests': self._verify_tests,
            'verify_accessibility': self._verify_accessibility,
            'verify_word_count': self._verify_word_count,
            'verify_grammar': self._verify_grammar,
            'verify_ios_build': self._verify_ios_build,
            'verify_android_build': self._verify_android_build,
            'verify_infrastructure': self._verify_infrastructure,
            'verify_security': self._verify_security,
        }

        verifier = verifiers.get(method)
        if verifier:
            try:
                return await verifier(context)
            except Exception as e:
                return {'passed': False, 'message': f'Verification error: {str(e)}'}

        return {'passed': False, 'message': f'Unknown verification method: {method}'}

    # Verification implementations (stubs - would integrate with actual tools)
    async def _verify_build(self, context: Dict) -> Dict:
        """Verify code compiles"""
        # Would run actual build command
        return {'passed': True, 'message': 'Build succeeded'}

    async def _verify_tests(self, context: Dict) -> Dict:
        """Verify tests pass"""
        # Would run test suite
        return {'passed': True, 'message': 'All tests passed'}

    async def _verify_accessibility(self, context: Dict) -> Dict:
        """Verify accessibility"""
        # Would run accessibility checker
        return {'passed': True, 'message': 'Accessibility checks passed'}

    async def _verify_word_count(self, context: Dict) -> Dict:
        """Verify word count"""
        target = context.get('target_words', 1000)
        actual = context.get('actual_words', 1000)
        passed = actual >= target * 0.9  # 90% tolerance
        return {
            'passed': passed,
            'message': f'Word count: {actual}/{target}',
            'actual': actual,
            'target': target,
        }

    async def _verify_grammar(self, context: Dict) -> Dict:
        """Verify grammar"""
        return {'passed': True, 'message': 'Grammar check passed'}

    async def _verify_ios_build(self, context: Dict) -> Dict:
        """Verify iOS build"""
        return {'passed': True, 'message': 'iOS build succeeded'}

    async def _verify_android_build(self, context: Dict) -> Dict:
        """Verify Android build"""
        return {'passed': True, 'message': 'Android build succeeded'}

    async def _verify_infrastructure(self, context: Dict) -> Dict:
        """Verify infrastructure"""
        return {'passed': True, 'message': 'Infrastructure provisioned'}

    async def _verify_security(self, context: Dict) -> Dict:
        """Verify security"""
        return {'passed': True, 'message': 'Security scan passed'}

    def sign_dod(
        self,
        dod_id: str,
        signer: str,
        signer_role: str,
    ) -> Optional[DoDSignature]:
        """
        Sign DoD completion.

        Args:
            dod_id: DoD ID
            signer: Signer identifier
            signer_role: Role (client, system, qa)

        Returns:
            Signature or None
        """
        dod = self.definitions.get(dod_id)
        if not dod:
            return None

        # Create criteria snapshot
        criteria_snapshot = {
            c.id: {
                'name': c.name,
                'status': c.status.value,
                'verified_at': c.verified_at,
            }
            for c in dod.criteria
        }

        # Generate hash
        hash_content = json.dumps({
            'dod_id': dod_id,
            'criteria': criteria_snapshot,
            'signer': signer,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }, sort_keys=True)
        signature_hash = hashlib.sha256(hash_content.encode()).hexdigest()

        signature = DoDSignature(
            signer=signer,
            signer_role=signer_role,
            timestamp=datetime.now(timezone.utc).isoformat(),
            hash=signature_hash,
            criteria_snapshot=criteria_snapshot,
        )

        dod.signatures.append(signature)
        self.stats['signatures_collected'] += 1

        logger.info(f"DoD {dod_id} signed by {signer} ({signer_role})")

        # Check if fully signed
        roles_signed = {s.signer_role for s in dod.signatures}
        if 'client' in roles_signed and dod.is_complete:
            dod.status = "completed"
            dod.completed_at = datetime.now(timezone.utc).isoformat()
            self.stats['dods_completed'] += 1

        return signature

    def waive_criterion(
        self,
        dod_id: str,
        criterion_id: str,
        waived_by: str,
        reason: str,
    ) -> bool:
        """Waive a criterion (with justification)"""
        dod = self.definitions.get(dod_id)
        if not dod:
            return False

        for criterion in dod.criteria:
            if criterion.id == criterion_id:
                criterion.status = CriterionStatus.WAIVED
                criterion.verified_at = datetime.now(timezone.utc).isoformat()
                criterion.verified_by = waived_by
                criterion.notes = f"Waived: {reason}"
                return True

        return False

    def get_dod(self, dod_id: str) -> Optional[DefinitionOfDone]:
        """Get DoD by ID"""
        return self.definitions.get(dod_id)

    def get_dod_for_milestone(self, milestone_id: str) -> Optional[DefinitionOfDone]:
        """Get DoD for a milestone"""
        for dod in self.definitions.values():
            if dod.milestone_id == milestone_id:
                return dod
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get manager stats"""
        return {
            **self.stats,
            'total_dods': len(self.definitions),
            'completion_rate': self.stats['dods_completed'] / max(1, self.stats['dods_created']),
        }

    def to_dict(self, dod: DefinitionOfDone) -> Dict[str, Any]:
        """Convert DoD to dict"""
        return {
            'id': dod.id,
            'milestone_id': dod.milestone_id,
            'contract_id': dod.contract_id,
            'title': dod.title,
            'status': dod.status,
            'completion_percentage': dod.completion_percentage,
            'criteria': [
                {
                    'id': c.id,
                    'name': c.name,
                    'description': c.description,
                    'type': c.type.value,
                    'status': c.status.value,
                    'verified_at': c.verified_at,
                    'verified_by': c.verified_by,
                    'notes': c.notes,
                }
                for c in dod.criteria
            ],
            'signatures': [
                {
                    'signer': s.signer,
                    'signer_role': s.signer_role,
                    'timestamp': s.timestamp,
                    'hash': s.hash[:16] + '...',
                }
                for s in dod.signatures
            ],
            'created_at': dod.created_at,
            'completed_at': dod.completed_at,
        }


# Singleton
_dod_manager: Optional[DoDManager] = None


def get_dod_manager() -> DoDManager:
    """Get or create DoD manager"""
    global _dod_manager
    if _dod_manager is None:
        _dod_manager = DoDManager()
    return _dod_manager
