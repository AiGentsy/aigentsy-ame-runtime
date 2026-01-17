"""
UNIVERSAL AUTONOMOUS EXECUTOR
The system that transforms AiGentsy from chatbots to actual autonomous business

This is the CORE ENGINE that:
1. Takes discovered opportunities
2. Autonomously executes work
3. Submits deliverables to platforms
4. Collects payment
5. Learns and improves

Integration Points:
- alpha_discovery_engine.py (discovers opportunities)
- execution_scorer.py (scores win probability)
- pricing_oracle.py (calculates pricing)
- aigentsy_conductor.py (routes to AI models)
- outcome_oracle.py (tracks results)

This file BIRTHS the autonomous system.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum
import json

# Import your existing infrastructure
try:
    from aigentsy_conductor import AiGentsyConductor  # Fixed: capital G
    CONDUCTOR_AVAILABLE = True
except Exception as e:
    CONDUCTOR_AVAILABLE = False
    print(f"⚠️ aigentsy_conductor not available: {e}")

try:
    from pricing_oracle import calculate_dynamic_price
    PRICING_AVAILABLE = True
except:
    PRICING_AVAILABLE = False

try:
    from outcome_oracle import OutcomeOracle
    OUTCOME_AVAILABLE = True
except:
    try:
        from outcome_oracle_max import OutcomeOracle
        OUTCOME_AVAILABLE = True
    except:
        OUTCOME_AVAILABLE = False
        class OutcomeOracle:  # Stub class
            def __init__(self): pass

try:
    from execution_scorer import ExecutionScorer
    SCORER_AVAILABLE = True
except:
    SCORER_AVAILABLE = False


class ExecutionStage(Enum):
    """Stages of autonomous execution"""
    DISCOVERED = "discovered"
    SCORED = "scored"
    APPROVED = "approved"
    PLANNING = "planning"
    GENERATING = "generating"
    VALIDATING = "validating"
    SUBMITTING = "submitting"
    MONITORING = "monitoring"
    FEEDBACK = "handling_feedback"
    COMPLETED = "completed"
    FAILED = "failed"
    PAID = "paid"


class UniversalAutonomousExecutor:
    """
    THE CORE AUTONOMOUS EXECUTION ENGINE
    
    This class orchestrates the entire lifecycle from opportunity → payment.
    It's the "robot" that actually does the work your chatbots describe.
    
    Architecture:
    - Platform-agnostic core logic
    - Platform-specific executors plugged in
    - AI conductor for generation
    - Learning from every execution
    """
    
    def __init__(self):
        print("\n" + "="*60)
        print("🚀 INITIALIZING UNIVERSAL AUTONOMOUS EXECUTOR")
        print("="*60)
        
        # AI Conductor (routes to Claude/GPT-4/Gemini)
        if CONDUCTOR_AVAILABLE:
            self.conductor = AiGentsyConductor()  # Fixed: capital G
            print("✅ AI Conductor loaded (Claude/GPT-4/Gemini routing)")
        else:
            self.conductor = None
            print("⚠️ AI Conductor not available - using stubs")
        
        # Scoring system
        if SCORER_AVAILABLE:
            self.scorer = ExecutionScorer()
            print("✅ Execution Scorer loaded")
        else:
            self.scorer = None
        
        # Outcome tracking
        if OUTCOME_AVAILABLE:
            self.outcomes = OutcomeOracle()
            print("✅ Outcome Oracle loaded")
        else:
            self.outcomes = None
        
        # Platform executors (loaded from platform_apis.py)
        self.platform_executors = {}
        self._load_platform_executors()
        
        # Execution state tracking
        self.active_executions = {}  # {execution_id: execution_state}
        self.completed_executions = []
        self.learning_data = {
            'wins': [],
            'losses': [],
            'patterns': {}
        }
        
        print(f"✅ {len(self.platform_executors)} platform executors loaded")
        print("="*60 + "\n")
    
    
    def _load_platform_executors(self):
        """Load platform-specific executors"""
        try:
            from platform_apis import (
                GitHubExecutor,
                UpworkExecutor,
                RedditExecutor,
                EmailExecutor,
                TwitterExecutor
            )
            
            self.platform_executors = {
                'github': GitHubExecutor(),
                'upwork': UpworkExecutor(),
                'reddit': RedditExecutor(),
                'email': EmailExecutor(),
                'twitter': TwitterExecutor()
            }
        except ImportError as e:
            print(f"⚠️ Platform executors not available: {e}")
            print("   Using stub executors")
            self.platform_executors = {}
    
    
    async def execute_opportunity(
        self,
        opportunity: Dict[str, Any],
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        MAIN EXECUTION PIPELINE
        
        Takes a discovered opportunity and autonomously:
        1. Plans the approach
        2. Generates the solution
        3. Validates quality
        4. Submits to platform
        5. Monitors for completion
        6. Handles feedback
        7. Collects payment
        8. Learns from results
        
        Args:
            opportunity: Discovered opportunity from alpha_discovery_engine
            auto_approve: If True, skip approval gate
            
        Returns:
            Execution result with status, deliverables, payment info
        """
        
        execution_id = f"{opportunity['platform']}_{opportunity['id']}_{int(datetime.now().timestamp())}"
        
        print(f"\n{'='*60}")
        print(f"🎯 EXECUTING OPPORTUNITY: {execution_id}")
        print(f"Platform: {opportunity['platform']}")
        print(f"Type: {opportunity.get('type', 'unknown')}")
        print(f"Value: ${opportunity.get('value', 0):,.2f}")
        print(f"{'='*60}\n")
        
        # Initialize execution state
        execution_state = {
            'execution_id': execution_id,
            'opportunity': opportunity,
            'stage': ExecutionStage.DISCOVERED,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'history': [],
            'attempts': 0,
            'max_attempts': 3
        }
        
        self.active_executions[execution_id] = execution_state
        
        try:
            # STAGE 1: SCORING
            execution_state = await self._stage_scoring(execution_state)
            
            # STAGE 2: APPROVAL (if needed)
            if not auto_approve:
                execution_state = await self._stage_approval(execution_state)
                if execution_state['stage'] == ExecutionStage.FAILED:
                    return self._finalize_execution(execution_state)
            
            # STAGE 3: PLANNING
            execution_state = await self._stage_planning(execution_state)
            
            # STAGE 4: GENERATION
            execution_state = await self._stage_generation(execution_state)
            
            # STAGE 5: VALIDATION
            execution_state = await self._stage_validation(execution_state)
            
            # STAGE 6: SUBMISSION
            execution_state = await self._stage_submission(execution_state)
            
            # STAGE 7: MONITORING (async, continues in background)
            asyncio.create_task(
                self._stage_monitoring(execution_state)
            )
            
            return self._get_execution_status(execution_state)
            
        except Exception as e:
            print(f"❌ Execution failed: {e}")
            import traceback
            traceback.print_exc()
            
            execution_state['stage'] = ExecutionStage.FAILED
            execution_state['error'] = str(e)
            execution_state['traceback'] = traceback.format_exc()
            
            return self._finalize_execution(execution_state)
    
    
    async def _stage_scoring(self, state: Dict) -> Dict:
        """
        STAGE 1: Score the opportunity
        Calculate win probability, expected value, risk
        """
        print("📊 STAGE 1: SCORING")
        
        state['stage'] = ExecutionStage.SCORED
        state['history'].append({
            'stage': 'scoring',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        if self.scorer:
            score = self.scorer.score_opportunity(state['opportunity'])
            state['score'] = score
            
            print(f"   Win Probability: {score['win_probability']*100:.1f}%")
            print(f"   Expected Value: ${score['expected_value']:,.2f}")
            print(f"   Risk Level: {score['risk_level']}")
            print(f"   Recommendation: {score['recommendation']}")
        else:
            # Fallback scoring
            state['score'] = {
                'win_probability': 0.5,
                'expected_value': state['opportunity'].get('value', 0) * 0.5,
                'risk_level': 'medium',
                'recommendation': 'CONSIDER'
            }
        
        print("✅ Scoring complete\n")
        return state
    
    
    async def _stage_approval(self, state: Dict) -> Dict:
        """
        STAGE 2: Wait for approval
        In production, this checks approval queue
        """
        print("⏳ STAGE 2: AWAITING APPROVAL")
        
        state['stage'] = ExecutionStage.APPROVED
        
        # Check if opportunity requires approval
        requires_approval = state['opportunity'].get('routing', {}).get('requires_wade_approval', False)
        
        if requires_approval:
            print("   ⚠️ Requires Wade approval - holding for approval queue")
            state['awaiting_approval'] = True
            # In production, this would wait for approval API
            # For now, we'll simulate approval
            state['approved'] = False
            state['stage'] = ExecutionStage.FAILED
            state['reason'] = 'awaiting_approval'
        else:
            print("   ✅ Auto-approved (user opportunity)")
            state['approved'] = True
        
        print("✅ Approval stage complete\n")
        return state
    
    
    async def _stage_planning(self, state: Dict) -> Dict:
        """
        STAGE 3: Plan the execution
        Use AI to understand requirements and plan approach
        """
        print("🧠 STAGE 3: PLANNING")
        
        state['stage'] = ExecutionStage.PLANNING
        state['history'].append({
            'stage': 'planning',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        opportunity = state['opportunity']
        
        # Build planning prompt
        planning_prompt = f"""
Analyze this opportunity and create an execution plan:

OPPORTUNITY:
- Platform: {opportunity['platform']}
- Type: {opportunity.get('type')}
- Title: {opportunity.get('title')}
- Description: {opportunity.get('description', '')}
- Value: ${opportunity.get('value', 0)}
- URL: {opportunity.get('url', '')}

Create a detailed execution plan that includes:
1. Requirements analysis
2. Approach/strategy
3. Key deliverables
4. Quality criteria
5. Submission checklist
6. Potential risks

Respond in JSON format.
"""
        
        if self.conductor and CONDUCTOR_AVAILABLE:
            plan = await self.conductor.execute_task(
                task_type='analysis',
                prompt=planning_prompt,
                preferred_model='claude'
            )
            state['plan'] = plan
            print(f"   ✅ AI-generated execution plan created")
        else:
            # Fallback plan
            state['plan'] = {
                'approach': 'Standard execution',
                'deliverables': ['Solution addressing requirements'],
                'risks': ['Time constraints', 'Quality requirements']
            }
            print("   ⚠️ Using fallback plan (AI conductor not available)")
        
        print("✅ Planning complete\n")
        return state
    
    
    async def _stage_generation(self, state: Dict) -> Dict:
        """
        STAGE 4: Generate the solution
        Use AI to create actual deliverables
        """
        print("⚙️ STAGE 4: GENERATING SOLUTION")
        
        state['stage'] = ExecutionStage.GENERATING
        state['history'].append({
            'stage': 'generation',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        opportunity = state['opportunity']
        platform = opportunity['platform']
        
        # Route to platform-specific generator
        if platform in self.platform_executors:
            executor = self.platform_executors[platform]
            solution = await executor.generate_solution(opportunity, state.get('plan'))
            state['solution'] = solution
            print(f"   ✅ Solution generated via {platform} executor")
        else:
            # Generic generation
            solution = await self._generic_solution_generation(opportunity, state.get('plan'))
            state['solution'] = solution
            print(f"   ⚠️ Generic solution generated (no platform executor)")
        
        print("✅ Generation complete\n")
        return state
    
    
    async def _generic_solution_generation(self, opportunity: Dict, plan: Dict) -> Dict:
        """
        Generic solution generation for any platform
        Uses AI conductor to generate appropriate deliverables
        """
        
        opp_type = opportunity.get('type', 'unknown')
        
        generation_prompt = f"""
Generate a complete solution for this opportunity:

TYPE: {opp_type}
TITLE: {opportunity.get('title')}
DESCRIPTION: {opportunity.get('description', '')}

PLAN:
{json.dumps(plan, indent=2)}

Generate production-ready deliverables that fully address the requirements.

For code tasks: Include complete, working code with tests
For content tasks: Include publication-ready content
For design tasks: Include detailed specifications

Respond with complete deliverables in appropriate format.
"""
        
        if self.conductor and CONDUCTOR_AVAILABLE:
            result = await self.conductor.execute_task(
                task_type=opp_type,
                prompt=generation_prompt,
                preferred_model='claude'
            )
            
            return {
                'type': opp_type,
                'deliverables': result,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            return {
                'type': opp_type,
                'deliverables': '[Solution would be generated here]',
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
    
    
    async def _stage_validation(self, state: Dict) -> Dict:
        """
        STAGE 5: Validate the solution
        Check quality before submission
        """
        print("✓ STAGE 5: VALIDATING")
        
        state['stage'] = ExecutionStage.VALIDATING
        state['history'].append({
            'stage': 'validation',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        solution = state['solution']
        opportunity = state['opportunity']
        
        # Platform-specific validation
        platform = opportunity['platform']
        if platform in self.platform_executors:
            executor = self.platform_executors[platform]
            validation = await executor.validate_solution(solution, opportunity)
            state['validation'] = validation
            
            if not validation.get('passed', False):
                print(f"   ❌ Validation failed: {validation.get('errors')}")
                
                # Retry generation if we have attempts left
                state['attempts'] += 1
                if state['attempts'] < state['max_attempts']:
                    print(f"   🔄 Retrying generation (attempt {state['attempts'] + 1}/{state['max_attempts']})")
                    return await self._stage_generation(state)
                else:
                    state['stage'] = ExecutionStage.FAILED
                    state['error'] = 'Validation failed after max attempts'
                    return state
        else:
            # Generic validation
            state['validation'] = {'passed': True, 'warnings': ['No platform-specific validation']}
        
        print("✅ Validation passed\n")
        return state
    
    
    async def _stage_submission(self, state: Dict) -> Dict:
        """
        STAGE 6: Submit to platform
        Actually deliver the work via platform APIs
        """
        print("📤 STAGE 6: SUBMITTING")
        
        state['stage'] = ExecutionStage.SUBMITTING
        state['history'].append({
            'stage': 'submission',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        opportunity = state['opportunity']
        solution = state['solution']
        platform = opportunity['platform']
        
        # Platform-specific submission
        if platform in self.platform_executors:
            executor = self.platform_executors[platform]
            submission_result = await executor.submit(solution, opportunity)
            state['submission'] = submission_result
            
            print(f"   ✅ Submitted to {platform}")
            print(f"   Submission URL: {submission_result.get('url', 'N/A')}")
            print(f"   Submission ID: {submission_result.get('id', 'N/A')}")
        else:
            # Simulated submission
            state['submission'] = {
                'id': f"sim_{platform}_{int(datetime.now().timestamp())}",
                'url': opportunity.get('url', ''),
                'status': 'submitted',
                'platform': platform
            }
            print(f"   ⚠️ Simulated submission (no {platform} executor)")
        
        print("✅ Submission complete\n")
        return state
    
    
    async def _stage_monitoring(self, state: Dict) -> Dict:
        """
        STAGE 7: Monitor for completion
        Track the submission until merge/acceptance/payment
        Runs in background
        """
        print("👁️ STAGE 7: MONITORING (background)")
        
        state['stage'] = ExecutionStage.MONITORING
        state['history'].append({
            'stage': 'monitoring',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        opportunity = state['opportunity']
        platform = opportunity['platform']
        submission = state.get('submission', {})
        
        # Platform-specific monitoring
        if platform in self.platform_executors:
            executor = self.platform_executors[platform]
            
            # Monitor until completion
            while True:
                await asyncio.sleep(3600)  # Check every hour
                
                status = await executor.check_status(submission['id'])
                
                if status['completed']:
                    state['stage'] = ExecutionStage.COMPLETED
                    state['completion'] = status
                    state['completed_at'] = datetime.now(timezone.utc).isoformat()
                    
                    print(f"\n✅ EXECUTION COMPLETED: {state['execution_id']}")
                    print(f"   Platform: {platform}")
                    print(f"   Status: {status.get('status')}")
                    
                    # Record outcome
                    if self.outcomes:
                        await self.outcomes.record_execution_completed(
                            execution_id=state['execution_id'],
                            outcome=status.get('status'),
                            value=opportunity.get('value', 0)
                        )
                    
                    # Learn from success
                    await self._learn_from_execution(state, success=True)
                    
                    break
                
                elif status['failed']:
                    state['stage'] = ExecutionStage.FAILED
                    state['error'] = status.get('reason')
                    
                    print(f"\n❌ EXECUTION FAILED: {state['execution_id']}")
                    
                    # Learn from failure
                    await self._learn_from_execution(state, success=False)
                    
                    break
                
                # Handle feedback
                if status.get('feedback'):
                    await self._handle_feedback(state, status['feedback'])
        
        return state
    
    
    async def _handle_feedback(self, state: Dict, feedback: Dict):
        """
        Handle feedback/review comments
        Regenerate solution based on feedback
        """
        print(f"\n💬 HANDLING FEEDBACK: {state['execution_id']}")
        
        state['stage'] = ExecutionStage.FEEDBACK
        
        # Use AI to understand feedback and regenerate
        if self.conductor and CONDUCTOR_AVAILABLE:
            regeneration_prompt = f"""
The submitted solution received feedback:

FEEDBACK:
{json.dumps(feedback, indent=2)}

ORIGINAL SOLUTION:
{json.dumps(state['solution'], indent=2)}

Regenerate the solution addressing all feedback points.
"""
            
            updated_solution = await self.conductor.execute_task(
                task_type='code',
                prompt=regeneration_prompt,
                preferred_model='claude'
            )
            
            # Resubmit
            platform = state['opportunity']['platform']
            if platform in self.platform_executors:
                executor = self.platform_executors[platform]
                await executor.update_submission(
                    state['submission']['id'],
                    updated_solution
                )
                
                print("   ✅ Updated submission with feedback addressed")
    
    
    async def _learn_from_execution(self, state: Dict, success: bool):
        """
        Learn from execution results
        Update models and strategies
        """
        learning_entry = {
            'execution_id': state['execution_id'],
            'platform': state['opportunity']['platform'],
            'type': state['opportunity'].get('type'),
            'success': success,
            'win_probability': state.get('score', {}).get('win_probability'),
            'actual_outcome': 'win' if success else 'loss',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if success:
            self.learning_data['wins'].append(learning_entry)
        else:
            self.learning_data['losses'].append(learning_entry)
        
        # Update patterns
        platform = state['opportunity']['platform']
        if platform not in self.learning_data['patterns']:
            self.learning_data['patterns'][platform] = {
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0
            }
        
        patterns = self.learning_data['patterns'][platform]
        if success:
            patterns['wins'] += 1
        else:
            patterns['losses'] += 1
        
        total = patterns['wins'] + patterns['losses']
        patterns['win_rate'] = patterns['wins'] / total if total > 0 else 0.0
        
        print(f"\n📊 LEARNING UPDATE:")
        print(f"   Platform: {platform}")
        print(f"   Win Rate: {patterns['win_rate']*100:.1f}%")
        print(f"   Total Executions: {total}")
    
    
    def _get_execution_status(self, state: Dict) -> Dict:
        """Get current execution status"""
        return {
            'execution_id': state['execution_id'],
            'stage': state['stage'].value,
            'opportunity': state['opportunity'],
            'score': state.get('score'),
            'submission': state.get('submission'),
            'status': 'active' if state['stage'] not in [ExecutionStage.COMPLETED, ExecutionStage.FAILED] else 'finished'
        }
    
    
    def _finalize_execution(self, state: Dict) -> Dict:
        """Finalize and archive execution"""
        self.completed_executions.append(state)
        if state['execution_id'] in self.active_executions:
            del self.active_executions[state['execution_id']]
        
        return self._get_execution_status(state)
    
    
    def get_stats(self) -> Dict:
        """Get execution statistics"""
        total_wins = len(self.learning_data['wins'])
        total_losses = len(self.learning_data['losses'])
        total = total_wins + total_losses
        
        return {
            'active_executions': len(self.active_executions),
            'completed_executions': len(self.completed_executions),
            'total_wins': total_wins,
            'total_losses': total_losses,
            'overall_win_rate': total_wins / total if total > 0 else 0.0,
            'platform_stats': self.learning_data['patterns']
        }


# =========================
# CONVENIENCE FUNCTIONS
# =========================

_executor_instance = None

def get_executor() -> UniversalAutonomousExecutor:
    """Get singleton executor instance"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = UniversalAutonomousExecutor()
    return _executor_instance


async def execute_opportunity(opportunity: Dict, auto_approve: bool = False) -> Dict:
    """Convenience function to execute an opportunity"""
    executor = get_executor()
    return await executor.execute_opportunity(opportunity, auto_approve)
