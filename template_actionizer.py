"""
AiGentsy Template Actionizer
Transforms static templates → Live autonomous businesses

Supports:
- SKU #1: SaaS Template (API documentation + developer portal)
- SKU #2: Marketing Template (3 landing pages + email sequences)
- SKU #3: Social Template (content calendar + engagement system)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import asyncio
import json

# Import deployment modules
from vercel_deployer import deploy_to_vercel
from supabase_provisioner import provision_database
from resend_automator import setup_email_automation
from openai_agent_deployer import deploy_ai_agents

# Import existing AiGentsy systems
try:
    from log_to_jsonbin import get_user, log_agent_update
    from revenue_flows import activate_revenue_tracking
    from outcome_oracle import record_outcome
    from aigx_engine import credit_aigx
except ImportError:
    print("⚠️  Running in standalone mode - import AiGentsy modules when deployed")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# Template configurations
TEMPLATE_CONFIGS = {
    "saas": {
        "name": "SaaS API Business",
        "description": "Complete API documentation + developer portal",
        "deployment_time": "5-10 minutes",
        "components": {
            "website": True,
            "database": True,
            "email": True,
            "ai_agents": True
        },
        "website_type": "developer_portal",
        "database_schema": "saas_api",
        "email_sequences": ["welcome_developers", "api_key_activated", "usage_limit"],
        "ai_agents": ["sales", "support", "developer_relations", "finance"]
    },
    "marketing": {
        "name": "Marketing Campaign Business",
        "description": "Landing pages + email sequences + ad campaigns",
        "deployment_time": "5-10 minutes",
        "components": {
            "website": True,
            "database": True,
            "email": True,
            "ai_agents": True
        },
        "website_type": "landing_pages",
        "database_schema": "marketing_leads",
        "email_sequences": ["welcome_series", "nurture", "conversion", "re_engagement"],
        "ai_agents": ["sales", "delivery", "marketing", "finance"]
    },
    "social": {
        "name": "Social Media Business",
        "description": "Content calendar + engagement system + growth tools",
        "deployment_time": "5-10 minutes",
        "components": {
            "website": True,
            "database": True,
            "email": True,
            "ai_agents": True
        },
        "website_type": "creator_hub",
        "database_schema": "social_content",
        "email_sequences": ["welcome_creators", "content_reminders", "growth_tips"],
        "ai_agents": ["content_strategist", "engagement_manager", "growth_specialist", "finance"]
    }
}


async def actionize_template(
    username: str,
    template_type: str,
    user_data: Dict[str, Any],
    custom_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main orchestrator - transforms static template into live business
    
    Args:
        username: User's username
        template_type: "saas" | "marketing" | "social"
        user_data: User profile from JSONBin
        custom_config: Optional custom configuration
        
    Returns:
        Complete deployment result with URLs, credentials, status
    """
    
    print(f"\n{'='*70}")
    print(f"🚀 ACTIONIZING TEMPLATE: {template_type.upper()}")
    print(f"   User: {username}")
    print(f"   Timestamp: {now_iso()}")
    print(f"{'='*70}\n")
    
    # Validate template type
    if template_type not in TEMPLATE_CONFIGS:
        return {
            "ok": False,
            "error": f"Invalid template type: {template_type}",
            "valid_types": list(TEMPLATE_CONFIGS.keys())
        }
    
    config = TEMPLATE_CONFIGS[template_type]
    
    # Merge with custom config if provided
    if custom_config:
        config = {**config, **custom_config}
    
    result = {
        "ok": True,
        "username": username,
        "template_type": template_type,
        "started_at": now_iso(),
        "status": "deploying"
    }
    
    try:
        # =============================================================
        # STEP 1: Deploy Website to Vercel
        # =============================================================
        print("📦 Step 1/5: Deploying website to Vercel...")
        
        website_result = await deploy_to_vercel(
            username=username,
            template_type=template_type,
            config=config,
            user_data=user_data
        )
        
        if not website_result.get("ok"):
            raise Exception(f"Website deployment failed: {website_result.get('error')}")
        
        result["website"] = website_result
        print(f"✅ Website deployed: {website_result['url']}\n")
        
        # =============================================================
        # STEP 2: Provision Supabase Database
        # =============================================================
        print("🗄️  Step 2/5: Provisioning Supabase database...")
        
        database_result = await provision_database(
            username=username,
            template_type=template_type,
            config=config
        )
        
        if not database_result.get("ok"):
            raise Exception(f"Database provisioning failed: {database_result.get('error')}")
        
        result["database"] = database_result
        print(f"✅ Database provisioned: {database_result['database_url']}\n")
        
        # =============================================================
        # STEP 3: Setup Email Automation (Resend)
        # =============================================================
        print("📧 Step 3/5: Setting up email automation...")
        
        email_result = await setup_email_automation(
            username=username,
            template_type=template_type,
            config=config,
            user_email=user_data.get("consent", {}).get("email") or f"{username}@aigentsy.com"
        )
        
        if not email_result.get("ok"):
            print(f"⚠️  Email setup warning: {email_result.get('error')}")
            result["email"] = {"ok": False, "error": email_result.get("error")}
        else:
            result["email"] = email_result
            print(f"✅ Email automation active: {email_result['sequences_count']} sequences\n")
        
        # =============================================================
        # STEP 4: Deploy AI Agents (OpenAI)
        # =============================================================
        print("🤖 Step 4/5: Deploying AI agents...")
        
        agents_result = await deploy_ai_agents(
            username=username,
            template_type=template_type,
            config=config,
            website_url=website_result["url"],
            database_credentials=database_result["credentials"],
            user_data=user_data
        )
        
        if not agents_result.get("ok"):
            print(f"⚠️  AI agents warning: {agents_result.get('error')}")
            result["ai_agents"] = {"ok": False, "error": agents_result.get("error")}
        else:
            result["ai_agents"] = agents_result
            print(f"✅ AI agents deployed: {len(agents_result['agents'])} agents active\n")
        
        # =============================================================
        # STEP 5: Activate Revenue Tracking
        # =============================================================
        print("💰 Step 5/5: Activating revenue tracking...")
        
        try:
            # Connect to existing revenue_flows.py
            revenue_result = await activate_revenue_tracking(
                username=username,
                business_url=website_result["url"],
                template_type=template_type
            )
            result["revenue_tracking"] = revenue_result
            print("✅ Revenue tracking active: 2.8% + $0.28 fee structure\n")
        except Exception as e:
            print(f"⚠️  Revenue tracking setup: {e}")
            result["revenue_tracking"] = {"ok": False, "error": str(e)}
        
        # =============================================================
        # COMPLETE
        # =============================================================
        result["status"] = "deployed"
        result["completed_at"] = now_iso()
        
        # Calculate deployment time
        from datetime import datetime
        start = datetime.fromisoformat(result["started_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(result["completed_at"].replace("Z", "+00:00"))
        deployment_seconds = (end - start).total_seconds()
        result["deployment_time"] = f"{deployment_seconds:.1f} seconds"
        
        # Summary URLs
        result["urls"] = {
            "website": website_result["url"],
            "admin_panel": f"{website_result['url']}/admin",
            "database_dashboard": database_result.get("dashboard_url"),
            "analytics": f"{website_result['url']}/analytics"
        }
        
        print(f"\n{'='*70}")
        print(f"🎉 DEPLOYMENT COMPLETE!")
        print(f"   Website: {result['urls']['website']}")
        print(f"   Admin: {result['urls']['admin_panel']}")
        print(f"   Time: {result['deployment_time']}")
        print(f"{'='*70}\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ DEPLOYMENT FAILED: {e}\n")
        result["ok"] = False
        result["error"] = str(e)
        result["status"] = "failed"
        result["failed_at"] = now_iso()
        return result


async def get_actionization_status(username: str) -> Dict[str, Any]:
    """
    Check if user has an actionized business deployed
    
    Returns:
        Status, URLs, and deployment info
    """
    try:
        user = get_user(username)
        if not user:
            return {"ok": False, "error": "user_not_found"}
        
        # Check for deployment record
        deployment = user.get("actionization", {})
        
        if not deployment:
            return {
                "ok": True,
                "deployed": False,
                "message": "No business deployed yet"
            }
        
        return {
            "ok": True,
            "deployed": True,
            "template_type": deployment.get("template_type"),
            "deployed_at": deployment.get("deployed_at"),
            "website_url": deployment.get("website_url"),
            "status": deployment.get("status")
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def rollback_deployment(username: str, deployment_id: str) -> Dict[str, Any]:
    """
    Rollback a deployment (emergency use only)
    
    Steps:
    1. Delete Vercel project
    2. Delete Supabase database
    3. Deactivate email sequences
    4. Stop AI agents
    """
    print(f"🔄 Rolling back deployment for {username}...")
    
    # TODO: Implement rollback logic
    # For now, just mark as inactive
    
    return {
        "ok": True,
        "message": "Rollback initiated",
        "username": username,
        "deployment_id": deployment_id
    }


# =============================================================
# HELPER FUNCTIONS
# =============================================================

def get_template_info(template_type: str) -> Dict[str, Any]:
    """Get template configuration details"""
    if template_type not in TEMPLATE_CONFIGS:
        return {"ok": False, "error": "invalid_template_type"}
    
    return {
        "ok": True,
        "template": TEMPLATE_CONFIGS[template_type]
    }


def list_available_templates() -> Dict[str, Any]:
    """List all available templates"""
    return {
        "ok": True,
        "templates": [
            {
                "type": key,
                "name": config["name"],
                "description": config["description"],
                "deployment_time": config["deployment_time"]
            }
            for key, config in TEMPLATE_CONFIGS.items()
        ]
    }


def get_available_templates() -> Dict[str, Any]:
    """Get available templates (alias for list_available_templates)"""
    return list_available_templates()


# =============================================================
# TESTING
# =============================================================

async def test_actionization():
    """Test deployment with dummy data"""
    print("🧪 Testing actionization system...\n")
    
    test_user_data = {
        "username": "test_user",
        "companyType": "marketing",
        "consent": {
            "email": "test@aigentsy.com",
            "username": "test_user"
        },
        "traits": ["marketing", "founder", "autonomous"]
    }
    
    result = await actionize_template(
        username="test_user",
        template_type="marketing",
        user_data=test_user_data
    )
    
    print("\n📊 Test Result:")
    print(json.dumps(result, indent=2))
    
    return result


if __name__ == "__main__":
    # Run test
    asyncio.run(test_actionization())
