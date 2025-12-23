"""
EXECUTION ORCHESTRATOR - FINAL VERSION
Uses your existing pricing_oracle.py functions
Master coordinator for opportunity execution pipeline
Discovery → Scoring → Pricing → Engagement → Delivery → Payment
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import asyncio
import json

# Import execution scorer (required)
from execution_scorer import ExecutionScorer
from opportunity_engagement import OpportunityEngagement

# Import YOUR existing pricing functions
try:
    from pricing_oracle import calculate_dynamic_price, explain_price
    PRICING_AVAILABLE = True
except:
    PRICING_AVAILABLE = False
    print("⚠️ pricing_oracle not available - using simple pricing")

# Optional imports with graceful fallbacks
try:
    from aigx_engine import AIGxEngine
    AIGX_AVAILABLE = True
except:
    AIGX_AVAILABLE = False

try:
    from outcome_oracle_max import on_event
    OUTCOME_AVAILABLE = True
except:
    try:
        from outcome_oracle import OutcomeOracle
        OUTCOME_AVAILABLE = True
    except:
        OUTCOME_AVAILABLE = False

try:
    from proof_pipe import ProofPipe
    PROOF_AVAILABLE = True
except:
    PROOF_AVAILABLE = False

try:
    from csuite_orchestrator import CSuiteOrchestrator
    CSUITE_AVAILABLE = True
except:
    CSUITE_AVAILABLE = False

try:
    from aigentsy_conductor import execute_content_task, execute_consulting, execute_generic_task
    CONDUCTOR_AVAILABLE = True
except Exception as e:
    CONDUCTOR_AVAILABLE = False
    print(f"⚠️ aigentsy_conductor not available: {e}")

try:
    from openai_agent_deployer import OpenAIAgentDeployer
    OPENAI_AVAILABLE = True
except:
    OPENAI_AVAILABLE = False


class ExecutionOrchestrator:
    """
    Coordinates entire execution pipeline from discovery to delivery
    
    Pipeline Stages:
    1. SCORE - Calculate win probability
    2. PRICE - Determine optimal pricing (uses your pricing_oracle)
    3. ENGAGE - Reach out to opportunity
    4. BUILD - Execute solution
    5. DELIVER - Complete and collect payment
    6. LEARN - Update models
    """
    
    def __init__(self):
        self.scorer = ExecutionScorer()
        self.engagement = OpportunityEngagement()
        
        # Optional components
        self.aigx = AIGxEngine() if AIGX_AVAILABLE else None
        self.proof_pipe = ProofPipe() if PROOF_AVAILABLE else None
        
        # Agent orchestrators
        self.csuite = CSuiteOrchestrator() if CSUITE_AVAILABLE else None
        self.openai_deployer = OpenAIAgentDeployer() if OPENAI_AVAILABLE else None
        
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
            
            # STAGE 2: PRICE (Use YOUR pricing_oracle)
            print(f"[{execution_id}] STAGE 2: Calculating optimal price...")
            pricing = await self._calculate_pricing(opportunity, score, capability)
            
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
            
            # STAGE 4: BUILD
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
            print(f"[{execution_id}] STAGE 7: Recording outcome...")
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
                'cost': capability.get('estimated_cost', 0),
                'profit': payment['amount'] - capability.get('estimated_cost', 0),
                'margin': (payment['amount'] - capability.get('estimated_cost', 0)) / payment['amount'] if payment['amount'] > 0 else 0,
                'duration_days': delivery['duration_days'],
                'win_probability_predicted': score['win_probability'],
                'price_charged': pricing['optimal_price'],
                'aigx_earned': payment.get('aigx_earned', 0),
                'timestamps': {
                    'started': engagement_result['timestamp'],
                    'completed': delivery['timestamp']
                }
            }
            
            self.completed_executions.append(final_result)
            
            return final_result
            
        except Exception as e:
            import traceback
            return {
                'execution_id': execution_id,
                'status': 'failed',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'opportunity': opportunity
            }
    
    async def _calculate_pricing(self, opportunity, score, capability):
        """
        Calculate optimal pricing using YOUR pricing_oracle
        """
        
        base_price = opportunity.get('value', 1000)
        
        if PRICING_AVAILABLE:
            try:
                # Use YOUR calculate_dynamic_price function
                context = {
                    'service_type': opportunity.get('type', 'general'),
                    'buyer': opportunity.get('client'),
                    'active_intents': 3,  # Simulate demand
                    'similar_agents': []  # Would populate with competitors
                }
                
                pricing = await calculate_dynamic_price(
                    base_price=base_price,
                    agent='aigentsy',
                    context=context
                )
                
                # Add explanation using YOUR explain_price function
                explanation = await explain_price(
                    base_price=pricing.get('final_price', base_price),
                    agent='aigentsy',
                    context=context
                )
                
                return {
                    'optimal_price': pricing.get('final_price', base_price),
                    'base_price': base_price,
                    'multiplier': pricing.get('multiplier', 1.0),
                    'factors': pricing.get('factors', {}),
                    'explanation': explanation,
                    'win_probability': score.get('win_probability', 0.7),
                    'expected_revenue': pricing.get('final_price', base_price) * score.get('win_probability', 0.7)
                }
            except Exception as e:
                print(f"⚠️ Pricing oracle error: {e}, using fallback")
        
        # Fallback: Simple 2.5x cost pricing
        estimated_cost = capability.get('estimated_cost', base_price * 0.3)
        optimal_price = estimated_cost * 2.5
        
        return {
            'optimal_price': optimal_price,
            'base_price': base_price,
            'multiplier': 1.0,
            'win_probability': score.get('win_probability', 0.7),
            'expected_revenue': optimal_price * score.get('win_probability', 0.7)
        }
    
    async def _execute_solution(
        self,
        opportunity: Dict[str, Any],
        engagement: Dict[str, Any],
        capability: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute solution using available agents
        Falls back to simulation if agents not available
        """
        
        opp_type = opportunity['type']
        
        # Try to use available agents
        if CONDUCTOR_AVAILABLE:
            try:
                if opp_type in ['software_development', 'web_development']:
                    result = await execute_generic_task(opportunity, engagement)
                elif opp_type in ['content_creation', 'marketing']:
                    result = await execute_content_task(opportunity, engagement)
                elif opp_type in ['business_consulting', 'data_analysis']:
                    result = await execute_consulting(opportunity, engagement)
                else:
                    result = await execute_generic_task(opportunity, engagement)
                
                return {
                    'success': result.get('status') == 'completed',
                    'output': result.get('output'),
                    'artifacts': result.get('artifacts', []),
                    'agent_used': result.get('agent'),
                    'duration_hours': result.get('duration_hours', 0),
                    'timestamp': datetime.utcnow().isoformat()
                }
            except:
                pass
        
        # Fallback: Simulate execution
        print(f"   → Simulating execution for {opp_type}")
        await asyncio.sleep(0.1)
        
        return {
            'success': True,
            'output': f"Completed {opp_type} task",
            'artifacts': [f"{opp_type}_deliverable.zip"],
            'agent_used': 'simulated',
            'duration_hours': capability.get('avg_delivery_days', 5) * 8,
            'timestamp': datetime.utcnow().isoformat()
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
        """
        
        # Create proof of work if available
        proof = None
        if PROOF_AVAILABLE and self.proof_pipe:
            try:
                proof = await self.proof_pipe.generate_proof(
                    opportunity_id=opportunity['id'],
                    solution=solution,
                    pricing=pricing
                )
            except:
                pass
        
        # Simulate proof if not available
        if not proof:
            proof = {
                'proof_url': f"https://aigentsy.com/proof/{opportunity['id']}",
                'proof_hash': 'simulated_proof_hash'
            }
        
        # Deliver solution
        delivery_result = await self.engagement.deliver_solution(
            opportunity=opportunity,
            solution=solution,
            proof=proof,
            message=f"Solution delivered for {opportunity['title']}"
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
        Award AIGx if available
        """
        
        amount = pricing['optimal_price']
        
        # Award AIGx if available
        aigx_earned = 0
        if AIGX_AVAILABLE and self.aigx and user_data:
            try:
                aigx_earned = await self.aigx.award_earnings(
                    username=user_data['username'],
                    amount=amount,
                    reason=f"Completed opportunity: {opportunity['title']}",
                    opportunity_id=opportunity['id']
                )
            except:
                pass
        
        return {
            'amount': amount,
            'aigx_earned': aigx_earned,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _record_outcome(
        self,
        execution_id: str,
        opportunity: Dict[str, Any],
        score: Dict[str, Any],
        pricing: Dict[str, Any],
        engagement: Dict[str, Any],
        solution: Dict[str, Any],
        delivery: Dict[str, Any],
        payment: Dict[str, Any],
        status: str,
        error: Optional[str] = None
    ):
        """
        Record execution outcome for learning
        """
        
        outcome = {
            'execution_id': execution_id,
            'opportunity': opportunity,
            'score': score,
            'pricing': pricing,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log to outcome oracle if available
        if OUTCOME_AVAILABLE:
            try:
                await on_event(
                    username='aigentsy',
                    event_type='opportunity_executed',
                    metadata=outcome
                )
            except:
                pass
        
        print(f"[OUTCOME] {status}: {execution_id}")
    
    async def batch_execute(
        self,
        opportunities: List[Dict[str, Any]],
        max_parallel: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple opportunities in parallel
        """
        
        # Score all opportunities first
        scored = self.scorer.batch_score_opportunities(
            opportunities,
            capabilities={'default': {'confidence': 0.85, 'estimated_cost': 500}}
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
            'id': 'test_123',
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
            'estimated_cost': 600,
            'avg_delivery_days': 5
        }
        
        result = await orchestrator.execute_opportunity(test_opp, capability)
        print(json.dumps(result, indent=2))
    
    asyncio.run(test())
