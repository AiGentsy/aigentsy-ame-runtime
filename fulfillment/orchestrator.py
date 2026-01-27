"""
FULFILLMENT ORCHESTRATOR: Runbook → PDL Auto-Orchestration
═══════════════════════════════════════════════════════════════════════════════

Converts offer packs into executable DAGs mapped to PDLs/Universal Fabric.

Features:
- Auto-generates execution plans from runbooks
- Maps steps to PDL actions
- Tracks progress and artifacts
- Integrates QA gates

Updated: Jan 2026
"""

import logging
import yaml
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """A single step in the execution plan"""
    id: str
    name: str
    description: str
    pdl_action: Optional[str] = None  # e.g., "github.post_comment"
    fabric_action: Optional[str] = None  # For universal fabric
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    sla_minutes: int = 60
    qa_gate: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Complete execution plan for an opportunity"""
    opportunity_id: str
    offer_pack: str
    steps: List[ExecutionStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_sla_minutes: int = 0
    estimated_cost_usd: float = 0.0
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)


# Default runbook definitions per offer pack
DEFAULT_RUNBOOKS = {
    'web_dev': {
        'name': 'Web Development',
        'sla_hours': 24,
        'steps': [
            {
                'id': 'analyze',
                'name': 'Analyze Requirements',
                'description': 'Analyze the opportunity requirements',
                'pdl_action': 'ai.analyze_requirements',
                'sla_minutes': 30,
            },
            {
                'id': 'plan',
                'name': 'Create Implementation Plan',
                'description': 'Create detailed implementation plan',
                'pdl_action': 'ai.create_plan',
                'sla_minutes': 30,
                'dependencies': ['analyze'],
            },
            {
                'id': 'implement',
                'name': 'Implement Solution',
                'description': 'Build the web application/feature',
                'fabric_action': 'code_generation',
                'sla_minutes': 480,
                'dependencies': ['plan'],
                'qa_gate': 'code_review',
            },
            {
                'id': 'test',
                'name': 'Test Solution',
                'description': 'Run tests and verify functionality',
                'pdl_action': 'ci.run_tests',
                'sla_minutes': 60,
                'dependencies': ['implement'],
                'qa_gate': 'tests_passing',
            },
            {
                'id': 'deliver',
                'name': 'Deliver Artifact',
                'description': 'Submit PR or deliver code package',
                'pdl_action': 'github.submit_pr',
                'sla_minutes': 30,
                'dependencies': ['test'],
            },
        ]
    },
    'mobile_dev': {
        'name': 'Mobile Development',
        'sla_hours': 48,
        'steps': [
            {'id': 'analyze', 'name': 'Analyze Requirements', 'pdl_action': 'ai.analyze_requirements', 'sla_minutes': 60},
            {'id': 'design', 'name': 'UI/UX Design', 'fabric_action': 'design_generation', 'sla_minutes': 120, 'dependencies': ['analyze']},
            {'id': 'implement', 'name': 'Implement App', 'fabric_action': 'mobile_code_generation', 'sla_minutes': 960, 'dependencies': ['design'], 'qa_gate': 'code_review'},
            {'id': 'test', 'name': 'Test on Devices', 'pdl_action': 'ci.mobile_tests', 'sla_minutes': 120, 'dependencies': ['implement']},
            {'id': 'deliver', 'name': 'Deliver Build', 'pdl_action': 'ci.create_build', 'sla_minutes': 60, 'dependencies': ['test']},
        ]
    },
    'data_ml': {
        'name': 'Data & ML',
        'sla_hours': 72,
        'steps': [
            {'id': 'analyze', 'name': 'Data Analysis', 'pdl_action': 'ai.analyze_data', 'sla_minutes': 120},
            {'id': 'model', 'name': 'Model Development', 'fabric_action': 'ml_pipeline', 'sla_minutes': 480, 'dependencies': ['analyze']},
            {'id': 'train', 'name': 'Model Training', 'fabric_action': 'ml_training', 'sla_minutes': 240, 'dependencies': ['model']},
            {'id': 'evaluate', 'name': 'Evaluate Results', 'pdl_action': 'ai.evaluate_model', 'sla_minutes': 60, 'dependencies': ['train'], 'qa_gate': 'accuracy_threshold'},
            {'id': 'deliver', 'name': 'Deliver Model', 'pdl_action': 'storage.upload_artifact', 'sla_minutes': 30, 'dependencies': ['evaluate']},
        ]
    },
    'devops': {
        'name': 'DevOps & Cloud',
        'sla_hours': 12,
        'steps': [
            {'id': 'analyze', 'name': 'Analyze Infrastructure', 'pdl_action': 'ai.analyze_infra', 'sla_minutes': 30},
            {'id': 'plan', 'name': 'Create Terraform/IaC', 'fabric_action': 'iac_generation', 'sla_minutes': 120, 'dependencies': ['analyze']},
            {'id': 'apply', 'name': 'Apply Changes', 'pdl_action': 'ci.terraform_apply', 'sla_minutes': 60, 'dependencies': ['plan'], 'qa_gate': 'plan_review'},
            {'id': 'verify', 'name': 'Verify Deployment', 'pdl_action': 'ci.health_check', 'sla_minutes': 30, 'dependencies': ['apply']},
        ]
    },
    'design': {
        'name': 'Design & UX',
        'sla_hours': 24,
        'steps': [
            {'id': 'research', 'name': 'UX Research', 'pdl_action': 'ai.ux_research', 'sla_minutes': 60},
            {'id': 'wireframe', 'name': 'Create Wireframes', 'fabric_action': 'design_wireframes', 'sla_minutes': 120, 'dependencies': ['research']},
            {'id': 'design', 'name': 'High-Fidelity Design', 'fabric_action': 'design_hifi', 'sla_minutes': 240, 'dependencies': ['wireframe'], 'qa_gate': 'design_review'},
            {'id': 'deliver', 'name': 'Export Assets', 'pdl_action': 'design.export_assets', 'sla_minutes': 30, 'dependencies': ['design']},
        ]
    },
    'writing': {
        'name': 'Writing & Content',
        'sla_hours': 6,
        'steps': [
            {'id': 'research', 'name': 'Research Topic', 'pdl_action': 'ai.research_topic', 'sla_minutes': 30},
            {'id': 'outline', 'name': 'Create Outline', 'pdl_action': 'ai.create_outline', 'sla_minutes': 15, 'dependencies': ['research']},
            {'id': 'draft', 'name': 'Write Draft', 'fabric_action': 'content_generation', 'sla_minutes': 60, 'dependencies': ['outline']},
            {'id': 'edit', 'name': 'Edit & Polish', 'pdl_action': 'ai.edit_content', 'sla_minutes': 30, 'dependencies': ['draft'], 'qa_gate': 'content_review'},
            {'id': 'deliver', 'name': 'Deliver Content', 'pdl_action': 'storage.upload_document', 'sla_minutes': 10, 'dependencies': ['edit']},
        ]
    },
    'automation': {
        'name': 'Automation & Scripting',
        'sla_hours': 8,
        'steps': [
            {'id': 'analyze', 'name': 'Analyze Workflow', 'pdl_action': 'ai.analyze_workflow', 'sla_minutes': 30},
            {'id': 'script', 'name': 'Write Script', 'fabric_action': 'script_generation', 'sla_minutes': 120, 'dependencies': ['analyze']},
            {'id': 'test', 'name': 'Test Automation', 'pdl_action': 'ci.run_script_tests', 'sla_minutes': 60, 'dependencies': ['script'], 'qa_gate': 'tests_passing'},
            {'id': 'deploy', 'name': 'Deploy Automation', 'pdl_action': 'ci.deploy_script', 'sla_minutes': 30, 'dependencies': ['test']},
        ]
    },
}


class FulfillmentOrchestrator:
    """
    Orchestrates fulfillment from offer pack to execution plan.

    Workflow:
    1. Match opportunity to offer pack
    2. Load runbook for pack
    3. Generate execution plan (DAG of steps)
    4. Map steps to PDLs/Fabric actions
    5. Track execution progress
    """

    def __init__(self):
        self.runbooks = DEFAULT_RUNBOOKS.copy()
        self._load_yaml_runbooks()
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.stats = {
            'plans_created': 0,
            'plans_completed': 0,
            'plans_failed': 0,
            'avg_completion_minutes': 0,
        }

    def _load_yaml_runbooks(self):
        """Load custom runbooks from YAML files"""
        runbook_dir = os.path.join(os.path.dirname(__file__), 'runbooks')
        if os.path.exists(runbook_dir):
            for filename in os.listdir(runbook_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    filepath = os.path.join(runbook_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            runbook = yaml.safe_load(f)
                            if runbook and 'id' in runbook:
                                self.runbooks[runbook['id']] = runbook
                                logger.info(f"Loaded runbook: {runbook['id']}")
                    except Exception as e:
                        logger.warning(f"Failed to load runbook {filename}: {e}")

    def plan_from_offerpack(self, opportunity: Dict[str, Any]) -> ExecutionPlan:
        """
        Generate execution plan from opportunity and matched offer pack.

        Args:
            opportunity: The opportunity dict with enrichment data

        Returns:
            ExecutionPlan with steps mapped to PDLs
        """
        opp_id = opportunity.get('id', 'unknown')

        # Determine best offer pack
        inventory_scores = opportunity.get('enrichment', {}).get('inventory_scores', {})
        if inventory_scores:
            best_pack = max(inventory_scores.items(), key=lambda x: x[1])[0]
        else:
            best_pack = 'web_dev'  # Default

        # Get runbook
        runbook = self.runbooks.get(best_pack, self.runbooks.get('web_dev'))

        # Create plan
        plan = ExecutionPlan(
            opportunity_id=opp_id,
            offer_pack=best_pack,
            metadata={
                'opportunity_title': opportunity.get('title', ''),
                'opportunity_url': opportunity.get('url', ''),
                'platform': opportunity.get('platform', ''),
                'runbook_name': runbook.get('name', best_pack),
            }
        )

        # Convert runbook steps to execution steps
        for step_def in runbook.get('steps', []):
            step = ExecutionStep(
                id=step_def.get('id', ''),
                name=step_def.get('name', ''),
                description=step_def.get('description', step_def.get('name', '')),
                pdl_action=step_def.get('pdl_action'),
                fabric_action=step_def.get('fabric_action'),
                dependencies=step_def.get('dependencies', []),
                sla_minutes=step_def.get('sla_minutes', 60),
                qa_gate=step_def.get('qa_gate'),
                inputs=step_def.get('inputs', {}),
            )
            plan.steps.append(step)
            plan.total_sla_minutes += step.sla_minutes

        # Estimate cost
        plan.estimated_cost_usd = self._estimate_cost(plan)

        # Store plan
        self.active_plans[opp_id] = plan
        self.stats['plans_created'] += 1

        logger.info(f"Created plan for {opp_id}: {len(plan.steps)} steps, {plan.total_sla_minutes}min SLA")

        return plan

    def _estimate_cost(self, plan: ExecutionPlan) -> float:
        """Estimate execution cost"""
        cost = 0.0
        for step in plan.steps:
            if step.pdl_action:
                # PDL actions: ~$0.01-0.10 per call
                cost += 0.05
            if step.fabric_action:
                # Fabric actions: ~$0.10-1.00 per call
                cost += 0.50
        return round(cost, 2)

    def get_next_steps(self, plan: ExecutionPlan) -> List[ExecutionStep]:
        """Get steps ready to execute (dependencies met)"""
        completed_ids = {s.id for s in plan.steps if s.status == StepStatus.COMPLETED}

        ready = []
        for step in plan.steps:
            if step.status == StepStatus.PENDING:
                deps_met = all(d in completed_ids for d in step.dependencies)
                if deps_met:
                    ready.append(step)

        return ready

    def mark_step_complete(self, plan_id: str, step_id: str, artifacts: List[str] = None):
        """Mark a step as completed"""
        plan = self.active_plans.get(plan_id)
        if not plan:
            return

        for step in plan.steps:
            if step.id == step_id:
                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc).isoformat()
                step.artifacts = artifacts or []
                break

        # Check if plan is complete
        if all(s.status == StepStatus.COMPLETED for s in plan.steps):
            plan.status = 'completed'
            self.stats['plans_completed'] += 1

    def mark_step_failed(self, plan_id: str, step_id: str, error: str):
        """Mark a step as failed"""
        plan = self.active_plans.get(plan_id)
        if not plan:
            return

        for step in plan.steps:
            if step.id == step_id:
                step.status = StepStatus.FAILED
                step.error = error
                break

        plan.status = 'failed'
        self.stats['plans_failed'] += 1

    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get execution plan by ID"""
        return self.active_plans.get(plan_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator stats"""
        return {
            **self.stats,
            'active_plans': len(self.active_plans),
            'runbooks_loaded': len(self.runbooks),
        }

    def to_dict(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Convert plan to dict for API response"""
        return {
            'opportunity_id': plan.opportunity_id,
            'offer_pack': plan.offer_pack,
            'status': plan.status,
            'created_at': plan.created_at,
            'total_sla_minutes': plan.total_sla_minutes,
            'estimated_cost_usd': plan.estimated_cost_usd,
            'metadata': plan.metadata,
            'steps': [
                {
                    'id': s.id,
                    'name': s.name,
                    'description': s.description,
                    'pdl_action': s.pdl_action,
                    'fabric_action': s.fabric_action,
                    'dependencies': s.dependencies,
                    'sla_minutes': s.sla_minutes,
                    'qa_gate': s.qa_gate,
                    'status': s.status.value,
                    'started_at': s.started_at,
                    'completed_at': s.completed_at,
                    'artifacts': s.artifacts,
                    'error': s.error,
                }
                for s in plan.steps
            ]
        }


# Global instance
_orchestrator: Optional[FulfillmentOrchestrator] = None


def get_fulfillment_orchestrator() -> FulfillmentOrchestrator:
    """Get or create orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = FulfillmentOrchestrator()
    return _orchestrator


def plan_from_offerpack(opportunity: Dict[str, Any]) -> ExecutionPlan:
    """Convenience function to create plan"""
    return get_fulfillment_orchestrator().plan_from_offerpack(opportunity)
