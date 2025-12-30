"""
AiGentsy Integration Layer - Universal Discovery → Week 2 Automation Bridge
Connects Wade's 27-platform discovery system with specialized automation engines

INTEGRATION FLOW:
Universal Discovery (27 platforms) → Intelligent Router → Specialized Workers → Delivery

CURRENT AI WORKERS:
✅ Claude (code, content, analysis) 
✅ Graphics Engine (Stable Diffusion)
✅ ChatGPT (chatbots via openai_agent_deployer)

NEXT PHASE: Multi-AI orchestration as per master plan
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import existing systems
from ultimate_discovery_engine import discover_all_opportunities, get_wade_fulfillment_queue
from week2_master_orchestrator import Week2MasterOrchestrator
from graphics_engine import GraphicsEngine


@dataclass
class WorkerCapability:
    """Define what each AI worker can do"""
    worker_id: str
    name: str
    capabilities: List[str]
    cost_per_task: float
    quality_score: float
    speed_score: float
    platforms: List[str]
    max_concurrent: int


class IntelligentRouter:
    """
    Central nervous system - routes opportunities to best AI workers
    This is the core of the universal AI orchestration system
    """
    
    def __init__(self):
        self.ai_workers = self._initialize_workers()
        self.routing_history = []
        self.performance_metrics = {}
    
    def _initialize_workers(self) -> Dict[str, WorkerCapability]:
        """Initialize available AI workers and their capabilities"""
        
        return {
            'claude': WorkerCapability(
                worker_id='claude',
                name='Claude Sonnet 4',
                capabilities=[
                    'code_generation', 'content_writing', 'analysis', 
                    'documentation', 'debugging', 'api_development',
                    'technical_writing', 'project_planning'
                ],
                cost_per_task=0.50,
                quality_score=0.95,
                speed_score=0.90,
                platforms=['github', 'upwork', 'freelancer', 'stackoverflow'],
                max_concurrent=10
            ),
            
            'graphics_engine': WorkerCapability(
                worker_id='graphics_engine',
                name='AI Graphics Engine (Stable Diffusion)',
                capabilities=[
                    'logo_design', 'social_media_graphics', 'marketing_assets',
                    'business_cards', 'flyers', 'banners', 'illustrations',
                    'product_images', 'brand_identity'
                ],
                cost_per_task=0.012,  # $0.004 per image * 3 images
                quality_score=0.85,
                speed_score=0.80,
                platforms=['fiverr', '99designs', 'dribbble', 'upwork'],
                max_concurrent=5
            ),
            
            'video_engine': WorkerCapability(
                worker_id='video_engine',
                name='AI Video Engine (Multi-Worker)',
                capabilities=[
                    'explainer_videos', 'advertisement_videos', 'social_media_videos',
                    'testimonial_videos', 'training_videos', 'product_demos',
                    'animated_content', 'ai_presenter_videos', 'video_editing'
                ],
                cost_per_task=15.00,  # $5-50 depending on length/quality
                quality_score=0.88,
                speed_score=0.75,    # Video takes longer than graphics
                platforms=['fiverr', 'upwork', 'youtube', 'vimeo'],
                max_concurrent=3     # Limit concurrent video generation
            ),
            
            'chatgpt_agent': WorkerCapability(
                worker_id='chatgpt_agent',
                name='ChatGPT Agent Deployer',
                capabilities=[
                    'chatbot_creation', 'customer_service', 'lead_qualification',
                    'appointment_scheduling', 'faq_automation', 'conversation_flows'
                ],
                cost_per_task=2.00,
                quality_score=0.80,
                speed_score=0.95,
                platforms=['shopify', 'wordpress', 'custom_websites'],
                max_concurrent=3
            ),
            
            'template_actionizer': WorkerCapability(
                worker_id='template_actionizer',
                name='Business Template System',
                capabilities=[
                    'website_deployment', 'store_setup', 'landing_pages',
                    'ecommerce_stores', 'saas_deployment', 'business_automation'
                ],
                cost_per_task=10.00,
                quality_score=0.90,
                speed_score=0.70,
                platforms=['shopify', 'wordpress', 'webflow', 'custom'],
                max_concurrent=2
            )
        }
    
    async def analyze_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze opportunity and determine best fulfillment approach
        This is the intelligence layer that makes routing decisions
        """
        
        title = opportunity.get('title', '').lower()
        description = opportunity.get('description', '').lower()
        platform = opportunity.get('source', '')
        estimated_value = opportunity.get('estimated_value', 0)
        
        # Extract work type indicators
        work_indicators = {
            'code': ['code', 'api', 'bug', 'debug', 'script', 'function', 'programming', 'software', 'app'],
            'graphics': ['logo', 'design', 'graphic', 'banner', 'flyer', 'illustration', 'visual', 'brand'],
            'video': ['video', 'explainer', 'animation', 'commercial', 'ad', 'promo', 'tutorial', 'demo'],
            'content': ['blog', 'article', 'content', 'writing', 'copy', 'documentation'],
            'chatbot': ['chatbot', 'bot', 'assistant', 'customer service', 'automation'],
            'website': ['website', 'site', 'landing', 'store', 'ecommerce', 'shopify']
        }
        
        # Score each work type
        type_scores = {}
        full_text = f"{title} {description}".lower()
        
        for work_type, keywords in work_indicators.items():
            score = sum(1 for keyword in keywords if keyword in full_text)
            type_scores[work_type] = score
        
        # Determine primary work type
        primary_type = max(type_scores.items(), key=lambda x: x[1])[0] if any(type_scores.values()) else 'general'
        
        # Calculate complexity and urgency
        complexity = self._assess_complexity(opportunity)
        urgency = self._assess_urgency(opportunity)
        budget_tier = self._assess_budget_tier(estimated_value)
        
        analysis = {
            'opportunity_id': opportunity.get('id'),
            'primary_work_type': primary_type,
            'type_scores': type_scores,
            'complexity': complexity,
            'urgency': urgency,
            'budget_tier': budget_tier,
            'platform': platform,
            'estimated_value': estimated_value,
            'quality_requirements': self._determine_quality_requirements(platform, estimated_value),
            'analyzed_at': datetime.now(timezone.utc).isoformat()
        }
        
        return analysis
    
    def _assess_complexity(self, opportunity: Dict[str, Any]) -> str:
        """Assess task complexity: simple, medium, complex"""
        
        description = opportunity.get('description', '').lower()
        title = opportunity.get('title', '').lower()
        value = opportunity.get('estimated_value', 0)
        
        complex_indicators = ['custom', 'advanced', 'complex', 'enterprise', 'integration', 'multi', 'full-stack']
        simple_indicators = ['simple', 'basic', 'quick', 'small', 'minor', 'fix']
        
        complexity_score = 0
        
        # Check indicators
        for indicator in complex_indicators:
            if indicator in description or indicator in title:
                complexity_score += 2
        
        for indicator in simple_indicators:
            if indicator in description or indicator in title:
                complexity_score -= 1
        
        # Factor in budget
        if value > 1000:
            complexity_score += 1
        elif value < 100:
            complexity_score -= 1
        
        if complexity_score >= 2:
            return 'complex'
        elif complexity_score <= -1:
            return 'simple'
        else:
            return 'medium'
    
    def _assess_urgency(self, opportunity: Dict[str, Any]) -> str:
        """Assess urgency: low, medium, high"""
        
        text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()
        
        urgent_keywords = ['urgent', 'asap', 'immediately', 'rush', 'emergency', 'today', 'now']
        relaxed_keywords = ['flexible', 'whenever', 'no rush', 'eventually']
        
        if any(keyword in text for keyword in urgent_keywords):
            return 'high'
        elif any(keyword in text for keyword in relaxed_keywords):
            return 'low'
        else:
            return 'medium'
    
    def _assess_budget_tier(self, estimated_value: float) -> str:
        """Categorize budget level"""
        
        if estimated_value >= 1000:
            return 'premium'
        elif estimated_value >= 300:
            return 'standard'
        elif estimated_value >= 50:
            return 'basic'
        else:
            return 'micro'
    
    def _determine_quality_requirements(self, platform: str, estimated_value: float) -> str:
        """Determine required quality level"""
        
        high_quality_platforms = ['toptal', '99designs', 'dribbble']
        premium_budget = estimated_value >= 500
        
        if platform in high_quality_platforms or premium_budget:
            return 'premium'
        elif estimated_value >= 100:
            return 'standard'
        else:
            return 'basic'
    
    async def select_ai_worker(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select the best AI worker for the analyzed opportunity
        This is where the intelligent routing happens
        """
        
        work_type = analysis['primary_work_type']
        complexity = analysis['complexity']
        quality_req = analysis['quality_requirements']
        budget = analysis['estimated_value']
        platform = analysis['platform']
        
        # Map work types to workers
        worker_mapping = {
            'code': ['claude'],
            'graphics': ['graphics_engine'],
            'video': ['video_engine'],
            'content': ['claude'],
            'chatbot': ['chatgpt_agent'],
            'website': ['template_actionizer', 'claude'],
            'general': ['claude']
        }
        
        candidate_workers = worker_mapping.get(work_type, ['claude'])
        
        # Score each candidate worker
        worker_scores = {}
        
        for worker_id in candidate_workers:
            if worker_id not in self.ai_workers:
                continue
                
            worker = self.ai_workers[worker_id]
            score = 0
            
            # Capability match
            if work_type in ['code', 'content', 'general'] and 'claude' == worker_id:
                score += 0.9
            elif work_type == 'graphics' and 'graphics_engine' == worker_id:
                score += 0.9
            elif work_type == 'video' and 'video_engine' == worker_id:
                score += 0.95
            elif work_type == 'chatbot' and 'chatgpt_agent' == worker_id:
                score += 0.9
            elif work_type == 'website' and 'template_actionizer' == worker_id:
                score += 0.8
            
            # Quality match
            if quality_req == 'premium' and worker.quality_score >= 0.9:
                score += 0.2
            elif quality_req == 'standard' and worker.quality_score >= 0.8:
                score += 0.1
            
            # Cost efficiency
            if budget > 0:
                cost_efficiency = min(1.0, budget / (worker.cost_per_task * 10))
                score += cost_efficiency * 0.1
            
            # Platform compatibility
            if platform in worker.platforms:
                score += 0.1
            
            worker_scores[worker_id] = score
        
        # Select best worker
        if not worker_scores:
            selected_worker_id = 'claude'  # Fallback
        else:
            selected_worker_id = max(worker_scores.items(), key=lambda x: x[1])[0]
        
        selected_worker = self.ai_workers[selected_worker_id]
        
        # Calculate execution plan
        execution_plan = {
            'primary_worker': selected_worker_id,
            'worker_details': selected_worker,
            'backup_worker': 'claude' if selected_worker_id != 'claude' else 'graphics_engine',
            'estimated_cost': selected_worker.cost_per_task,
            'estimated_time_hours': self._estimate_time(complexity, selected_worker.speed_score),
            'quality_assurance': self._plan_quality_assurance(quality_req),
            'routing_score': worker_scores.get(selected_worker_id, 0),
            'routing_confidence': min(1.0, worker_scores.get(selected_worker_id, 0))
        }
        
        return execution_plan
    
    def _estimate_time(self, complexity: str, speed_score: float) -> float:
        """Estimate completion time in hours"""
        
        base_hours = {
            'simple': 1,
            'medium': 3,
            'complex': 8
        }
        
        base = base_hours.get(complexity, 3)
        adjusted = base / speed_score
        
        return round(adjusted, 1)
    
    def _plan_quality_assurance(self, quality_req: str) -> Dict[str, Any]:
        """Plan quality assurance approach"""
        
        qa_plans = {
            'basic': {
                'review_required': False,
                'testing_level': 'basic',
                'approval_needed': False
            },
            'standard': {
                'review_required': True,
                'testing_level': 'standard',
                'approval_needed': True
            },
            'premium': {
                'review_required': True,
                'testing_level': 'comprehensive',
                'approval_needed': True,
                'second_review': True
            }
        }
        
        return qa_plans.get(quality_req, qa_plans['standard'])


class IntegratedOrchestrator:
    """
    Master orchestrator that combines Universal Discovery with AI execution
    This is the main coordination layer
    """
    
    def __init__(self):
        self.router = IntelligentRouter()
        self.graphics_engine = None
        self.week2_orchestrator = None
        self.execution_queue = []
        self.active_tasks = {}
        
    async def initialize(self):
        """Initialize all subsystems"""
        
        # Initialize graphics engine
        try:
            from graphics_engine import GraphicsEngine
            self.graphics_engine = GraphicsEngine()
            print("✅ Graphics engine initialized")
        except Exception as e:
            print(f"⚠️  Graphics engine initialization failed: {e}")
        
        # Initialize Week 2 orchestrator if needed
        try:
            from week2_master_orchestrator import Week2MasterOrchestrator
            if self.graphics_engine:
                self.week2_orchestrator = Week2MasterOrchestrator(self.graphics_engine)
                print("✅ Week 2 orchestrator initialized")
        except Exception as e:
            print(f"⚠️  Week 2 orchestrator initialization failed: {e}")
    
    async def full_discovery_and_execution_cycle(self, username: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete cycle: Universal Discovery → Intelligent Routing → AI Execution
        This is the main entry point for the integrated system
        """
        
        print("🔄 STARTING INTEGRATED DISCOVERY & EXECUTION CYCLE")
        print("=" * 60)
        
        # Phase 1: Universal Discovery (use existing system)
        print("🔍 Phase 1: Universal Discovery (27+ platforms)")
        discovery_results = await discover_all_opportunities(username, user_profile)
        
        if not discovery_results['ok']:
            return {'success': False, 'error': 'Discovery failed', 'details': discovery_results}
        
        total_opportunities = len(discovery_results['opportunities'])
        wade_opportunities = discovery_results['routing']['wade']
        
        print(f"✅ Discovery complete: {total_opportunities} total, {len(wade_opportunities)} for Wade")
        
        # Phase 2: Intelligent Analysis & Routing
        print("\n🧠 Phase 2: Intelligent Analysis & Routing")
        routing_results = []
        
        for opp in wade_opportunities:
            # Analyze opportunity
            analysis = await self.router.analyze_opportunity(opp)
            
            # Select best AI worker
            execution_plan = await self.router.select_ai_worker(analysis)
            
            routing_result = {
                'opportunity': opp,
                'analysis': analysis,
                'execution_plan': execution_plan,
                'routed_at': datetime.now(timezone.utc).isoformat()
            }
            
            routing_results.append(routing_result)
            
            print(f"   📍 {opp['id']}: {analysis['primary_work_type']} → {execution_plan['primary_worker']}")
        
        # Phase 3: Execution Planning
        print(f"\n⚡ Phase 3: Execution Planning")
        
        # Group by worker type for batch processing
        grouped_tasks = {}
        for result in routing_results:
            worker = result['execution_plan']['primary_worker']
            if worker not in grouped_tasks:
                grouped_tasks[worker] = []
            grouped_tasks[worker].append(result)
        
        execution_summary = {}
        total_estimated_cost = 0
        total_estimated_revenue = 0
        
        for worker, tasks in grouped_tasks.items():
            task_count = len(tasks)
            estimated_cost = sum(t['execution_plan']['estimated_cost'] for t in tasks)
            estimated_revenue = sum(t['opportunity'].get('estimated_value', 0) for t in tasks)
            estimated_profit = estimated_revenue - estimated_cost
            
            execution_summary[worker] = {
                'task_count': task_count,
                'estimated_cost': estimated_cost,
                'estimated_revenue': estimated_revenue,
                'estimated_profit': estimated_profit,
                'roi': (estimated_profit / estimated_cost * 100) if estimated_cost > 0 else float('inf')
            }
            
            total_estimated_cost += estimated_cost
            total_estimated_revenue += estimated_revenue
            
            print(f"   🤖 {worker}: {task_count} tasks, ${estimated_cost:.2f} cost, ${estimated_revenue:.0f} revenue")
        
        # Phase 4: Queue for Execution
        self.execution_queue.extend(routing_results)
        
        integrated_results = {
            'success': True,
            'cycle_id': f"integrated_{datetime.now().timestamp()}",
            'discovery_results': {
                'total_opportunities': total_opportunities,
                'wade_opportunities': len(wade_opportunities),
                'platforms_scanned': discovery_results['platforms_scraped']
            },
            'routing_results': {
                'analyzed_opportunities': len(routing_results),
                'worker_distribution': {w: len(tasks) for w, tasks in grouped_tasks.items()},
                'total_estimated_cost': total_estimated_cost,
                'total_estimated_revenue': total_estimated_revenue,
                'total_estimated_profit': total_estimated_revenue - total_estimated_cost
            },
            'execution_summary': execution_summary,
            'queued_for_execution': len(self.execution_queue),
            'next_steps': [
                'Execute queued tasks via process_execution_queue()',
                'Monitor task completion and quality',
                'Deliver to platforms and collect revenue',
                'Analyze performance and optimize routing'
            ]
        }
        
        print(f"\n✅ INTEGRATED CYCLE COMPLETE")
        print(f"   💰 Estimated Revenue: ${total_estimated_revenue:.0f}")
        print(f"   💸 Estimated Cost: ${total_estimated_cost:.2f}")
        print(f"   📈 Estimated Profit: ${total_estimated_revenue - total_estimated_cost:.0f}")
        print(f"   🎯 ROI: {((total_estimated_revenue - total_estimated_cost) / total_estimated_cost * 100):.1f}%" if total_estimated_cost > 0 else "   🎯 ROI: ∞%")
        print("=" * 60)
        
        return integrated_results
    
    async def execute_queued_task(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single queued task using the appropriate AI worker
        """
        
        opportunity = task_result['opportunity']
        execution_plan = task_result['execution_plan']
        worker = execution_plan['primary_worker']
        
        print(f"🔨 Executing {opportunity['id']} with {worker}")
        
        try:
            if worker == 'graphics_engine':
                result = await self._execute_graphics_task(opportunity)
            elif worker == 'video_engine':
                result = await self._execute_video_task(opportunity)
            elif worker == 'claude':
                result = await self._execute_claude_task(opportunity)
            elif worker == 'chatgpt_agent':
                result = await self._execute_chatgpt_task(opportunity)
            elif worker == 'template_actionizer':
                result = await self._execute_template_task(opportunity)
            else:
                result = {'success': False, 'error': f'Unknown worker: {worker}'}
            
            return {
                'success': result['success'],
                'opportunity_id': opportunity['id'],
                'worker': worker,
                'result': result,
                'executed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'opportunity_id': opportunity['id'],
                'worker': worker,
                'error': str(e),
                'executed_at': datetime.now(timezone.utc).isoformat()
            }
    
    async def _execute_graphics_task(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute graphics task using graphics engine"""
        
        if not self.graphics_engine:
            return {'success': False, 'error': 'Graphics engine not available'}
        
        result = await self.graphics_engine.process_graphics_opportunity(opportunity)
        return result
    
    async def _execute_video_task(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute video task using video engine"""
        
        try:
            from video_engine import VideoEngine
            
            video_engine = VideoEngine()
            result = await video_engine.process_video_opportunity(opportunity)
            return result
            
        except ImportError:
            return {
                'success': False,
                'error': 'Video engine not available',
                'fallback': 'Install video engine dependencies'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Video execution error: {str(e)}'
            }
    
    async def _execute_claude_task(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code/content task using Claude"""
        
        # This would integrate with your existing Claude execution system
        # For now, return a placeholder
        return {
            'success': True,
            'deliverable_type': 'code_or_content',
            'message': 'Claude task execution not yet implemented in integration layer'
        }
    
    async def _execute_chatgpt_task(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chatbot task using ChatGPT agent deployer"""
        
        # This would integrate with your existing openai_agent_deployer
        return {
            'success': True,
            'deliverable_type': 'chatbot',
            'message': 'ChatGPT agent task execution not yet implemented in integration layer'
        }
    
    async def _execute_template_task(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Execute business deployment task using template actionizer"""
        
        # This would integrate with your existing template_actionizer
        return {
            'success': True,
            'deliverable_type': 'business_deployment',
            'message': 'Template actionizer execution not yet implemented in integration layer'
        }


# Export main classes
__all__ = ['IntegratedOrchestrator', 'IntelligentRouter']


# Test function for development
async def test_integration_system():
    """Test the integration layer"""
    
    orchestrator = IntegratedOrchestrator()
    await orchestrator.initialize()
    
    # Test user profile
    test_profile = {
        'skills': ['web development', 'graphic design', 'content writing'],
        'kits': {'universal': {'unlocked': True}},
        'region': 'Global'
    }
    
    # Run integration test
    result = await orchestrator.full_discovery_and_execution_cycle('test_user', test_profile)
    
    print("\n🧪 Integration Test Results:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(test_integration_system())
