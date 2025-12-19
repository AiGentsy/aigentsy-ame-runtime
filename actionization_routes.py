"""
FastAPI Endpoint Integration for main.py
Add these routes to enable template actionization

INSTALLATION:
1. Copy this file to your project root
2. Add to main.py: from actionization_routes import router as actionization_router
3. Add to main.py: app.include_router(actionization_router)
4. Set environment variables (see below)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

# Import actionization modules
from template_actionizer import actionize_template, get_actionization_status
from log_to_jsonbin import get_user, update_user
from aigx_engine import credit_aigx
from outcome_oracle import record_outcome

router = APIRouter(prefix="/actionize", tags=["actionization"])


# =============================================================
# REQUEST/RESPONSE MODELS
# =============================================================

class ActionizeRequest(BaseModel):
    username: str
    template_type: Optional[str] = None  # Auto-detected from user profile if not provided
    force_redeploy: Optional[bool] = False


class ActionizeResponse(BaseModel):
    ok: bool
    message: str
    username: str
    template_type: Optional[str] = None
    urls: Optional[Dict[str, str]] = None
    deployment_time: Optional[str] = None
    error: Optional[str] = None


# =============================================================
# MAIN ACTIONIZATION ENDPOINT
# =============================================================

@router.post("/deploy", response_model=ActionizeResponse)
async def deploy_business(request: ActionizeRequest):
    """
    Deploy live business from template
    
    This is the main endpoint called when user clicks "🚀 Publish Storefront"
    in the GX Drawer.
    
    Flow:
    1. Get user data
    2. Determine template type
    3. Check if already deployed
    4. Deploy infrastructure (website, database, email, agents)
    5. Credit AIGx
    6. Record outcome
    7. Return URLs
    """
    
    username = request.username
    
    try:
        # Step 1: Get user data
        user = get_user(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Step 2: Determine template type
        template_type = request.template_type or user.get("companyType", "marketing")
        
        # Validate template type
        valid_types = ["saas", "marketing", "social"]
        if template_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid template type: {template_type}. Must be one of: {valid_types}"
            )
        
        # Step 3: Check if already deployed
        existing_deployment = user.get("actionization", {})
        
        if existing_deployment.get("deployed") and not request.force_redeploy:
            return ActionizeResponse(
                ok=True,
                message="Business already deployed",
                username=username,
                template_type=template_type,
                urls={
                    "website": existing_deployment.get("website_url"),
                    "admin": existing_deployment.get("admin_url")
                }
            )
        
        # Step 4: Deploy infrastructure
        print(f"\n{'='*70}")
        print(f"🚀 DEPLOYING {template_type.upper()} BUSINESS FOR {username}")
        print(f"{'='*70}\n")
        
        deployment_result = await actionize_template(
            username=username,
            template_type=template_type,
            user_data=user
        )
        
        if not deployment_result.get("ok"):
            raise HTTPException(
                status_code=500,
                detail=deployment_result.get("error", "Deployment failed")
            )
        
        # Step 5: Save deployment to user profile
        user["actionization"] = {
            "deployed": True,
            "template_type": template_type,
            "website_url": deployment_result["urls"]["website"],
            "admin_url": deployment_result["urls"]["admin_panel"],
            "deployed_at": deployment_result["completed_at"],
            "deployment_time": deployment_result["deployment_time"],
            "status": "active"
        }
        
        update_user(username, user)
        
        # Step 6: Credit 30 AIGx for publishing
        try:
            await credit_aigx(username, 30, {
                "source": "site_published",
                "template_type": template_type
            })
            print("✅ Credited 30 AIGx for publishing")
        except Exception as e:
            print(f"⚠️  AIGx credit warning: {e}")
        
        # Step 7: Record outcome
        try:
            await record_outcome(username, "SITE_PUBLISHED", {
                "template_type": template_type,
                "website_url": deployment_result["urls"]["website"],
                "agents_deployed": deployment_result.get("ai_agents", {}).get("agents_count", 0)
            })
            print("✅ Recorded SITE_PUBLISHED outcome")
        except Exception as e:
            print(f"⚠️  Outcome recording warning: {e}")
        
        # Step 8: Return success
        return ActionizeResponse(
            ok=True,
            message="Business deployed successfully! 🎉",
            username=username,
            template_type=template_type,
            urls=deployment_result["urls"],
            deployment_time=deployment_result["deployment_time"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================
# STATUS ENDPOINT
# =============================================================

@router.get("/status/{username}")
async def get_deployment_status(username: str):
    """
    Check if user has deployed business
    
    Returns deployment status, URLs, and template type
    """
    
    try:
        status = await get_actionization_status(username)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================
# LEGACY ENDPOINT (for backwards compatibility)
# =============================================================

@router.post("")
async def actionize_legacy(body: dict):
    """
    Legacy endpoint for backwards compatibility
    Maps to /actionize/deploy
    """
    
    request = ActionizeRequest(**body)
    return await deploy_business(request)


# =============================================================
# ENVIRONMENT VARIABLES REQUIRED
# =============================================================

"""
Set these in your .env file or deployment environment:

# Vercel (Website Deployment)
VERCEL_API_TOKEN=your_vercel_token_here
VERCEL_TEAM_ID=your_team_id_here  # Optional

# Supabase (Database)
SUPABASE_API_KEY=your_supabase_key_here
SUPABASE_ORG_ID=your_org_id_here

# Resend (Email)
RESEND_API_KEY=your_resend_key_here

# OpenRouter (AI Agents) - YOU ALREADY HAVE THIS!
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # Optional

NOTES:
- If any key is missing, that component will use mock mode
- Mock mode is useful for testing without infrastructure costs
- Mock mode returns fake URLs but follows same flow
- OpenRouter gives you access to Claude, GPT-4, and more!
"""


# =============================================================
# INSTALLATION INSTRUCTIONS
# =============================================================

"""
ADD TO main.py:

# At top of file with other imports:
from actionization_routes import router as actionization_router

# After app = FastAPI():
app.include_router(actionization_router)

DONE! Now you have:
- POST /actionize/deploy - Main deployment endpoint
- POST /actionize - Legacy endpoint (backwards compatible)
- GET /actionize/status/{username} - Check deployment status
"""
