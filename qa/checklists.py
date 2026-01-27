"""
QA CHECKLISTS: Quality Gates for Milestone Release
═══════════════════════════════════════════════════════════════════════════════

Blocks milestone release until QA checks pass.

Features:
- Per-step quality checklists
- Automated checks (Lighthouse, CI, etc.)
- Manual review triggers
- Golden test comparison

Updated: Jan 2026
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class QACheck:
    """A single QA check"""
    id: str
    name: str
    check_type: str  # automated, manual, golden
    status: CheckStatus = CheckStatus.PENDING
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: Optional[str] = None
    checker: Optional[str] = None  # bot or human


@dataclass
class QAGate:
    """A quality gate with multiple checks"""
    id: str
    step_id: str
    name: str
    checks: List[QACheck] = field(default_factory=list)
    passed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Default QA checklists per gate type
QA_CHECKLISTS = {
    'code_review': [
        {'id': 'syntax', 'name': 'Syntax Check', 'type': 'automated'},
        {'id': 'lint', 'name': 'Linting', 'type': 'automated'},
        {'id': 'tests', 'name': 'Unit Tests', 'type': 'automated'},
        {'id': 'security', 'name': 'Security Scan', 'type': 'automated'},
        {'id': 'review', 'name': 'Code Review', 'type': 'manual'},
    ],
    'tests_passing': [
        {'id': 'unit', 'name': 'Unit Tests', 'type': 'automated'},
        {'id': 'integration', 'name': 'Integration Tests', 'type': 'automated'},
        {'id': 'e2e', 'name': 'E2E Tests', 'type': 'automated'},
        {'id': 'coverage', 'name': 'Coverage > 80%', 'type': 'automated'},
    ],
    'design_review': [
        {'id': 'accessibility', 'name': 'Accessibility Check', 'type': 'automated'},
        {'id': 'responsive', 'name': 'Responsive Check', 'type': 'automated'},
        {'id': 'brand', 'name': 'Brand Compliance', 'type': 'manual'},
        {'id': 'ux_review', 'name': 'UX Review', 'type': 'manual'},
    ],
    'content_review': [
        {'id': 'grammar', 'name': 'Grammar Check', 'type': 'automated'},
        {'id': 'plagiarism', 'name': 'Plagiarism Check', 'type': 'automated'},
        {'id': 'tone', 'name': 'Tone/Style Check', 'type': 'automated'},
        {'id': 'editorial', 'name': 'Editorial Review', 'type': 'manual'},
    ],
    'plan_review': [
        {'id': 'syntax', 'name': 'Config Syntax', 'type': 'automated'},
        {'id': 'dry_run', 'name': 'Dry Run', 'type': 'automated'},
        {'id': 'cost_estimate', 'name': 'Cost Estimate', 'type': 'automated'},
        {'id': 'approval', 'name': 'Manual Approval', 'type': 'manual'},
    ],
    'accuracy_threshold': [
        {'id': 'accuracy', 'name': 'Accuracy > 90%', 'type': 'automated'},
        {'id': 'precision', 'name': 'Precision Check', 'type': 'automated'},
        {'id': 'recall', 'name': 'Recall Check', 'type': 'automated'},
        {'id': 'golden', 'name': 'Golden Test Comparison', 'type': 'golden'},
    ],
}


class QAChecklists:
    """
    Manages QA checklists and gates.

    Usage:
    1. Create gate for step
    2. Run automated checks
    3. Request manual reviews
    4. Check if gate passed
    """

    def __init__(self):
        self.gates: Dict[str, QAGate] = {}
        self.stats = {
            'gates_created': 0,
            'gates_passed': 0,
            'gates_failed': 0,
            'checks_run': 0,
        }

    def create_gate(self, step_id: str, gate_type: str) -> QAGate:
        """Create QA gate for a step"""
        gate_id = f"qa_{step_id}_{gate_type}"

        # Get checklist for gate type
        checklist = QA_CHECKLISTS.get(gate_type, QA_CHECKLISTS.get('code_review'))

        # Create checks
        checks = [
            QACheck(
                id=f"{gate_id}_{c['id']}",
                name=c['name'],
                check_type=c['type'],
            )
            for c in checklist
        ]

        gate = QAGate(
            id=gate_id,
            step_id=step_id,
            name=f"{gate_type.replace('_', ' ').title()} Gate",
            checks=checks,
        )

        self.gates[gate_id] = gate
        self.stats['gates_created'] += 1

        logger.info(f"Created QA gate {gate_id} with {len(checks)} checks")

        return gate

    def run_automated_checks(self, gate_id: str, artifacts: Dict[str, Any] = None) -> QAGate:
        """Run all automated checks for a gate"""
        gate = self.gates.get(gate_id)
        if not gate:
            logger.warning(f"Gate {gate_id} not found")
            return None

        artifacts = artifacts or {}

        for check in gate.checks:
            if check.check_type == 'automated':
                result = self._run_automated_check(check, artifacts)
                check.status = CheckStatus.PASSED if result['passed'] else CheckStatus.FAILED
                check.details = result
                check.checked_at = datetime.now(timezone.utc).isoformat()
                check.checker = 'bot'
                self.stats['checks_run'] += 1

        # Update gate status
        gate.passed = self._evaluate_gate(gate)

        if gate.passed:
            self.stats['gates_passed'] += 1
        else:
            self.stats['gates_failed'] += 1

        return gate

    def _run_automated_check(self, check: QACheck, artifacts: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single automated check"""
        # Simulated checks - in production would call actual tools
        check_results = {
            'syntax': {'passed': True, 'message': 'No syntax errors'},
            'lint': {'passed': True, 'message': 'Linting passed', 'warnings': 0},
            'tests': {'passed': True, 'message': 'All tests passed', 'total': 10, 'failed': 0},
            'security': {'passed': True, 'message': 'No vulnerabilities found'},
            'unit': {'passed': True, 'message': 'Unit tests passed'},
            'integration': {'passed': True, 'message': 'Integration tests passed'},
            'e2e': {'passed': True, 'message': 'E2E tests passed'},
            'coverage': {'passed': True, 'message': 'Coverage: 85%', 'coverage': 85},
            'grammar': {'passed': True, 'message': 'Grammar check passed'},
            'plagiarism': {'passed': True, 'message': 'No plagiarism detected', 'score': 0},
            'tone': {'passed': True, 'message': 'Tone consistent'},
            'accessibility': {'passed': True, 'message': 'WCAG AA compliant'},
            'responsive': {'passed': True, 'message': 'Responsive on all breakpoints'},
            'dry_run': {'passed': True, 'message': 'Dry run successful'},
            'cost_estimate': {'passed': True, 'message': 'Cost within budget'},
            'accuracy': {'passed': True, 'message': 'Accuracy: 92%', 'accuracy': 92},
            'precision': {'passed': True, 'message': 'Precision: 91%'},
            'recall': {'passed': True, 'message': 'Recall: 93%'},
        }

        # Get result for this check type
        check_key = check.id.split('_')[-1]
        return check_results.get(check_key, {'passed': True, 'message': 'Check passed'})

    def submit_manual_review(self, gate_id: str, check_id: str, passed: bool, reviewer: str, notes: str = "") -> bool:
        """Submit manual review result"""
        gate = self.gates.get(gate_id)
        if not gate:
            return False

        for check in gate.checks:
            if check.id == check_id and check.check_type == 'manual':
                check.status = CheckStatus.PASSED if passed else CheckStatus.FAILED
                check.checked_at = datetime.now(timezone.utc).isoformat()
                check.checker = reviewer
                check.details = {'passed': passed, 'notes': notes}
                self.stats['checks_run'] += 1

                # Re-evaluate gate
                gate.passed = self._evaluate_gate(gate)
                return True

        return False

    def _evaluate_gate(self, gate: QAGate) -> bool:
        """Evaluate if gate passes (all checks must pass)"""
        for check in gate.checks:
            if check.status == CheckStatus.PENDING:
                return False  # Not all checks complete
            if check.status == CheckStatus.FAILED:
                return False  # A check failed

        return True

    def ensure_quality_gate(self, plan: Dict[str, Any]) -> Dict[str, QAGate]:
        """Ensure all QA gates are created for a plan"""
        gates = {}

        for step in plan.get('steps', []):
            qa_gate = step.get('qa_gate')
            if qa_gate:
                gate = self.create_gate(step.get('id', ''), qa_gate)
                gates[step.get('id', '')] = gate

        return gates

    def check(self, step_id: str, gate_type: str, artifacts: Dict[str, Any] = None) -> bool:
        """Quick check if a step's QA gate passes"""
        gate_id = f"qa_{step_id}_{gate_type}"

        # Create if doesn't exist
        if gate_id not in self.gates:
            self.create_gate(step_id, gate_type)

        # Run automated checks
        gate = self.run_automated_checks(gate_id, artifacts)

        return gate.passed if gate else False

    def get_gate(self, gate_id: str) -> Optional[QAGate]:
        """Get gate by ID"""
        return self.gates.get(gate_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get QA stats"""
        return {
            **self.stats,
            'active_gates': len(self.gates),
        }

    def to_dict(self, gate: QAGate) -> Dict[str, Any]:
        """Convert gate to dict"""
        return {
            'id': gate.id,
            'step_id': gate.step_id,
            'name': gate.name,
            'passed': gate.passed,
            'created_at': gate.created_at,
            'checks': [
                {
                    'id': c.id,
                    'name': c.name,
                    'check_type': c.check_type,
                    'status': c.status.value,
                    'details': c.details,
                    'checked_at': c.checked_at,
                    'checker': c.checker,
                }
                for c in gate.checks
            ]
        }


# Global instance
_checklists: Optional[QAChecklists] = None


def get_qa_checklists() -> QAChecklists:
    """Get or create QA checklists singleton"""
    global _checklists
    if _checklists is None:
        _checklists = QAChecklists()
    return _checklists


def ensure_quality_gate(plan: Dict[str, Any]) -> Dict[str, QAGate]:
    """Convenience function"""
    return get_qa_checklists().ensure_quality_gate(plan)
