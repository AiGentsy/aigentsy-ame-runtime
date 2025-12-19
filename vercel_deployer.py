"""
Vercel Deployer
Deploys websites to Vercel with custom subdomains

Supports:
- SaaS: Developer portal with API docs
- Marketing: Landing pages with forms
- Social: Creator hub with content calendar
"""

import os
import httpx
from typing import Dict, Any
from datetime import datetime, timezone


VERCEL_API_TOKEN = os.getenv("VERCEL_API_TOKEN")
VERCEL_TEAM_ID = os.getenv("VERCEL_TEAM_ID")
AIGENTSY_DOMAIN = "aigentsy.com"


def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


# Website templates for each type
WEBSITE_TEMPLATES = {
    "saas": {
        "name": "SaaS API Portal",
        "framework": "nextjs",
        "build_command": "npm run build",
        "output_directory": ".next",
        "install_command": "npm install",
        "dev_command": "npm run dev"
    },
    "marketing": {
        "name": "Marketing Landing Pages",
        "framework": "html",
        "build_command": None,  # Static HTML
        "output_directory": "public",
        "install_command": None,
        "dev_command": None
    },
    "social": {
        "name": "Creator Hub",
        "framework": "nextjs",
        "build_command": "npm run build",
        "output_directory": ".next",
        "install_command": "npm install",
        "dev_command": "npm run dev"
    }
}


