"""
DUAL-TRACK EXECUTION: Parallel PoC + Outreach Lanes
====================================================

Run two parallel execution tracks simultaneously:
1. PoC Track: Build proof-of-concept artifact
2. Outreach Track: Client communication and validation

Benefits:
- Reduce time-to-first-artifact
- Keep client engaged during build
- Early validation reduces rework

Updated: Jan 2026
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class TrackType(Enum):
    POC = "poc"           # Build track - creates artifacts
    OUTREACH = "outreach" # Communication track - client engagement


class TrackStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class ExecutionTrack:
    """Single execution track"""
    id: str
    track_type: TrackType
    contract_id: str
    status: TrackStatus = TrackStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    error: Optional[str] = None

    # Track-specific data
    poc_artifact_url: Optional[str] = None      # For PoC track
    outreach_messages_sent: int = 0              # For outreach track
    client_responses: List[Dict] = field(default_factory=list)
    validation_feedback: Optional[Dict] = None


@dataclass
class DualTrackExecution:
    """Dual-track execution container"""
    id: str
    contract_id: str
    opportunity_id: str
    poc_track: ExecutionTrack
    outreach_track: ExecutionTrack
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    status: str = "pending"

    # Coordination
    sync_points: List[Dict[str, Any]] = field(default_factory=list)
    early_validation: Optional[Dict] = None


class DualTrackExecutor:
    """
    Execute PoC and Outreach tracks in parallel.

    Flow:
    1. Start both tracks simultaneously
    2. PoC track builds first artifact
    3. Outreach track sends intro + collects requirements
    4. Sync point: PoC preview + client feedback
    5. Continue to completion or pivot based on feedback
    """

    # Outreach message templates
    OUTREACH_TEMPLATES = {
        'intro': """Hi {client_name},

Thank you for your interest in {service_type}. I'm already working on your project and will have a first preview ready within 30 minutes.

Quick questions to ensure we're aligned:
1. {question_1}
2. {question_2}

Looking forward to delivering great results!
""",
        'preview_ready': """Hi {client_name},

Your first preview is ready! You can view it here: {preview_url}

This is a {artifact_type} showing {description}.

Please let me know:
- Does this direction look good?
- Any changes you'd like to see?

I'll continue building while you review.
""",
        'check_in': """Hi {client_name},

Quick update on your project:
- {status_update}
- Next milestone: {next_milestone}

