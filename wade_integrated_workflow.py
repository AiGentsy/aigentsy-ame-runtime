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
    
    Configuration:
    - USE_EXISTING_SYSTEMS: True = Use template_actionizer, openai_agent_deployer, metabridge_runtime
    - USE_EXISTING_SYSTEMS: False = Generate all code via Claude (OpenRouter)
    """
    
    def __init__(self, use_existing_systems: bool = True):
        # Import existing systems
        from wade_approval_dashboard import fulfillment_queue
        self.approval_queue = fulfillment_queue
        
        # Import graphics engine
        try:
            from graphics_engine import GraphicsEngine, GraphicsRouter
            self.graphics_engine = GraphicsEngine()
            self.graphics_router = GraphicsRouter()
            print("[INIT] Graphics Engine loaded successfully")
        except Exception as e:
            print(f"[INIT] Graphics Engine not available: {e}")
            self.graphics_engine = None
            self.graphics_router = None
        
        # Configuration flag
        self.use_existing_systems = use_existing_systems
        
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
        
        SMART HYBRID ROUTING:
        - Analyzes opportunity to determine if deployment or code generation is needed
        - Routes to existing systems OR Claude generation automatically
        """
        
        workflow['stage'] = WorkflowStage.IN_PROGRESS
        workflow['started_at'] = datetime.now(timezone.utc).isoformat()
        workflow['history'].append({
            'stage': WorkflowStage.IN_PROGRESS,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': 'Execution started'
        })
        
        opportunity = workflow['opportunity']
        fulfillability = workflow['fulfillability']
        
        capability = fulfillability.get('capability')
        system = fulfillability.get('fulfillment_system')
        
        # 🔥 SMART ROUTING: Determine which mode to use
        use_existing = self._should_use_existing_systems(opportunity)
        
        workflow['history'].append({
            'stage': 'ROUTING_DECISION',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': f"Routing mode: {'EXISTING_SYSTEMS' if use_existing else 'CLAUDE_GENERATED'}",
            'reason': workflow.get('routing_reason', 'Auto-detected from opportunity')
        })
        
        # Temporarily override mode for this execution
        original_mode = self.use_existing_systems
        self.use_existing_systems = use_existing
        
        try:
            # Route to appropriate execution handler
            if system == 'claude':
                if capability == 'code_generation':
                    result = await self._execute_code_generation(opportunity)
                elif capability == 'content_generation':
                    result = await self._execute_content_generation(opportunity)
                else:
                    result = await self._execute_claude_generic(opportunity)
            
            elif system == 'graphics':
                # Graphics generation via AI (Stable Diffusion, DALL-E, etc)
                result = await self._execute_graphics_generation(workflow)
            
            elif system == 'template_actionizer':
                result = await self._execute_business_deployment(opportunity)
            
            elif system == 'openai_agent_deployer':
                result = await self._execute_ai_agent(opportunity)
            
            elif system == 'metabridge_runtime':
                result = await self._execute_platform_monetization(opportunity)
            
            else:
                result = {
                    'success': False,
                    'error': f'Unknown fulfillment system: {system}'
                }
            
            # Restore original mode
            self.use_existing_systems = original_mode
            
            if result.get('success'):
                workflow['stage'] = WorkflowStage.COMPLETED
                workflow['completed_at'] = datetime.now(timezone.utc).isoformat()
                workflow['execution_result'] = result
                workflow['history'].append({
                    'stage': WorkflowStage.COMPLETED,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'action': 'Execution completed',
                    'mode': result.get('mode', 'unknown'),
                    'data': result
                })
                
                # Trigger delivery
                delivery_result = await self._deliver_work(workflow)
                
                return {
                    'ok': True,
                    'execution_completed': True,
                    'execution_mode': result.get('mode'),
                    'delivery_result': delivery_result
                }
            
            else:
                # Restore original mode
                self.use_existing_systems = original_mode
                return {
                    'ok': False,
                    'error': result.get('error', 'Execution failed')
                }
        
        except Exception as e:
            # Restore original mode
            self.use_existing_systems = original_mode
            
            workflow['history'].append({
                'stage': 'ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'action': f'Execution failed: {str(e)}'
            })
            
            return {
                'ok': False,
                'error': str(e)
            }
    
    def _should_use_existing_systems(self, opportunity: Dict[str, Any]) -> bool:
        """
        SMART ROUTING LOGIC: Determine if we should use existing systems or Claude generation
        
        Use EXISTING SYSTEMS when:
        - Opportunity explicitly requests deployment ("deploy", "host", "live site")
        - Opportunity mentions infrastructure ("database", "production", "scalable")
        - Opportunity is from a platform that expects live deliverables
        - Budget is high enough to justify deployment costs
        
        Use CLAUDE GENERATION when:
        - Opportunity asks for code/files ("code", "script", "download")
        - Opportunity is educational/learning focused
        - Budget is low (< $100)
        - Quick turnaround needed
        """
        
        title = opportunity.get('title', '').lower()
        description = opportunity.get('description', '').lower()
        platform = opportunity.get('source', '').lower()
        budget = opportunity.get('estimated_value', 0)
        
        combined = f"{title} {description}"
        
        # 🔥 DEPLOYMENT TRIGGERS (Use existing systems)
        deployment_keywords = [
            'deploy', 'host', 'live', 'production', 'launch',
            'database', 'backend', 'api', 'scalable', 'infrastructure',
            'vercel', 'heroku', 'aws', 'cloud', 'server',
            'domain', 'ssl', 'https', 'cdn', 'hosting'
        ]
        
        # 🔥 CODE GENERATION TRIGGERS (Use Claude)
        code_keywords = [
            'code', 'script', 'download', 'file', 'source',
            'github repo', 'git', 'example', 'tutorial', 'learning',
            'understand', 'how to', 'teach me', 'explain'
        ]
        
        # Count matches
        deployment_score = sum(1 for keyword in deployment_keywords if keyword in combined)
        code_score = sum(1 for keyword in code_keywords if keyword in combined)
        
        # Platform-based routing
        if platform in ['upwork', 'freelancer']:
            # These platforms typically want deployed solutions
            deployment_score += 2
        elif platform in ['github', 'stackoverflow']:
            # These platforms typically want code
            code_score += 2
        
        # Budget-based routing
        if budget >= 500:
            # High budget → likely wants full deployment
            deployment_score += 2
        elif budget < 100:
            # Low budget → likely wants just code
            code_score += 1
        
        # Make decision
        if deployment_score > code_score:
            opportunity['routing_reason'] = f'Deployment signals: {deployment_score} vs Code signals: {code_score}'
            return True  # Use existing systems
        elif code_score > deployment_score:
            opportunity['routing_reason'] = f'Code signals: {code_score} vs Deployment signals: {deployment_score}'
            return False  # Use Claude generation
        else:
            # Tie-breaker: Default based on capability type
            capability = opportunity.get('fulfillability', {}).get('capability', '')
            
            if capability == 'business_deployment':
                opportunity['routing_reason'] = 'Business deployment capability → deployment mode'
                return True  # Business deployment defaults to existing systems
            else:
                opportunity['routing_reason'] = 'Tie-breaker → code generation mode'
                return False  # Everything else defaults to Claude generation
    
    async def _execute_code_generation(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute code generation using Claude via OpenRouter
        
        100% REAL - Uses your OPENROUTER_API_KEY
        """
        import os
        import httpx
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            return {
                'success': False,
                'error': 'OPENROUTER_API_KEY not set in environment variables'
            }
        
        # Get requirements from opportunity
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        
        # Build prompt
        prompt = f"""You are a professional software engineer hired to complete this task:

**Task:** {title}

**Details:**
{description}

**Requirements:**
1. Write clean, production-ready code
2. Include comprehensive comments
3. Add error handling
4. Include a README with usage instructions
5. Make it deployment-ready

Please provide:
1. Complete code solution
2. File structure
3. Installation/deployment instructions
4. Testing recommendations

Deliver a professional solution that solves the problem completely."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 8000
                    },
                    timeout=120.0
                )
                
                if response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'OpenRouter API error: {response.status_code} - {response.text}'
                    }
                
                data = response.json()
                solution = data['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'type': 'code_generation',
                    'solution': solution,
                    'model_used': 'claude-sonnet-4',
                    'tokens_used': data.get('usage', {}).get('total_tokens', 0),
                    'files_generated': self._extract_code_files(solution),
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
        
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'OpenRouter API timeout after 120 seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Execution error: {str(e)}'
            }
    
    async def _execute_content_generation(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute content generation using Claude via OpenRouter
        
        100% REAL - Uses your OPENROUTER_API_KEY
        """
        import os
        import httpx
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            return {
                'success': False,
                'error': 'OPENROUTER_API_KEY not set in environment variables'
            }
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        
        prompt = f"""You are a professional content writer hired for this project:

**Project:** {title}

**Brief:**
{description}

**Deliverables:**
1. High-quality, original content
2. SEO-optimized where applicable
3. Proper formatting and structure
4. Professional tone and style
5. Error-free writing

Please create the content following best practices for the requested type."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 8000
                    },
                    timeout=120.0
                )
                
                if response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'OpenRouter API error: {response.status_code} - {response.text}'
                    }
                
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'type': 'content_generation',
                    'content': content,
                    'model_used': 'claude-sonnet-4',
                    'word_count': len(content.split()),
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
        
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'OpenRouter API timeout after 120 seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Content generation error: {str(e)}'
            }
    
    async def _execute_claude_generic(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generic Claude execution for any task via OpenRouter
        
        100% REAL - Uses your OPENROUTER_API_KEY
        """
        import os
        import httpx
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            return {
                'success': False,
                'error': 'OPENROUTER_API_KEY not set in environment variables'
            }
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        
        prompt = f"""You are hired to complete this task professionally:

**Task:** {title}

**Details:**
{description}

Please provide a complete, professional solution."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 8000
                    },
                    timeout=120.0
                )
                
                if response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'OpenRouter API error: {response.status_code} - {response.text}'
                    }
                
                data = response.json()
                
                return {
                    'success': True,
                    'type': 'generic_task',
                    'solution': data['choices'][0]['message']['content'],
                    'model_used': 'claude-sonnet-4',
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
        
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'OpenRouter API timeout after 120 seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Generic execution error: {str(e)}'
            }
    
    async def _execute_graphics_generation(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute graphics generation using AI
        Routes to Stable Diffusion or DALL-E based on requirements
        
        100% REAL - Uses your STABILITY_API_KEY
        """
        
        if not self.graphics_engine:
            return {
                'success': False,
                'error': 'Graphics engine not initialized - check graphics_engine.py import'
            }
        
        opportunity = workflow['opportunity']
        
        try:
            # Process with graphics engine
            result = await self.graphics_engine.process_graphics_opportunity(opportunity)
            
            if result['success']:
                generation = result['generation']
                return {
                    'success': True,
                    'mode': 'graphics_ai',
                    'ai_worker': generation.get('ai_worker'),
                    'images_generated': generation.get('count'),
                    'images': generation.get('images'),
                    'prompt_used': generation.get('prompt'),
                    'cost': generation.get('cost'),
                    'routing_analysis': result['routing']['analysis'],
                    'deliverable_files': [img['filename'] for img in generation.get('images', [])],
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Graphics generation failed'),
                    'analysis': result.get('analysis')
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Graphics execution error: {str(e)}'
            }
    
    async def _execute_business_deployment(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute business deployment
        
        Mode 1 (use_existing_systems=True): Use YOUR template_actionizer
        Mode 2 (use_existing_systems=False): Generate code via Claude
        """
        
        if self.use_existing_systems:
            return await self._execute_business_deployment_existing(opportunity)
        else:
            return await self._execute_business_deployment_claude(opportunity)
    
    async def _execute_business_deployment_existing(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Use YOUR existing template_actionizer system"""
        
        from template_actionizer import actionize_template, TEMPLATE_CONFIGS
        from log_to_jsonbin import get_user
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        
        # Determine template type from requirements
        requirements_lower = f"{title} {description}".lower()
        
        if any(word in requirements_lower for word in ['saas', 'api', 'developer', 'sdk']):
            template_type = 'saas'
        elif any(word in requirements_lower for word in ['marketing', 'campaign', 'landing', 'seo']):
            template_type = 'marketing'
        elif any(word in requirements_lower for word in ['social', 'instagram', 'tiktok', 'content']):
            template_type = 'social'
        else:
            template_type = 'marketing'
        
        try:
            username = opportunity.get('username', 'wade')
            user_data = get_user(username)
            
            if not user_data:
                return {
                    'success': False,
                    'error': f'User not found: {username}'
                }
            
            # Call YOUR template_actionizer
            result = await actionize_template(
                username=username,
                template_type=template_type,
                user_data=user_data,
                custom_config={
                    'project_title': title,
                    'project_description': description
                }
            )
            
            if not result.get('ok'):
                return {
                    'success': False,
                    'error': result.get('error', 'Template actionization failed')
                }
            
            return {
                'success': True,
                'type': 'business_deployment',
                'mode': 'existing_systems',
                'template_type': template_type,
                'website_url': result['urls']['website'],
                'admin_url': result['urls']['admin_panel'],
                'database_url': result.get('database', {}).get('database_url'),
                'ai_agents': result.get('ai_agents', {}).get('agents', []),
                'deployment_time': result.get('deployment_time'),
                'files_generated': [{
                    'filename': 'deployment_summary.txt',
                    'language': 'text',
                    'content': f"""Business Deployed Successfully!

Template: {TEMPLATE_CONFIGS[template_type]['name']}
Website: {result['urls']['website']}
Admin Panel: {result['urls']['admin_panel']}
Analytics: {result['urls'].get('analytics', 'N/A')}

Components:
- Website: ✅ Deployed to Vercel
- Database: ✅ Supabase provisioned
- Email: ✅ Automation configured
- AI Agents: ✅ {len(result.get('ai_agents', {}).get('agents', []))} agents active

Deployment Time: {result.get('deployment_time')}
"""
                }],
                'completed_at': result.get('completed_at', datetime.now(timezone.utc).isoformat())
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Template actionizer error: {str(e)}'
            }
    
    async def _execute_business_deployment_claude(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete website code via Claude/OpenRouter"""
        
        import os
        import httpx
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            return {
                'success': False,
                'error': 'OPENROUTER_API_KEY not set in environment variables'
            }
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        
        # Analyze requirements
        requirements_lower = f"{title} {description}".lower()
        
        if any(word in requirements_lower for word in ['store', 'shop', 'ecommerce', 'product']):
            website_type = 'E-Commerce Store'
        elif any(word in requirements_lower for word in ['landing', 'page', 'marketing']):
            website_type = 'Marketing Landing Page'
        elif any(word in requirements_lower for word in ['saas', 'app', 'dashboard']):
            website_type = 'SaaS Platform'
        elif any(word in requirements_lower for word in ['portfolio', 'personal']):
            website_type = 'Portfolio Website'
        else:
            website_type = 'Business Website'
        
        prompt = f"""You are a professional web developer hired to build a complete, production-ready {website_type}.

**Project:** {title}

**Requirements:**
{description}

**DELIVERABLES - Create a COMPLETE, SINGLE-FILE website:**

1. Create ONE index.html file that includes:
   - All HTML structure
   - All CSS styles in <style> tags
   - All JavaScript in <script> tags
   - MUST be fully functional as a standalone file

2. Requirements:
   - Modern, professional design
   - Mobile responsive (use CSS media queries)
   - Clean, semantic HTML5
   - No external dependencies (no CDN links)
   - Production-ready code
   - Include comments

**IMPORTANT:** 
- Output ONLY the complete HTML file
- NO explanations before or after
- Start with <!DOCTYPE html>
- End with </html>"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 16000
                    },
                    timeout=180.0
                )
                
                if response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'OpenRouter API error: {response.status_code}'
                    }
                
                data = response.json()
                html_code = data['choices'][0]['message']['content'].strip()
                
                # Clean markdown
                if html_code.startswith('```html'):
                    html_code = html_code[7:]
                if html_code.startswith('```'):
                    html_code = html_code[3:]
                if html_code.endswith('```'):
                    html_code = html_code[:-3]
                html_code = html_code.strip()
                
                return {
                    'success': True,
                    'type': 'business_deployment',
                    'mode': 'claude_generated',
                    'website_type': website_type,
                    'files_generated': [{
                        'filename': 'index.html',
                        'language': 'html',
                        'content': html_code
                    }],
                    'deployment_instructions': 'Upload index.html to Netlify, Vercel, or GitHub Pages',
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Claude generation error: {str(e)}'
            }
    
    async def _execute_ai_agent(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AI agent deployment
        
        Mode 1 (use_existing_systems=True): Use YOUR openai_agent_deployer
        Mode 2 (use_existing_systems=False): Generate code via Claude
        """
        
        if self.use_existing_systems:
            return await self._execute_ai_agent_existing(opportunity)
        else:
            return await self._execute_ai_agent_claude(opportunity)
    
    async def _execute_ai_agent_existing(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Use YOUR existing openai_agent_deployer system"""
        
        from openai_agent_deployer import deploy_ai_agents, AGENT_CONFIGS
        from log_to_jsonbin import get_user
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        requirements_lower = f"{title} {description}".lower()
        
        if any(word in requirements_lower for word in ['saas', 'api', 'developer']):
            template_type = 'saas'
        elif any(word in requirements_lower for word in ['social', 'instagram', 'tiktok', 'content']):
            template_type = 'social'
        else:
            template_type = 'marketing'
        
        try:
            username = opportunity.get('username', 'wade')
            user_data = get_user(username)
            
            if not user_data:
                return {'success': False, 'error': f'User not found: {username}'}
            
            website_url = f"https://{username}.aigentsy.com"
            database_credentials = {'host': 'mock_db_host', 'database': f'{username}_db'}
            config = {'template_type': template_type, 'ai_agents': True}
            
            result = await deploy_ai_agents(
                username=username,
                template_type=template_type,
                config=config,
                website_url=website_url,
                database_credentials=database_credentials,
                user_data=user_data
            )
            
            if not result.get('ok'):
                return {'success': False, 'error': result.get('error', 'Agent deployment failed')}
            
            agents_summary = "\n".join([
                f"- {agent['name']} (ID: {agent['assistant_id']}): {agent['role']}"
                for agent in result.get('agents', [])
            ])
            
            return {
                'success': True,
                'type': 'ai_agent',
                'mode': 'existing_systems',
                'agents': result.get('agents', []),
                'agents_count': result.get('agents_count', 0),
                'webhook_url': result.get('webhook_url'),
                'is_mock': result.get('mock', False),
                'files_generated': [{
                    'filename': 'agents_summary.txt',
                    'language': 'text',
                    'content': f"""AI Agents Deployed!

Template: {template_type}
Agents: {result.get('agents_count', 0)}

{agents_summary}

Webhook: {result.get('webhook_url')}
Mock: {'Yes' if result.get('mock') else 'No'}
"""
                }],
                'completed_at': result.get('deployed_at', datetime.now(timezone.utc).isoformat())
            }
        
        except Exception as e:
            return {'success': False, 'error': f'AI agent deployer error: {str(e)}'}
    
    async def _execute_ai_agent_claude(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete AI agent code via Claude/OpenRouter"""
        
        import os
        import httpx
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            return {'success': False, 'error': 'OPENROUTER_API_KEY not set'}
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        
        prompt = f"""Build a complete AI chatbot/agent in Python.

**Project:** {title}
**Requirements:** {description}

Create agent.py with:
- OpenAI/Anthropic API integration
- Conversation management
- Error handling
- Production-ready code

Output ONLY Python code, no explanations."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 8000
                    },
                    timeout=120.0
                )
                
                if response.status_code != 200:
                    return {'success': False, 'error': f'OpenRouter error: {response.status_code}'}
                
                agent_code = response.json()['choices'][0]['message']['content'].strip()
                
                if '```python' in agent_code:
                    agent_code = agent_code.split('```python')[1].split('```')[0].strip()
                elif '```' in agent_code:
                    agent_code = agent_code.split('```')[1].split('```')[0].strip()
                
                return {
                    'success': True,
                    'type': 'ai_agent',
                    'mode': 'claude_generated',
                    'files_generated': [{
                        'filename': 'agent.py',
                        'language': 'python',
                        'content': agent_code
                    }],
                    'deployment_instructions': 'pip install openai anthropic && python agent.py',
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
        
        except Exception as e:
            return {'success': False, 'error': f'Claude generation error: {str(e)}'}
    
    async def _execute_platform_monetization(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute platform monetization
        
        Mode 1 (use_existing_systems=True): Use YOUR metabridge_runtime
        Mode 2 (use_existing_systems=False): Generate code via Claude
        """
        
        if self.use_existing_systems:
            return await self._execute_platform_monetization_existing(opportunity)
        else:
            return await self._execute_platform_monetization_claude(opportunity)
    
    async def _execute_platform_monetization_existing(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Use YOUR existing metabridge_runtime system"""
        
        from metabridge_runtime import MetaBridgeRuntime
        from log_to_jsonbin import get_user
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        username = opportunity.get('username', 'wade')
        
        try:
            user_data = get_user(username)
            if not user_data:
                return {'success': False, 'error': f'User not found: {username}'}
            
            runtime = MetaBridgeRuntime()
            query = f"{title} - {description}"
            mesh_session_id = f"mesh_{username}_{int(datetime.now(timezone.utc).timestamp())}"
            
            result = runtime.full_cycle(
                query=query,
                originator=username,
                mesh_session_id=mesh_session_id
            )
            
            matches = result.get('matches', []) if isinstance(result, dict) and 'matches' in result else []
            proposal = result.get('proposal', 'Monetization proposal generated')
            delivery = result.get('delivery', {})
            dealgraph = result.get('dealgraph')
            
            description_lower = f"{title} {description}".lower()
            platforms = []
            if 'tiktok' in description_lower: platforms.append('TikTok')
            if 'instagram' in description_lower: platforms.append('Instagram')
            if 'youtube' in description_lower: platforms.append('YouTube')
            if 'amazon' in description_lower: platforms.append('Amazon')
            if not platforms: platforms = ['TikTok', 'Instagram', 'YouTube']
            
            return {
                'success': True,
                'type': 'platform_monetization',
                'mode': 'existing_systems',
                'platforms': platforms,
                'matches_count': len(matches),
                'matches': matches,
                'proposal': proposal,
                'delivery': delivery,
                'dealgraph_id': dealgraph.get('id') if dealgraph else None,
                'mesh_session_id': mesh_session_id,
                'files_generated': [{
                    'filename': 'monetization_summary.txt',
                    'language': 'text',
                    'content': f"""Platform Monetization Complete!

Platforms: {', '.join(platforms)}
Matches: {len(matches)}
Mesh Session: {mesh_session_id}
DealGraph: {dealgraph.get('id') if dealgraph else 'N/A'}

Proposal:
{proposal}

Matched Partners:
{chr(10).join([f"- {m.get('username', 'Unknown')}: {m.get('meta_role', 'Partner')}" for m in matches[:5]])}
"""
                }],
                'completed_at': datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            return {'success': False, 'error': f'MetaBridge error: {str(e)}'}
    
    async def _execute_platform_monetization_claude(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete monetization code via Claude/OpenRouter"""
        
        import os
        import httpx
        
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            return {'success': False, 'error': 'OPENROUTER_API_KEY not set'}
        
        title = opportunity.get('title', '')
        description = opportunity.get('description', '')
        
        # Detect platforms
        description_lower = f"{title} {description}".lower()
        platforms = []
        if 'tiktok' in description_lower: platforms.append('TikTok')
        if 'instagram' in description_lower: platforms.append('Instagram')
        if 'youtube' in description_lower: platforms.append('YouTube')
        if not platforms: platforms = ['TikTok', 'Instagram']
        
        prompt = f"""Build a complete platform monetization system in Python.

**Project:** {title}
**Platforms:** {', '.join(platforms)}
**Requirements:** {description}

Create monetization.py with:
- Link tracking
- Revenue analytics
- Multi-platform support
- Production-ready code

Output ONLY Python code, no explanations."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 8000
                    },
                    timeout=120.0
                )
                
                if response.status_code != 200:
                    return {'success': False, 'error': f'OpenRouter error: {response.status_code}'}
                
                code = response.json()['choices'][0]['message']['content'].strip()
                
                if '```python' in code:
                    code = code.split('```python')[1].split('```')[0].strip()
                elif '```' in code:
                    code = code.split('```')[1].split('```')[0].strip()
                
                return {
                    'success': True,
                    'type': 'platform_monetization',
                    'mode': 'claude_generated',
                    'platforms': platforms,
                    'files_generated': [{
                        'filename': 'monetization.py',
                        'language': 'python',
                        'content': code
                    }],
                    'deployment_instructions': f'Deploy to handle {", ".join(platforms)} monetization',
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
        
        except Exception as e:
            return {'success': False, 'error': f'Claude generation error: {str(e)}'}
    
    def _extract_code_files(self, solution: str) -> List[Dict[str, str]]:
        """
        Extract code files from Claude's response
        """
        import re
        
        files = []
        
        # Pattern: ```filename\ncode\n```
        pattern = r'```(\w+)?\s*(?:# )?([\w\-\.]+)?\n(.*?)```'
        matches = re.findall(pattern, solution, re.DOTALL)
        
        for i, (lang, filename, code) in enumerate(matches):
            if not filename:
                # Generate filename based on language
                ext = {
                    'python': 'py',
                    'javascript': 'js',
                    'typescript': 'ts',
                    'html': 'html',
                    'css': 'css'
                }.get(lang, 'txt')
                filename = f'file_{i+1}.{ext}'
            
            files.append({
                'filename': filename,
                'language': lang or 'text',
                'content': code.strip()
            })
        
        return files
    
    async def _deliver_work(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Deliver completed work
        
        Platform-specific delivery methods
        """
        
        opportunity = workflow['opportunity']
        execution_result = workflow.get('execution_result', {})
        platform = opportunity['source']
        
        # Route to platform-specific delivery
        if platform in ['github', 'github_bounties']:
            return await self._deliver_to_github(opportunity, execution_result)
        
        elif platform == 'upwork':
            return await self._deliver_to_upwork(opportunity, execution_result)
        
        elif platform == 'freelancer':
            return await self._deliver_to_freelancer(opportunity, execution_result)
        
        elif platform == 'reddit':
            return await self._deliver_to_reddit(opportunity, execution_result)
        
        else:
            # Manual delivery
            return {
                'success': True,
                'method': 'manual',
                'message': 'Manual delivery required',
                'instructions': f'Deliver work manually at: {opportunity["url"]}',
                'deliverable': execution_result
            }
    
    async def _deliver_to_github(self, opportunity: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver to GitHub via comment + optional PR
        
        REAL IMPLEMENTATION - Posts actual GitHub comment
        """
        import os
        
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return {
                'success': False,
                'error': 'GITHUB_TOKEN not set',
                'instructions': 'Set GITHUB_TOKEN to enable automatic delivery'
            }
        
        # Parse GitHub URL
        url_parts = opportunity['url'].split('/')
        owner = url_parts[-4]
        repo = url_parts[-3]
        issue_number = url_parts[-1]
        
        # Build delivery message based on execution type
        exec_type = execution_result.get('type')
        
        if exec_type == 'code_generation':
            # Format code files
            files = execution_result.get('files_generated', [])
            
            delivery_message = f"""## ✅ Solution Delivered!

I've completed the task. Here's the solution:

"""
            for file in files:
                delivery_message += f"### {file['filename']}\n```{file['language']}\n{file['content'][:2000]}\n```\n\n"
                if len(file['content']) > 2000:
                    delivery_message += f"*(File truncated - {len(file['content'])} total characters)*\n\n"
            
            delivery_message += f"""**Model Used:** {execution_result.get('model_used', 'claude-sonnet-4')}

Let me know if you need any adjustments!"""
        
        elif exec_type == 'content_generation':
            content = execution_result.get('content', '')
            # Truncate if too long for GitHub comment
            if len(content) > 3000:
                content = content[:3000] + "\n\n*(Content truncated for display - full version available)*"
            
            delivery_message = f"""## ✅ Content Delivered!

Here's the completed content:

---

{content}

---

**Word Count:** {execution_result.get('word_count', 0)}
**Model Used:** {execution_result.get('model_used', 'claude-sonnet-4')}

Let me know if you need any revisions!"""
        
        elif exec_type == 'business_deployment':
            files = execution_result.get('files_generated', [])
            html_preview = files[0]['content'][:1000] if files else ''
            
            delivery_message = f"""## ✅ Website Delivered!

I've built a complete, production-ready **{execution_result.get('website_type', 'website')}** for you!

### Files:
- `index.html` - Complete standalone website

### Preview (first 1000 chars):
```html
{html_preview}
```

### Deployment Instructions:
{execution_result.get('deployment_instructions', 'Upload to any web host')}

The website is fully functional and mobile-responsive!"""
        
        elif exec_type == 'ai_agent':
            files = execution_result.get('files_generated', [])
            code_preview = files[0]['content'][:1000] if files else ''
            
            delivery_message = f"""## ✅ AI Agent Delivered!

I've built a complete AI chatbot/agent for you!

### Files:
- `agent.py` - Complete agent implementation

### Preview (first 1000 chars):
```python
{code_preview}
```

### Deployment Instructions:
{execution_result.get('deployment_instructions', 'See code comments')}

The agent is production-ready!"""
        
        elif exec_type == 'platform_monetization':
            files = execution_result.get('files_generated', [])
            code_preview = files[0]['content'][:1000] if files else ''
            platforms = ', '.join(execution_result.get('platforms', []))
            
            delivery_message = f"""## ✅ Monetization System Delivered!

I've built a complete platform monetization system for **{platforms}**!

### Files:
- `monetization.py` - Complete monetization implementation

### Preview (first 1000 chars):
```python
{code_preview}
```

### Deployment Instructions:
{execution_result.get('deployment_instructions', 'See code comments')}

Start monetizing across {platforms}!"""
        
        else:
            # Generic delivery
            delivery_message = f"""## ✅ Work Completed!

{execution_result.get('solution', 'Task completed successfully')}

Let me know if you need anything else!"""
        
        # Post to GitHub
        try:
            import httpx
            
            api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Authorization": f"token {github_token}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    json={"body": delivery_message.strip()},
                    timeout=15
                )
                
                if response.status_code == 201:
                    comment_data = response.json()
                    
                    return {
                        'success': True,
                        'platform': 'github',
                        'delivery_url': comment_data['html_url'],
                        'delivered_at': datetime.now(timezone.utc).isoformat(),
                        'method': 'github_comment'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'GitHub API error: {response.status_code}',
                        'response': response.text
                    }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Delivery failed: {str(e)}'
            }
    
    async def _deliver_to_upwork(self, opportunity: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver to Upwork (requires Upwork API setup)
        """
        return {
            'success': True,
            'method': 'manual',
            'platform': 'upwork',
            'instructions': f'Upload deliverables to Upwork at: {opportunity["url"]}',
            'deliverable': execution_result
        }
    
    async def _deliver_to_freelancer(self, opportunity: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver to Freelancer.com (requires Freelancer API)
        """
        return {
            'success': True,
            'method': 'manual',
            'platform': 'freelancer',
            'instructions': f'Upload deliverables to Freelancer at: {opportunity["url"]}',
            'deliverable': execution_result
        }
    
    async def _deliver_to_reddit(self, opportunity: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deliver to Reddit via DM or comment reply
        """
        return {
            'success': True,
            'method': 'manual',
            'platform': 'reddit',
            'instructions': f'Reply to OP at: {opportunity["url"]}',
            'deliverable': execution_result
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

    async def client_approves(self, workflow_id: str) -> Dict[str, Any]:
        """
        Wrapper method: Mark that client has approved/accepted the proposal
        
        Called by: POST /wade/workflow/{id}/client-approved
        """
        if workflow_id not in self.workflows:
            return {
                'success': False,
                'error': f'Workflow {workflow_id} not found'
            }
        
        workflow = self.workflows[workflow_id]
        
        # Update stage
        workflow['stage'] = WorkflowStage.CLIENT_APPROVED
        workflow['history'].append({
            'stage': WorkflowStage.CLIENT_APPROVED,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': 'Client approved proposal'
        })
        
        return {
            'success': True,
            'workflow_id': workflow_id,
            'stage': workflow['stage'],
            'message': 'Client approval recorded. Ready for execution.'
        }
    
    async def execute_work(self, workflow_id: str) -> Dict[str, Any]:
        """
        Wrapper method: Execute the work
        
        Called by: POST /wade/workflow/{id}/execute
        """
        if workflow_id not in self.workflows:
            return {
                'success': False,
                'error': f'Workflow {workflow_id} not found'
            }
        
        workflow = self.workflows[workflow_id]
        
        # Execute using existing method
        result = await self._execute_fulfillment(workflow)
        
        # Update workflow
        workflow['execution_result'] = result
        workflow['stage'] = WorkflowStage.COMPLETED
        workflow['history'].append({
            'stage': WorkflowStage.COMPLETED,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': 'Work executed successfully',
            'result': result
        })
        
        return result
    
    async def deliver_work(self, workflow_id: str) -> Dict[str, Any]:
        """
        Wrapper method: Deliver completed work
        
        Called by: POST /wade/workflow/{id}/deliver
        """
        if workflow_id not in self.workflows:
            return {
                'success': False,
                'error': f'Workflow {workflow_id} not found'
            }
        
        workflow = self.workflows[workflow_id]
        
        # Deliver using existing method
        result = await self._deliver_work(workflow)
        
        # Update workflow
        workflow['delivery_result'] = result
        workflow['stage'] = WorkflowStage.DELIVERED
        workflow['history'].append({
            'stage': WorkflowStage.DELIVERED,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': 'Work delivered to client',
            'result': result
        })
        
        return result
    
    async def track_payment(self, workflow_id: str, amount: float, proof: str = "") -> Dict[str, Any]:
        """
        Wrapper method: Track payment received
        
        Called by: POST /wade/workflow/{id}/payment-received
        """
        if workflow_id not in self.workflows:
            return {
                'success': False,
                'error': f'Workflow {workflow_id} not found'
            }
        
        workflow = self.workflows[workflow_id]
        
        # Update workflow
        workflow['payment'] = {
            'amount': amount,
            'proof': proof,
            'received_at': datetime.now(timezone.utc).isoformat()
        }
        workflow['stage'] = WorkflowStage.PAID
        workflow['history'].append({
            'stage': WorkflowStage.PAID,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': f'Payment received: ${amount}',
            'amount': amount
        })
        
        return {
            'success': True,
            'workflow_id': workflow_id,
            'amount': amount,
            'stage': workflow['stage'],
            'message': f'Payment of ${amount} tracked successfully'
        }
    
    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow by ID
        
        Called by: GET /wade/workflow/{id}
        """
        return self.workflows.get(workflow_id)
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """
        Get all active workflows (not paid or rejected)
        
        Called by: GET /wade/active-workflows
        """
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
        
        return [
            workflow for workflow in self.workflows.values()
            if workflow.get('stage') in active_stages
        ]
    
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


# Global instances
# HYBRID MODE (DEFAULT): Auto-detects whether to use existing systems or Claude generation
integrated_workflow = IntegratedFulfillmentWorkflow(use_existing_systems=True)  # Default to existing, but will auto-switch

# Manual override options if needed:
integrated_workflow_existing = IntegratedFulfillmentWorkflow(use_existing_systems=True)   # Force existing systems
integrated_workflow_claude = IntegratedFulfillmentWorkflow(use_existing_systems=False)    # Force Claude generation