async def deploy_to_vercel(
    username: str,
    template_type: str,
    config: Dict[str, Any],
    user_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deploy website to Vercel with custom subdomain
    
    Steps:
    1. Create Vercel project
    2. Configure subdomain: {username}.aigentsy.com
    3. Deploy website files
    4. Set environment variables
    5. Return deployment URL
    
    Args:
        username: User's username (becomes subdomain)
        template_type: "saas" | "marketing" | "social"
        config: Template configuration
        user_data: User profile data
        
    Returns:
        {
            "ok": True,
            "url": "https://{username}.aigentsy.com",
            "project_id": "...",
            "deployment_id": "...",
            "admin_url": "https://{username}.aigentsy.com/admin"
        }
    """
    
    print(f"📦 Deploying {template_type} website for {username}...")
    
    # Check if Vercel is configured
    if not VERCEL_API_TOKEN:
        print("⚠️  Vercel API token not configured - using mock deployment")
        return await _mock_deployment(username, template_type, config)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "Authorization": f"Bearer {VERCEL_API_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # Step 1: Create project
            project_name = f"aigentsy-{username}-{template_type}"
            
            project_payload = {
                "name": project_name,
                "framework": WEBSITE_TEMPLATES[template_type]["framework"],
                "gitRepository": None,  # We'll deploy directly
                "environmentVariables": [
                    {"key": "USERNAME", "value": username, "target": ["production"]},
                    {"key": "TEMPLATE_TYPE", "value": template_type, "target": ["production"]},
                    {"key": "AIGENTSY_USER_ID", "value": user_data.get("id", ""), "target": ["production"]}
                ]
            }
            
            if VERCEL_TEAM_ID:
                project_payload["teamId"] = VERCEL_TEAM_ID
            
            # Create project
            response = await client.post(
                "https://api.vercel.com/v9/projects",
                headers=headers,
                json=project_payload
            )
            
            if response.status_code not in [200, 201]:
                # Project might already exist - try to get it
                existing = await client.get(
                    f"https://api.vercel.com/v9/projects/{project_name}",
                    headers=headers
                )
                
                if existing.status_code == 200:
                    project_data = existing.json()
                else:
                    return {
                        "ok": False,
                        "error": f"Failed to create Vercel project: {response.status_code}",
                        "details": response.text
                    }
            else:
                project_data = response.json()
            
            project_id = project_data.get("id")
            
            # Step 2: Configure custom domain
            subdomain = f"{username}.{AIGENTSY_DOMAIN}"
            
            domain_payload = {
                "name": subdomain
            }
            
            if VERCEL_TEAM_ID:
                domain_payload["teamId"] = VERCEL_TEAM_ID
            
            domain_response = await client.post(
                f"https://api.vercel.com/v10/projects/{project_id}/domains",
                headers=headers,
                json=domain_payload
            )
            
            # Domain might already exist - that's okay
            if domain_response.status_code not in [200, 201, 409]:
                print(f"⚠️  Domain configuration warning: {domain_response.status_code}")
            
            # Step 3: Deploy website files
            # For now, we'll create a deployment pointing to our template repo
            # TODO: Generate actual website files from templates
            
            deployment_payload = {
                "name": project_name,
                "project": project_id,
                "target": "production",
                "gitSource": None,  # Direct deployment
                "files": await _generate_website_files(template_type, username, user_data)
            }
            
            if VERCEL_TEAM_ID:
                deployment_payload["teamId"] = VERCEL_TEAM_ID
            
            deploy_response = await client.post(
                "https://api.vercel.com/v13/deployments",
                headers=headers,
                json=deployment_payload
            )
            
            if deploy_response.status_code not in [200, 201]:
                return {
                    "ok": False,
                    "error": f"Deployment failed: {deploy_response.status_code}",
                    "details": deploy_response.text
                }
            
            deployment_data = deploy_response.json()
            deployment_url = deployment_data.get("url", f"https://{subdomain}")
            
            return {
                "ok": True,
                "url": f"https://{subdomain}",
                "vercel_url": deployment_url,
                "project_id": project_id,
                "deployment_id": deployment_data.get("id"),
                "admin_url": f"https://{subdomain}/admin",
                "deployed_at": now_iso()
            }
            
    except Exception as e:
        print(f"❌ Vercel deployment error: {e}")
        return {
            "ok": False,
            "error": str(e)
        }


async def _generate_website_files(
    template_type: str,
    username: str,
    user_data: Dict[str, Any]
) -> list:
    """
    Generate website files for deployment
    
    Returns array of file objects for Vercel API
    """
    
    files = []
    
    if template_type == "marketing":
        # Generate marketing landing page
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{username}'s Marketing Business | Powered by AiGentsy</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; }}
        h1 {{ color: #00bfff; }}
        .cta {{ background: #00bfff; color: white; padding: 12px 24px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to {username}'s Marketing Business</h1>
        <p>Your autonomous marketing business is now live!</p>
        <p>This is powered by AiGentsy and deployed automatically.</p>
        <button class="cta">Get Started</button>
    </div>
</body>
</html>"""
        
        files.append({
            "file": "index.html",
            "data": index_html
        })
    
    elif template_type == "saas":
        # Generate SaaS developer portal
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{username}'s API | Developer Portal</title>
    <style>
        body {{ font-family: monospace; margin: 0; padding: 40px; background: #1a1a1a; color: #fff; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #00bfff; }}
        code {{ background: #2a2a2a; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{username}'s API Documentation</h1>
        <p>Your autonomous SaaS business is now live!</p>
        <p>Base URL: <code>https://{username}.aigentsy.com/api</code></p>
        <p>Powered by AiGentsy</p>
    </div>
</body>
</html>"""
        
        files.append({
            "file": "index.html",
            "data": index_html
        })
    
    elif template_type == "social":
        # Generate social creator hub
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{username}'s Creator Hub | Powered by AiGentsy</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ font-size: 3rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>@{username}</h1>
        <p>Your autonomous social media business is now live!</p>
        <p>Content calendar, engagement tools, and growth system activated.</p>
        <p>Powered by AiGentsy</p>
    </div>
</body>
</html>"""
        
        files.append({
            "file": "index.html",
            "data": index_html
        })
    
    return files


async def _mock_deployment(
    username: str,
    template_type: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mock deployment for testing without Vercel API
    """
    
    subdomain = f"{username}.{AIGENTSY_DOMAIN}"
    
    print(f"✅ Mock deployment: https://{subdomain}")
    
    return {
        "ok": True,
        "url": f"https://{subdomain}",
        "vercel_url": f"https://{subdomain}",
        "project_id": f"mock_{username}_{template_type}",
        "deployment_id": f"dpl_mock_{username}",
        "admin_url": f"https://{subdomain}/admin",
        "deployed_at": now_iso(),
        "mock": True
    }


async def delete_deployment(project_id: str) -> Dict[str, Any]:
    """Delete a Vercel project (rollback)"""
    
    if not VERCEL_API_TOKEN:
        return {"ok": True, "mock": True, "message": "Mock deletion"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Authorization": f"Bearer {VERCEL_API_TOKEN}"}
            
            url = f"https://api.vercel.com/v9/projects/{project_id}"
            if VERCEL_TEAM_ID:
                url += f"?teamId={VERCEL_TEAM_ID}"
            
            response = await client.delete(url, headers=headers)
            
            if response.status_code in [200, 204]:
                return {"ok": True, "deleted": True}
            else:
                return {
                    "ok": False,
                    "error": f"Deletion failed: {response.status_code}"
                }
                
    except Exception as e:
        return {"ok": False, "error": str(e)}
      