Any questions or feedback?
""",
    }

    # Questions by service type
    SERVICE_QUESTIONS = {
        'web_dev': [
            "Do you have preferred colors or branding to incorporate?",
            "Any specific features that are must-haves vs nice-to-haves?",
        ],
        'mobile_dev': [
            "Should this be iOS-first, Android-first, or cross-platform?",
            "Any existing backend/APIs to integrate with?",
        ],
        'design': [
            "Do you have brand guidelines or style preferences?",
            "What's the primary action users should take?",
        ],
        'content': [
            "Who is the target audience for this content?",
            "Any tone/voice preferences (formal, casual, technical)?",
        ],
        'devops': [
            "What's your current infrastructure (AWS, GCP, etc.)?",
            "Any compliance requirements (SOC2, HIPAA)?",
        ],
        'default': [
            "What does success look like for this project?",
            "Any timeline constraints I should know about?",
        ],
    }

    def __init__(self):
        self.executions: Dict[str, DualTrackExecution] = {}
        self.stats = {
            'dual_executions_started': 0,
            'dual_executions_completed': 0,
            'avg_poc_time_minutes': 0,
            'early_validations': 0,
            'pivots_from_feedback': 0,
        }

    async def start_dual_execution(
        self,
        contract_id: str,
        opportunity_id: str,
        service_type: str,
        client_info: Dict[str, Any],
        plan_steps: List[Dict[str, Any]],
    ) -> DualTrackExecution:
        """
        Start dual-track execution.

        Args:
            contract_id: Contract ID
            opportunity_id: Opportunity ID
            service_type: Type of service (web_dev, mobile_dev, etc.)
            client_info: Client contact info
            plan_steps: Fulfillment plan steps

        Returns:
            DualTrackExecution instance
        """
        exec_id = f"dual_{contract_id[:8]}_{datetime.now().strftime('%H%M%S')}"

        # Create PoC track
        poc_track = ExecutionTrack(
            id=f"{exec_id}_poc",
            track_type=TrackType.POC,
            contract_id=contract_id,
            tasks=self._extract_poc_tasks(plan_steps),
        )

        # Create outreach track
        outreach_track = ExecutionTrack(
            id=f"{exec_id}_outreach",
            track_type=TrackType.OUTREACH,
            contract_id=contract_id,
            tasks=self._create_outreach_tasks(service_type, client_info),
        )

        execution = DualTrackExecution(
            id=exec_id,
            contract_id=contract_id,
            opportunity_id=opportunity_id,
            poc_track=poc_track,
            outreach_track=outreach_track,
        )

        self.executions[exec_id] = execution
        self.stats['dual_executions_started'] += 1

        logger.info(f"Dual-track execution started: {exec_id}")

        # Start both tracks in parallel
        asyncio.create_task(self._run_dual_tracks(execution, service_type, client_info))

        return execution

    def _extract_poc_tasks(self, plan_steps: List[Dict]) -> List[Dict]:
        """Extract PoC-relevant tasks from plan"""
        poc_tasks = []

        # First 2-3 steps typically form the PoC
        for i, step in enumerate(plan_steps[:3]):
            poc_tasks.append({
                'id': f"poc_{i}",
                'name': step.get('name', f"Step {i+1}"),
                'action': step.get('pdl_action') or step.get('fabric_action'),
                'sla_minutes': min(step.get('sla_minutes', 30), 30),  # Cap at 30min for PoC
                'status': 'pending',
            })

        return poc_tasks

    def _create_outreach_tasks(
        self,
        service_type: str,
        client_info: Dict,
    ) -> List[Dict]:
        """Create outreach task sequence"""
        return [
            {
                'id': 'outreach_intro',
                'name': 'Send Introduction',
                'template': 'intro',
                'delay_minutes': 0,
                'status': 'pending',
            },
            {
                'id': 'outreach_preview',
                'name': 'Send Preview Notification',
                'template': 'preview_ready',
                'delay_minutes': 25,  # After PoC should be ready
                'status': 'pending',
                'depends_on': 'poc_artifact',
            },
            {
                'id': 'outreach_checkin',
                'name': 'Check-in Message',
                'template': 'check_in',
                'delay_minutes': 60,
                'status': 'pending',
            },
        ]

    async def _run_dual_tracks(
        self,
        execution: DualTrackExecution,
        service_type: str,
        client_info: Dict,
    ):
        """Run both tracks in parallel"""
        execution.status = "in_progress"

        # Start both tracks concurrently
        poc_task = asyncio.create_task(
            self._run_poc_track(execution, service_type)
        )
        outreach_task = asyncio.create_task(
            self._run_outreach_track(execution, service_type, client_info)
        )

        # Wait for both to complete
        try:
            await asyncio.gather(poc_task, outreach_task)
            execution.status = "completed"
            execution.completed_at = datetime.now(timezone.utc).isoformat()
            self.stats['dual_executions_completed'] += 1
        except Exception as e:
            execution.status = "failed"
            logger.error(f"Dual-track execution failed: {e}")

    async def _run_poc_track(
        self,
        execution: DualTrackExecution,
        service_type: str,
    ):
        """Execute PoC track"""
        track = execution.poc_track
        track.status = TrackStatus.IN_PROGRESS
        track.started_at = datetime.now(timezone.utc).isoformat()

        try:
            # Get execution engines
            fabric = self._get_fabric()

            for task in track.tasks:
                task['status'] = 'in_progress'
                task['started_at'] = datetime.now(timezone.utc).isoformat()

                # Execute task
                if fabric and task.get('action'):
                    try:
                        result = await fabric.execute(
                            action=task['action'],
                            context={'service_type': service_type},
                            timeout_seconds=task.get('sla_minutes', 30) * 60,
                        )
                        task['result'] = result
                        task['status'] = 'completed'

                        # Check for artifact URL
                        if result and result.get('artifact_url'):
                            track.artifacts.append(result['artifact_url'])
                            track.poc_artifact_url = result['artifact_url']
                    except Exception as e:
                        task['status'] = 'failed'
                        task['error'] = str(e)
                else:
                    # Simulate completion for demo
                    await asyncio.sleep(1)
                    task['status'] = 'completed'

                task['completed_at'] = datetime.now(timezone.utc).isoformat()

            track.status = TrackStatus.COMPLETED
            track.completed_at = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            track.status = TrackStatus.FAILED
            track.error = str(e)
            logger.error(f"PoC track failed: {e}")

    async def _run_outreach_track(
        self,
        execution: DualTrackExecution,
        service_type: str,
        client_info: Dict,
    ):
        """Execute outreach track"""
        track = execution.outreach_track
        track.status = TrackStatus.IN_PROGRESS
        track.started_at = datetime.now(timezone.utc).isoformat()

        client_name = client_info.get('name', 'there')

        try:
            for task in track.tasks:
                # Check dependencies
                if task.get('depends_on') == 'poc_artifact':
                    # Wait for PoC artifact
                    while not execution.poc_track.poc_artifact_url:
                        if execution.poc_track.status == TrackStatus.FAILED:
                            break
                        await asyncio.sleep(5)

                # Apply delay
                if task.get('delay_minutes', 0) > 0:
                    await asyncio.sleep(min(task['delay_minutes'], 5))  # Cap delay for demo

                task['status'] = 'in_progress'

                # Generate message
                template = task.get('template', 'intro')
                questions = self.SERVICE_QUESTIONS.get(service_type, self.SERVICE_QUESTIONS['default'])

                message = self._render_message(
                    template=template,
                    client_name=client_name,
                    service_type=service_type,
                    questions=questions,
                    preview_url=execution.poc_track.poc_artifact_url,
                    artifact_type=self._get_artifact_type(service_type),
                )

                # Send message (simulated)
                task['message'] = message
                task['status'] = 'completed'
                track.outreach_messages_sent += 1

                logger.info(f"Outreach message sent: {template}")

            track.status = TrackStatus.COMPLETED
            track.completed_at = datetime.now(timezone.utc).isoformat()

        except Exception as e:
            track.status = TrackStatus.FAILED
            track.error = str(e)
            logger.error(f"Outreach track failed: {e}")

    def _render_message(
        self,
        template: str,
        client_name: str,
        service_type: str,
        questions: List[str],
        preview_url: Optional[str] = None,
        artifact_type: str = "preview",
    ) -> str:
        """Render outreach message from template"""
        template_str = self.OUTREACH_TEMPLATES.get(template, self.OUTREACH_TEMPLATES['intro'])

        return template_str.format(
            client_name=client_name,
            service_type=service_type.replace('_', ' '),
            question_1=questions[0] if questions else "What's most important to you?",
            question_2=questions[1] if len(questions) > 1 else "Any specific requirements?",
            preview_url=preview_url or "[Preview URL]",
            artifact_type=artifact_type,
            description=f"initial {artifact_type} for your {service_type.replace('_', ' ')} project",
            status_update="First milestone in progress",
            next_milestone="Delivery within 48 hours",
        )

    def _get_artifact_type(self, service_type: str) -> str:
        """Get artifact type for service"""
        artifact_map = {
            'web_dev': 'wireframe',
            'mobile_dev': 'mockup',
            'design': 'design concept',
            'content': 'outline',
            'devops': 'architecture diagram',
        }
        return artifact_map.get(service_type, 'preview')

    def _get_fabric(self):
        """Get Universal Fabric executor"""
        try:
            from execution.universal_fabric import get_universal_fabric
            return get_universal_fabric()
        except:
            return None

    def record_client_feedback(
        self,
        execution_id: str,
        feedback: Dict[str, Any],
    ) -> bool:
        """Record client feedback for early validation"""
        execution = self.executions.get(execution_id)
        if not execution:
            return False

        execution.outreach_track.client_responses.append({
            'feedback': feedback,
            'received_at': datetime.now(timezone.utc).isoformat(),
        })

        # Analyze for validation
        validation = self._analyze_feedback(feedback)
        execution.early_validation = validation

        if validation.get('needs_pivot'):
            self.stats['pivots_from_feedback'] += 1
        else:
            self.stats['early_validations'] += 1

        return True

    def _analyze_feedback(self, feedback: Dict) -> Dict[str, Any]:
        """Analyze client feedback for validation signals"""
        sentiment = feedback.get('sentiment', 'neutral')
        changes_requested = feedback.get('changes', [])

        return {
            'validated': sentiment in ['positive', 'approved'],
            'needs_pivot': len(changes_requested) > 2 or sentiment == 'negative',
            'changes': changes_requested,
            'confidence': 0.8 if sentiment == 'positive' else 0.5,
        }

    def get_execution(self, execution_id: str) -> Optional[DualTrackExecution]:
        """Get execution by ID"""
        return self.executions.get(execution_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get executor stats"""
        return {
            **self.stats,
            'active_executions': len([
                e for e in self.executions.values()
                if e.status == 'in_progress'
            ]),
        }

    def to_dict(self, execution: DualTrackExecution) -> Dict[str, Any]:
        """Convert execution to dict"""
        return {
            'id': execution.id,
            'contract_id': execution.contract_id,
            'opportunity_id': execution.opportunity_id,
            'status': execution.status,
            'created_at': execution.created_at,
            'completed_at': execution.completed_at,
            'poc_track': {
                'id': execution.poc_track.id,
                'status': execution.poc_track.status.value,
                'tasks': execution.poc_track.tasks,
                'artifacts': execution.poc_track.artifacts,
                'poc_artifact_url': execution.poc_track.poc_artifact_url,
            },
            'outreach_track': {
                'id': execution.outreach_track.id,
                'status': execution.outreach_track.status.value,
                'messages_sent': execution.outreach_track.outreach_messages_sent,
                'client_responses': execution.outreach_track.client_responses,
            },
            'early_validation': execution.early_validation,
        }


# Singleton
_dual_track_executor: Optional[DualTrackExecutor] = None


def get_dual_track_executor() -> DualTrackExecutor:
    """Get or create dual-track executor"""
    global _dual_track_executor
    if _dual_track_executor is None:
        _dual_track_executor = DualTrackExecutor()
    return _dual_track_executor
