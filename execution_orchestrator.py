"""
EXECUTION ORCHESTRATOR - COMPLETE INTEGRATION
Every single AiGentsy system wired into the execution pipeline

This orchestrator CASCADE through all 127 systems:
- Discovery → Intelligence → Approval → Execution → Delivery → Payment
- Auto-triggers: OCL (P2P), Factoring (P2P), R3, AMG, Growth, Analytics
- Handles both AiGentsy opportunities (Wade's Stripe) and User opportunities (their business)

FULLY AUTONOMOUS PIPELINE
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import asyncio
import json
from revenue_flows import calculate_base_fee, ingest_service_payment

# ===== CORE EXECUTION =====
from execution_scorer import ExecutionScorer
from opportunity_engagement import OpportunityEngagement

# ===== AUTONOMOUS EXECUTION (NEW) =====
try:
    from universal_executor import get_executor
    AUTONOMOUS_EXECUTION_AVAILABLE = True
except:
    AUTONOMOUS_EXECUTION_AVAILABLE = False
    print("⚠️ universal_executor not available - using basic execution")

try:
    from platform_apis import GitHubExecutor, UpworkExecutor, RedditExecutor, EmailExecutor, TwitterExecutor
    PLATFORM_APIS_AVAILABLE = True
except:
    PLATFORM_APIS_AVAILABLE = False
    print("⚠️ platform_apis not available")

# ===== REVENUE & PAYMENT =====
try:
    from payment_collector import record_revenue, mark_paid
    PAYMENT_TRACKING_AVAILABLE = True
except:
    PAYMENT_TRACKING_AVAILABLE = False

from revenue_flows import (
    ingest_ame_conversion, ingest_intent_settlement, 
    ingest_service_payment, calculate_base_fee
)

# ===== FINANCIAL TOOLS (P2P) =====
try:
    from ocl_p2p_lending import request_loan, offer_stake, get_available_stakes
    OCL_P2P_AVAILABLE = True
except:
    OCL_P2P_AVAILABLE = False

try:
    from agent_factoring import calculate_factoring_tier, request_factoring_advance
    FACTORING_AVAILABLE = True
except:
    FACTORING_AVAILABLE = False

try:
    from performance_bonds import create_bond, claim_bond
    BONDS_AVAILABLE = True
except:
    BONDS_AVAILABLE = False

# ===== GROWTH & OPTIMIZATION =====
try:
    from r3_autopilot import execute_autopilot_spend
    R3_AVAILABLE = True
except:
    R3_AVAILABLE = False

try:
    from amg_orchestrator import AMGOrchestrator
    AMG_AVAILABLE = True
except:
    AMG_AVAILABLE = False

try:
    from proposal_autoclose import auto_close_won_proposals
    AUTOCLOSE_AVAILABLE = True
except:
    AUTOCLOSE_AVAILABLE = False

try:
    from aigent_growth_agent import metabridge as launch_growth_campaign
    GROWTH_AGENT_AVAILABLE = True
except:
    GROWTH_AGENT_AVAILABLE = False

# ===== ANALYTICS & INTELLIGENCE =====
try:
    from analytics_engine import calculate_agent_metrics
    ANALYTICS_AVAILABLE = True
except:
    ANALYTICS_AVAILABLE = False

try:
    from ltv_forecaster import calculate_ltv_with_churn
    LTV_AVAILABLE = True
except:
    LTV_AVAILABLE = False

try:
    from pricing_oracle import calculate_dynamic_price
    PRICING_AVAILABLE = True
except:
    PRICING_AVAILABLE = False

# ===== MARKETPLACE =====
try:
    from metabridge_dealgraph_UPGRADED import create as create_deal
    DEALGRAPH_AVAILABLE = True
except:
    DEALGRAPH_AVAILABLE = False

try:
    from jv_mesh import create_jv_opportunity
    JV_MESH_AVAILABLE = True
except:
    JV_MESH_AVAILABLE = False

# ===== RISK & COMPLIANCE =====
try:
    from fraud_detector import check_fraud_signals
    FRAUD_DETECTION_AVAILABLE = True
except:
    FRAUD_DETECTION_AVAILABLE = False

try:
    from compliance_oracle import check_transaction_allowed
    COMPLIANCE_AVAILABLE = True
except:
    COMPLIANCE_AVAILABLE = False

# ===== OUTCOME TRACKING =====
from outcome_oracle_max import on_event, credit_aigx
from log_to_jsonbin import get_user, log_agent_update


class ExecutionOrchestrator:
    """
    MASTER ORCHESTRATOR - Wires all 127 systems together
    
    Flow:
    1. Receive opportunity (from discovery or approval)
    2. Pre-execution checks (fraud, compliance, financing)
    3. Execute work (autonomous or engagement)
    4. Deliver results
    5. Collect payment
    6. Post-execution (reinvest, optimize, scale)
    """
    
    def __init__(self):
        print("\n" + "="*70)
        print("🚀 INITIALIZING EXECUTION ORCHESTRATOR - FULL INTEGRATION")
        print("="*70)
        
        self.scorer = ExecutionScorer()
        self.engagement = OpportunityEngagement()
        
        # Track execution stats
        self.executions = []
        
        print(f"✅ Core systems loaded")
        print(f"✅ Autonomous execution: {AUTONOMOUS_EXECUTION_AVAILABLE}")
        print(f"✅ Platform APIs: {PLATFORM_APIS_AVAILABLE}")
        print(f"✅ Payment tracking: {PAYMENT_TRACKING_AVAILABLE}")
        print(f"✅ P2P OCL: {OCL_P2P_AVAILABLE}")
        print(f"✅ Factoring: {FACTORING_AVAILABLE}")
        print(f"✅ R3 Autopilot: {R3_AVAILABLE}")
        print(f"✅ AMG: {AMG_AVAILABLE}")
        print("="*70 + "\n")
    
    
    async def execute_opportunity(
        self,
        opportunity: Dict[str, Any],
        capability: Dict[str, Any],
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        COMPLETE EXECUTION PIPELINE
        
        Orchestrates ALL systems in proper sequence
        """
        
        execution_id = f"exec_{int(datetime.now().timestamp())}_{opportunity.get('id', 'unknown')}"
        username = user_data.get('username')
        is_aigentsy = not username  # If no username, it's AiGentsy opportunity (Wade executes)
        
        print(f"\n{'='*70}")
        print(f"🎯 EXECUTING OPPORTUNITY: {opportunity.get('title', 'Untitled')}")
        print(f"   ID: {execution_id}")
        print(f"   Platform: {opportunity.get('platform')}")
        print(f"   Value: ${opportunity.get('value', 0):,.2f}")
        print(f"   Executor: {'AiGentsy (Wade)' if is_aigentsy else f'User ({username})'}")
        print(f"{'='*70}\n")
        
        result = {
            'execution_id': execution_id,
            'opportunity': opportunity,
            'capability': capability,
            'executor': 'aigentsy' if is_aigentsy else username,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'stages': {}
        }
        
        try:
            # ===== STAGE 1: PRE-EXECUTION CHECKS =====
            print("📋 STAGE 1: Pre-execution checks...")
            pre_checks = await self._pre_execution_checks(opportunity, username, is_aigentsy)
            result['stages']['pre_checks'] = pre_checks
            
            if not pre_checks['passed']:
                result['status'] = 'rejected'
                result['reason'] = pre_checks['reason']
                return result
            
            # ===== STAGE 2: FINANCING (P2P) =====
            print("💰 STAGE 2: Financing setup...")
            financing = await self._setup_financing(opportunity, username, is_aigentsy)
            result['stages']['financing'] = financing
            
            # ===== STAGE 3: EXECUTION =====
            print("⚡ STAGE 3: Executing work...")
            execution = await self._execute_work(opportunity, capability, username, is_aigentsy)
            result['stages']['execution'] = execution
            
            if not execution['success']:
                result['status'] = 'failed'
                result['reason'] = execution.get('error')
                return result
            
            # ===== STAGE 4: DELIVERY =====
            print("📦 STAGE 4: Delivering results...")
            delivery = await self._deliver_results(opportunity, execution, username, is_aigentsy)
            result['stages']['delivery'] = delivery
            
            # ===== STAGE 5: PAYMENT =====
            print("💵 STAGE 5: Processing payment...")
            payment = await self._process_payment(opportunity, delivery, username, is_aigentsy)
            result['stages']['payment'] = payment
            
            # ===== STAGE 6: POST-EXECUTION =====
            print("🚀 STAGE 6: Post-execution optimization...")
            post_exec = await self._post_execution(opportunity, payment, username, is_aigentsy)
            result['stages']['post_execution'] = post_exec
            
            result['status'] = 'completed'
            result['completed_at'] = datetime.now(timezone.utc).isoformat()
            
            print(f"\n✅ EXECUTION COMPLETE: {execution_id}")
            print(f"   Revenue: ${payment.get('amount', 0):,.2f}")
            print(f"   Duration: {result['completed_at']}\n")
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"❌ EXECUTION FAILED: {str(e)}\n")
        
        # Track execution
        self.executions.append(result)
        
        return result
    
    
    async def _pre_execution_checks(
        self,
        opportunity: Dict,
        username: Optional[str],
        is_aigentsy: bool
    ) -> Dict[str, Any]:
        """
        Stage 1: Pre-execution validation
        - Fraud detection
        - Compliance checks
        - Risk assessment
        """
        
        checks = {
            'passed': True,
            'reason': None,
            'fraud_score': 0,
            'compliance_ok': True,
            'risk_level': 'low'
        }
        
        # Fraud detection
        if FRAUD_DETECTION_AVAILABLE:
            try:
                fraud_signals = check_fraud_signals({
                    'opportunity': opportunity,
                    'username': username,
                    'executor': 'aigentsy' if is_aigentsy else username
                })
                
                checks['fraud_score'] = fraud_signals.get('score', 0)
                
                if fraud_signals.get('score', 0) > 0.7:
                    checks['passed'] = False
                    checks['reason'] = 'High fraud risk detected'
                    return checks
            except Exception as e:
                print(f"⚠️ Fraud check error: {e}")
        
        # Compliance check
        if COMPLIANCE_AVAILABLE:
            try:
                compliance = check_transaction_allowed({
                    'amount': opportunity.get('value', 0),
                    'platform': opportunity.get('platform'),
                    'user': username
                })
                
                checks['compliance_ok'] = compliance.get('allowed', True)
                
                if not compliance.get('allowed'):
                    checks['passed'] = False
                    checks['reason'] = 'Compliance violation'
                    return checks
            except Exception as e:
                print(f"⚠️ Compliance check error: {e}")
        
        return checks
    
    
    async def _setup_financing(
        self,
        opportunity: Dict,
        username: Optional[str],
        is_aigentsy: bool
    ) -> Dict[str, Any]:
        """
        Stage 2: Setup P2P financing if needed
        - OCL P2P (users stake on users)
        - Factoring offers (advance on future payment)
        - Performance bonds (optional guarantees)
        """
        
        financing = {
            'needed': False,
            'ocl_loan': None,
            'factoring_offer': None,
            'bond': None
        }
        
        estimated_cost = opportunity.get('estimated_cost', 0)
        
        # Only for user opportunities (not AiGentsy)
        if not is_aigentsy and estimated_cost > 0:
            financing['needed'] = True
            
            # Check P2P OCL availability
            if OCL_P2P_AVAILABLE and username:
                try:
                    # Get available stakes from other users
                    stakes = get_available_stakes(
                        amount_needed=estimated_cost,
                        user_requesting=username
                    )
                    
                    if stakes and stakes.get('total_available', 0) >= estimated_cost:
                        # Request P2P loan
                        loan = request_loan(
                            username=username,
                            amount=estimated_cost,
                            purpose='execution_funding',
                            opportunity_id=opportunity['id']
                        )
                        
                        financing['ocl_loan'] = {
                            'amount': loan.get('amount', 0),
                            'stakers': loan.get('stakers', []),
                            'terms': loan.get('terms', {})
                        }
                        
                        print(f"   💰 P2P Loan secured: ${estimated_cost:,.2f} from {len(loan.get('stakers', []))} stakers")
                except Exception as e:
                    print(f"   ⚠️ P2P loan error: {e}")
            
            # Offer factoring (advance on payment)
            if FACTORING_AVAILABLE and username:
                try:
                    tier = calculate_factoring_tier(username)
                    
                    if tier.get('eligible'):
                        financing['factoring_offer'] = {
                            'tier': tier.get('tier'),
                            'advance_rate': tier.get('advance_rate', 0.7),
                            'fee': tier.get('fee', 0.05),
                            'available': True
                        }
                        
                        print(f"   💵 Factoring available: {tier.get('advance_rate', 0)*100}% advance")
                except Exception as e:
                    print(f"   ⚠️ Factoring check error: {e}")
        
        return financing
    
    
    async def _execute_work(
        self,
        opportunity: Dict,
        capability: Dict,
        username: Optional[str],
        is_aigentsy: bool
    ) -> Dict[str, Any]:
        """
        Stage 3: Actually execute the work
        - AiGentsy opportunities: Use universal_executor (Wade's autonomous system)
        - User opportunities: Use universal_executor (User's autonomous system)
        """
        
        execution = {
            'success': False,
            'method': None,
            'output': None,
            'error': None
        }
        
        # Try autonomous execution first
        if AUTONOMOUS_EXECUTION_AVAILABLE:
            try:
                print(f"   🤖 Using autonomous executor...")
                
                executor = get_executor()
                
                # Execute autonomously
                exec_result = await executor.execute_opportunity(
                    opportunity=opportunity,
                    auto_approve=True  # Already approved via 4-stage approval
                )
                
                execution['success'] = exec_result.get('stage') in ['submitted', 'completed']
                execution['method'] = 'autonomous'
                execution['output'] = exec_result
                
                if execution['success']:
                    print(f"   ✅ Autonomous execution successful")
                else:
                    print(f"   ⚠️ Autonomous execution incomplete: {exec_result.get('stage')}")
                
            except Exception as e:
                print(f"   ❌ Autonomous execution error: {e}")
                execution['error'] = str(e)
        
        # Fallback to engagement-based execution
        if not execution['success']:
            try:
                print(f"   📧 Using engagement-based execution...")
                
                # Score opportunity
                score = self.scorer.score_opportunity(opportunity, capability)
                
                # Engage (send proposal/message)
                engagement_result = await self.engagement.engage(
                    opportunity=opportunity,
                    pricing={'final_price': opportunity.get('value', 0)},
                    score=score
                )
                
                execution['success'] = engagement_result.get('sent', False)
                execution['method'] = 'engagement'
                execution['output'] = engagement_result
                
                print(f"   ✅ Engagement sent")
                
            except Exception as e:
                print(f"   ❌ Engagement error: {e}")
                execution['error'] = str(e)
        
        return execution
    
    
    async def _deliver_results(
        self,
        opportunity: Dict,
        execution: Dict,
        username: Optional[str],
        is_aigentsy: bool
    ) -> Dict[str, Any]:
        """
        Stage 4: Deliver results to client
        - Submit PR (GitHub)
        - Submit proposal (Upwork)
        - Post content (Reddit/Twitter)
        - Send deliverables (Email)
        """
        
        delivery = {
            'delivered': False,
            'method': None,
            'proof': None
        }
        
        # If autonomous execution, delivery is already done
        if execution.get('method') == 'autonomous':
            exec_output = execution.get('output', {})
            
            delivery['delivered'] = True
            delivery['method'] = 'autonomous_submission'
            delivery['proof'] = {
                'submission_id': exec_output.get('submission_id'),
                'submission_url': exec_output.get('submission_url'),
                'stage': exec_output.get('stage')
            }
            
            print(f"   ✅ Delivered via autonomous submission")
        
        # If engagement-based, mark as delivered when proposal sent
        elif execution.get('method') == 'engagement':
            delivery['delivered'] = True
            delivery['method'] = 'engagement_proposal'
            delivery['proof'] = execution.get('output')
            
            print(f"   ✅ Delivered via engagement proposal")
        
        return delivery
    
    
    async def _process_payment(
        self,
        opportunity: Dict,
        delivery: Dict,
        username: Optional[str],
        is_aigentsy: bool
    ) -> Dict[str, Any]:
        """
        Stage 5: Process payment
        - AiGentsy opportunities: Wade's Stripe account
        - User opportunities: User's business/Stripe
        - Track via payment_collector
        - Record via revenue_flows
        """
        
        amount = opportunity.get('value', 0)
        platform = opportunity.get('platform')
        
        payment = {
            'amount': amount,
            'recipient': 'aigentsy' if is_aigentsy else username,
            'stripe_account': 'wade_stripe' if is_aigentsy else f'{username}_stripe',
            'status': 'pending',
            'tracked': False
        }
        
        # Calculate fees
        fees = calculate_base_fee(amount)
        
        if is_aigentsy:
            # AiGentsy opportunity - Wade gets 70% margin
            payment['gross'] = amount
            payment['cost'] = amount * 0.30
            payment['net'] = amount * 0.70
            payment['aigentsy_revenue'] = amount * 0.70
        else:
            # User opportunity - User gets 97.2%, AiGentsy gets 2.8%
            payment['gross'] = amount
            payment['platform_fee'] = fees['total']
            payment['user_revenue'] = amount * 0.972
            payment['aigentsy_revenue'] = fees['total']
        
        # Track payment
        if PAYMENT_TRACKING_AVAILABLE:
            try:
                await record_revenue(
                    execution_id=delivery.get('proof', {}).get('submission_id', 'unknown'),
                    platform=platform,
                    value=amount,
                    user=username,
                    status='pending'
                )
                
                payment['tracked'] = True
                print(f"   ✅ Payment tracked: ${amount:,.2f}")
            except Exception as e:
                print(f"   ⚠️ Payment tracking error: {e}")
        
        # Record in revenue_flows
        try:
            if is_aigentsy:
                # AiGentsy service payment
                await ingest_service_payment(
                    username='aigentsy',
                    amount=payment['net'],
                    platform=platform,
                    service_type=opportunity.get('type', 'general')
                )
            else:
                # User service payment
                await ingest_service_payment(
                    username=username,
                    amount=payment['user_revenue'],
                    platform=platform,
                    service_type=opportunity.get('type', 'general')
                )
            
            print(f"   ✅ Revenue recorded")
        except Exception as e:
            print(f"   ⚠️ Revenue recording error: {e}")
        
        # Credit AIGx to user (for platform activity)
        if not is_aigentsy and username:
            try:
                aigx_earned = amount * 0.001  # 0.1% of transaction value as AIGx
                credit_aigx(username, aigx_earned, 'execution_completion')
                print(f"   🪙 AIGx credited: {aigx_earned} AIGx")
            except Exception as e:
                print(f"   ⚠️ AIGx credit error: {e}")
        
        return payment
    
    
    async def _post_execution(
        self,
        opportunity: Dict,
        payment: Dict,
        username: Optional[str],
        is_aigentsy: bool
    ) -> Dict[str, Any]:
        """
        Stage 6: Post-execution optimization
        - R3 autopilot (auto-reinvest 20%)
        - AMG optimization (improve next opportunities)
        - Growth agent (scale what works)
        - Analytics (track performance)
        - Auto-close won proposals
        """
        
        post_exec = {
            'reinvestment': None,
            'optimization': None,
            'analytics': None,
            'growth': None
        }
        
        revenue = payment.get('user_revenue' if not is_aigentsy else 'net', 0)
        
        # R3 Autopilot - auto-reinvest 20%
        if R3_AVAILABLE and not is_aigentsy and username:
            try:
                reinvest_amount = revenue * 0.20
                
                r3_result = await execute_autopilot_spend(
                    username=username,
                    amount=reinvest_amount
                )
                
                post_exec['reinvestment'] = {
                    'amount': reinvest_amount,
                    'allocated_to': r3_result.get('allocations', [])
                }
                
                print(f"   🔄 R3 reinvested: ${reinvest_amount:,.2f}")
            except Exception as e:
                print(f"   ⚠️ R3 error: {e}")
        
        # AMG Optimization
        if AMG_AVAILABLE and username:
            try:
                amg = AMGOrchestrator()
                optimization = await amg.optimize_revenue(username)
                
                post_exec['optimization'] = optimization
                print(f"   📊 AMG optimized")
            except Exception as e:
                print(f"   ⚠️ AMG error: {e}")
        
        # Analytics tracking
        if ANALYTICS_AVAILABLE and username:
            try:
                metrics = calculate_agent_metrics(username)
                post_exec['analytics'] = metrics
                print(f"   📈 Analytics updated")
            except Exception as e:
                print(f"   ⚠️ Analytics error: {e}")
        
        # Auto-close won proposals
        if AUTOCLOSE_AVAILABLE and username:
            try:
                await auto_close_won_proposals(username)
                print(f"   ✅ Won proposals auto-closed")
            except Exception as e:
                print(f"   ⚠️ Auto-close error: {e}")
        
        # Growth agent - scale what works
        if GROWTH_AGENT_AVAILABLE and not is_aigentsy and username:
            try:
                # If this opportunity type succeeded, find more like it
                growth = await launch_growth_campaign(
                    username=username,
                    successful_opportunity=opportunity
                )
                
                post_exec['growth'] = growth
                print(f"   🚀 Growth campaign launched")
            except Exception as e:
                print(f"   ⚠️ Growth error: {e}")
        
        return post_exec
    
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        
        total = len(self.executions)
        completed = len([e for e in self.executions if e.get('status') == 'completed'])
        failed = len([e for e in self.executions if e.get('status') in ['failed', 'error']])
        
        return {
            'total_executions': total,
            'completed': completed,
            'failed': failed,
            'success_rate': (completed / total * 100) if total > 0 else 0,
            'recent_executions': self.executions[-10:]
        }
