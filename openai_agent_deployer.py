"""
OpenAI Agent Deployer
Deploys 4 AI agents for each user's business

Agents:
1. Sales Agent - Responds to inquiries, qualifies leads
2. Delivery Agent - Manages projects, timelines  
3. Marketing Agent - Creates content, optimizes SEO
4. Finance Agent - Invoicing, expense tracking
"""

import os
import httpx
from typing import Dict, Any, List
from datetime import datetime, timezone


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Agent configurations for each template type
AGENT_CONFIGS = {
    "saas": {
        "sales": {
            "name": "API Sales Agent",
            "role": "You are a helpful API sales agent. Help developers understand our API capabilities and get started quickly.",
            "tools": ["email_send", "slack_notify", "crm_update"],
            "knowledge_base": [
                "API documentation",
                "Pricing tiers",
                "Common use cases",
                "Integration examples"
            ]
        },
        "support": {
            "name": "Developer Support Agent",
            "role": "You are a technical support agent helping developers integrate our API. Provide clear, code-focused solutions.",
            "tools": ["code_debug", "docs_search", "ticket_create"],
            "knowledge_base": [
                "API reference",
                "Error codes",
                "Debugging guides",
                "SDK documentation"
            ]
        },
        "developer_relations": {
            "name": "Developer Relations Agent",
            "role": "You build relationships with developers. Share content, gather feedback, and foster community.",
            "tools": ["social_post", "community_moderate", "feedback_collect"],
            "knowledge_base": [
                "Community guidelines",
                "Developer stories",
                "Product roadmap",
                "Best practices"
            ]
        },
        "finance": {
            "name": "Finance Agent",
            "role": "You handle billing, invoices, and payment tracking for API customers.",
            "tools": ["invoice_generate", "payment_track", "subscription_manage"],
            "knowledge_base": [
                "Pricing plans",
                "Billing cycles",
                "Payment terms",
                "Tax policies"
            ]
        }
    },
    
    "marketing": {
        "sales": {
            "name": "Lead Qualification Agent",
            "role": "You qualify marketing leads and book sales calls. Be helpful, not pushy.",
            "tools": ["email_send", "calendar_book", "crm_update"],
            "knowledge_base": [
                "Service offerings",
                "Pricing packages",
                "Case studies",
                "Client testimonials"
            ]
        },
        "delivery": {
            "name": "Campaign Manager Agent",
            "role": "You manage marketing campaign delivery. Keep clients updated on progress and results.",
            "tools": ["project_update", "report_generate", "client_notify"],
            "knowledge_base": [
                "Campaign processes",
                "Reporting templates",
                "Timeline expectations",
                "Quality standards"
            ]
        },
        "marketing": {
            "name": "Content Marketing Agent",
            "role": "You create marketing content including blog posts, ad copy, and social media posts.",
            "tools": ["blog_post", "ad_copy_generate", "social_schedule"],
            "knowledge_base": [
                "Brand voice",
                "SEO keywords",
                "Content calendar",
                "Performance data"
            ]
        },
        "finance": {
            "name": "Finance Agent",
            "role": "You handle invoicing, payment collection, and expense tracking for marketing campaigns.",
            "tools": ["invoice_send", "payment_track", "expense_log"],
            "knowledge_base": [
                "Service pricing",
                "Payment terms",
                "Refund policy",
                "Tax information"
            ]
        }
    },
    
    "social": {
        "content_strategist": {
            "name": "Content Strategy Agent",
            "role": "You help creators plan and optimize their content strategy across platforms.",
            "tools": ["content_analyze", "trend_identify", "schedule_optimize"],
            "knowledge_base": [
                "Content templates",
                "Viral hooks",
                "Platform algorithms",
                "Posting schedules"
            ]
        },
        "engagement_manager": {
            "name": "Engagement Manager Agent",
            "role": "You manage daily engagement activities - likes, comments, follows, and community building.",
            "tools": ["comment_reply", "dm_respond", "engagement_track"],
            "knowledge_base": [
                "Engagement playbook",
                "Response templates",
                "Community guidelines",
                "5-3-1 ritual"
            ]
        },
        "growth_specialist": {
            "name": "Growth Specialist Agent",
            "role": "You analyze growth metrics and recommend strategies to increase followers and engagement.",
            "tools": ["analytics_analyze", "strategy_recommend", "ab_test"],
            "knowledge_base": [
                "Growth frameworks",
                "Platform analytics",
                "Competitor analysis",
                "Viral patterns"
            ]
        },
        "finance": {
            "name": "Finance Agent",
            "role": "You track creator earnings, brand deals, and sponsorship opportunities.",
            "tools": ["deal_track", "invoice_send", "payment_collect"],
            "knowledge_base": [
                "Brand deal rates",
                "Payment terms",
                "Tax guidance",
                "Revenue tracking"
            ]
        }
    }
}


