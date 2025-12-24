"""
WADE INTEGRATED WORKFLOW
Combines approval dashboard + bidding system for complete automation

Flow:
1. Discovery Engine finds opportunities
2. Wade Approval Dashboard - Manual review & approval
3. Bidding System - Auto-bid on approved opportunities
4. Execution System - Fulfill approved work
5. Delivery System - Submit & collect payment

Updated: Dec 24, 2025
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from enum import Enum


class WorkflowStage(str, Enum):
    """Stages in Wade's fulfillment workflow"""
    DISCOVERED = "discovered"
    PENDING_WADE_APPROVAL = "pending_wade_approval"
    WADE_APPROVED = "wade_approved"
    BID_SUBMITTED = "bid_submitted"
    PENDING_CLIENT_APPROVAL = "pending_client_approval"
    CLIENT_APPROVED = "client_approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    PAID = "paid"
    WADE_REJECTED = "wade_rejected"
    CLIENT_REJECTED = "client_rejected"


class IntegratedFulfillmentWorkflow:
    """
    Master workflow orchestrator
    Manages the complete lifecycle from discovery → payment
    """
    
    def __init__(self):
        # Import existing systems
        from wade_approval_dashboard import fulfillment_queue
        self.approval_queue = fulfillment_queue
        
        # State tracking
        self.workflows = {}  # opportunity_id → workflow_state
    
    async def process_discovered_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entry point: New opportunity discovered
        
        Step 1: Add to Wade's approval queue
        """
        
        workflow_id = opportunity['id']
        
        # Check if Wade can fulfill
        fulfillability = opportunity.get('fulfillability', {})
        
        if not fulfillability.get('can_wade_fulfill'):
            return {
                'workflow_id': workflow_id,
                'stage': 'skipped',
                'reason': 'Not Wade-fulfillable',
                'routed_to': 'user'
            }
        
        # Add to approval queue
        fulfillment = self.approval_queue.add_to_queue(
            opportunity=opportunity,
            routing=fulfillability
        )
        
        # Initialize workflow
        workflow = {
            'workflow_id': workflow_id,
            'opportunity_id': opportunity['id'],
            'fulfillment_id': fulfillment['id'],
            'stage': WorkflowStage.PENDING_WADE_APPROVAL,
            'opportunity': opportunity,
            'fulfillability': fulfillability,
            'fulfillment': fulfillment,
            'history': [
                {
                    'stage': WorkflowStage.DISCOVERED,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'action': 'Opportunity discovered and added to Wade approval queue'
                }
            ],
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        self.workflows[workflow_id] = workflow
        
        return {
            'workflow_id': workflow_id,
            'fulfillment_id': fulfillment['id'],
            'stage': WorkflowStage.PENDING_WADE_APPROVAL,
            'message': 'Added to Wade approval queue',
            'approval_url': f'/wade/fulfillment-queue'
        }
    
    async def wade_approves(self, fulfillment_id: str) -> Dict[str, Any]:
        """
        Step 2: Wade manually approves opportunity
        
        Triggers: Auto-bid submission
        """
        
        # Approve in dashboard
        approval_result = self.approval_queue.approve_fulfillment(fulfillment_id)
        
        if not approval_result['ok']:
            return approval_result
        
        # Find workflow
        workflow = None
        for wf in self.workflows.values():
            if wf.get('fulfillment_id') == fulfillment_id:
                workflow = wf
                break
        
        if not workflow:
            return {'ok': False, 'error': 'Workflow not found'}
        
        # Update workflow
        workflow['stage'] = WorkflowStage.WADE_APPROVED
        workflow['wade_approved_at'] = datetime.now(timezone.utc).isoformat()
        workflow['history'].append({
            'stage': WorkflowStage.WADE_APPROVED,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': 'Wade approved - triggering auto-bid'
        })
        
        # Trigger auto-bid
        bid_result = await self._submit_auto_bid(workflow)
        
        workflow['bid_result'] = bid_result
        workflow['history'].append({
            'stage': WorkflowStage.BID_SUBMITTED,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': f"Bid submitted via {bid_result.get('method', 'unknown')}",
            'data': bid_result
        })
        
        if bid_result.get('success'):
            workflow['stage'] = WorkflowStage.PENDING_CLIENT_APPROVAL
        
        return {
            'ok': True,
            'workflow_id': workflow['workflow_id'],
            'stage': workflow['stage'],
            'bid_result': bid_result
        }
    
    async def _submit_auto_bid(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-submit bid using bidding system
        """
        
        from wade_bidding_system import generate_bid_proposal, submit_github_bid, submit_bid_to_platform
        
        opportunity = workflow['opportunity']
        
        # Generate proposal
        proposal = await generate_bid_proposal(opportunity)
        
        # Submit based on platform
        platform = opportunity['source']
        
        if platform in ['github', 'github_bounties']:
            # Real GitHub submission
            result = await submit_github_bid(opportunity, proposal)
            return result
        
        else:
            # Prepare for manual submission
            result = await submit_bid_to_platform(opportunity, proposal)
            return {
                'success': True,
                'method': 'manual_submission_required',
                'instructions': result['instructions'],
                'proposal': proposal,
                'url': opportunity['url']
            }
    
    async def check_client_approval(self, workflow_id: str) -> Dict[str, Any]:
        """
        Step 3: Monitor for client approval
        
        Background job checks periodically
        """
        
        from wade_bidding_system import check_github_approval
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {'ok': False, 'error': 'Workflow not found'}
        
        opportunity = workflow['opportunity']
        bid_record = workflow.get('bid_result', {})
        
        # Check approval based on platform
        if opportunity['source'] in ['github', 'github_bounties']:
            approval = await check_github_approval(opportunity, bid_record)
            
            if approval.get('approved'):
                # Update workflow
                workflow['stage'] = WorkflowStage.CLIENT_APPROVED
                workflow['client_approved_at'] = approval['approved_at']
                workflow['approval_method'] = approval['method']
                workflow['history'].append({
                    'stage': WorkflowStage.CLIENT_APPROVED,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'action': f"Client approved via {approval['method']}",
                    'data': approval
                })
                
                # Trigger execution
                execution_result = await self._execute_fulfillment(workflow)
                
                return {
                    'ok': True,
                    'approved': True,
                    'workflow_id': workflow_id,
                    'stage': workflow['stage'],
                    'execution_started': True,
                    'execution_result': execution_result
                }
            
            else:
                return {
                    'ok': True,
                    'approved': False,
                    'reason': approval.get('reason', 'Still pending')
                }
        
        else:
            return {
                'ok': True,
                'message': 'Manual approval detection required for this platform'
            }
    
    async def _execute_fulfillment(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4: Execute the actual work
        """
        
        from wade_bidding_system import execute_fulfillment
        
        workflow['stage'] = WorkflowStage.IN_PROGRESS
        workflow['started_at'] = datetime.now(timezone.utc).isoformat()
        workflow['history'].append({
            'stage': WorkflowStage.IN_PROGRESS,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': 'Execution started'
        })
        
        opportunity = workflow['opportunity']
        approval = {
            'approved_at': workflow.get('client_approved_at'),
            'method': workflow.get('approval_method')
        }
        
        # Execute
        result = await execute_fulfillment(opportunity, approval)
        
        if result.get('success'):
            workflow['stage'] = WorkflowStage.COMPLETED
            workflow['completed_at'] = result['completed_at']
            workflow['execution_result'] = result
            workflow['history'].append({
                'stage': WorkflowStage.COMPLETED,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'action': 'Execution completed',
                'data': result
            })
            
            # Trigger delivery
            delivery_result = await self._deliver_work(workflow)
            
            return {
                'ok': True,
                'execution_completed': True,
                'delivery_result': delivery_result
            }
        
        else:
            return {
                'ok': False,
                'error': result.get('error', 'Execution failed')
            }
    
    async def _deliver_work(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Deliver completed work
        """
        
        from wade_bidding_system import deliver_to_github
        
        opportunity = workflow['opportunity']
        fulfillment = workflow.get('execution_result', {})
        
        if opportunity['source'] in ['github', 'github_bounties']:
            result = await deliver_to_github(opportunity, fulfillment)
            
            if result.get('success'):
                workflow['stage'] = WorkflowStage.DELIVERED
                workflow['delivered_at'] = result['delivered_at']
                workflow['delivery_url'] = result['delivery_url']
                workflow['history'].append({
                    'stage': WorkflowStage.DELIVERED,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'action': 'Work delivered',
                    'data': result
                })
            
            return result
        
        else:
            return {
                'success': False,
                'message': 'Manual delivery required for this platform'
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {'ok': False, 'error': 'Workflow not found'}
        
        return {
            'ok': True,
            'workflow_id': workflow_id,
            'stage': workflow['stage'],
            'opportunity': {
                'title': workflow['opportunity']['title'],
                'platform': workflow['opportunity']['source'],
                'url': workflow['opportunity']['url'],
                'value': workflow['opportunity']['estimated_value']
            },
            'history': workflow['history'],
            'created_at': workflow['created_at'],
            'current_action': self._get_next_action(workflow)
        }
    
    def _get_next_action(self, workflow: Dict[str, Any]) -> str:
        """Determine what needs to happen next"""
        
        stage = workflow['stage']
        
        actions = {
            WorkflowStage.PENDING_WADE_APPROVAL: "Wade needs to approve in dashboard",
            WorkflowStage.WADE_APPROVED: "Auto-bidding in progress",
            WorkflowStage.BID_SUBMITTED: "Monitoring for client approval",
            WorkflowStage.PENDING_CLIENT_APPROVAL: "Waiting for client to accept bid",
            WorkflowStage.CLIENT_APPROVED: "Execution in progress",
            WorkflowStage.IN_PROGRESS: "Wade is working on fulfillment",
            WorkflowStage.COMPLETED: "Delivery in progress",
            WorkflowStage.DELIVERED: "Waiting for payment confirmation",
            WorkflowStage.PAID: "Complete - payment received",
            WorkflowStage.WADE_REJECTED: "Wade rejected this opportunity",
            WorkflowStage.CLIENT_REJECTED: "Client rejected bid"
        }
        
        return actions.get(stage, "Unknown")
    
    def get_all_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows that aren't complete"""
        
        active_stages = [
            WorkflowStage.PENDING_WADE_APPROVAL,
            WorkflowStage.WADE_APPROVED,
            WorkflowStage.BID_SUBMITTED,
            WorkflowStage.PENDING_CLIENT_APPROVAL,
            WorkflowStage.CLIENT_APPROVED,
            WorkflowStage.IN_PROGRESS,
            WorkflowStage.COMPLETED,
            WorkflowStage.DELIVERED
        ]
        
        active = []
        for workflow in self.workflows.values():
            if workflow['stage'] in active_stages:
                active.append({
                    'workflow_id': workflow['workflow_id'],
                    'stage': workflow['stage'],
                    'title': workflow['opportunity']['title'],
                    'platform': workflow['opportunity']['source'],
                    'value': workflow['opportunity']['estimated_value'],
                    'next_action': self._get_next_action(workflow),
                    'created_at': workflow['created_at']
                })
        
        return active


# Global instance
integrated_workflow = IntegratedFulfillmentWorkflow()


# ============================================================
# API ENDPOINTS (Add to main.py)
# ============================================================

"""
# Add these to your main.py:

from wade_integrated_workflow import integrated_workflow

@app.post("/wade/process-opportunity")
async def process_opportunity(opportunity: Dict):
    '''
    Step 1: Process discovered opportunity
    Adds to Wade's approval queue
    '''
    result = await integrated_workflow.process_discovered_opportunity(opportunity)
    return result

@app.post("/wade/approve/{fulfillment_id}")
async def wade_approve(fulfillment_id: str):
    '''
    Step 2: Wade approves + auto-bids
    '''
    result = await integrated_workflow.wade_approves(fulfillment_id)
    return result

@app.get("/wade/workflow/{workflow_id}")
async def get_workflow(workflow_id: str):
    '''
    Check workflow status
    '''
    return integrated_workflow.get_workflow_status(workflow_id)

@app.get("/wade/active-workflows")
async def get_active_workflows():
    '''
    See all active workflows
    '''
    return {
        'ok': True,
        'workflows': integrated_workflow.get_all_active_workflows()
    }

@app.post("/wade/check-approval/{workflow_id}")
async def check_approval(workflow_id: str):
    '''
    Manually check if client approved
    (Background job would do this automatically)
    '''
    result = await integrated_workflow.check_client_approval(workflow_id)
    return result
"""
