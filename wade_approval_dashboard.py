"""
WADE'S APPROVAL DASHBOARD
Dashboard for reviewing and approving AiGentsy direct fulfillment opportunities

Endpoint: /wade/fulfillment-queue
"""

from typing import Dict, List
from datetime import datetime


class AiGentsyFulfillmentQueue:
    """
    Manages opportunities that AiGentsy can fulfill directly
    Requires Wade's approval before execution
    """
    
    def __init__(self):
        self.pending_fulfillments = []
        self.approved_fulfillments = []
        self.rejected_fulfillments = []
    
    def add_to_queue(self, opportunity: Dict, routing: Dict) -> Dict:
        """
        Add opportunity to Wade's approval queue
        
        Args:
            opportunity: The discovered opportunity
            routing: Fulfillability data from discovery engine
        
        Returns:
            Fulfillment record
        """
        
        # Handle both old (nested economics) and new (flat) structures
        if 'economics' in routing:
            # Old structure
            estimated_profit = routing['economics']['estimated_profit']
            estimated_cost = routing['economics']['estimated_cost']
            estimated_days = routing['economics'].get('estimated_days', 7)
        else:
            # New flat structure from discovery engine
            estimated_profit = routing.get('estimated_profit', 0)
            estimated_cost = routing.get('estimated_cost', 0)
            estimated_days = routing.get('delivery_days', 7)
        
        fulfillment = {
            'id': f"fulfillment_{datetime.utcnow().timestamp()}",
            'opportunity': opportunity,
            'routing': routing,
            'status': 'pending_approval',
            'created_at': datetime.utcnow().isoformat(),
            'estimated_profit': estimated_profit,
            'estimated_cost': estimated_cost,
            'estimated_days': estimated_days,
            'fulfillment_plan': self._generate_fulfillment_plan(opportunity, routing),
            'ai_models': routing.get('ai_models', [routing.get('fulfillment_system', 'claude')]),
            'confidence': routing.get('confidence', 0.8)
        }
        
        self.pending_fulfillments.append(fulfillment)
        
        return fulfillment
    
    def _generate_fulfillment_plan(self, opportunity: Dict, routing: Dict) -> Dict:
        """
        Generate recommended approach for fulfillment
        """
        
        # Handle both nested and flat structures
        if 'capability' in routing and isinstance(routing['capability'], dict):
            ai_models = routing['capability'].get('ai_models', ['claude'])
            tools_needed = routing['capability'].get('tools', [])
        else:
            ai_models = [routing.get('fulfillment_system', 'claude')]
            tools_needed = []
        
        estimated_days = routing.get('delivery_days', routing.get('economics', {}).get('estimated_days', 7))
        confidence = routing.get('confidence', 0.8)
        
        return {
            'approach': f"Use {', '.join(ai_models)} to fulfill {opportunity.get('type', 'opportunity')}",
            'steps': [
                'Analyze requirements with Claude',
                'Generate deliverables with AI',
                'Wade reviews output',
                'Deliver to client',
                'Collect payment'
            ],
            'tools_needed': tools_needed,
            'estimated_hours': estimated_days * 4,  # 4 hours per day estimate
            'risk_level': 'low' if confidence > 0.85 else 'medium'
        }
    
    def get_pending_queue(self) -> List[Dict]:
        """Get all pending fulfillments awaiting approval"""
        return self.pending_fulfillments
    
    def approve_fulfillment(self, fulfillment_id: str, approved_by: str = 'wade') -> Dict:
        """
        Wade approves a fulfillment
        """
        
        # Find fulfillment
        fulfillment = None
        for f in self.pending_fulfillments:
            if f['id'] == fulfillment_id:
                fulfillment = f
                break
        
        if not fulfillment:
            return {'ok': False, 'error': 'Fulfillment not found'}
        
        # Update status
        fulfillment['status'] = 'approved'
        fulfillment['approved_at'] = datetime.utcnow().isoformat()
        fulfillment['approved_by'] = approved_by
        
        # Move to approved queue
        self.pending_fulfillments.remove(fulfillment)
        self.approved_fulfillments.append(fulfillment)
        
        return {
            'ok': True,
            'fulfillment_id': fulfillment_id,
            'status': 'approved',
            'message': 'Fulfillment approved and ready for execution'
        }
    
    def reject_fulfillment(self, fulfillment_id: str, reason: str = None) -> Dict:
        """
        Wade rejects a fulfillment
        """
        
        # Find fulfillment
        fulfillment = None
        for f in self.pending_fulfillments:
            if f['id'] == fulfillment_id:
                fulfillment = f
                break
        
        if not fulfillment:
            return {'ok': False, 'error': 'Fulfillment not found'}
        
        # Update status
        fulfillment['status'] = 'rejected'
        fulfillment['rejected_at'] = datetime.utcnow().isoformat()
        fulfillment['rejection_reason'] = reason
        
        # Move to rejected queue
        self.pending_fulfillments.remove(fulfillment)
        self.rejected_fulfillments.append(fulfillment)
        
        return {
            'ok': True,
            'fulfillment_id': fulfillment_id,
            'status': 'rejected'
        }
    
    def get_stats(self) -> Dict:
        """Get queue statistics"""
        
        pending_value = sum(f['opportunity'].get('estimated_value', f['opportunity'].get('value', 0)) for f in self.pending_fulfillments)
        pending_profit = sum(f['estimated_profit'] for f in self.pending_fulfillments)
        
        approved_value = sum(f['opportunity'].get('estimated_value', f['opportunity'].get('value', 0)) for f in self.approved_fulfillments)
        approved_profit = sum(f['estimated_profit'] for f in self.approved_fulfillments)
        
        return {
            'pending': {
                'count': len(self.pending_fulfillments),
                'total_value': pending_value,
                'total_profit': pending_profit
            },
            'approved': {
                'count': len(self.approved_fulfillments),
                'total_value': approved_value,
                'total_profit': approved_profit
            },
            'rejected': {
                'count': len(self.rejected_fulfillments)
            }
        }


