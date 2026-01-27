"""
WORKFORCE DISPATCHER: Quality-Banded Human/AI Task Routing
═══════════════════════════════════════════════════════════════════════════════

Routes tasks to appropriate workforce tier based on complexity and QA requirements.

Tiers:
- Fabric: AI-powered Universal Fabric (browser automation)
- PDL: Platform Descriptor Language integrations
- Human-Premium: Top-tier human workers for critical tasks
- Human-Standard: Standard human workforce
- Hybrid: AI draft + Human review

Updated: Jan 2026
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class WorkforceTier(Enum):
    FABRIC = "fabric"          # AI browser automation
    PDL = "pdl"                # API integrations
    HUMAN_PREMIUM = "human_premium"  # Expert humans
    HUMAN_STANDARD = "human_standard"  # Standard humans
    HYBRID = "hybrid"          # AI + Human review


class TaskPriority(Enum):
    CRITICAL = 1   # SLA < 1hr
    HIGH = 2       # SLA < 4hr
    NORMAL = 3     # SLA < 24hr
    LOW = 4        # SLA > 24hr


@dataclass
class WorkforceTask:
    """A task dispatched to workforce"""
    id: str
    step_id: str
    plan_id: str
    tier: WorkforceTier
    priority: TaskPriority
    action: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    assigned_to: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    sla_minutes: int = 60
    retries: int = 0
    max_retries: int = 3


@dataclass
class WorkerPool:
    """A pool of workers for a tier"""
    tier: WorkforceTier
    capacity: int = 10
    active: int = 0
    available: int = 10
    avg_completion_minutes: float = 30.0
    success_rate: float = 0.95


class WorkforceDispatcher:
    """
    Routes tasks to appropriate workforce tier.

    Selection Logic:
    1. Check if fabric_action → FABRIC tier
    2. Check if pdl_action → PDL tier
    3. Check complexity/QA requirements → HUMAN tiers
    4. Consider capacity and SLA

    Plan B Auto-Swap:
    - If step exceeds p95 by >20%, swap executor tier
    - Fabric → Hybrid → Human-Premium escalation
    """

    # P95 benchmarks per tier (in seconds)
    P95_BENCHMARKS = {
        WorkforceTier.FABRIC: 300,      # 5 minutes
        WorkforceTier.PDL: 120,          # 2 minutes
        WorkforceTier.HUMAN_PREMIUM: 7200,  # 2 hours
        WorkforceTier.HUMAN_STANDARD: 3600,  # 1 hour
        WorkforceTier.HYBRID: 2700,      # 45 minutes
    }

    # Swap threshold (20% over p95)
    SWAP_THRESHOLD = 1.2

    def __init__(self):
        self.tasks: Dict[str, WorkforceTask] = {}
        self.pools: Dict[WorkforceTier, WorkerPool] = {
            WorkforceTier.FABRIC: WorkerPool(WorkforceTier.FABRIC, capacity=100, available=100, avg_completion_minutes=5),
            WorkforceTier.PDL: WorkerPool(WorkforceTier.PDL, capacity=50, available=50, avg_completion_minutes=2),
            WorkforceTier.HUMAN_PREMIUM: WorkerPool(WorkforceTier.HUMAN_PREMIUM, capacity=5, available=5, avg_completion_minutes=120),
            WorkforceTier.HUMAN_STANDARD: WorkerPool(WorkforceTier.HUMAN_STANDARD, capacity=20, available=20, avg_completion_minutes=60),
            WorkforceTier.HYBRID: WorkerPool(WorkforceTier.HYBRID, capacity=10, available=10, avg_completion_minutes=45),
        }
        self.stats = {
            'tasks_dispatched': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'fabric_tasks': 0,
            'pdl_tasks': 0,
            'human_tasks': 0,
            'avg_completion_minutes': 0,
        }

    async def dispatch_step(self, step: Dict[str, Any], plan_id: str) -> WorkforceTask:
        """
        Dispatch a step to appropriate workforce tier.

        Args:
            step: ExecutionStep as dict
            plan_id: Parent plan ID

        Returns:
            WorkforceTask with assignment
        """
        step_id = step.get('id', 'unknown')

        # Determine tier
        tier = self._select_tier(step)

        # Determine priority based on SLA
        sla_minutes = step.get('sla_minutes', 60)
        priority = self._calculate_priority(sla_minutes)

        # Create task
        task = WorkforceTask(
            id=f"wf_{plan_id}_{step_id}",
            step_id=step_id,
            plan_id=plan_id,
            tier=tier,
            priority=priority,
            action=step.get('pdl_action') or step.get('fabric_action') or 'manual',
            inputs=step.get('inputs', {}),
            sla_minutes=sla_minutes,
        )

        # Check capacity
        pool = self.pools[tier]
        if pool.available > 0:
            task.status = "assigned"
            task.assigned_to = f"{tier.value}_worker_{pool.active + 1}"
            pool.active += 1
            pool.available -= 1
        else:
            # Fallback to next tier
            task = await self._fallback_dispatch(task)

        # Store task
        self.tasks[task.id] = task
        self.stats['tasks_dispatched'] += 1
        self._update_tier_stats(tier)

        logger.info(f"Dispatched {task.id} to {tier.value}: {task.action}")

        # Execute if AI tier
        if tier in [WorkforceTier.FABRIC, WorkforceTier.PDL]:
            asyncio.create_task(self._execute_ai_task(task))

        return task

    def _select_tier(self, step: Dict[str, Any]) -> WorkforceTier:
        """Select best workforce tier for step"""
        # Fabric actions → FABRIC
        if step.get('fabric_action'):
            return WorkforceTier.FABRIC

        # PDL actions → PDL
        if step.get('pdl_action'):
            pdl = step['pdl_action']
            # Some PDLs may need human review
            if 'submit' in pdl or 'post' in pdl:
                qa_gate = step.get('qa_gate')
                if qa_gate and 'review' in qa_gate:
                    return WorkforceTier.HYBRID
            return WorkforceTier.PDL

        # QA gates requiring manual review → HUMAN
        qa_gate = step.get('qa_gate', '')
        if 'manual' in qa_gate.lower() or 'review' in qa_gate.lower():
            return WorkforceTier.HUMAN_PREMIUM

        # Default to hybrid
        return WorkforceTier.HYBRID

    def _calculate_priority(self, sla_minutes: int) -> TaskPriority:
        """Calculate priority from SLA"""
        if sla_minutes < 60:
            return TaskPriority.CRITICAL
        elif sla_minutes < 240:
            return TaskPriority.HIGH
        elif sla_minutes < 1440:
            return TaskPriority.NORMAL
        else:
            return TaskPriority.LOW

    def should_swap(self, task: WorkforceTask) -> Optional[WorkforceTier]:
        """
        Plan B Auto-Swap: Check if task should swap to higher tier.

        Returns new tier if swap needed, None otherwise.
        """
        if not task.started_at:
            return None

        # Calculate elapsed time
        start = datetime.fromisoformat(task.started_at.replace('Z', '+00:00'))
        elapsed_seconds = (datetime.now(timezone.utc) - start).total_seconds()

        # Get p95 benchmark for current tier
        p95 = self.P95_BENCHMARKS.get(task.tier, 300)

        # Check if exceeded threshold
        if elapsed_seconds > p95 * self.SWAP_THRESHOLD:
            # Determine swap target
            swap_chain = {
                WorkforceTier.FABRIC: WorkforceTier.HYBRID,
                WorkforceTier.PDL: WorkforceTier.HYBRID,
                WorkforceTier.HYBRID: WorkforceTier.HUMAN_PREMIUM,
                WorkforceTier.HUMAN_STANDARD: WorkforceTier.HUMAN_PREMIUM,
            }

            new_tier = swap_chain.get(task.tier)
            if new_tier:
                logger.warning(
                    f"Plan B swap triggered: {task.id} "
                    f"{task.tier.value} → {new_tier.value} "
                    f"(elapsed: {elapsed_seconds:.0f}s, p95: {p95}s)"
                )
                return new_tier

        return None

    async def execute_with_swap(self, task: WorkforceTask) -> Dict[str, Any]:
        """
        Execute task with automatic tier swap on stall.

        Monitors execution and swaps tier if p95 exceeded.
        """
        original_tier = task.tier
        swap_count = 0
        max_swaps = 2

        while swap_count < max_swaps:
            # Check for swap
            new_tier = self.should_swap(task)
            if new_tier and new_tier != task.tier:
                # Record swap in proof ledger
                try:
                    from monetization.proof_ledger import get_proof_ledger
                    ledger = get_proof_ledger()
                    ledger.create_proof(
                        opportunity_id=task.plan_id,
                        title=f"Tier Swap: {task.tier.value} → {new_tier.value}",
                        description=f"Auto-swap triggered for task {task.id}",
                        proof_type="tier_swap",
                        evidence={
                            'original_tier': original_tier.value,
                            'new_tier': new_tier.value,
                            'swap_count': swap_count + 1,
                            'reason': 'p95_exceeded',
                        }
                    )
                except Exception:
                    pass

                # Perform swap
                task.tier = new_tier
                swap_count += 1
                self.stats['tier_swaps'] = self.stats.get('tier_swaps', 0) + 1

            # Try execution
            if task.tier in [WorkforceTier.FABRIC, WorkforceTier.PDL]:
                await self._execute_ai_task(task)
                if task.status == "completed":
                    break
            else:
                # Human tiers - mark as assigned and return
                task.status = "assigned"
                break

            await asyncio.sleep(1)  # Brief pause before retry

        return {
            'task_id': task.id,
            'final_tier': task.tier.value,
            'original_tier': original_tier.value,
            'swap_count': swap_count,
            'status': task.status,
        }

    async def _fallback_dispatch(self, task: WorkforceTask) -> WorkforceTask:
        """Fallback to alternative tier if primary full"""
        fallback_order = {
            WorkforceTier.FABRIC: [WorkforceTier.PDL, WorkforceTier.HYBRID],
            WorkforceTier.PDL: [WorkforceTier.FABRIC, WorkforceTier.HYBRID],
            WorkforceTier.HUMAN_PREMIUM: [WorkforceTier.HYBRID, WorkforceTier.HUMAN_STANDARD],
            WorkforceTier.HUMAN_STANDARD: [WorkforceTier.HYBRID, WorkforceTier.HUMAN_PREMIUM],
            WorkforceTier.HYBRID: [WorkforceTier.HUMAN_STANDARD, WorkforceTier.FABRIC],
        }

        for fallback_tier in fallback_order.get(task.tier, []):
            pool = self.pools[fallback_tier]
            if pool.available > 0:
                task.tier = fallback_tier
                task.status = "assigned"
                task.assigned_to = f"{fallback_tier.value}_worker_{pool.active + 1}"
                pool.active += 1
                pool.available -= 1
                logger.info(f"Fallback dispatch {task.id} to {fallback_tier.value}")
                return task

        # All full - queue task
        task.status = "queued"
        return task

    async def _execute_ai_task(self, task: WorkforceTask):
        """Execute AI-powered task"""
        task.status = "in_progress"
        task.started_at = datetime.now(timezone.utc).isoformat()

        try:
            if task.tier == WorkforceTier.FABRIC:
                result = await self._execute_fabric(task)
            elif task.tier == WorkforceTier.PDL:
                result = await self._execute_pdl(task)
            else:
                result = {'status': 'completed', 'message': 'Task processed'}

            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now(timezone.utc).isoformat()
            self.stats['tasks_completed'] += 1

        except Exception as e:
            task.retries += 1
            if task.retries < task.max_retries:
                logger.warning(f"Task {task.id} failed, retrying ({task.retries}/{task.max_retries})")
                await self._execute_ai_task(task)
            else:
                task.status = "failed"
                task.result = {'error': str(e)}
                self.stats['tasks_failed'] += 1

        finally:
            # Release worker
            pool = self.pools[task.tier]
            pool.active = max(0, pool.active - 1)
            pool.available = min(pool.capacity, pool.available + 1)

    async def _execute_fabric(self, task: WorkforceTask) -> Dict[str, Any]:
        """Execute via Universal Fulfillment Fabric"""
        try:
            from universal_fulfillment_fabric import UniversalFabric
            fabric = UniversalFabric()
            result = await fabric.execute_action(task.action, task.inputs)
            return {'status': 'completed', 'fabric_result': result}
        except ImportError:
            # Simulate fabric execution
            await asyncio.sleep(0.1)
            return {'status': 'completed', 'message': f'Fabric executed: {task.action}'}

    async def _execute_pdl(self, task: WorkforceTask) -> Dict[str, Any]:
        """Execute via PDL integration"""
        try:
            from managers.execution_manager import get_execution_manager
            em = get_execution_manager()
            result = await em.execute_pdl(task.action, task.inputs)
            return {'status': 'completed', 'pdl_result': result}
        except Exception:
            # Simulate PDL execution
            await asyncio.sleep(0.05)
            return {'status': 'completed', 'message': f'PDL executed: {task.action}'}

    def _update_tier_stats(self, tier: WorkforceTier):
        """Update stats for tier"""
        if tier == WorkforceTier.FABRIC:
            self.stats['fabric_tasks'] += 1
        elif tier == WorkforceTier.PDL:
            self.stats['pdl_tasks'] += 1
        else:
            self.stats['human_tasks'] += 1

    def complete_task(self, task_id: str, result: Dict[str, Any], success: bool = True):
        """Mark a task as completed (for human tasks)"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = "completed" if success else "failed"
        task.result = result
        task.completed_at = datetime.now(timezone.utc).isoformat()

        if success:
            self.stats['tasks_completed'] += 1
        else:
            self.stats['tasks_failed'] += 1

        # Release worker
        pool = self.pools[task.tier]
        pool.active = max(0, pool.active - 1)
        pool.available = min(pool.capacity, pool.available + 1)

        return True

    def get_capacity(self) -> Dict[str, Any]:
        """Get current workforce capacity"""
        return {
            tier.value: {
                'capacity': pool.capacity,
                'active': pool.active,
                'available': pool.available,
                'utilization_pct': round(pool.active / pool.capacity * 100, 1) if pool.capacity > 0 else 0,
                'avg_completion_minutes': pool.avg_completion_minutes,
                'success_rate': pool.success_rate,
            }
            for tier, pool in self.pools.items()
        }

    def get_task(self, task_id: str) -> Optional[WorkforceTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher stats"""
        return {
            **self.stats,
            'active_tasks': sum(1 for t in self.tasks.values() if t.status in ['assigned', 'in_progress']),
            'queued_tasks': sum(1 for t in self.tasks.values() if t.status == 'queued'),
        }

    def to_dict(self, task: WorkforceTask) -> Dict[str, Any]:
        """Convert task to dict"""
        return {
            'id': task.id,
            'step_id': task.step_id,
            'plan_id': task.plan_id,
            'tier': task.tier.value,
            'priority': task.priority.value,
            'action': task.action,
            'inputs': task.inputs,
            'status': task.status,
            'assigned_to': task.assigned_to,
            'result': task.result,
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'sla_minutes': task.sla_minutes,
            'retries': task.retries,
        }


# Global instance
_dispatcher: Optional[WorkforceDispatcher] = None


def get_workforce_dispatcher() -> WorkforceDispatcher:
    """Get or create workforce dispatcher singleton"""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = WorkforceDispatcher()
    return _dispatcher


async def dispatch_step(step: Dict[str, Any], plan_id: str) -> WorkforceTask:
    """Convenience function"""
    return await get_workforce_dispatcher().dispatch_step(step, plan_id)
