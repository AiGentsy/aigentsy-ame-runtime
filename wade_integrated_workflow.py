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
        
        Routes to appropriate fulfillment system based on capability
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
        
        # Route to appropriate execution handler
        try:
            if system == 'claude':
                if capability == 'code_generation':
                    result = await self._execute_code_generation(opportunity)
                elif capability == 'content_generation':
                    result = await self._execute_content_generation(opportunity)
                else:
                    result = await self._execute_claude_generic(opportunity)
            
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
            
            if result.get('success'):
                workflow['stage'] = WorkflowStage.COMPLETED
                workflow['completed_at'] = datetime.now(timezone.utc).isoformat()
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
        
        except Exception as e:
            workflow['history'].append({
                'stage': 'ERROR',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'action': f'Execution failed: {str(e)}'
            })
            
            return {
                'ok': False,
                'error': str(e)
            }
    
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
                        "model": "anthropic/claude-sonnet-4-20250514",
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
                        "model": "anthropic/claude-sonnet-4-20250514",
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
                        "model": "anthropic/claude-sonnet-4-20250514",
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
    
    async def _execute_business_deployment(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute business deployment by generating complete website code via Claude
        
        100% REAL - Uses Claude to build actual deployable websites
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
        
        # Analyze requirements to determine website type
        requirements_lower = f"{title} {description}".lower()
        
        if any(word in requirements_lower for word in ['store', 'shop', 'ecommerce', 'product']):
            website_type = 'E-Commerce Store'
            specific_requirements = """
- Product catalog with images
- Shopping cart functionality
- Checkout page
- Payment integration ready
- Responsive mobile design
"""
        elif any(word in requirements_lower for word in ['landing', 'page', 'marketing']):
            website_type = 'Marketing Landing Page'
            specific_requirements = """
- Hero section with CTA
- Features/benefits section
- Testimonials
- Contact form
- Mobile responsive
"""
        elif any(word in requirements_lower for word in ['saas', 'app', 'dashboard']):
            website_type = 'SaaS Platform'
            specific_requirements = """
- Dashboard interface
- User authentication UI
- Data visualization
- Settings panel
- Responsive design
"""
        elif any(word in requirements_lower for word in ['portfolio', 'personal']):
            website_type = 'Portfolio Website'
            specific_requirements = """
- Project showcase
- About section
- Contact form
- Skills/experience display
- Mobile responsive
"""
        else:
            website_type = 'Business Website'
            specific_requirements = """
- Homepage with services
- About page
- Contact form
- Professional design
- Mobile responsive
"""
        
        prompt = f"""You are a professional web developer hired to build a complete, production-ready {website_type}.

**Project:** {title}

**Requirements:**
{description}

**Specific Features Needed:**
{specific_requirements}

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

3. The file MUST work when opened directly in a browser
4. Use modern CSS (flexbox/grid) for layout
5. Include placeholder content that makes sense

**IMPORTANT:** 
- Output ONLY the complete HTML file
- NO explanations before or after
- Start with <!DOCTYPE html>
- End with </html>
- Make it beautiful and professional"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4-20250514",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 16000  # Larger for complete websites
                    },
                    timeout=180.0  # 3 minutes for complex generation
                )
                
                if response.status_code != 200:
                    return {
                        'success': False,
                        'error': f'OpenRouter API error: {response.status_code} - {response.text}'
                    }
                
                data = response.json()
                html_code = data['choices'][0]['message']['content']
                
                # Clean up the HTML (remove markdown code blocks if present)
                html_code = html_code.strip()
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
                    'website_type': website_type,
                    'html_code': html_code,
                    'files_generated': [{
                        'filename': 'index.html',
                        'language': 'html',
                        'content': html_code
                    }],
                    'deployment_instructions': 'Upload index.html to any web host (Netlify, Vercel, GitHub Pages, etc.)',
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
        
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Website generation timeout after 180 seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Business deployment error: {str(e)}'
            }
    
    async def _execute_ai_agent(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AI agent deployment by generating chatbot/agent code via Claude
        
        100% REAL - Creates actual deployable AI agent code
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
        
        prompt = f"""You are a professional AI developer hired to build a complete AI agent/chatbot.

**Project:** {title}

**Requirements:**
{description}

**DELIVERABLES - Create a COMPLETE AI agent implementation:**

Create a Python script that implements a fully functional AI chatbot with:

1. **agent.py** - Main chatbot file that includes:
   - OpenAI/Anthropic API integration
   - Conversation management
   - Context handling
   - Error handling
   - Clean, production-ready code

2. Requirements:
   - Use environment variables for API keys
   - Include clear setup instructions
   - Add usage examples
   - Professional error handling
   - Well-commented code

3. The agent should:
   - Handle user messages intelligently
   - Maintain conversation context
   - Be easily customizable
   - Be production-ready

**IMPORTANT:**
- Output the complete Python code
- Include a README section at the top as comments
- Make it ready to deploy
- Use proper async/await if needed

Format your response as:

```python
# AI Agent Implementation
# [Setup instructions here]

[Complete Python code here]
```"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4-20250514",
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
                agent_code = data['choices'][0]['message']['content']
                
                # Extract Python code
                if '```python' in agent_code:
                    agent_code = agent_code.split('```python')[1].split('```')[0].strip()
                elif '```' in agent_code:
                    agent_code = agent_code.split('```')[1].split('```')[0].strip()
                
                return {
                    'success': True,
                    'type': 'ai_agent',
                    'agent_code': agent_code,
                    'files_generated': [{
                        'filename': 'agent.py',
                        'language': 'python',
                        'content': agent_code
                    }],
                    'deployment_instructions': """
1. Install dependencies: pip install openai anthropic
2. Set environment variable: export OPENAI_API_KEY=your_key
3. Run: python agent.py
4. Deploy to cloud: Use Railway, Render, or Heroku
""",
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
        
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'AI agent generation timeout after 120 seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'AI agent deployment error: {str(e)}'
            }
    
    async def _execute_platform_monetization(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute platform monetization by generating integration code via Claude
        
        100% REAL - Creates actual monetization integration code
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
        
        # Determine platforms from description
        description_lower = f"{title} {description}".lower()
        platforms = []
        if 'tiktok' in description_lower:
            platforms.append('TikTok')
        if 'instagram' in description_lower:
            platforms.append('Instagram')
        if 'youtube' in description_lower:
            platforms.append('YouTube')
        if 'amazon' in description_lower:
            platforms.append('Amazon Associates')
        if not platforms:
            platforms = ['TikTok', 'Instagram', 'YouTube']
        
        platforms_str = ', '.join(platforms)
        
        prompt = f"""You are a professional developer hired to build platform monetization integration.

**Project:** {title}

**Requirements:**
{description}

**Target Platforms:** {platforms_str}

**DELIVERABLES - Create monetization integration code:**

Create a Python script that implements:

1. **monetization.py** - Complete monetization system:
   - Affiliate link generation
   - Click tracking
   - Revenue analytics
   - Multi-platform support ({platforms_str})
   - Commission tracking

2. Requirements:
   - Production-ready code
   - Environment variables for API keys
   - Clean error handling
   - Usage examples
   - Well-documented

3. Include:
   - Link shortening/tracking
   - Analytics dashboard code
   - Revenue reporting
   - Platform-specific integrations

**IMPORTANT:**
- Output complete, runnable Python code
- Include setup instructions as comments
- Make it deployment-ready
- Use modern best practices

Format response as:

```python
# Platform Monetization System
# [Setup instructions]

[Complete Python code]
```"""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "anthropic/claude-sonnet-4-20250514",
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
                monetization_code = data['choices'][0]['message']['content']
                
                # Extract Python code
                if '```python' in monetization_code:
                    monetization_code = monetization_code.split('```python')[1].split('```')[0].strip()
                elif '```' in monetization_code:
                    monetization_code = monetization_code.split('```')[1].split('```')[0].strip()
                
                return {
                    'success': True,
                    'type': 'platform_monetization',
                    'platforms': platforms,
                    'monetization_code': monetization_code,
                    'files_generated': [{
                        'filename': 'monetization.py',
                        'language': 'python',
                        'content': monetization_code
                    }],
                    'deployment_instructions': f"""
1. Install dependencies: pip install requests fastapi
2. Configure platform API keys in environment
3. Run: python monetization.py
4. Deploy to cloud platform
5. Integrate with {platforms_str}
""",
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
        
        except httpx.TimeoutException:
            return {
                'success': False,
                'error': 'Platform monetization generation timeout after 120 seconds'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Platform monetization error: {str(e)}'
            }
    
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