# Global instance
fulfillment_queue = AiGentsyFulfillmentQueue()


# ============================================================
# FLASK/FASTAPI ENDPOINTS (for integration into main.py)
# ============================================================

"""
Add these endpoints to main.py:

@app.get("/wade/fulfillment-queue")
async def get_wade_fulfillment_queue():
    '''
    Wade's approval dashboard
    '''
    from wade_approval_dashboard import fulfillment_queue
    
    pending = fulfillment_queue.get_pending_queue()
    stats = fulfillment_queue.get_stats()
    
    return {
        'ok': True,
        'stats': stats,
        'pending_opportunities': [
            {
                'id': f['id'],
                'title': f['opportunity']['title'],
                'platform': f['opportunity']['platform'],
                'type': f['opportunity']['type'],
                'value': f['opportunity']['value'],
                'estimated_profit': f['estimated_profit'],
                'estimated_cost': f['estimated_cost'],
                'estimated_days': f['estimated_days'],
                'confidence': f['confidence'],
                'fulfillment_plan': f['fulfillment_plan'],
                'ai_models': f['ai_models'],
                'opportunity_url': f['opportunity']['url'],
                'created_at': f['created_at']
            }
            for f in pending
        ]
    }

@app.post("/wade/approve/{fulfillment_id}")
async def approve_fulfillment(fulfillment_id: str):
    '''
    Wade approves a fulfillment
    '''
    from wade_approval_dashboard import fulfillment_queue
    
    result = fulfillment_queue.approve_fulfillment(fulfillment_id)
    
    if result['ok']:
        # TODO: Trigger execution
        # await execute_fulfillment(fulfillment_id)
        pass
    
    return result

@app.post("/wade/reject/{fulfillment_id}")
async def reject_fulfillment(fulfillment_id: str, reason: str = None):
    '''
    Wade rejects a fulfillment
    '''
    from wade_approval_dashboard import fulfillment_queue
    
    result = fulfillment_queue.reject_fulfillment(fulfillment_id, reason)
    
    return result
"""
