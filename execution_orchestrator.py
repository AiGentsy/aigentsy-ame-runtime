"""
EXECUTION ORCHESTRATOR
Master coordinator for opportunity execution pipeline
Discovery → Scoring → Pricing → Engagement → Delivery → Payment
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio
import json

# Import existing engines
from execution_scorer import ExecutionScorer
from pricing_oracle import PricingOracle  # Your existing pricing
from aigx_engine import AIGxEngine  # Your existing currency
from outcome_oracle import OutcomeOracle  # Your existing tracking
from proof_pipe import ProofPipe  # Your existing proof
from opportunity_engagement import OpportunityEngagement  # New file (below)

# Import agent orchestrators
from csuite_orchestrator import CSuiteOrchestrator
from aigentsy_conductor import AigentsyConductor
from openai_agent_deployer import OpenAIAgentDeployer

class ExecutionOrchestrator:
    """
    Coordinates entire execution pipeline from discovery to delivery
    
    Pipeline Stages:
    1. SCORE - Calculate win probability
    2. PRICE - Determine optimal pricing
    3. ENGAGE - Reach out to opportunity
    4. BUILD - Execute solution
    5. DELIVER - Complete and collect payment
    6. LEARN - Update models
    """
    
    def __init__(self):
        self.scorer = ExecutionScorer()
        self.pricer = PricingOracle()
        self.aigx = AIGxEngine()
        self.outcome_oracle = OutcomeOracle()
        self.proof_pipe = ProofPipe()
        self.engagement = OpportunityEngagement()
        
        # Agent orchestrators
        self.csuite = CSuiteOrchestrator()
        self.conductor = AigentsyConductor()
        self.openai_deployer = OpenAIAgentDeployer()
        
        # Execution state
        self.active_executions = {}
        self.completed_executions = []
        
    async def execute_opportunity(
        self, 
        opportunity: Dict[str, Any],
        capability: Dict[str, Any],
        user_data: Optional[Dict[str, Any]] = None,
        wade_approved: bool = False
    ) -> Dict[str, Any]:
        """
        Execute full opportunity pipeline
        
        Args:
            opportunity: Discovered opportunity
            capability: AiGentsy or user capability
            user_data: If routing to user
            wade_approved: If Wade pre-approved (skip approval)
        
        Returns:
            Execution result with status and revenue
        """
        
        execution_id = f"exec_{opportunity['id']}_{int(datetime.utcnow().timestamp())}"
        
        try:
            # STAGE 1: SCORE
            print(f"[{execution_id}] STAGE 1: Scoring opportunity...")
            score = self.scorer.score_opportunity(opportunity, capability, user_data)
            
            # Check if worth executing
            if score['win_probability'] < 0.3:
                return {
                    'execution_id': execution_id,
                    'status': 'skipped',
                    'reason': 'Low win probability',
                    'score': score
                }
            
            # STAGE 2: PRICE
            print(f"[{execution_id}] STAGE 2: Calculating optimal price...")
            pricing = await self.pricer.calculate_optimal_price(
                opportunity, 
                score,
                capability
            )
            
            # STAGE 3: ENGAGE
            print(f"[{execution_id}] STAGE 3: Engaging opportunity...")
            engagement_result = await self.engagement.engage(
                opportunity,
                pricing,
                score
            )
            
            if not engagement_result['success']:
                return {
                    'execution_id': execution_id,
                    'status': 'engagement_failed',
                    'reason': engagement_result.get('reason'),
                    'score': score,
                    'pricing': pricing
                }
            
            # STAGE 4: BUILD (Parallel multi-agent execution)
            print(f"[{execution_id}] STAGE 4: Building solution...")
            solution = await self._execute_solution(
                opportunity,
                engagement_result,
                capability
            )
            
            if not solution['success']:
                return {
                    'execution_id': execution_id,
                    'status': 'build_failed',
                    'reason': solution.get('error'),
                    'score': score,
                    'pricing': pricing,
                    'engagement': engagement_result
                }
            
            # STAGE 5: DELIVER
            print(f"[{execution_id}] STAGE 5: Delivering solution...")
            delivery = await self._deliver_solution(
                opportunity,
                solution,
                engagement_result,
                pricing
            )
            
            if not delivery['success']:
                return {
                    'execution_id': execution_id,
                    'status': 'delivery_failed',
                    'reason': delivery.get('error'),
                    'score': score,
                    'pricing': pricing,
                    'engagement': engagement_result,
                    'solution': solution
                }
            
            # STAGE 6: COLLECT PAYMENT
            print(f"[{execution_id}] STAGE 6: Processing payment...")
            payment = await self._collect_payment(
                opportunity,
                delivery,
                pricing,
                user_data
            )
            
            # STAGE 7: LEARN
            print(f"[{execution_id}] STAGE 7: Updating learning models...")
            await self._record_outcome(
                execution_id,
                opportunity,
                score,
                pricing,
                engagement_result,
                solution,
                delivery,
                payment,
                'completed'
            )
            
            # Calculate final economics
            final_result = {
                'execution_id': execution_id,
                'status': 'completed',
                'opportunity_id': opportunity['id'],
                'revenue': payment['amount'],
                'cost': capability['estimated_cost'],
                'profit': payment['amount'] - capability['estimated_cost'],
                'margin': (payment['amount'] - capability['estimated_cost']) / payment['amount'],
                'duration_days': delivery['duration_days'],
                'win_probability_predicted': score['win_probability'],
                'price_charged': pricing['optimal_price'],
                'aigx_earned': payment.get('aigx_earned', 0),
                'timestamps': {
                    'started': engagement_result['timestamp'],
                    'completed': delivery['timestamp']
                },
                'score': score,
                'pricing': pricing,
                'engagement': engagement_result,
                'solution': solution,
                'delivery': delivery,
                'payment': payment
            }
            
            self.completed_executions.append(final_result)
            
            return final_result
            
        except Exception as e:
            # Record failure
            await self._record_outcome(
                execution_id,
                opportunity,
                score if 'score' in locals() else None,
                pricing if 'pricing' in locals() else None,
                engagement_result if 'engagement_result' in locals() else None,
                solution if 'solution' in locals() else None,
                delivery if 'delivery' in locals() else None,
                None,
                'failed',
                error=str(e)
            )
            
            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e),
                'opportunity': opportunity
            }
    
    async def _execute_solution(
        self,
        opportunity: Dict[str, Any],
        engagement: Dict[str, Any],
        capability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute solution using multi-agent orchestration
        Routes to appropriate agent(s) based on opportunity type
        """
        
        opp_type = opportunity['type']
        
        # Route to appropriate agent team
        if opp_type in ['software_development', 'web_development', 'api_integration']:
            # Use OpenAI agents for coding
            result = await self.openai_deployer.execute_task(
                task_type='code',
                requirements=opportunity['description'],
                context=engagement
            )
        
        elif opp_type in ['content_creation', 'marketing', 'copywriting']:
            # Use conductor for content tasks
            result = await self.conductor.execute_content_task(
                opportunity=opportunity,
                engagement_context=engagement
            )
        
        elif opp_type in ['business_consulting', 'data_analysis']:
            # Use C-Suite orchestrator for consulting
            result = await self.csuite.execute_consulting(
                opportunity=opportunity,
                engagement_context=engagement
            )
        
        else:
            # Default: Use conductor
            result = await self.conductor.execute_generic_task(
                opportunity=opportunity,
                engagement_context=engagement
            )
        
        return {
            'success': result.get('status') == 'completed',
            'output': result.get('output'),
            'artifacts': result.get('artifacts', []),
            'agent_used': result.get('agent'),
            'duration_hours': result.get('duration_hours', 0),
            'timestamp': datetime.utcnow().isoformat(),
            'error': result.get('error')
        }
    
    async def _deliver_solution(
        self,
        opportunity: Dict[str, Any],
        solution: Dict[str, Any],
        engagement: Dict[str, Any],
        pricing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deliver completed solution to client
        Generate proof of work
        """
        
        # Create proof of work
        proof = await self.proof_pipe.generate_proof(
            opportunity_id=opportunity['id'],
            solution=solution,
            pricing=pricing
        )
        
        # Send delivery notification
        delivery_message = f"""
Solution delivered for: {opportunity['title']}

Deliverables:
{json.dumps(solution['artifacts'], indent=2)}

Proof of Work: {proof['proof_url']}

Ready for review and payment.
        """
        
        # Actually deliver (email, GitHub PR, upload, etc)
        delivery_result = await self.engagement.deliver_solution(
            opportunity=opportunity,
            solution=solution,
            proof=proof,
            message=delivery_message
        )
        
        return {
            'success': delivery_result['success'],
            'proof': proof,
            'delivery_method': delivery_result['method'],
            'duration_days': solution['duration_hours'] / 24,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _collect_payment(
        self,
        opportunity: Dict[str, Any],
        delivery: Dict[str, Any],
        pricing: Dict[str, Any],
        user_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process payment collection
        Award AIGx for completion
        """
        
        amount = pricing['optimal_price']
        
        # Award AIGx to executor (user or AiGentsy)
        if user_data:
            # User executed - award them
            aigx_earned = await self.aigx.award_earnings(
                username=user_data['username'],
                amount=amount,
                reason=f"Completed opportunity: {opportunity['title']}",
                opportunity_id=opportunity['id']
            )
        else:
            # AiGentsy executed - credit platform
            aigx_earned = 0
        
        return {
            'amount': amount,
            'aigx_earned': aigx_earned,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _record_outcome(
        self,
        execution_id: str,
        opportunity: Dict[str, Any],
        score: Optional[Dict[str, Any]],
        pricing: Optional[Dict[str, Any]],
        engagement: Optional[Dict[str, Any]],
        solution: Optional[Dict[str, Any]],
        delivery: Optional[Dict[str, Any]],
        payment: Optional[Dict[str, Any]],
        status: str,
        error: Optional[str] = None
    ):
        """
        Record execution outcome for learning
        Updates win probability models
        """
        
        outcome = {
            'execution_id': execution_id,
            'opportunity': opportunity,
            'score': score,
            'pricing': pricing,
            'engagement': engagement,
            'solution': solution,
            'delivery': delivery,
            'payment': payment,
            'status': status,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log to outcome oracle
        await self.outcome_oracle.record_outcome(outcome)
        
        # Update learning models
        if status == 'completed':
            await self.scorer.learn_from_success(opportunity, score)
            await self.pricer.learn_from_success(opportunity, pricing, payment)
        elif status == 'failed':
            await self.scorer.learn_from_failure(opportunity, score, error)
    
    async def batch_execute(
        self,
        opportunities: List[Dict[str, Any]],
        max_parallel: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple opportunities in parallel
        Respects max_parallel limit to avoid overload
        """
        
        # Score all opportunities first
        scored = self.scorer.batch_score_opportunities(
            opportunities,
            capabilities={'default': {'confidence': 0.85}}
        )
        
        # Filter to only high-probability opportunities
        executable = [
            s for s in scored 
            if s['score']['win_probability'] > 0.3
        ]
        
        print(f"Executing {len(executable)} opportunities (filtered from {len(opportunities)})")
        
        # Execute in parallel batches
        results = []
        for i in range(0, len(executable), max_parallel):
            batch = executable[i:i+max_parallel]
            
            tasks = [
                self.execute_opportunity(
                    s['opportunity'],
                    {'confidence': 0.85, 'estimated_cost': 500}
                )
                for s in batch
            ]
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        
        return results
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get aggregate execution statistics"""
        
        if not self.completed_executions:
            return {'message': 'No completed executions yet'}
        
        total = len(self.completed_executions)
        total_revenue = sum(e['revenue'] for e in self.completed_executions)
        total_profit = sum(e['profit'] for e in self.completed_executions)
        avg_margin = sum(e['margin'] for e in self.completed_executions) / total
        avg_duration = sum(e['duration_days'] for e in self.completed_executions) / total
        
        return {
            'total_executions': total,
            'total_revenue': round(total_revenue, 2),
            'total_profit': round(total_profit, 2),
            'avg_margin': round(avg_margin, 3),
            'avg_duration_days': round(avg_duration, 1),
            'revenue_per_day': round(total_revenue / sum(e['duration_days'] for e in self.completed_executions), 2)
        }


# Example usage
if __name__ == "__main__":
    async def test():
        orchestrator = ExecutionOrchestrator()
        
        test_opp = {
            'id': 'github_123',
            'platform': 'github',
            'type': 'software_development',
            'title': 'Fix React bug',
            'description': 'State management issue in checkout flow',
            'value': 2000,
            'urgency': 'high',
            'source': 'explicit_marketplace',
            'created_at': datetime.utcnow().isoformat(),
            'url': 'https://github.com/example/repo/issues/123'
        }
        
        capability = {
            'confidence': 0.9,
            'method': 'aigentsy_direct',
            'estimated_cost': 600
        }
        
        result = await orchestrator.execute_opportunity(test_opp, capability)
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
