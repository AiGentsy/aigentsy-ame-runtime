"""
APPROVAL SYSTEM - USER CONTROL FOR IMPORTANT DECISIONS
Wade approves high-value AiGentsy opportunities before execution

Integration:
- Works with universal_executor.py
- Stores approvals in JSONBin
- Provides API endpoints
- Sends notifications (optional)
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4

# Import JSONBin for persistence
try:
    from log_to_jsonbin import log_agent_update, get_user
    JSONBIN_AVAILABLE = True
except:
    JSONBIN_AVAILABLE = False
    print("⚠️ JSONBin not available - using in-memory storage")


class ApprovalSystem:
    """
    Manages approval workflow for autonomous executions
    
    Workflow:
    1. Execution needs approval → added to queue
    2. Wade reviews via dashboard/API
    3. Wade approves/rejects
    4. System continues or halts execution
    """
    
    def __init__(self):
        # In-memory queue (will sync with JSONBin)
        self.approval_queue = []
        print("✅ Approval system initialized")
    
    
    async def request_approval(
        self,
        execution_id: str,
        opportunity: Dict[str, Any],
        score: Dict[str, Any],
        estimated_value: float,
        estimated_cost: float,
        requester: str = "aigentsy"
    ) -> Dict[str, Any]:
        """
        Add execution to approval queue
        
        Args:
            execution_id: Unique execution ID
            opportunity: Full opportunity data
            score: Win probability and scoring
            estimated_value: Expected revenue
            estimated_cost: Expected cost
            requester: Who's requesting (user or aigentsy)
        
        Returns:
            Approval request record
        """
        
        approval_request = {
            "id": execution_id,
            "approval_id": str(uuid4()),
            "status": "pending",
            "requester": requester,
            "opportunity": {
                "platform": opportunity.get("platform"),
                "type": opportunity.get("type"),
                "title": opportunity.get("title"),
                "description": opportunity.get("description", "")[:200],  # Truncate
                "url": opportunity.get("url"),
                "value": opportunity.get("value")
            },
            "score": {
                "win_probability": score.get("win_probability"),
                "expected_value": score.get("expected_value"),
                "risk_level": score.get("risk_level"),
                "recommendation": score.get("recommendation")
            },
            "financials": {
                "estimated_value": estimated_value,
                "estimated_cost": estimated_cost,
                "estimated_profit": estimated_value - estimated_cost,
                "margin": ((estimated_value - estimated_cost) / estimated_value * 100) if estimated_value > 0 else 0
            },
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "decided_at": None,
            "decision": None,
            "decision_notes": None
        }
        
        # Add to queue
        self.approval_queue.append(approval_request)
        
        # Save to JSONBin
        if JSONBIN_AVAILABLE:
            try:
                log_agent_update({
                    "type": "approval_request",
                    "data": approval_request
                })
            except Exception as e:
                print(f"⚠️ Could not save to JSONBin: {e}")
        
        print(f"📋 Approval requested for {execution_id}")
        print(f"   Value: ${estimated_value:,.2f}")
        print(f"   Win Probability: {score.get('win_probability', 0)*100:.1f}%")
        
        return approval_request
    
    
    async def get_pending_approvals(self, requester: str = None) -> List[Dict[str, Any]]:
        """
        Get all pending approval requests
        
        Args:
            requester: Filter by requester (user/aigentsy)
        
        Returns:
            List of pending approvals
        """
        
        pending = [
            a for a in self.approval_queue
            if a["status"] == "pending"
        ]
        
        if requester:
            pending = [a for a in pending if a["requester"] == requester]
        
        # Sort by expected value (highest first)
        pending.sort(
            key=lambda x: x["financials"]["estimated_value"],
            reverse=True
        )
        
        return pending
    
    
    async def approve(
        self,
        execution_id: str,
        approved: bool,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Approve or reject an execution
        
        Args:
            execution_id: ID of execution to approve
            approved: True to approve, False to reject
            notes: Optional decision notes
        
        Returns:
            Updated approval record
        """
        
        # Find approval request
        approval = None
        for a in self.approval_queue:
            if a["id"] == execution_id:
                approval = a
                break
        
        if not approval:
            raise ValueError(f"Approval request not found: {execution_id}")
        
        # Update approval
        approval["status"] = "approved" if approved else "rejected"
        approval["decision"] = "approved" if approved else "rejected"
        approval["decided_at"] = datetime.now(timezone.utc).isoformat()
        approval["decision_notes"] = notes
        
        # Save to JSONBin
        if JSONBIN_AVAILABLE:
            try:
                log_agent_update({
                    "type": "approval_decision",
                    "data": approval
                })
            except:
                pass
        
        decision_text = "✅ APPROVED" if approved else "❌ REJECTED"
        print(f"{decision_text}: {execution_id}")
        
        return approval
    
    
    async def get_approval_stats(self) -> Dict[str, Any]:
        """
        Get approval statistics
        
        Returns:
            Stats about approval requests and decisions
        """
        
        stats = {
            "total_requests": len(self.approval_queue),
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "approval_rate": 0.0,
            "avg_decision_time_seconds": 0,
            "total_value_pending": 0.0,
            "total_value_approved": 0.0,
            "total_value_rejected": 0.0
        }
        
        decision_times = []
        
        for approval in self.approval_queue:
            status = approval["status"]
            
            if status == "pending":
                stats["pending"] += 1
                stats["total_value_pending"] += approval["financials"]["estimated_value"]
            
            elif status == "approved":
                stats["approved"] += 1
                stats["total_value_approved"] += approval["financials"]["estimated_value"]
                
                # Calculate decision time
                if approval["decided_at"] and approval["submitted_at"]:
                    submitted = datetime.fromisoformat(approval["submitted_at"].replace("Z", "+00:00"))
                    decided = datetime.fromisoformat(approval["decided_at"].replace("Z", "+00:00"))
                    decision_times.append((decided - submitted).total_seconds())
            
            elif status == "rejected":
                stats["rejected"] += 1
                stats["total_value_rejected"] += approval["financials"]["estimated_value"]
        
        # Calculate approval rate
        total_decided = stats["approved"] + stats["rejected"]
        if total_decided > 0:
            stats["approval_rate"] = stats["approved"] / total_decided
        
        # Calculate avg decision time
        if decision_times:
            stats["avg_decision_time_seconds"] = sum(decision_times) / len(decision_times)
        
        return stats


# Singleton instance
_approval_system = None

def get_approval_system() -> ApprovalSystem:
    """Get singleton approval system instance"""
    global _approval_system
    if _approval_system is None:
        _approval_system = ApprovalSystem()
    return _approval_system


# Convenience functions
async def request_approval(execution_id: str, opportunity: Dict, score: Dict, 
                          estimated_value: float, estimated_cost: float):
    """Request approval for an execution"""
    system = get_approval_system()
    return await system.request_approval(
        execution_id, opportunity, score, estimated_value, estimated_cost
    )


async def get_pending_approvals():
    """Get all pending approvals"""
    system = get_approval_system()
    return await system.get_pending_approvals()


async def approve_execution(execution_id: str, approved: bool, notes: str = None):
    """Approve or reject an execution"""
    system = get_approval_system()
    return await system.approve(execution_id, approved, notes)