async def deploy_ai_agents(
    username: str,
    template_type: str,
    config: Dict[str, Any],
    website_url: str,
    database_credentials: Dict[str, Any],
    user_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deploy AI agents for user's business
    
    Steps:
    1. Create OpenAI Assistants for each agent
    2. Configure knowledge bases
    3. Setup tool integrations
    4. Return agent IDs and webhooks
    
    Args:
        username: User's username
        template_type: "saas" | "marketing" | "social"
        config: Template configuration
        website_url: Deployed website URL
        database_credentials: Database connection info
        user_data: User profile
        
    Returns:
        {
            "ok": True,
            "agents": [{agent details}],
            "webhook_url": "..."
        }
    """
    
    print(f"🤖 Deploying AI agents for {username}...")
    
    # Check if OpenAI is configured
    if not OPENAI_API_KEY:
        print("⚠️  OpenAI API key not configured - using mock agents")
        return await _mock_agents(username, template_type, config)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
                "OpenAI-Beta": "assistants=v2"
            }
            
            # Get agent configs for this template type
            agents_config = AGENT_CONFIGS.get(template_type, {})
            
            if not agents_config:
                return {
                    "ok": False,
                    "error": f"No agent configs defined for template type: {template_type}"
                }
            
            deployed_agents = []
            
            # Deploy each agent
            for agent_key, agent_spec in agents_config.items():
                print(f"   Deploying {agent_spec['name']}...")
                
                # Create OpenAI Assistant
                assistant_payload = {
                    "model": "gpt-4-turbo-preview",
                    "name": f"{username} - {agent_spec['name']}",
                    "instructions": agent_spec["role"],
                    "tools": [{"type": "code_interpreter"}],  # Basic tools for now
                    "metadata": {
                        "username": username,
                        "template_type": template_type,
                        "agent_key": agent_key,
                        "website_url": website_url
                    }
                }
                
                response = await client.post(
                    "https://api.openai.com/v1/assistants",
                    headers=headers,
                    json=assistant_payload
                )
                
                if response.status_code not in [200, 201]:
                    print(f"⚠️  Failed to create assistant: {response.status_code}")
                    continue
                
                assistant_data = response.json()
                assistant_id = assistant_data.get("id")
                
                agent_info = {
                    "key": agent_key,
                    "name": agent_spec["name"],
                    "assistant_id": assistant_id,
                    "role": agent_spec["role"],
                    "tools": agent_spec["tools"],
                    "knowledge_base": agent_spec["knowledge_base"],
                    "status": "active",
                    "created_at": now_iso()
                }
                
                deployed_agents.append(agent_info)
                print(f"   ✅ {agent_spec['name']} deployed (ID: {assistant_id})")
            
            return {
                "ok": True,
                "agents": deployed_agents,
                "agents_count": len(deployed_agents),
                "webhook_url": f"{website_url}/api/agents/webhook",
                "deployed_at": now_iso()
            }
            
    except Exception as e:
        print(f"❌ Agent deployment error: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


async def _mock_agents(
    username: str,
    template_type: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mock agents for testing without OpenAI API
    """
    
    agents_config = AGENT_CONFIGS.get(template_type, {})
    
    mock_agents = []
    
    for agent_key, agent_spec in agents_config.items():
        agent_info = {
            "key": agent_key,
            "name": agent_spec["name"],
            "assistant_id": f"asst_mock_{username}_{agent_key}",
            "role": agent_spec["role"],
            "tools": agent_spec["tools"],
            "knowledge_base": agent_spec["knowledge_base"],
            "status": "active",
            "created_at": now_iso()
        }
        mock_agents.append(agent_info)
    
    print(f"✅ Mock agents deployed: {len(mock_agents)} agents")
    
    return {
        "ok": True,
        "agents": mock_agents,
        "agents_count": len(mock_agents),
        "webhook_url": f"https://{username}.aigentsy.com/api/agents/webhook",
        "deployed_at": now_iso(),
        "mock": True
    }


async def delete_agent(assistant_id: str) -> Dict[str, Any]:
    """Delete an OpenAI assistant (rollback)"""
    
    if not OPENAI_API_KEY:
        return {"ok": True, "mock": True, "message": "Mock deletion"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "assistants=v2"
            }
            
            response = await client.delete(
                f"https://api.openai.com/v1/assistants/{assistant_id}",
                headers=headers
            )
            
            if response.status_code in [200, 204]:
                return {"ok": True, "deleted": True}
            else:
                return {
                    "ok": False,
                    "error": f"Deletion failed: {response.status_code}"
                }
                
    except Exception as e:
        return {"ok": False, "error": str(e)}
